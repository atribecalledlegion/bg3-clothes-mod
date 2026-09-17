import struct
from lspk import lz4_block_decompress

TYPES = {0:'None',1:'Byte',2:'Short',3:'UShort',4:'Int',5:'UInt',6:'Float',7:'Double',
 8:'IVec2',9:'IVec3',10:'IVec4',11:'Vec2',12:'Vec3',13:'Vec4',14:'Mat2',15:'Mat3',
 16:'Mat3x4',17:'Mat4x3',18:'Mat4',19:'Bool',20:'String',21:'Path',22:'FixedString',
 23:'LSString',24:'ULongLong',25:'ScratchBuffer',26:'Long',27:'Int8',
 28:'TranslatedString',29:'WString',30:'LSWString',31:'UUID',32:'Int64',33:'TranslatedFSString'}
STR_T = {20,21,22,23,29,30}

def guid(b):
    """Format a 16-byte UUID the way LSLib does.

    The first three fields are little-endian (.NET Guid layout), and the last 8 bytes
    additionally get their 16-bit words swapped -- LSLib advertises this as bswap_guids
    in the lslib_meta of every .lsx it writes.

    This must match LSLib exactly. Reading a guid one way and handing the string back to
    Divine to re-encode writes DIFFERENT bytes than the original, which silently breaks
    every reference keyed by that UUID."""
    a, c, d = struct.unpack_from('<IHH', b, 0)
    t = bytes([b[9], b[8], b[11], b[10], b[13], b[12], b[15], b[14]])
    return '%08x-%04x-%04x-%s-%s' % (a, c, d, t[:2].hex(), t[2:].hex())

class LSF:
    def __init__(self, data):
        magic, ver = struct.unpack_from('<4sI', data, 0)
        assert magic == b'LSOF', magic
        self.ver = ver
        o = 8 + (8 if ver >= 5 else 4)
        m = struct.unpack_from('<10I', data, o); o += 40
        cflags = data[o]; o += 4
        self.extended = struct.unpack_from('<I', data, o)[0]; o += 4
        strU,strD, keyU,keyD, nodU,nodD, attU,attD, valU,valD = m
        def blk(unc, disk):
            nonlocal o
            if disk == 0:
                b = data[o:o+unc]; o += unc
            else:
                raw = data[o:o+disk]; o += disk
                meth = cflags & 0x0F
                import zlib
                b = lz4_block_decompress(raw, unc) if meth == 2 else (zlib.decompress(raw) if meth == 1 else raw)
            return b
        sb = blk(strU, strD); blk(keyU, keyD)
        nb = blk(nodU, nodD); ab = blk(attU, attD); self.vb = blk(valU, valD)

        self.names = []
        p = 0
        (nh,) = struct.unpack_from('<I', sb, p); p += 4
        for _ in range(nh):
            (ns,) = struct.unpack_from('<H', sb, p); p += 2
            row = []
            for _ in range(ns):
                (ln,) = struct.unpack_from('<H', sb, p); p += 2
                row.append(sb[p:p+ln].decode('utf-8','replace')); p += ln
            self.names.append(row)
        self.nm = lambda i: self.names[i >> 16][i & 0xFFFF]

        # V2 node = (NameHashTableIndex u32, FirstAttributeIndex i32, ParentIndex i32).
        # ParentIndex is SIGNED: root nodes carry -1, and reading it unsigned turns
        # every region root into 0xFFFFFFFF and hides the region layer entirely.
        self.nodes = [struct.unpack_from('<Iii', nb, p) for p in range(0, len(nb), 12)]
        self.byNode = {}
        off = 0
        self.attrs = []
        for p in range(0, len(ab), 12):
            ni, tl, node = struct.unpack_from('<IIi', ab, p)
            t, ln = tl & 0x3F, tl >> 6
            self.attrs.append((ni, t, ln, off, node))
            self.byNode.setdefault(node, []).append(len(self.attrs) - 1)
            off += ln

    def value(self, t, ln, off):
        v = self.vb
        if t in STR_T: return v[off:off+ln].split(b'\0')[0].decode('utf-8','replace')
        if t == 31: return guid(v[off:off+16])
        if t == 19: return bool(v[off])
        if t == 4:  return struct.unpack_from('<i', v, off)[0]
        if t == 5:  return struct.unpack_from('<I', v, off)[0]
        if t == 6:  return struct.unpack_from('<f', v, off)[0]
        if t in (1, 27): return v[off]
        if t == 28:
            n = struct.unpack_from('<i', v, off+2)[0]
            return v[off+6:off+6+n].decode('utf-8','replace')
        if t in (11,12,13):
            n = {11:2,12:3,13:4}[t]
            return struct.unpack_from('<%df'%n, v, off)
        return v[off:off+ln].hex()

    def node_attrs(self, i):
        out = {}
        for ai in self.byNode.get(i, []):
            ni, t, ln, off, node = self.attrs[ai]
            out[self.nm(ni)] = (TYPES.get(t, t), self.value(t, ln, off))
        return out

    def node_attrs_raw(self, i):
        """Same as node_attrs but also returns the raw value bytes, which ScratchBuffer
        (binary blobs such as cloth proxy mappings) needs in order to round-trip."""
        out = {}
        for ai in self.byNode.get(i, []):
            ni, t, ln, off, node = self.attrs[ai]
            out[self.nm(ni)] = (TYPES.get(t, t), self.value(t, ln, off), self.vb[off:off+ln])
        return out

    def node_name(self, i): return self.nm(self.nodes[i][0])
    def parent(self, i):    return self.nodes[i][2]

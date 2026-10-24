"""Minimal Skyrim NIF (20.2.0.7; BS version 83 = LE, 100 = SE) reader/writer: split into header and blocks, edit blocks, write back.

Block sizes live in the header's block size table, so a block may grow or shrink (e.g. a texture path swapped for a
longer one) and write() rewrites the table.
"""
import struct


class Nif:
    def __init__(self, path):
        d = open(path, 'rb').read()
        o = d.index(b'\n') + 1
        ver, _endian, _user, nblocks, bsver = struct.unpack_from('<IBIII', d, o); o += 17
        assert ver == 0x14020007 and bsver in (83, 100), (hex(ver), bsver)    # Skyrim LE or SE
        self.bsver = bsver
        for _ in range(3):                  # author, process script, export script
            o += 1 + d[o]
        ntypes = struct.unpack_from('<H', d, o)[0]; o += 2
        self.types = []
        for _ in range(ntypes):
            n = struct.unpack_from('<I', d, o)[0]; self.types.append(d[o+4:o+4+n].decode('latin1')); o += 4 + n
        self.type_idx = struct.unpack_from('<%dH' % nblocks, d, o); o += 2 * nblocks
        self.sizes_at = o
        sizes = struct.unpack_from('<%dI' % nblocks, d, o); o += 4 * nblocks
        nstr = struct.unpack_from('<I', d, o)[0]; o += 8
        for _ in range(nstr):
            o += 4 + struct.unpack_from('<I', d, o)[0]
        o += 4 + 4 * struct.unpack_from('<I', d, o)[0]
        self.head = bytearray(d[:o])
        self.blocks = []
        for s in sizes:
            self.blocks.append(bytearray(d[o:o+s])); o += s
        self.tail = d[o:]

    def type_of(self, i):
        return self.types[self.type_idx[i] & 0x7FFF]

    def of_type(self, name):
        return [i for i in range(len(self.blocks)) if self.type_of(i) == name]

    def swap_string(self, i, old, new):
        """Replace a sized string (uint32 length + text) inside block i. Returns how many were replaced."""
        b = self.blocks[i]
        key = struct.pack('<I', len(old)) + old
        n = b.count(key)
        if n:
            self.blocks[i] = bytearray(b.replace(key, struct.pack('<I', len(new)) + new))
        return n

    def write(self, path):
        head = bytearray(self.head)
        struct.pack_into('<%dI' % len(self.blocks), head, self.sizes_at, *[len(b) for b in self.blocks])
        open(path, 'wb').write(bytes(head) + b''.join(bytes(b) for b in self.blocks) + self.tail)


def lighting_emissive_offset(b):
    """BSLightingShaderProperty: shader type, NiObjectNET (name, extra data list, controller), flags 1/2,
    UV offset/scale, texture set ref, then the emissive colour (3 f) and emissive multiple (f)."""
    p = 4 + 4
    p += 4 + 4 * struct.unpack_from('<I', b, p)[0]
    p += 4 + 8 + 16 + 4
    return p


def effect_emissive_offset(b):
    """BSEffectShaderProperty: NiObjectNET, flags 1/2, UV offset/scale, source texture (sized string), 4 bytes,
    falloff angles/opacities (4 f), then the emissive colour (4 f) and emissive multiple (f)."""
    p = 4
    p += 4 + 4 * struct.unpack_from('<I', b, p)[0]
    p += 4 + 8 + 16
    p += 4 + struct.unpack_from('<I', b, p)[0]
    p += 4 + 16
    return p

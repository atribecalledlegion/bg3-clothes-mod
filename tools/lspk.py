import struct, sys, zlib, os

def lz4_block_decompress(src, out_size):
    dst = bytearray(out_size)
    d = 0; i = 0; n = len(src)
    while i < n:
        tok = src[i]; i += 1
        ll = tok >> 4
        if ll == 15:
            while True:
                b = src[i]; i += 1; ll += b
                if b != 255: break
        if ll:
            dst[d:d+ll] = src[i:i+ll]; i += ll; d += ll
        if i >= n: break
        off = src[i] | (src[i+1] << 8); i += 2
        ml = tok & 0xF
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        s = d - off
        if off >= ml:
            dst[d:d+ml] = dst[s:s+ml]; d += ml
        else:
            for k in range(ml):
                dst[d] = dst[s+k]; d += 1
    return bytes(dst[:d])

class Pak:
    def __init__(self, path):
        self.path = path
        f = open(path, 'rb'); self.f = f
        magic, ver = struct.unpack('<4sI', f.read(8))
        assert magic == b'LSPK', magic
        self.ver = ver
        flo, fls = struct.unpack('<QI', f.read(12))
        f.seek(flo)
        num, csize = struct.unpack('<II', f.read(8))
        comp = f.read(csize)
        raw = lz4_block_decompress(comp, num * 272)
        self.entries = {}
        for k in range(num):
            b = raw[k*272:(k+1)*272]
            name = b[:256].split(b'\0')[0].decode('utf-8', 'replace')
            o1, o2, part, flags, sod, uns = struct.unpack('<IHBBII', b[256:272])
            self.entries[name] = (o1 | (o2 << 32), part, flags, sod, uns)

    def read(self, name):
        off, part, flags, sod, uns = self.entries[name]
        p = self.path
        if part != 0:
            p = p[:-4] + '_%d.pak' % part
        with open(p, 'rb') as g:
            g.seek(off); data = g.read(sod)
        m = flags & 0x0F
        if m == 0: return data
        if m == 1: return zlib.decompress(data)
        if m == 2: return lz4_block_decompress(data, uns)
        raise ValueError('method %d' % m)

if __name__ == '__main__':
    pak = Pak(sys.argv[1])
    pats = [a.lower() for a in sys.argv[2:]]
    hits = [n for n in pak.entries if all(p in n.lower() for p in pats)] if pats else list(pak.entries)
    print('%d files, %d matches' % (len(pak.entries), len(hits)))
    for h in sorted(hits)[:120]:
        print(' ', h)

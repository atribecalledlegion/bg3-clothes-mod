"""Minimal Skyrim SE BSA (v105) reader: list and extract files (pure Python, LZ4 frame decoding included).
Usage: bsa.py list archive.bsa [filter]
       bsa.py extract archive.bsa out_dir path_regex"""
import os, re, struct, sys

def lz4_block(src, dst):
    i = 0; n = len(src)
    while i < n:
        token = src[i]; i += 1
        lit = token >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1; lit += b
                if b != 255: break
        dst += src[i:i+lit]; i += lit
        if i >= n: break
        off = src[i] | (src[i+1] << 8); i += 2
        ml = token & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        start = len(dst) - off
        if off >= ml:
            dst += dst[start:start+ml]
        else:
            for k in range(ml): dst.append(dst[start + k])
    return dst

def lz4_frame(data):
    assert struct.unpack_from('<I', data, 0)[0] == 0x184D2204, 'not an LZ4 frame'
    flg = data[4]; i = 6
    if flg & 0x08: i += 8                      # content size
    if flg & 0x01: i += 4                      # dict id
    i += 1                                     # header checksum
    out = bytearray()
    while True:
        bs = struct.unpack_from('<I', data, i)[0]; i += 4
        if bs == 0: break
        raw = bs & 0x80000000; bs &= 0x7FFFFFFF
        if raw: out += data[i:i+bs]
        else: lz4_block(data[i:i+bs], out)
        i += bs
        if flg & 0x10: i += 4                  # block checksum
    return bytes(out)

def entries(path):
    b = open(path, 'rb').read()
    magic, ver, off, aflags, nfold, nfile, lfold, lfile, fflags = struct.unpack_from('<4sIIIIIIIH', b, 0)
    assert magic == b'BSA\0' and ver == 105, (magic, ver)
    p = off
    folders = []
    for _ in range(nfold):
        h, cnt, pad, foff = struct.unpack_from('<QIIQ', b, p); p += 24; folders.append(cnt)
    recs = []
    for cnt in folders:
        name = ''
        if aflags & 0x1:
            ln = b[p]; name = b[p+1:p+ln].decode('latin1'); p += 1 + ln
        for _ in range(cnt):
            h, size, foff = struct.unpack_from('<QII', b, p); p += 16
            recs.append([name, size, foff])
    if aflags & 0x2:
        for r in recs:
            e = b.index(b'\0', p); r.append(b[p:e].decode('latin1')); p = e + 1
    out = []
    for folder, size, foff, fname in recs:
        out.append((folder + '\\' + fname, size, foff))
    return b, aflags, out

def read_file(b, aflags, size, foff):
    comp = bool(aflags & 0x4) ^ bool(size & 0x40000000)
    size &= 0x3FFFFFFF
    p = foff
    if aflags & 0x100:
        ln = b[p]; p += 1 + ln; size -= 1 + ln
    if comp:
        orig = struct.unpack_from('<I', b, p)[0]
        data = lz4_frame(b[p+4:p+size])
        assert len(data) == orig, (len(data), orig)
        return data
    return b[p:p+size]

if __name__ == '__main__':
    cmd, arc = sys.argv[1], sys.argv[2]
    b, aflags, ents = entries(arc)
    if cmd == 'list':
        rx = re.compile(sys.argv[3], re.I) if len(sys.argv) > 3 else None
        for name, size, foff in ents:
            if not rx or rx.search(name): print(name, size & 0x3FFFFFFF)
    elif cmd == 'extract':
        out, rx = sys.argv[3], re.compile(sys.argv[4], re.I)
        for name, size, foff in ents:
            if rx.search(name):
                dst = os.path.join(out, *name.split('\\'))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, 'wb').write(read_file(b, aflags, size, foff)); print('extracted', name)

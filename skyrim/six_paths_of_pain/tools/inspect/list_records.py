"""List records (type, FormID, EDID, FULL) in a Skyrim SE plugin. Usage: list_records.py plugin [TYPES,...]"""
import struct, sys, zlib

def subrecords(data):
    i = 0
    big = None
    while i + 6 <= len(data):
        t = data[i:i+4].decode('latin1'); sz = struct.unpack_from('<H', data, i+4)[0]; i += 6
        if t == 'XXXX':
            big = struct.unpack_from('<I', data, i)[0]; i += sz; continue
        if big is not None: sz, big = big, None
        yield t, data[i:i+sz]; i += sz

def walk(buf, off, end, out, want):
    while off < end:
        t = buf[off:off+4].decode('latin1'); sz = struct.unpack_from('<I', buf, off+4)[0]
        if t == 'GRUP':
            walk(buf, off+24, off+sz, out, want); off += sz; continue
        flags, fid = struct.unpack_from('<II', buf, off+8)
        body = buf[off+24:off+24+sz]; off += 24 + sz
        if want and t not in want: continue
        if flags & 0x40000:
            try: body = zlib.decompress(body[4:])
            except Exception: continue
        edid = full = ''; extra = []
        for st, sd in subrecords(body):
            if st == 'EDID': edid = sd.rstrip(b'\0').decode('latin1')
            elif st == 'FULL' and len(sd) > 4: full = sd.rstrip(b'\0').decode('latin1', 'replace')
            elif st in ('MODL', 'MOD2', 'MOD3', 'MOD4') : extra.append(sd.rstrip(b'\0').decode('latin1'))
            elif st == 'VMAD':
                # script names: crude scan
                n = struct.unpack_from('<H', sd, 4)[0]; j = 6
                for _ in range(n):
                    l = struct.unpack_from('<H', sd, j)[0]; extra.append('script:' + sd[j+2:j+2+l].decode('latin1')); break
        out.append((t, fid, edid, full, extra))

buf = open(sys.argv[1], 'rb').read()
want = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
hsz = struct.unpack_from('<I', buf, 4)[0]
masters = [sd.rstrip(b'\0').decode() for st, sd in subrecords(buf[24:24+hsz]) if st == 'MAST']
print('masters:', masters)
out = []
walk(buf, 24 + hsz, len(buf), out, want)
for t, fid, edid, full, extra in out:
    print(f'{t} {fid:08X} {edid} | {full} | {" ".join(extra[:2])}')

"""List ARMO records of a plugin with biped slots and their ARMA male/female world models.
Usage: armor_list.py plugin.esp [name filter regex]"""
import re, struct, sys, zlib
exec(open(__file__.replace('armor_list.py', 'list_records.py')).read().split("buf = open")[0])

buf = open(sys.argv[1], 'rb').read(); hsz = struct.unpack_from('<I', buf, 4)[0]
flt = re.compile(sys.argv[2], re.I) if len(sys.argv) > 2 else None
recs = {}
def w(o, e):
    while o < e:
        t = buf[o:o+4]; n = struct.unpack_from('<I', buf, o+4)[0]
        if t == b'GRUP': w(o+24, o+n); o += n; continue
        fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
        if t not in (b'ARMO', b'ARMA'): continue
        if fl & 0x40000: b = zlib.decompress(b[4:])
        recs[fid & 0xFFFFFF] = (t.decode(), fid, fl, list(subrecords(b)))
w(24 + hsz, len(buf))

def slots(mask):
    return [30 + i for i in range(32) if mask >> i & 1]

for oid, (t, fid, fl, s) in sorted(recs.items(), key=lambda x: x[0]):
    if t != 'ARMO': continue
    d = dict(s); ed = d.get('EDID', b'').rstrip(b'\0').decode('latin1')
    full = d.get('FULL', b'').rstrip(b'\0').decode('latin1', 'replace')
    if flt and not (flt.search(ed) or flt.search(full)): continue
    mask = struct.unpack_from('<I', d['BOD2'])[0] if 'BOD2' in d else None
    arma = [struct.unpack('<I', v)[0] for k, v in s if k == 'MODL' and len(v) == 4]
    models = []
    for a in arma:
        r = recs.get(a & 0xFFFFFF)
        if not r: models.append(f'ext:{a:08X}'); continue
        ad = dict(r[3])
        m = ad.get('MOD2', b'').rstrip(b'\0').decode('latin1'); f = ad.get('MOD3', b'').rstrip(b'\0').decode('latin1')
        models.append(f'M={m.split(chr(92))[-1] or "-"} F={f.split(chr(92))[-1] or "-"}')
    np = ' nonplayable' if fl & 0x4 else ''
    print(f'{fid:08X} {ed} | {full} | slots {slots(mask) if mask is not None else "?"}{np} | {"; ".join(models)}')

import struct, sys, zlib, re
sys.argv += []
exec(open('list_records.py').read().split("buf = open")[0])
def recs(path):
    buf=open(path,'rb').read(); hsz=struct.unpack_from('<I',buf,4)[0]; res={}
    def w(o,e):
        while o<e:
            t=buf[o:o+4].decode('latin1'); sz=struct.unpack_from('<I',buf,o+4)[0]
            if t=='GRUP': w(o+24,o+sz); o+=sz; continue
            fl,fid=struct.unpack_from('<II',buf,o+8); b=buf[o+24:o+24+sz]; o+=24+sz
            if t not in('SPEL','MGEF'): continue
            if fl&0x40000: b=zlib.decompress(b[4:])
            res[fid&0xFFFFFF]=(t,list(subrecords(b)))
    w(24+hsz,len(buf)); return res
R={}
for p in sys.argv[1:3]: 
    for k,v in recs(p).items(): R.setdefault(k,v)
pat=re.compile(sys.argv[3],re.I)
for fid,(t,subs) in R.items():
    if t!='SPEL': continue
    d=dict((a,b) for a,b in subs); edid=d.get('EDID',b'').rstrip(b'\0').decode()
    if not pat.search(edid): continue
    out=[]
    for a,b in subs:
        if a=='EFID':
            m=struct.unpack('<I',b)[0]&0xFFFFFF; mt=R.get(m)
            if not mt: out.append(f'{m:06X}(ext)'); continue
            md=dict(mt[1]); me=md.get('EDID',b'').rstrip(b'\0').decode()
            sc=''
            if 'VMAD' in md:
                v=md['VMAD']; l=struct.unpack_from('<H',v,6)[0]; sc=v[8:8+l].decode('latin1')
            dn=md.get('DATA',b'\0'*0x44); arch=struct.unpack_from('<I',dn,0x40)[0] if len(dn)>0x44 else -1
            out.append(f'{me}[arch{arch}{" script:"+sc if sc else ""}]')
    print(edid,'->',', '.join(out))

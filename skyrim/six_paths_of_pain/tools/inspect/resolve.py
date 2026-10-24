import struct,sys,zlib
exec(open('list_records.py').read().split("buf = open")[0])
files=sys.argv[1].split('|'); want=[int(x,16) for x in sys.argv[2:]]
for w_ in want:
    idx=w_>>24; path=files[idx]; buf=open(path,'rb').read(); hsz=struct.unpack_from('<I',buf,4)[0]
    found=[]
    def w(o,e):
        while o<e:
            t=buf[o:o+4].decode('latin1'); sz=struct.unpack_from('<I',buf,o+4)[0]
            if t=='GRUP': w(o+24,o+sz); o+=sz; continue
            fl,fid=struct.unpack_from('<II',buf,o+8); b=buf[o+24:o+24+sz]; o+=24+sz
            if fid & 0xFFFFFF == w_ & 0xFFFFFF:
                if fl&0x40000: b=zlib.decompress(b[4:])
                found.append((t,dict(subrecords(b)).get('EDID',b'').rstrip(b'\0').decode('latin1'),hex(fid)))
    w(24+hsz,len(buf)); print(hex(w_), path.split('/')[-1], found)

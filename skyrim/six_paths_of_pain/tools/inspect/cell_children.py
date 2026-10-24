import struct,sys,zlib
exec(open('list_records.py').read().split("buf = open")[0])
buf=open(sys.argv[1],'rb').read(); target=int(sys.argv[2],16); hsz=struct.unpack_from('<I',buf,4)[0]
def recs(o,e,depth,path):
    while o<e:
        t=buf[o:o+4].decode('latin1'); sz=struct.unpack_from('<I',buf,o+4)[0]
        if t=='GRUP':
            label,gt=struct.unpack_from('<II',buf,o+8)
            if gt in (6,8,9,10) and label==target:
                print('GROUP type',gt,'size',sz)
                inner(o+24,o+sz)
            else: recs(o+24,o+sz,depth+1,path)
            o+=sz; continue
        fl,fid=struct.unpack_from('<II',buf,o+8)
        if fid==target:
            b=buf[o+24:o+24+sz]
            if fl&0x40000: b=zlib.decompress(b[4:])
            print('CELL flags',hex(fl)); [print('  ',k,len(v),v.hex()[:100]) for k,v in subrecords(b)]
        o+=24+sz
def inner(o,e):
    while o<e:
        t=buf[o:o+4].decode('latin1'); sz=struct.unpack_from('<I',buf,o+4)[0]
        if t=='GRUP':
            print(' subgroup type',struct.unpack_from('<I',buf,o+12)[0]); inner(o+24,o+sz); o+=sz; continue
        fl,fid=struct.unpack_from('<II',buf,o+8); b=buf[o+24:o+24+sz]
        if fl&0x40000: b=zlib.decompress(b[4:])
        d=dict(subrecords(b)); base=struct.unpack('<I',d['NAME'])[0] if 'NAME' in d else 0
        pos=struct.unpack('<6f',d['DATA']) if 'DATA' in d and len(d['DATA'])==24 else None
        print('  ',t,hex(fid),hex(fl),d.get('EDID',b'').rstrip(b'\0').decode('latin1'),'base',hex(base),[round(x,1) for x in pos] if pos else '')
        o+=24+sz
recs(24+hsz,len(buf),0,'')

import struct,sys,zlib
exec(open('list_records.py').read().split("buf = open")[0])
buf=open(sys.argv[1],'rb').read(); hsz=struct.unpack_from('<I',buf,4)[0]; names=set(sys.argv[2].split(','))
def w(o,e):
    while o<e:
        t=buf[o:o+4].decode('latin1'); sz=struct.unpack_from('<I',buf,o+4)[0]
        if t=='GRUP': w(o+24,o+sz); o+=sz; continue
        fl,fid,vc,ver=struct.unpack_from('<IIIH',buf,o+8); b=buf[o+24:o+24+sz]; o+=24+sz
        if fl&0x40000: b=zlib.decompress(b[4:])
        s=list(subrecords(b)); ed=dict(s).get('EDID',b'').rstrip(b'\0').decode('latin1')
        if ed in names or (t in names and len([1 for _ in [0]])): 
            if ed in names:
                print(t,hex(fid),'flags',hex(fl),'ver',ver); [print('  ',k,len(v),v.hex()) for k,v in s]
w(24+hsz,len(buf))

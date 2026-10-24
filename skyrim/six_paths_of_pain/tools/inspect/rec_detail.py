import struct,sys,zlib
exec(open('list_records.py').read().split("buf = open")[0])
buf=open(sys.argv[1],'rb').read(); hsz=struct.unpack_from('<I',buf,4)[0]; names=set(sys.argv[2].split(','))
def w(o,e):
    while o<e:
        t=buf[o:o+4].decode('latin1'); sz=struct.unpack_from('<I',buf,o+4)[0]
        if t=='GRUP': w(o+24,o+sz); o+=sz; continue
        fl,fid=struct.unpack_from('<II',buf,o+8); b=buf[o+24:o+24+sz]; o+=24+sz
        if fl&0x40000: b=zlib.decompress(b[4:])
        s=list(subrecords(b)); d=dict(s); ed=d.get('EDID',b'').rstrip(b'\0').decode('latin1')
        if ed not in names: continue
        info={}
        if t=='CSTY': info['CSGD']=[round(x,2) for x in struct.unpack_from('<10f',d['CSGD'])]; info['DATA']=d.get('DATA',b'').hex(); info['CSME']=[round(x,2) for x in struct.unpack_from('<%df'%(len(d.get('CSME',b''))//4),d.get('CSME',b''))]; info['CSCR']=[round(x,2) for x in struct.unpack_from('<%df'%(len(d.get('CSCR',b''))//4),d.get('CSCR',b''))]
        if t=='ARMO': info['BOD2']=hex(struct.unpack_from('<I',d['BOD2'])[0]) if 'BOD2' in d else None; info['EITM']=d.get('EITM',b'').hex(); info['ARMA']=[hex(struct.unpack('<I',v)[0]) for k,v in s if k=='MODL' and len(v)==4]; info['KW']=d.get('KWDA',b'').hex()[:80]
        if t=='MGEF': dd=d['DATA']; info['flags']=hex(struct.unpack_from('<I',dd,0)[0]); info['arch']=struct.unpack_from('<I',dd,0x40)[0]; info['av']=struct.unpack_from('<i',dd,0x44)[0]
        print(t,hex(fid),ed,info)
w(24+hsz,len(buf))

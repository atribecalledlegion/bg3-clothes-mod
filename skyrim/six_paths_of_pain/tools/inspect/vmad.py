import struct,sys,zlib
exec(open('list_records.py').read().split("buf = open")[0])
class R:
    def __init__(s,b): s.b=b; s.o=0
    def u8(s): v=s.b[s.o]; s.o+=1; return v
    def u16(s): v=struct.unpack_from('<H',s.b,s.o)[0]; s.o+=2; return v
    def i16(s): v=struct.unpack_from('<h',s.b,s.o)[0]; s.o+=2; return v
    def u32(s): v=struct.unpack_from('<I',s.b,s.o)[0]; s.o+=4; return v
    def i32(s): v=struct.unpack_from('<i',s.b,s.o)[0]; s.o+=4; return v
    def f(s): v=struct.unpack_from('<f',s.b,s.o)[0]; s.o+=4; return v
    def ws(s): n=s.u16(); v=s.b[s.o:s.o+n].decode('latin1'); s.o+=n; return v
def obj(r,fmt):
    if fmt==2: r.u16(); a=r.i16(); fid=r.u32()
    else: fid=r.u32(); a=r.i16(); r.u16()
    return ('obj',hex(fid),a)
def val(r,t,fmt):
    if t==1: return obj(r,fmt)
    if t==2: return r.ws()
    if t==3: return r.i32()
    if t==4: return r.f()
    if t==5: return r.u8()
    if t>=11: n=r.u32(); return [val(r,t-10,fmt) for _ in range(n)]
def scripts(r,ver,fmt,ind):
    n=r.u16()
    for _ in range(n):
        name=r.ws(); st=r.u8(); np=r.u16(); print(ind,'script',name,'status',st)
        for _ in range(np):
            pn=r.ws(); pt=r.u8(); ps=r.u8(); print(ind,'  ',pn,'type',pt,'status',ps,val(r,pt,fmt))
def parse(b,rtype):
    r=R(b); ver=r.i16(); fmt=r.i16(); print('ver',ver,'fmt',fmt); scripts(r,ver,fmt,'')
    if rtype=='QUST':
        print('frag section at',r.o,'rest',b[r.o:r.o+16].hex())
        unk=r.u8(); nfrag=r.u16(); fn=r.ws(); print('unk',unk,'nfrag',nfrag,'file',fn)
        for _ in range(nfrag): idx=r.u16(); r.u16(); li=r.i32(); r.u8(); sn=r.ws(); fnm=r.ws(); print(' frag',idx,li,sn,fnm)
        na=r.u16(); print('aliases',na)
        for _ in range(na): o=obj(r,fmt); v=r.i16(); f2=r.i16(); print(' alias',o,'ver',v,'fmt',f2); scripts(r,v,f2,'   ')
    print('consumed',r.o,'of',len(b))
buf=open(sys.argv[1],'rb').read(); hsz=struct.unpack_from('<I',buf,4)[0]; target=sys.argv[2]
def w(o,e):
    while o<e:
        t=buf[o:o+4].decode('latin1'); sz=struct.unpack_from('<I',buf,o+4)[0]
        if t=='GRUP': w(o+24,o+sz); o+=sz; continue
        fl,fid=struct.unpack_from('<II',buf,o+8); b=buf[o+24:o+24+sz]; o+=24+sz
        if fl&0x40000: b=zlib.decompress(b[4:])
        d=dict(subrecords(b))
        if d.get('EDID',b'').rstrip(b'\0').decode('latin1')==target and 'VMAD' in d: print(t,hex(fid)); parse(d['VMAD'],t)
w(24+hsz,len(buf))

"""Build Elden Counter - Block Only.esp (ESL, master Skyrim.esm only; Elden Counter's forms are found at runtime).

Usage: build_ecb_esp.py <out.esp>

Records:
  0x800 QUST ECB_Quest   start game enabled, script ECB_Guard (removes Elden Counter's guard-counter window when it
                         opens without a block, so MCO combos keep their own power attacks)
"""
import struct, sys

OUT = sys.argv[1]
OWN = 1 << 24
PLAYER_REF = 0x14

def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data
def z(s): return s.encode('cp1252') + b'\0'
def u32(*v): return struct.pack('<%dI' % len(v), *v)
def f32(*v): return struct.pack('<%df' % len(v), *v)
def ws(s): b = s.encode('cp1252'); return struct.pack('<H', len(b)) + b
def rec(t, fid, subs, flags=0, ver=44):
    body = b''.join(subs)
    return t.encode() + struct.pack('<IIIIHH', len(body), flags, fid, 0, ver, 0) + body
def grup(label, body):
    return b'GRUP' + struct.pack('<I', 24 + len(body)) + label.encode() + struct.pack('<IHHI', 0, 0, 0, 0) + body
def p_obj(name, fid): return ws(name) + bytes([1, 1]) + struct.pack('<hhI', 0, -1, fid)
def script(name, props): return ws(name) + bytes([0]) + struct.pack('<H', len(props)) + b''.join(props)
def qvmad(scripts):
    return sub('VMAD', struct.pack('<hhH', 5, 2, len(scripts)) + b''.join(scripts) + bytes([2]) + struct.pack('<H', 0)
               + ws('') + struct.pack('<H', 0))

quest = rec('QUST', OWN | 0x800, [
    sub('EDID', z('ECB_Quest')), qvmad([script('ECB_Guard', [p_obj('PlayerRef', PLAYER_REF)])]),
    sub('FULL', z('Elden Counter - Block Only')), sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)),
    sub('NEXT', b''), sub('ANAM', u32(0))])
hdr = [sub('HEDR', f32(1.7) + u32(2, 0x801)), sub('CNAM', z('Claude')),
       sub('SNAM', z('Elden Counter guard counters only after a real block')),
       sub('MAST', z('Skyrim.esm')), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + grup('QUST', quest))
print('wrote', OUT)

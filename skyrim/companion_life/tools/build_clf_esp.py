"""Build Companion Life.esp (ESL) - v6 (2026-10-17): BAREFOOT AT HOME ONLY.

Usage: build_clf_esp.py <out.esp>

The downtime AI of v1-v5 (activity faction + sandbox/follow/travel packages on Serana's and Ashe's aliases) never got
them using furniture at home, so the user went back to their own AI and kept only this: when Serana or Ashe is in a
player home she takes off her boots and calf pieces, and puts exactly those back on once she is out of the home.
That build is kept in old_v5/.

Records (append-only object IDs; 0x800-0x808 and 0x80B were v1-v5's faction and packages, now removed - the IDs stay
retired):
  0x809 QUST CLF_Quest     start game enabled, script CLF_Brain. Aliases 0-3 kept EMPTY (no packages, nothing
                           forced; v7 2026-10-19: the script clears them in old saves) so the layout saves know stays.
                           Priority 50.
  0x80A GLOB CLF_Enabled   1 = on (console: set CLF_Enabled to 0)
"""
import struct, sys

OUT = sys.argv[1]
MASTERS = ['Skyrim.esm', 'Dawnguard.esm']
OWN = len(MASTERS) << 24
FID = {'CLF_Quest': OWN | 0x809, 'CLF_Enabled': OWN | 0x80A}
PLAYER_REF = 0x14
SERANA_REF = 0x01002B74             # Dawnguard DLC1Serana reference
LOC_TYPE_PLAYER_HOUSE = 0x0FC1A3

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
def qvmad(scripts):    # QUST: script list + empty fragment block, no alias scripts
    return sub('VMAD', struct.pack('<hhH', 5, 2, len(scripts)) + b''.join(scripts) + bytes([2]) + struct.pack('<H', 0)
               + ws('') + struct.pack('<H', 0))

glob = rec('GLOB', FID['CLF_Enabled'], [sub('EDID', z('CLF_Enabled')), sub('FNAM', b'f'), sub('FLTV', f32(1.0))])

AFLAGS = 0x20A    # optional, allow reuse in quest, allow reserved
def alias(i, name, forced=None):
    s = [sub('ALST', u32(i)), sub('ALID', z(name)), sub('FNAM', u32(AFLAGS))]
    if forced:
        s += [sub('ALFI', u32(1)), sub('ALFR', u32(forced))]
    s += [sub('VTCK', u32(0)), sub('ALED', b'')]
    return s

props = [p_obj('PlayerRef', PLAYER_REF), p_obj('Enabled', FID['CLF_Enabled']),
         p_obj('LocTypePlayerHouse', LOC_TYPE_PLAYER_HOUSE)]
quest = rec('QUST', FID['CLF_Quest'], [
    sub('EDID', z('CLF_Quest')), qvmad([script('CLF_Brain', props)]), sub('FULL', z('Companion Life')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)),     # start game enabled
    sub('NEXT', b''), sub('ANAM', u32(4))]
    + alias(0, 'Serana') + alias(1, 'Ashe') + alias(2, 'SeranaTarget') + alias(3, 'AsheTarget'))

groups = grup('GLOB', glob) + grup('QUST', quest)
hdr = [sub('HEDR', f32(1.7) + u32(len(FID) + 2, 0x80C)), sub('CNAM', z('Claude')),
       sub('SNAM', z('Companion Life: Serana and Ashe go barefoot at home'))]
for m in MASTERS:
    hdr += [sub('MAST', z(m)), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + groups)
print('wrote', OUT)
for k, v in FID.items(): print(f'  {v:08X} {k}')

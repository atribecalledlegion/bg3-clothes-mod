"""Build Companion Life.esp (ESL) - downtime ("passive") AI for Serana and Ashe.

Usage: build_clf_esp.py <out.esp>

How it works: CLF_Quest (priority 81, one above the companions' own mental-model quests at 80) holds Serana and Ashe
in aliases whose packages only run while the companion's rank in CLF_ActivityFaction picks them. Rank 0 = no package
of ours applies and their own follow / sandbox AI runs as before. The script CLF_Brain picks the rank (the activity)
from hidden needs and the place; the packages make the engine find the chair, the bed, the idle marker or the person.

Records (append-only object IDs):
  0x800 FACT CLF_ActivityFaction  rank = activity (1 rest .. 7 hold)
  0x801 PACK CLF_Rest      rank 1  sandbox near the player: sitting + idle markers (v2)
  0x802 PACK CLF_Comfort   rank 2  sandbox near the player: idle markers, sitting, special furniture, wandering (v2)
  0x803 PACK CLF_Drink     rank 3  sandbox near the player, sitting only; the script plays ChairDrinkingStart once seated
  0x804 PACK CLF_Social    rank 4  sandbox near the player: conversation + wandering + idle markers
  0x805 PACK CLF_VisitS    rank 5  travel to alias 2 (Serana's target)
  0x806 PACK CLF_VisitA    rank 5  travel to alias 3 (Ashe's target)
  0x807 PACK CLF_Sleep     rank 6  sandbox near the player, sleeping only
  0x808 PACK CLF_Hold      rank 7  stay where she stands (scripted idles: warming hands, chats)
  0x809 QUST CLF_Quest     start game enabled, script CLF_Brain; aliases 0 Serana (forced), 1 Ashe (filled by the
                           script, Ashe's plugin is not a master), 2 SeranaTarget, 3 AsheTarget
  0x80A GLOB CLF_Enabled   1 = on (console: set CLF_Enabled to 0)
  0x80B PACK CLF_FollowHome rank 8 follow the player at 280-420 (v4: at home/inn while you walk about; their own
                           follow/sandbox flip-flopped and v1-v3 sandboxed in place, so in a long cave home like
                           Rayek's End they were left behind in the hallway)
"""
import struct, sys

OUT = sys.argv[1]
MASTERS = ['Skyrim.esm', 'Dawnguard.esm']
OWN = len(MASTERS) << 24
NAMES = ['CLF_ActivityFaction', 'CLF_Rest', 'CLF_Comfort', 'CLF_Drink', 'CLF_Social', 'CLF_VisitS', 'CLF_VisitA',
         'CLF_Sleep', 'CLF_Hold', 'CLF_Quest', 'CLF_Enabled', 'CLF_FollowHome']
FID = {n: OWN | (0x800 + i) for i, n in enumerate(NAMES)}
PLAYER_REF = 0x14
SERANA_REF = 0x01002B74             # Dawnguard DLC1Serana reference
SANDBOX, TRAVEL = 0x1C254, 0x16FAA  # Skyrim.esm package templates
GET_FACTION_RANK = 73

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
def ctda(fn, p1, value=1.0, op=0x00, runon=0):
    return sub('CTDA', struct.pack('<B3xfHHIIIIi', op, value, fn, 0, p1, 0, runon, 0, -1))

# package tail shared by all template packages (procedure-tree begin/end/change slots, empty)
TAIL = [sub('POBA', b''), sub('INAM', u32(0)), sub('PDTO', bytes(8)),
        sub('POEA', b''), sub('INAM', u32(0)), sub('PDTO', bytes(8)),
        sub('POCA', b''), sub('INAM', u32(0)), sub('PDTO', bytes(8))]
WALK = 0    # PKDT preferred speed: walk (they are relaxing)

def pkdt(): return sub('PKDT', struct.pack('<IBBBBHH', 0, 0x12, 0, WALK, 0x72, 0xFEFF, 0))
PSDT = sub('PSDT', bytes.fromhex('ffff00ffff00000000000000'))     # any time, any day (as DLC1NPCSandboxAroundPlayer600)

def sandbox(name, rank, radius, eat=0, sleep=0, talk=0, markers=0, sit=0, special=0, wander=0, energy=50.0):
    # Sandbox data inputs in template order: Location, then Bools: Unlock On Arrival, Allow Eating, Allow Sleeping,
    # Allow Conversation, Allow Idle Markers, Allow Sitting, Allow Special Furniture, Allow Wandering, Preferred Path
    # Only, Ride Horse; Float Energy (UNAM order 00 0e 01 03 04 05 06 1f 07 19 1b 1d, as the vanilla records)
    bools = [0, eat, sleep, talk, markers, sit, special, wander, 0, 0]
    s = [sub('EDID', z(name)), pkdt(), PSDT, ctda(GET_FACTION_RANK, FID['CLF_ActivityFaction'], float(rank)),
         sub('PKCU', u32(12, SANDBOX, 10)),
         sub('ANAM', z('Location')), sub('PLDT', u32(0, PLAYER_REF, radius))]     # near reference: the player
    for b in bools:
        s += [sub('ANAM', z('Bool')), sub('CNAM', bytes([b]))]
    s += [sub('ANAM', z('Float')), sub('CNAM', f32(energy))]
    s += [sub('UNAM', bytes([u])) for u in (0x00, 0x0E, 0x01, 0x03, 0x04, 0x05, 0x06, 0x1F, 0x07, 0x19, 0x1B, 0x1D)]
    s += [sub('XNAM', bytes([0x20]))] + TAIL
    return rec('PACK', FID[name], s)

def travel(name, rank, pldt, owner=None):
    # Travel inputs: Location (Place to Travel), Bool Ride Horse, Bool Prefer Preferred Path
    s = [sub('EDID', z(name)), pkdt(), PSDT, ctda(GET_FACTION_RANK, FID['CLF_ActivityFaction'], float(rank))]
    if owner:
        s.append(sub('QNAM', u32(owner)))
    s += [sub('PKCU', u32(3, TRAVEL, 3)), sub('ANAM', z('Location')), sub('PLDT', pldt),
          sub('ANAM', z('Bool')), sub('CNAM', b'\0'), sub('ANAM', z('Bool')), sub('CNAM', b'\0'),
          sub('UNAM', b'\x00'), sub('UNAM', b'\x02'), sub('UNAM', b'\x04'), sub('XNAM', b'\x03')] + TAIL
    return rec('PACK', FID[name], s)

# v2 (2026-10-17): v1 rest was sit-only, so with no free chair she just stood; comfort lacked wandering. Rest now
# also leans/uses idle markers; comfort = exactly what their own sandbox allows (markers, chairs, crafting furniture
# such as grindstones and alchemy tables, wandering), wider radius so the whole house counts.
packs = (sandbox('CLF_Rest', 1, 1500, sit=1, markers=1)
         + sandbox('CLF_Comfort', 2, 2000, markers=1, sit=1, special=1, wander=1)
         + sandbox('CLF_Drink', 3, 1500, sit=1)
         + sandbox('CLF_Social', 4, 1500, talk=1, markers=1, wander=1)
         + travel('CLF_VisitS', 5, u32(8, 2, 150), FID['CLF_Quest'])      # near ref alias 2, radius 150
         + travel('CLF_VisitA', 5, u32(8, 3, 150), FID['CLF_Quest'])      # near ref alias 3
         + sandbox('CLF_Sleep', 6, 2500, sleep=1)
         + travel('CLF_Hold', 7, u32(12, 0, 0)))                          # near self, radius 0 = stand still

def follow(name, rank, dmin, dmax):
    # copy of Dawnguard DLC1NPCFollowClose (Follow template Skyrim.esm 0x0750BE) with our condition and distances
    s = [sub('EDID', z(name)), sub('PKDT', bytes.fromhex('000004001200024dfffe0000')), PSDT,
         ctda(GET_FACTION_RANK, FID['CLF_ActivityFaction'], float(rank)),
         sub('PKCU', u32(15, 0x0750BE, 8)),
         sub('ANAM', z('SingleRef')), sub('PTDA', u32(0, PLAYER_REF, 0)),
         sub('ANAM', z('Float')), sub('CNAM', f32(dmin)), sub('ANAM', z('Float')), sub('CNAM', f32(dmax)),
         sub('ANAM', z('Bool')), sub('CNAM', bytes(1)),
         sub('ANAM', z('Location')), sub('PLDT', bytes.fromhex('0c0000000000000000010000'))]
    for b in (1, 0, 1, 0, 0, 1, 1, 1, 1):
        s += [sub('ANAM', z('Bool')), sub('CNAM', bytes([b]))]
    s += [sub('ANAM', z('Float')), sub('CNAM', f32(0.0))]
    s += [sub('UNAM', bytes([u])) for u in (0x00, 0x01, 0x02, 0x06, 0x09, 0x0A, 0x0B, 0x10, 0x11, 0x12, 0x13, 0x14, 0x19, 0x15, 0x17)]
    s += [sub('XNAM', bytes([0x1A]))] + TAIL
    return rec('PACK', FID[name], s)

packs += follow('CLF_FollowHome', 8, 280.0, 420.0)

fact = rec('FACT', FID['CLF_ActivityFaction'], [sub('EDID', z('CLF_ActivityFaction')), sub('DATA', u32(1)),
                                                sub('CRVA', bytes(20))])
glob = rec('GLOB', FID['CLF_Enabled'], [sub('EDID', z('CLF_Enabled')), sub('FNAM', b'f'), sub('FLTV', f32(1.0))])

# alias flags: 0x2 optional, 0x8 allow reuse in quest, 0x200 allow reserved (the companions' own quests hold them too)
AFLAGS = 0x20A
def alias(i, name, pkgs=(), forced=None):
    s = [sub('ALST', u32(i)), sub('ALID', z(name)), sub('FNAM', u32(AFLAGS))]
    if forced:
        s += [sub('ALFI', u32(1)), sub('ALFR', u32(forced))]
    s += [sub('ALPC', u32(p)) for p in pkgs]
    s += [sub('VTCK', u32(0)), sub('ALED', b'')]
    return s

common = [FID['CLF_FollowHome'], FID['CLF_Hold'], FID['CLF_Sleep'], FID['CLF_Drink'], FID['CLF_Rest'], FID['CLF_Comfort'], FID['CLF_Social']]
IDLES = {   # Skyrim.esm
    'ChairDrink': 0x065D07, 'StandDrink': 0x0640FC, 'WarmHands': 0x0E8642, 'WarmHandsCrouched': 0x0E8643,
    'Stretch': 0x0F50F1, 'TalkHappy': 0x0E5191, 'TalkNeutral': 0x0E5190, 'Laugh': 0x075C5F,
    'ResponsePositive': 0x058B45, 'LookFar': 0x075C62, 'Wave': 0x03EA32}
KEYWORDS = {'LocTypePlayerHouse': 0x0FC1A3, 'LocTypeInn': 0x01CB87, 'LocTypeCity': 0x013168, 'LocTypeTown': 0x013166,
            'LocTypeHabitation': 0x039793, 'LocTypeDwelling': 0x0130DC, 'LocTypeDungeon': 0x0130DB}
props = [p_obj('PlayerRef', PLAYER_REF), p_obj('ActivityFaction', FID['CLF_ActivityFaction']),
         p_obj('Enabled', FID['CLF_Enabled']), p_obj('GameHour', 0x38)]
props += [p_obj(k, v) for k, v in IDLES.items()] + [p_obj(k, v) for k, v in KEYWORDS.items()]
quest = rec('QUST', FID['CLF_Quest'], [
    sub('EDID', z('CLF_Quest')), qvmad([script('CLF_Brain', props)]), sub('FULL', z('Companion Life')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 81, 0, 0, 0)),     # start game enabled, priority 81
    sub('NEXT', b''), sub('ANAM', u32(4))]
    + alias(0, 'Serana', [FID['CLF_VisitS']] + common, forced=SERANA_REF)
    + alias(1, 'Ashe', [FID['CLF_VisitA']] + common)
    + alias(2, 'SeranaTarget') + alias(3, 'AsheTarget'))

groups = grup('GLOB', glob) + grup('FACT', fact) + grup('QUST', quest) + grup('PACK', packs)
hdr = [sub('HEDR', f32(1.7) + u32(len(FID) + 4, 0x80C)), sub('CNAM', z('Claude')),
       sub('SNAM', z('Companion Life: downtime AI for Serana and Ashe'))]
for m in MASTERS:
    hdr += [sub('MAST', z(m)), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + groups)
print('wrote', OUT)
for k, v in FID.items(): print(f'  {v:08X} {k}')

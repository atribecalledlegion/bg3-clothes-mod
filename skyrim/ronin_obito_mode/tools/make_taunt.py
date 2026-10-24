"""Ronin Obito's taunt animation: VergilSDT 1.3's Devil Trigger power-up pose (1hm_shout_exhale.hkx, 1.87 s, with
1.5 s of invincibility frames), with its Devil Trigger calls made inert: the PIE call that summons the demon form and
its two sounds are overwritten in place with annotation names nothing listens to (a shorter text, padded with nulls,
so no offsets move). Copied as the five combat idle names for the 'Ronin Obito/Taunt' OAR folder.
(History: VergilSDT's EX Taunt was 33 s and summoned the demon; the Yamato combat idle was 8 s and got him killed.)

usage: make_taunt.py <1hm_shout_exhale.hkx> <out dir>
"""
import os, sys
SRC, OUT = sys.argv[1], sys.argv[2]
INERT = {b'PIE.$SDTmodeON': b'ROMtaunt',
         b'SoundPlay.JCEuiNotEnough_SFXSD': b'ROMtauntSound1',
         b'SoundPlay.dtONsfx': b'ROMtauntSound2'}
d = bytearray(open(SRC, 'rb').read())
for old, new in INERT.items():
    key = old + b'\0'
    n = d.count(key)
    assert n == 1, (old, n)
    i = d.index(key)
    d[i:i + len(key)] = new + b'\0' * (len(key) - len(new))
os.makedirs(OUT, exist_ok=True)
for name in ('CombatIdleA', 'CombatIdleB', 'CombatIdleC', 'CombatIdlesmallA', 'CombatIdlesmallB'):
    open(os.path.join(OUT, name + '.hkx'), 'wb').write(d)
print('wrote', OUT)

"""Ronin Obito's Issen animation: the Vergil Yamato's Judgement Cut quick-draw (91100016 mco_attack1.hkx, 1.5 s:
blade out at 0.1 s, back in at 0.27 s), played as his combat idle while ROM_IssenMark is on him.

As an idle it must not drive MCO or SCAR: its combo windows, next-attack and attack-speed graph variables, recovery
and SCAR action data are overwritten in place with annotation names nothing listens to (a shorter text padded with
nulls, so no offsets move). Kept: the draw/sheath (ShdEquip, bowReset: the Yamato's own stance switch), the NEAE
sheath effect pair, the particles, and the Judgement Cut sounds.
Copied as the five combat idle names for the 'Ronin Obito/Issen' OAR folder.

usage: make_issen_anim.py <JC mco_attack1.hkx> <out dir>
"""
import os, re, sys

SRC, OUT = sys.argv[1], sys.argv[2]
d = bytearray(open(SRC, 'rb').read())
INERT = [rb'PIE\.@SGVF\|MCO_AttackSpeed\|[0-9.]+', rb'PIE\.@SGVI\|MCO_next(power)?attack\|[0-9]+',
         rb'MCO_(Power)?Win(Open|Close)', rb'MCO_Recovery', rb'SCAR_ComboStart', rb'SCAR_ActionData\{[^\x00]*\}']
total = 0
for pat in INERT:
    for m in list(re.finditer(pat + rb'\x00', d)):
        a, b = m.span()
        text = d[a:b - 1]
        new = b'ROMissen'[:len(text)]
        d[a:b - 1] = new + b'\0' * (len(text) - len(new))
        total += 1
assert total >= 12, total          # 2 speed, 4 next-attack, 4 windows, recovery, 3 SCAR
os.makedirs(OUT, exist_ok=True)
for name in ('CombatIdleA', 'CombatIdleB', 'CombatIdleC', 'CombatIdlesmallA', 'CombatIdlesmallB'):
    open(os.path.join(OUT, name + '.hkx'), 'wb').write(d)
print('made %d annotations inert; wrote %s' % (total, OUT))

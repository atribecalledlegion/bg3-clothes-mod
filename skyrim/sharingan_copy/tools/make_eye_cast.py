"""Kamui Barrage eye-cast: vanilla IdleLookFar (hand raised to the eyes) sped up to TARGET seconds, installed as an
OAR submod over the shout exhale clips (which play when a power is released), only for the player while
"Kamui: Shuriken Barrage" (Sharingan Copy.esp 0x839) is the equipped power."""
import struct, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hkanno import Pack

TARGET = 1.8
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vanilla_anims', 'idlelookfar.hkx')
MOD = 'C:/games/ModOrganizer/Skyrim Special Edition/mods/Sharingan Copy/meshes/actors/character/animations/OpenAnimationReplacer/Sharingan Copy'
SUB = MOD + '/Kamui Barrage - Eye Cast'
CLIPS = ['1hm_shout_exhale.hkx', '1hm_shout_exhale_medium.hkx', '1hm_shout_exhale_long.hkx',
         'mt_shout_exhale.hkx', 'mt_shout_exhale_medium.hkx', 'mt_shout_exhale_long.hkx',
         'sneak1hm_shout_exhale.hkx', 'sneak1hm_shout_exhale_medium.hkx', 'sneak1hm_shout_exhale_long.hkx']

pk = Pack(SRC); a = pk.animations()[0]; d = pk.d; b = pk.ds + a
dur = struct.unpack_from('<f', d, b + 20)[0]
k = TARGET / dur                                   # time scale (< 1 = faster)
struct.pack_into('<f', d, b + 20, dur * k)
bd, binv, fd = struct.unpack_from('<fff', d, b + 72)
struct.pack_into('<fff', d, b + 72, bd * k, binv / k, fd * k)
os.makedirs(SUB, exist_ok=True)
for c in CLIPS: open(os.path.join(SUB, c), 'wb').write(d)
print('IdleLookFar %.3f s -> %.3f s (x%.2f speed), written as %d exhale clips' % (dur, dur * k, 1 / k, len(CLIPS)))

json.dump({'name': 'Sharingan Copy', 'author': 'Claude',
           'description': 'Kamui: Shuriken Barrage hand-to-eye cast (vanilla IdleLookFar, sped up).'},
          open(MOD + '/config.json', 'w'), indent=4)
json.dump({'name': 'Kamui Barrage - Eye Cast',
           'description': 'Obito raises his hand to his Mangekyou while Kamui: Shuriken Barrage is released.',
           'priority': 2000014100,
           'conditions': [
               {'condition': 'IsActorBase', 'requiredVersion': '1.0.0.0',
                'Actor base': {'pluginName': 'Skyrim.esm', 'formID': '7'}},
               {'condition': 'IsEquippedPower', 'requiredVersion': '1.0.0.0',
                'Form': {'pluginName': 'Sharingan Copy.esp', 'formID': '839'}}]},
          open(SUB + '/config.json', 'w'), indent=4)
print('configs written')

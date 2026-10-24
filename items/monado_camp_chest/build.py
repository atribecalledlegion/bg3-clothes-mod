"""Package items/monado_camp_chest into MonadoCampChest.pak (repo root) and, with --install, copy it to the
BG3 Mods folder. The mod is only a meta.lsx and a Script Extender Lua script, so there is nothing to convert.

    python items/monado_camp_chest/build.py [--install]
"""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIVINE = os.environ.get('DIVINE', os.path.join(os.environ.get('USERPROFILE', ''), 'Tools', 'LSLib', 'Tools', 'Divine.exe'))
MODS = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Larian Studios', "Baldur's Gate 3", 'Mods')
NAME = 'MonadoCampChest'

stage = os.path.join(ROOT, 'build', 'stage', 'monado_camp_chest')
pak = os.path.join(ROOT, NAME + '.pak')
shutil.rmtree(stage, ignore_errors=True)
shutil.copytree(os.path.join(HERE, 'src'), stage)
subprocess.run([DIVINE, '-g', 'bg3', '-a', 'create-package', '-s', stage, '-d', pak, '-c', 'lz4', '-l', 'warn'], check=True)
print('built', pak, os.path.getsize(pak), 'bytes')

if '--install' in sys.argv:
    dst = os.path.join(MODS, NAME + '.pak')
    if os.path.exists(dst):
        raise SystemExit('%s is already installed; not overwriting' % dst)
    shutil.copy2(pak, dst)
    print('installed', dst)

"""Copy vanilla voice files (every voice type that recorded the line) to our generic lines' names.

Usage: copy_generic_voice.py <Skyrim Data dir> <bsa.py> <work dir>
Writes data/Sound/Voice/Shinobi Enemies.esp/<voice type>/<name>.fuz (lines in companion_lines.py GENERIC).
"""
import os, re, shutil, subprocess, sys
DATA, BSA_PY, WORK = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'companion_lines.py')).read())
OUT = os.path.join(HERE, '..', 'data', 'Sound', 'Voice', 'Shinobi Enemies.esp')
ARC = os.path.join(DATA, 'Skyrim - Voices_en0.bsa')
total = 0
for i, (topic, cat, src_id, emo, text) in enumerate(GENERIC):
    d, n = generic_ids(i)
    out = os.path.join(WORK, 'g%07x' % src_id)
    os.makedirs(out, exist_ok=True)
    plugin = 'dawnguard' if src_id & DG else 'skyrim'
    src_id &= 0xFFFFFF
    pat = plugin + r'\.esm[\\/][^\\/]+[\\/][^\\/]*_%08x_1\.fuz$' % src_id    # BSA paths use backslashes
    subprocess.run([sys.executable, '-I', BSA_PY, 'extract', ARC, out, pat], check=True, capture_output=True)
    count = 0
    for dp, dn, fn in os.walk(out):
        for f in fn:
            if not f.lower().endswith('_%08x_1.fuz' % src_id): continue
            vt = os.path.basename(dp)
            dst_dir = os.path.join(OUT, vt)
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy2(os.path.join(dp, f), os.path.join(dst_dir, generic_voice_name(topic, n)))
            count += 1
    total += count
    print(f'{topic:12} {text[:40]:40} -> {count} voice types')
print('files', total)

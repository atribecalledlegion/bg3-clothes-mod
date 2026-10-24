"""Copy the companions' existing voice files to the names our own dialogue (companion_lines.py) needs.

Usage: copy_companion_voice.py <MO2 mods dir> <Skyrim Data dir> <bsa.py> <work dir>
Writes data/Sound/Voice/Shinobi Enemies.esp/<voice type>/<name>.fuz and prints each copy.
"""
import os, re, shutil, subprocess, sys
MODS, DATA, BSA_PY, WORK = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'companion_lines.py')).read())
OUT = os.path.join(HERE, '..', 'data', 'Sound', 'Voice', 'Shinobi Enemies.esp')
SOURCES = {
    'sda': [('bsa', os.path.join(MODS, 'Serana Dialogue Add-On', 'SeranaDialogAddon.bsa'), 'seranadialogaddon.esp/dlc1seranavoice')],
    'dg': [('dir', os.path.join(MODS, 'Serana Revamped - Dawnguard Revoice - KerstynVoices', 'Sound', 'Voice', 'Dawnguard.esm'), 'dlc1seranavoice'),
           ('bsa', os.path.join(DATA, 'Skyrim - Voices_en0.bsa'), 'dawnguard.esm/dlc1seranavoice')],
    'ashe': [('bsa', os.path.join(MODS, 'Ashe - Crystal Heart', 'Ashe - Fire and Blood.bsa'), 'ashe - fire and blood.esp/mm_ashevoice')],
}
def find_in_dir(root, sub, src_id):
    for dp, dn, fn in os.walk(root):
        if os.path.basename(dp).lower() != sub: continue
        for f in fn:
            if re.search(r'_%08x_1\.fuz$' % src_id, f.lower()): return os.path.join(dp, f)
    return None
def find_in_bsa(archive, sub, src_id):
    pat = r'%s[\\/][^\\/]*_%08x_1\.fuz' % (re.escape(sub).replace('/', r'[\\/]'), src_id)    # BSA paths use backslashes
    out = os.path.join(WORK, 'x%06x' % src_id)
    os.makedirs(out, exist_ok=True)
    subprocess.run([sys.executable, '-I', BSA_PY, 'extract', archive, out, pat], check=True, capture_output=True)
    for dp, dn, fn in os.walk(out):
        for f in fn:
            if f.lower().endswith('_%08x_1.fuz' % src_id): return os.path.join(dp, f)
    return None
missing = 0
for i, (topic, cat, source, src_id, emo, text) in enumerate(LINES):
    dial_id, info_id = line_ids(i)
    got = None
    for kind, where, sub in SOURCES[source]:
        got = find_in_dir(where, sub, src_id) if kind == 'dir' else find_in_bsa(where, sub, src_id)
        if got: break
    dst_dir = os.path.join(OUT, voice_type(source))
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, voice_name(topic, info_id))
    if not got:
        print(f'MISSING {topic} {source} {src_id:06X}'); missing += 1; continue
    shutil.copy2(got, dst)
    print(f'{topic:14} <- {os.path.relpath(got, WORK) if got.startswith(WORK) else got}  ->  {os.path.basename(dst)} ({os.path.getsize(dst)} B)')
print('missing', missing)

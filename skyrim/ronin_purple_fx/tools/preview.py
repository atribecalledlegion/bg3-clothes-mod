"""Before/after contact sheet of the recoloured textures (left original, right purple, on black).
usage (from the MO2 mods folder): preview.py <ronin_purple_fx dir>"""
import json, os, sys
from PIL import Image, ImageDraw

R = sys.argv[1]
sv = json.load(open(os.path.join(R, 'build', 'texture_survey.json')))['mod']
rp = json.load(open(os.path.join(R, 'build', 'repoint.json')))
items = [(k, v['path']) for k, v in sorted(sv.items()) if v['blue'] >= 0.2]
T, cols = 96, 6
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (2 * T + 12), rows * (T + 18)), (24, 24, 28))
d = ImageDraw.Draw(sheet)
for n, (rel, src) in enumerate(items):
    out = os.path.join(R, 'build', 'mod', *rp.get(rel, rel).split('\\'))
    x, y = (n % cols) * (2 * T + 12), (n // cols) * (T + 18)
    for k, p in enumerate((src, out)):
        im = Image.open(p).convert('RGBA').resize((T, T))
        bg = Image.new('RGBA', (T, T), (0, 0, 0, 255))
        bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB'), (x + k * T, y))
    d.text((x + 2, y + T + 3), rel.split('\\')[-1][:30], fill=(200, 200, 200))
sheet.save(os.path.join(R, 'preview_textures.png'))
print('ok', len(items))

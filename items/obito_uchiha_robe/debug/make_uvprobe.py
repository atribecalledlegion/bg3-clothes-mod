"""DIAGNOSTIC BUILD -- not for release.

Paints the whole 2048 base texture as a 4x4 grid of 16 highly distinguishable colours and
overlays the crest where the pipeline believes the upper back is.

Whatever colour the robe's BACK shows in game identifies exactly which texture cell the
back panel samples. That pins the UV mapping empirically rather than by inference -- which
matters, because the previous diagnostic (flat green with only edge/centre lines) could
not distinguish a correct mapping from a wrong one: the predicted back region contains no
lines, so it looked identical either way.

Predicted by tools/crestplace.py: masculine back panel = x 1347-1995, y 59-704,
i.e. the top-right quadrant, cells C1/D1. The crest sits at (1695, 382) = cell D1.

Restore the real artwork with:  sh items/obito_uchiha_robe/art/make_textures.sh  &&  ./build.ps1 -Item obito_uchiha_robe -Install
"""
import os, subprocess

M = os.environ.get('MAGICK', r"C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/magick.exe")
OUT = 'items/obito_uchiha_robe/src/Public/ObitoUchihaRobe/Assets/Textures/Armor'
COLS = ['#E6194B', '#3CB44B', '#FFE119', '#4363D8',
        '#F58231', '#911EB4', '#46F0F0', '#F032E6',
        '#BCF60C', '#FABEBE', '#008080', '#9A6324',
        '#FFFAC8', '#800000', '#AAFFC3', '#000075']
CELL = 512

def run(args):
    subprocess.run([M] + args, check=True)

cmd = ['-size', '2048x2048', 'xc:black']
for i, col in enumerate(COLS):
    r, c = divmod(i, 4)
    x0, y0 = c * CELL, r * CELL
    cmd += ['-fill', col, '-draw',
            'rectangle %d,%d %d,%d' % (x0, y0, x0 + CELL - 1, y0 + CELL - 1)]
    # cell label, large enough to read on a body in game
    cmd += ['-fill', 'black', '-pointsize', '150', '-annotate',
            '+%d+%d' % (x0 + 30, y0 + 170), '%s%d' % (chr(65 + c), r + 1)]
cmd += ['PNG24:build/work/obito_uchiha_robe/uvprobe.png']
run(cmd)

for src, w, h, rot, ox, oy in (
        ('HUM_M_ARM_Robe_A_BM.DDS', 200, 266, '90', 1529, 282),
        ('HUM_F_ARM_Robe_A_Body_BM.DDS', 151, 201, '0', 240, 335)):
    run(['build/work/obito_uchiha_robe/uvprobe.png',
         '(', 'items/obito_uchiha_robe/art/source/uchiha_crest.png', '-resize', '%dx%d!' % (w, h), '-rotate', rot, ')',
         '-geometry', '+%d+%d' % (ox, oy), '-compose', 'Over', '-composite',
         '-define', 'dds:compression=dxt1', '-define', 'dds:mipmaps=12',
         os.path.join(OUT, src)])

run(['identify', '-format', '%f  %wx%h\n',
     os.path.join(OUT, 'HUM_M_ARM_Robe_A_BM.DDS'),
     os.path.join(OUT, 'HUM_F_ARM_Robe_A_Body_BM.DDS')])
print('grid: columns A-D left to right, rows 1-4 top to bottom; crest drawn in D1')

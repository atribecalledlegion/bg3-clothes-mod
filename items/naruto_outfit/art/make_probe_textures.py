"""DIAGNOSTIC textures: a labelled grid instead of the model's atlas.

    python items/naruto_outfit/art/make_probe_textures.py naruto_outfit
    (then rebuild and install; restore with art/make_textures.py)

In game the imported garments show the atlas as scrambled patches, but rendering the
PACKED model against the PACKED texture offline reproduces the atlas correctly. So the
game is not sampling the way the file says. This replaces the base colour with a 4x4 grid
of distinct colours, each cell labelled A1..D4, which answers both questions at once:

  * garment shows flat grey/white, no grid  -> the game is not using our texture at all
    (material or texture resource wiring), not a UV problem
  * garment shows clean lettered cells      -> texture and UVs are fine, and the atlas
    itself was the problem
  * garment shows jumbled fragments of many -> UVs in game differ from the file: the cells
    cells                                      named tell us which part of the texture the
                                               garment samples

The same trick settled the Obito robe's UV question; see items/obito_uchiha_robe/debug.
"""
import os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import item as itemlib

COLS = ['#E6194B', '#3CB44B', '#FFE119', '#4363D8',
        '#F58231', '#911EB4', '#46F0F0', '#F032E6',
        '#BCF60C', '#FABEBE', '#008080', '#9A6324',
        '#FFFAC8', '#800000', '#AAFFC3', '#000075']
CELL = 512


def main():
    it = itemlib.load()
    work = os.path.join(it.work, 'probe.png')
    cmd = [itemlib.MAGICK, '-size', '2048x2048', 'xc:black']
    for i, col in enumerate(COLS):
        x, y = (i % 4) * CELL, (i // 4) * CELL
        label = '%s%d' % ('ABCD'[i % 4], i // 4 + 1)
        cmd += ['-fill', col, '-draw', 'rectangle %d,%d %d,%d' % (x + 4, y + 4, x + CELL - 4, y + CELL - 4),
                '-fill', 'black', '-pointsize', '150', '-annotate', '+%d+%d' % (x + 40, y + 200), label]
    cmd += ['PNG24:' + work]
    subprocess.run(cmd, check=True)
    for tag, s, _ in it.sets():
        for name in (s['bm'],):
            subprocess.run([itemlib.MAGICK, work, '-alpha', 'off',
                            '-define', 'dds:compression=dxt1', '-define', 'dds:mipmaps=12',
                            os.path.join(it.textures, name)], check=True)
            print('%-8s probe -> %s' % (tag, name))


if __name__ == '__main__':
    main()

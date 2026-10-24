"""Read (and later write) annotation tracks of 64-bit Havok 2010 packfiles (Skyrim SE .hkx animations).
usage: hkanno.py dump <file.hkx>...
Layout notes (hk_2010.2.0, 64-bit pointers):
  file header 0x40 bytes, then section headers (0x30 each, + 0x10 padding when version >= 11)
  section header: name[20], absoluteDataStart, localFixupsOffset, globalFixupsOffset,
                  virtualFixupsOffset, exportsOffset, importsOffset, endOffset (all relative to data start)
  local fixups: (src, dst) pairs, pointer at src points to dst (same section)
  global fixups: (src, dstSection, dst)
  virtual fixups: (objectOffset, classNameSection, classNameOffset)
  hkaAnimation: vtable 8, memSizeAndFlags 2, refCount 2, pad 4 | type 4, duration 4, numTransformTracks 4,
                numFloatTracks 4, extractedMotion ptr 8, annotationTracks hkArray (ptr 8, size 4, capFlags 4)
  hkaAnnotationTrack (24 bytes): trackName hkStringPtr 8, annotations hkArray 16
  hkaAnnotationTrack::Annotation (16 bytes): time float 4, pad 4, text hkStringPtr 8
"""
import struct, sys, os

class Pack:
    def __init__(self, path):
        self.path = path; self.d = bytearray(open(path, 'rb').read())
        d = self.d
        self.nsec = struct.unpack_from('<i', d, 0x14)[0]
        ver = struct.unpack_from('<i', d, 0x10)[0]
        self.sh_size = 0x40 if ver >= 11 else 0x30
        self.secs = {}
        p = 0x40 + (0x10 if ver >= 11 else 0)
        # hk2010 (contents version 8) has no padding; detect by name check
        for pad in (0, 0x10):
            p = 0x40 + pad; ok = True; secs = {}
            for i in range(self.nsec):
                name = bytes(d[p:p+19]).split(b'\0')[0]
                if not name.startswith(b'__'): ok = False; break
                vals = list(struct.unpack_from('<7I', d, p + 20))
                secs[name.decode()] = (p, vals); p += 0x30
            if ok: self.secs = secs; self.hdr_pad = pad; break
        assert self.secs, 'section headers not found'
        self.ds_hdr, (self.ds, self.loc, self.glob, self.virt, self.exp, self.imp, self.end) = self.secs['__data__']
        cs = self.secs['__classnames__'][1][0]
        self.local = {}
        p = self.ds + self.loc
        while p < self.ds + self.glob:
            src, dst = struct.unpack_from('<ii', d, p); p += 8
            if src != -1: self.local[src] = dst
        self.objects = []
        p = self.ds + self.virt
        while p + 12 <= self.ds + self.exp and p + 12 <= len(d):
            obj, sec, cname = struct.unpack_from('<iii', d, p); p += 12
            if obj == -1: break
            self.objects.append((obj, bytes(d[cs + cname:]).split(b'\0')[0].decode()))
    def cstr(self, rel):
        return bytes(self.d[self.ds + rel:]).split(b'\0')[0].decode('latin1')
    def animations(self):
        return [o for o, n in self.objects if 'Animation' in n and 'Binding' not in n and 'Container' not in n]
    def tracks(self, anim):
        """-> list of (track_rel, name, [(ann_rel, time, text)])"""
        arr_rel = anim + 40
        size = struct.unpack_from('<i', self.d, self.ds + arr_rel + 8)[0]
        base = self.local.get(arr_rel)
        out = []
        for i in range(size):
            t = base + 24 * i
            name = self.cstr(self.local[t]) if t in self.local else ''
            n = struct.unpack_from('<i', self.d, self.ds + t + 16)[0]
            ab = self.local.get(t + 8)
            anns = []
            for k in range(n):
                a = ab + 16 * k
                time = struct.unpack_from('<f', self.d, self.ds + a)[0]
                anns.append((a, time, self.cstr(self.local[a + 8]) if (a + 8) in self.local else ''))
            out.append((t, name, anns))
        return out
    def duration(self, anim):
        return struct.unpack_from('<f', self.d, self.ds + anim + 20)[0]

    def add_annotations(self, anim, new, out_path):
        """Append (time, text) annotations to the first annotated track (or track 0). The grown annotation
        array and the new strings go at the end of the data section; fixup tables after it are shifted."""
        d = self.d
        assert self.secs['__data__'][0] == max(p for p, _ in self.secs.values()), '__data__ must be the last section header'
        tr = self.tracks(anim)
        ti = next((i for i, (t, n, a) in enumerate(tr) if a), 0)
        t, name, anns = tr[ti]
        old = [(time, a) for a, time, text in anns]          # keep old entries (their text pointers stay as-is)
        blob = bytearray()
        start = self.loc                                       # new data goes where the local fixup table began
        def align(n, a=16): return (n + a - 1) // a * a
        arr_rel = align(start)
        pad0 = arr_rel - start
        count = len(old) + len(new)
        arr = bytearray(16 * count)
        new_fix = {}
        for k, (time, a) in enumerate(old):
            struct.pack_into('<f', arr, 16 * k, time)
            if (a + 8) in self.local: new_fix[arr_rel + 16 * k + 8] = self.local[a + 8]
        str_rel = arr_rel + len(arr)
        strings = bytearray()
        for j, (time, text) in enumerate(new):
            k = len(old) + j
            struct.pack_into('<f', arr, 16 * k, time)
            new_fix[arr_rel + 16 * k + 8] = str_rel + len(strings)
            strings += text.encode('latin1') + b'\0'
        blob = bytes(pad0) + arr + strings
        blob += bytes(align(start + len(blob)) - (start + len(blob)))
        delta = len(blob)
        # track's annotation array -> new array, size and capacity
        local = dict(self.local); local[t + 8] = arr_rel; local.update(new_fix)
        struct.pack_into('<iI', d, self.ds + t + 16, count, count | 0x80000000)
        # rebuild local fixup table
        table = bytearray()
        for src in sorted(local): table += struct.pack('<ii', src, local[src])
        while len(table) % 16: table += struct.pack('<i', -1)
        old_local_len = self.glob - self.loc
        tail = d[self.ds + self.glob:]
        newd = d[:self.ds + self.loc] + blob + table + tail
        shift = delta + len(table) - old_local_len
        p, vals = self.secs['__data__']
        vals = [vals[0], vals[1] + delta] + [v + shift for v in vals[2:]]
        struct.pack_into('<7I', newd, p + 20, *vals)
        open(out_path, 'wb').write(newd)
        return count

if __name__ == '__main__':
    if sys.argv[1] == 'test-add':
        pk = Pack(sys.argv[2]); a = pk.animations()[0]
        n = pk.add_annotations(a, [(0.5, 'TEST_Annotation'), (0.6, 'Second')], sys.argv[3])
        print('wrote', n, 'annotations')
    if sys.argv[1] == 'dump':
        for path in sys.argv[2:]:
            pk = Pack(path)
            for anim in pk.animations():
                tr = pk.tracks(anim)
                with_ann = [(n, a) for t, n, a in tr if a]
                print(f'== {os.path.basename(path)}  duration {pk.duration(anim):.3f}  tracks {len(tr)}  annotated tracks {len(with_ann)}')
                for n, anns in with_ann:
                    for a, time, text in anns: print(f'   [{n}] {time:.3f} {text}')

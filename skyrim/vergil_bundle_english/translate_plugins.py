"""English names for the Korean-translated plugins of the Vergil Yamato 5.7 bundle (installed 2026-10-18 for Ronin
Obito Mode). Rewrites text subrecords (FULL, DESC, DNAM of effects, CNAM of books) in place: whole strings from NAMES,
then any Korean phrase left from PHRASES (longest first). Rebuilds record and group sizes; compressed records are
recompressed. Refuses to write a plugin if any Hangul is left in a text field. Originals are kept by the caller.

usage: translate_plugins.py <plugin>...
"""
import sys, struct, zlib, re
sys.stdout.reconfigure(encoding='utf-8')
HANGUL = re.compile('[가-힣ㄱ-ㆎ]')
TEXT = {'FULL', 'DESC', 'ITXT', 'RNAM', 'NNAM', 'SHRT'}

NAMES = {
    # Vergil Yamato / SDT / Summoned Swords / Magistrate Levitate
    'EX Sword (데미지)': 'EX Sword (Damage)',
    '야마토 이펙트': 'Yamato Effect',
    '인트로 이펙트': 'Intro effect.',
    '스탠스 토글 - Iai': 'Stance Toggle - Iai',
    '스탠스 토글 - Open': 'Stance Toggle - Open',
    '마검 야마토의 칼집': 'Yamato Scabbard',
    '마검 야마토': 'Yamato',
    '얼티밋 슬레이 : 템페스트 쿨타임': 'Ultimate Slay: Tempest Cooldown',
    '얼티밋 슬레이 : 보이드 래피드 쿨타임': 'Ultimate Slay: Void Rapid Cooldown',
    '얼티밋 슬레이 : 헬 온 어스 쿨타임': 'Ultimate Slay: Hell on Earth Cooldown',
    '얼티밋 슬레이 : 보이드 래피드 준비': 'Ultimate Slay: Void Rapid Ready',
    '버질 순간이동': 'Vergil Teleport',
    '공중,지상 저지먼트 컷': 'Judgement Cut (Air and Ground)',
    '진 데빌 트리거 모드': 'Sin Devil Trigger Mode',
    '진정한 악마의 힘을 개방합니다, 모든 능력이 극한으로 강화됩니다': 'Unleashes true demonic power: every ability is pushed to its limit.',
    '마법 책 : Levitate': 'Spell Tome: Levitate',
    '성취의 전당': 'Hall of Attainment',
    '스카이림': 'Skyrim',
    # Flames of Coldharbour (bundled with the moveset): the coldfire spells
    '차가운 불꽃의 망토': 'Cloak of Cold Flames',
    '냉기 화염 데미지': 'Coldfire Damage',
    '냉기 화염 위험': 'Coldfire Hazard',
    '퍽 충격 비틀거림': 'Perk Impact Stagger',
    '지팡이 마법부여': 'Staff Enchantment',
    '냉기 화염 룬': 'Coldfire Rune',
    '상급 냉기 화염 룬': 'Greater Coldfire Rune',
    '둔화': 'Slow',
    '물방울 제어장치': 'Droplet Control',
    '물방울 제어장치 퍽': 'Droplet Control Perk',
    '헬 온 어스': 'Hell on Earth',
    '낙화 제어장치 능력': 'Fall Control Ability',
    '서리 슬로우': 'Frost Slow',
    '<dur>초 동안 근처의 적은 초당 <mag> 냉기 피해를 입습니다. 냉기 파이어 대상은 시간이 지남에 따라 추가 피해를 입습니다.':
        'For <dur> seconds, nearby enemies take <mag> frost damage per second. Targets on coldfire take extra damage over time.',
    '초당 <mag> 냉기 피해를 입히는 벽을 생성합니다. 냉기 화염 대상은 시간이 지남에 따라 추가 피해를 입습니다.':
        'Creates a wall of cold flames that does <mag> frost damage per second. Targets on coldfire take extra damage over time.',
    '초당 <mag> 냉기 피해를 입힙니다. 냉기 화염 대상은 시간이 지남에 따라 추가 피해를 입습니다.':
        'Does <mag> frost damage per second. Targets on coldfire take extra damage over time.',
    '<mag> 냉기 피해를 입힙니다. 냉기 화염 대상은 시간이 지남에 따라 추가 피해를 입습니다.':
        'Does <mag> frost damage. Targets on coldfire take extra damage over time.',
    '넓은 지역에 <mag> 냉기 피해를 입힙니다. 냉기 화염 대상은 시간이 지남에 따라 추가 피해를 입습니다.':
        'Does <mag> frost damage in a wide area. Targets on coldfire take extra damage over time.',
    '광범위한 지역에 최대 <mag> 냉기 피해를 입힙니다. 근처에 있는 대상은 추가 피해를 입습니다. 냉기 화염 대상은 시간이 지남에 따라 추가 피해를 입습니다.':
        'Does up to <mag> frost damage over a large area; targets nearby take extra damage. Targets on coldfire take extra damage over time.',
    '근접 범위에 있는 적에게 <mag> 냉기 피해를 입힙니다. 냉기 화염 대상은 시간이 지남에 따라 추가 피해를 입습니다.':
        'Does <mag> frost damage to enemies at close range. Targets on coldfire take extra damage over time.',
    '적이 접근하면 폭발하여 <mag> 냉기 피해를 입히는 룬을 생성합니다. 냉기 화염 대상은 시간이 지남에 따라 추가 피해를 입습니다.':
        'Creates a rune that explodes when an enemy comes near, doing <mag> frost damage. Targets on coldfire take extra damage over time.',
}
# phrases for everything else (book titles, recipes, staves, scrolls): longest first
PHRASES = [
    ('아트로나크 포지 레시피 - ', 'Atronach Forge Recipe - '), ('아트로나크 포지 제작서 - ', 'Atronach Forge Recipe - '),
    ('마법부여 되지 않은 파괴의 지팡이', 'Unenchanted Destruction Staff'),
    ('최상금 냉기 화염룬', 'Master Coldfire Rune'), ('최상금 냉기 화염 룬', 'Master Coldfire Rune'),
    ('최상급 냉기 화염 룬', 'Master Coldfire Rune'), ('상급 냉기 화염 룬', 'Greater Coldfire Rune'),
    ('상급 냉기 화염', 'Greater Coldfire'), ('최상급 냉기 화염', 'Master Coldfire'),
    ('차가운 화염 벽', 'Wall of Cold Flames'), ('차가운 불꽃의 벽', 'Wall of Cold Flames'),
    ('차가운 불꽃', 'Cold Flames'), ('냉기 화염 연소', 'Cold Incineration'), ('냉기 연소', 'Cold Incineration'),
    ('냉기 화염 폭설', 'Coldfire Blizzard'), ('냉기 화염 폭풍', 'Coldfire Storm'), ('콜드 화염 폭풍', 'Coldfire Storm'),
    ('폭풍 냉기 화염', 'Coldfire Storm'), ('냉기 화염 망토', 'Coldfire Cloak'),
    ('냉기 붙타는 손길', 'Cold Burning Touch'), ('냉기 불타는 손길', 'Cold Burning Touch'),
    ('냉기 화염 손길', 'Coldfire Touch'), ('냉기 화염 볼트', 'Coldfire Bolt'), ('냉기 화염구', 'Coldfire Ball'),
    ('냉기 화염룬', 'Coldfire Rune'), ('냉기 화염 룬', 'Coldfire Rune'), ('거머쥔 냉기 화염', 'Clutching Coldfire'),
    ('냉기 폭발', 'Cold Blast'), ('검은 냉기', 'Black Frost'), ('냉기 화염', 'Coldfire'), ('냉기 룬', 'Frost Rune'),
    ('냉기 소금', 'Frost Salts'), ('냉기소금', 'Frost Salts'), ('주문서', 'Spell Tome'), ('마법책', 'Spell Tome'),
    ('소울 젬', 'Soul Gem'), ('소울젬', 'Soul Gem'), ('뼛가루', 'Bone Meal'), ('사파이어', 'Sapphire'),
    ('태워서 재로 만들다', 'Incinerate'), ('화염의 벽', 'Wall of Flames'), ('화염 볼트', 'Firebolt'),
    ('화염볼트', 'Firebolt'), ('불꽃 볼트', 'Firebolt'), ('불꽃 룬', 'Fire Rune'), ('불꽃룬', 'Fire Rune'),
    ('화염구', 'Fireball'), ('불꽃 망토', 'Flame Cloak'), ('폭풍 불', 'Fire Storm'), ('불꽃', 'Flames'),
    ('</폰트>', '</font>'), ('불', 'Fire'),
]


def staff_and_scroll(s):
    """'X 지팡이' / 'X의 지팡이' -> 'Staff of X'; 'X 두루마리' -> 'Scroll of X' (after the phrase pass)."""
    s = re.sub(r'^(Atronach Forge Recipe - )(.*?)\s*의?\s*지팡이\s*$', lambda m: m.group(1) + 'Staff of ' + m.group(2).strip(), s)
    s = re.sub(r'^(.*?)\s*의?\s*지팡이\s*$', lambda m: 'Staff of ' + m.group(1).strip(), s)
    s = re.sub(r'^(.*?)\s*두루마리\s*$', lambda m: 'Scroll of ' + m.group(1).strip(), s)
    return s


def translate(s):
    key = re.sub(r'\s+', ' ', s).strip()
    if key in NAMES:
        return NAMES[key]
    out = re.sub(r'(?<=\S) {2,}(?=\S)', ' ', s)    # the source has stray double spaces inside phrases
    for k, v in sorted(PHRASES, key=lambda kv: -len(kv[0])):
        out = out.replace(k, v)
    out = staff_and_scroll(out)
    out = re.sub(r'Spell Tome\s*:\s*', 'Spell Tome: ', out)
    if not HANGUL.search(s):
        return s
    return re.sub(r'[ \t]+$', '', re.sub(r'(?<=\S)[ \t]{2,}(?=\S)', ' ', out))


def subs(body):
    i = 0
    while i + 6 <= len(body):
        t = body[i:i+4]; n = struct.unpack_from('<H', body, i+4)[0]
        yield t, body[i+6:i+6+n]; i += 6 + n


changed = []
left = []


def fix_record(rtype, body):
    out = []
    dirty = False
    for t, v in subs(body):
        ts = t.decode('latin1')
        is_text = ts in TEXT or (ts == 'DNAM' and rtype == 'MGEF') or (ts == 'CNAM' and rtype == 'BOOK')
        if is_text:
            try:
                s = v.rstrip(b'\0').decode('utf-8')
            except UnicodeDecodeError:
                s = None
            if s is not None and HANGUL.search(s):
                new = translate(s)
                if HANGUL.search(new):
                    left.append((rtype, ts, s, new))
                changed.append((rtype, ts, s, new))
                v = new.encode('utf-8') + b'\0'
                dirty = True
        out.append(t + struct.pack('<H', len(v)) + v)
    return b''.join(out), dirty


def walk(d, o, e):
    res = []
    while o < e:
        t = d[o:o+4]; n = struct.unpack_from('<I', d, o+4)[0]
        if t == b'GRUP':
            inner = walk(d, o + 24, o + n)
            res.append(d[o:o+4] + struct.pack('<I', 24 + len(inner)) + d[o+8:o+24] + inner)
            o += n; continue
        hdr = bytearray(d[o:o+24]); fl = struct.unpack_from('<I', d, o+8)[0]
        body = d[o+24:o+24+n]; o += 24 + n
        raw = zlib.decompress(body[4:]) if fl & 0x40000 else body
        new, dirty = fix_record(t.decode('latin1'), raw)
        if dirty:
            if fl & 0x40000:
                body = struct.pack('<I', len(new)) + zlib.compress(new)
            else:
                body = new
            struct.pack_into('<I', hdr, 4, len(body))
        res.append(bytes(hdr) + body)
    return b''.join(res)


for path in sys.argv[1:]:
    changed.clear(); left.clear()
    d = open(path, 'rb').read()
    head = 24 + struct.unpack_from('<I', d, 4)[0]
    out = d[:head] + walk(d, head, len(d))
    name = path.replace(chr(92), '/').split('/')[-1]
    if left:
        print('NOT WRITTEN %s: %d strings still Korean' % (name, len(left)))
        for x in left[:20]:
            print('   ', x)
        continue
    if changed:
        open(path, 'wb').write(out)
    print('%-34s %3d strings translated' % (name, len(changed)))
    for rtype, ts, s, new in changed[:400]:
        print('   %s.%s  %s  ->  %s' % (rtype, ts, s.replace('\n', ' / ')[:60], new.replace('\n', ' / ')[:70]))

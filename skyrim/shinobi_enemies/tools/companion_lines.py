"""Voice lines for the companion brain (data only; exec'd by build_sne_esp.py and copy_companion_voice.py).

Each line becomes its own topic (DIAL + one INFO) owned by quest SNE_CQ, so the script can Say() an exact line.
Voice files are copies of the companions' existing recordings, renamed to the path the engine expects for our INFO:
  Sound/Voice/Shinobi Enemies.esp/<voice type>/<quest>_<topic>_<INFO id 00000xxx>_1.fuz
(if len(quest)+len(topic) > 25 the engine uses quest[:10] and topic[:15]; our names are short enough).

source: 'sda'   = Serana Dialogue Add-On (SeranaDialogAddon.bsa, folder seranadialogaddon.esp/dlc1seranavoice)
        'dg'    = Dawnguard (KerstynVoices revoice loose files first, else Skyrim - Voices_en0.bsa)
        'ashe'  = Ashe - Fire and Blood.bsa (folder ashe - fire and blood.esp/mm_ashevoice)
id = the source INFO's local form ID (as in the source voice file name).
emotion: 0 neutral, 1 anger, 3 fear, 4 sad, 5 happy, 6 surprise
"""
QUEST = 'SNE_CQ'
SERANA_VT, ASHE_VT = 'DLC1SeranaVoice', 'MM_AsheVoice'
# (topic EDID, category, source, id, emotion, text)
LINES = [
    # --- Serana ---
    ('SNE_SStart1', 'SerStart', 'sda', 0xF10114, 1, "There they are!"),
    ('SNE_SStart2', 'SerStart', 'sda', 0xB4B54C, 1, "There they are- come on, let's get them!"),
    ('SNE_SSurround', 'SerSurrounded', 'sda', 0x3F7CA6, 6, "How many of you are there?!"),
    ('SNE_STough', 'SerTough', 'sda', 0xF10104, 3, "These are some tough opponents. Keep your guard up."),
    ('SNE_SStagger', 'SerStagger', 'sda', 0x3F7CB0, 1, "Get it now while we can!"),
    ('SNE_SWatch', 'SerWatch', 'sda', 0x14FEE6, 0, "Hey, watch your footwork! Don't let them hit you, you're making vampire-kind look bad!"),
    ('SNE_SPanic1', 'SerPanic', 'sda', 0xF10103, 3, "Are you okay?! Just stay close, and you'll be fine."),
    ('SNE_SPanic2', 'SerPanic', 'dg', 0x003F46, 3, "Are you alright? Come on, we can do this. I know we can."),
    ('SNE_SAngry1', 'SerAngry', 'sda', 0x0F5DF8, 1, "If you lay one finger on my sweetheart... you're gonna get what's coming to you!"),
    ('SNE_SAngry2', 'SerAngry', 'sda', 0xB4643A, 1, "Hurts, doesn't it?"),
    ('SNE_SAngry3', 'SerAngry', 'sda', 0xB46439, 1, "Death to you!"),
    ('SNE_SAngry4', 'SerAngry', 'dg', 0x012DC0, 1, "I'll bring you down!"),
    ('SNE_SAngry5', 'SerAngry', 'dg', 0x010DCA, 1, "It's time for you to suffer!"),
    ('SNE_SRescue', 'SerRescue', 'sda', 0x5D8DDE, 1, "Stay away from him!"),
    ('SNE_SAfter1', 'SerAfterHurt', 'sda', 0x5501F3, 4, "Are you alright? You don't look so good."),
    ('SNE_SAfter2', 'SerAfterHurt', 'sda', 0xF10119, 0, "Heal up if you can. We may be in for more trouble."),
    # --- Ashe ---
    ('SNE_AStart1', 'AsheStart', 'ashe', 0x18B7D6, 0, "Target acquired."),
    ('SNE_AStart2', 'AsheStart', 'ashe', 0x18B7D4, 0, "Enemy presence confirmed. Engaging."),
    ('SNE_AFlank', 'AsheFlanker', 'ashe', 0x0B6C8A, 1, "Eliminating threat!"),
    ('SNE_AStagger1', 'AsheStagger', 'ashe', 0x0B6C8B, 1, "You let your guard down!"),
    ('SNE_AStagger2', 'AsheStagger', 'ashe', 0x18B7BB, 1, "Push the attack!"),
    ('SNE_AWin1', 'AsheWinning', 'ashe', 0x18B7C8, 5, "Our tactics are superior!"),
    ('SNE_AWin2', 'AsheWinning', 'ashe', 0xEBDEB2, 0, "Your movements are predictable."),
    ('SNE_AGuard', 'AsheGuard', 'ashe', 0x18B7BD, 1, "No hesitation!"),
    ('SNE_AAfter', 'AsheAfterHurt', 'ashe', 0x580093, 4, "Are you hurt? Let me see."),
    ('SNE_AShut1', 'AsheShutdown', 'ashe', 0x0B6CA6, 3, "FCS corrupted..."),
    ('SNE_AShut2', 'AsheShutdown', 'ashe', 0xEBDEA1, 3, "Systems... failing..."),
    ('SNE_AShut3', 'AsheShutdown', 'ashe', 0x0B6CA7, 3, "IMU damaged..."),
]
LINE_BASE = 0x830    # line i: DIAL = LINE_BASE + 2i, INFO = LINE_BASE + 2i + 1 (append-only, saves may reference them)
def line_ids(i): return LINE_BASE + 2 * i, LINE_BASE + 2 * i + 1
CATEGORIES = []
for _l in LINES:
    if _l[1] not in CATEGORIES: CATEGORIES.append(_l[1])
def voice_type(source): return ASHE_VT if source == 'ashe' else SERANA_VT
def voice_name(topic, info_local_id):
    q, t = QUEST, topic
    if len(q) + len(t) > 25: q, t = q[:10], t[:15]
    return f'{q}_{t}_{info_local_id:08X}_1.fuz'.lower()

# --- generic vanilla lines (any voice type that recorded them; copied by copy_generic_voice.py) ---
# Warlock arrogance (2026-10-15): owned by quest SNE_WQ.
GENERIC_QUEST = 'SNE_WQ'
DG = 0x2000000    # marks a source INFO id from Dawnguard.esm
# voice types that recorded Dawnguard's "My Lady." (DLC1DialogueVampireBase 0x0200324B); uniques left out
MY_LADY_VOICES = {'MaleElfHaughty': 0x13AF0, 'MaleNord': 0x13AE6, 'MaleCommander': 0x13AD8, 'MaleYoungEager': 0x13AD1,
                  'MaleNordCommander': 0xE5003, 'FemaleNord': 0x13AE7, 'FemaleCommander': 0x13AE3}
GENERIC_BASE = 0xA00    # line i: DIAL = GENERIC_BASE + 2i, INFO = GENERIC_BASE + 2i + 1
# (topic EDID, category, Skyrim.esm INFO id, emotion, text)
GENERIC = [
    ('SNE_WWarn1', 'WarlockWarn', 0x06CB2D, 1, "Hey, watch it!"),
    ('SNE_WWarn2', 'WarlockWarn', 0x023C19, 1, "Watch it!"),
    ('SNE_WSnap1', 'WarlockSnap', 0x0D361B, 1, "How dare you!"),
    ('SNE_WSnap2', 'WarlockSnap', 0x02A469, 1, "Why you..."),
    ('SNE_WSnap3', 'WarlockSnap', 0x0C2137, 1, "If you're planning violence against me or mine, you'll regret it."),
    # vampires turning for Serana (2026-10-16). DG flag = Dawnguard.esm line (sound/voice/dawnguard.esm/...)
    ('SNE_VMyLady', 'TurnMyLady', DG | 0x00324B, 0, "My Lady."),
    ('SNE_VObey', 'TurnObey', 0x0E0CBE, 5, "Whatever you say!"),
    # Thalmor superiority (2026-10-16); only the two ElfHaughty voice types recorded these
    ('SNE_TCont1', 'ThalContempt', 0x0967BF, 5, "Ha ha ha ha ha! You wish to defeat me? Impossible."),
    ('SNE_TCont2', 'ThalContempt', 0x09679E, 1, "Time for you humans to learn your place!"),
    ('SNE_TCont3', 'ThalContempt', 0x0967AA, 0, "Behold, the future. Behold, the Thalmor!"),
    ('SNE_TCont4', 'ThalContempt', 0x0968AF, 0, "Not impressed!"),
    ('SNE_TFlea', 'ThalFlea', 0x01770F, 5, "Ha! Like the bite of a flea!"),
    ('SNE_TSer1', 'ThalSerious', 0x06CCE2, 1, "You should not have meddled in the Thalmor's affairs."),
    ('SNE_TSer2', 'ThalSerious', 0x06CCE3, 1, "The Thalmor's memory is long."),
    ('SNE_TSer3', 'ThalSerious', 0x09671B, 1, "Fear the Thalmor!"),
    ('SNE_TSer4', 'ThalSerious', 0x09687D, 1, "Enough... of this!"),
    ('SNE_TPanic1', 'ThalPanic', 0x017708, 3, "Mercy!"),
    ('SNE_TPanic2', 'ThalPanic', 0x01770B, 3, "No more! I yield! I yield!"),
    ('SNE_TPanic3', 'ThalPanic', 0x0D3614, 3, "Help me, help me!"),
    ('SNE_THeretic', 'ThalHeretic', 0x0966B2, 1, "Fall to the Thalmor!"),
]
def generic_ids(i): return GENERIC_BASE + 2 * i, GENERIC_BASE + 2 * i + 1
def generic_voice_name(topic, info_local_id):
    q, t = GENERIC_QUEST, topic
    if len(q) + len(t) > 25: q, t = q[:10], t[:15]
    return f'{q}_{t}_{info_local_id:08X}_1.fuz'.lower()

# Black screen after loading a save (Hokage Obito installs) - debug hand-over (2026-10-19)

## Symptom
Loading ANY save (Legacy Daedric Gallery or open world) ends on a black loading screen that never closes, while the
game runs behind it (ambient sound, abilities/scripts firing). No crash log. Started after the Hokage Obito installs.

## PLAY PROFILE: "1.5.97 SAFE" (made 2026-10-19 23:15)
= main 1.5.97 minus Mouse Tracker V1.5, Weapon Art 3.2.7, Aether Gazer Kagutsuchi (needs Weapon Art's
EldenSkyrim_RimSkills.esp), MCO Ishida Mitsunari (never tested), MCO Jetstream Sam (never in a LOADING test - the old
"Sam cleared" note was wrong: A and C both black doesn't clear it). Keeps NEAE 3.0 + Vergil compat, PIM, AutoCancel,
po3, Elden Base 3.7.5, Katana. Status: NOT CONFIRMED YET (first load pending). Policy: user plays on SAFE; add a mod
back to SAFE only after a test proves it loads. Next candidates to try adding one at a time: Sam, Mitsunari.

### Results 2026-10-20 (round of 7)
SAFE loads; G (Sam+Mitsunari) loads -> ADDED to SAFE (SAFE == Test G now; old lists *.before-sam.txt);
W1 (WA plugin off) loads, W2 (WA no scripts) black -> Weapon Art cause = its PLUGIN records;
F3d (no idle) black, F3e (no quest) LOADS, F3f (no ESL) black -> Mouse Tracker cause = MouseTrackerQuest.
Analysis: MT quest = StartGameEnabled|RunOnce, forced PlayerRef alias with alias script. Flag 0x10 is NOT special (1486
SAFE quests have it). Sam's SamScabbardQuest (SGE, forced PlayerRef, alias spell, NO scripts) loads fine. Weapon Art
has 3 SGE player-alias quests, 2 with scripts (EldenUpdate, ERBWQuest). Theory: a NEW scripted start-game quest hangs
this save/load order. Papyrus logs from black sessions (19:54-20:11): VM freezes AND thaws, OnPlayerLoadGame handlers
run, then the log stops ~15 s later (working session keeps logging) -> stall happens after load, cause unseen.

### Results 2026-10-20 round 2
H + `coc Riverwood` (no save) LOADS; H + Obito save black -> SAVE-SPECIFIC clash, mods are fine on a fresh start.
F3g (MT quest kept, script binding stripped) black -> script binding NOT the trigger; the quest itself is.
W3 (Weapon Art minus its 3 quests) LOADS -> Weapon Art's trigger is also a quest.
Remaining difference vs Sam's working quest: RUN ONCE flag (DNAM 0x100) - on MouseTrackerQuest and WA's ERBWQuest,
not on Sam's SamScabbardQuest nor WA's other two quests.

### CLOSED 2026-10-20
New game on main 1.5.97 (full Hokage set + restored-files mod) CONFIRMED by user. Cleanup done: 23 Test profiles
(saves junctions removed first; 283 saves intact) and 10 `* - TEST *` mod copies deleted. Kept: 1.5.97, 1.5.97 SAFE
(old save), 1.5.97 pre-Hokage, 1.5.97-copy, Default, mod `Hokage - restored test-hidden files`. Originals verified.

### New playthrough prep (2026-10-20) - debugging STOPPED by user choice
- Cause inside the old save never found; no more cause-hunting. Old save -> "1.5.97 SAFE"; new game -> main "1.5.97".
- Made mod `Hokage - restored test-hidden files` (originals of NEAE 3.0 soundplay+ThrowAttack BDI jsons, Weapon Art
  EldenPayload BDI json, Sam's meshes/weapons/ebonyblade incl. scabbehaviors/wpbehaviors; verified identical) and
  enabled it at TOP priority in main only (backup modlist.before-restored-files-20261020.txt). SAFE untouched.
- Pending: user's new-game check on main (new game -> save -> quit to menu -> reload). Passes -> clean up Test
  profiles + `* - TEST *` mod copies. Fails -> retry main with the restore mod off to rule it out.

### Results 2026-10-20 round 3 + DECISION
F3h (MT, RunOnce cleared) black; W4 (WA RunOnce cleared + Kagutsuchi) black (SKSE logs 03:59 confirm W4) -> RunOnce is
NOT the trigger. Unexplained save-side clash with new start-game quests (Sam's works, MT's/WA's don't).
DECISION (user): start a NEW Obito playthrough. Old save stays playable on "1.5.97 SAFE".
Next: user does new game on main "1.5.97" (full Hokage set incl. original MT/WA/Kagutsuchi) -> save -> reload.
Passes -> main = new playthrough profile; then optionally restore the 3 hidden BDI jsons (*.mohidden in NEAE 3.0 /
Weapon Art) with one load test; then clean up all Test profiles + `* - TEST *` mod copies (WA copies are hard-linked:
deleting them does not touch the original).

### Round queued 2026-10-20 round 3 (the candidate FIX)
| Profile | Contents | Result |
|---|---|---|
| Test F3h - SAFE + MouseTracker no RunOnce | mod copy `Mouse Tracker V1.5 - TEST no RunOnce` (esp differs by 1 byte: quest 0x800 flags 0x111->0x11; script kept) | ? |
| Test W4 - SAFE + WeaponArt no RunOnce + Kagutsuchi | mod copy `Elden Rim - Weapon Art 3.2.7 - TEST no RunOnce` (hard-linked; own esp, ERBWQuest 0xB8AA flags 0x101->0x1) + Kagutsuchi (no quests) | ? |
Both load -> FIX: make these the real installs (rename copies, or patch originals after backup), add to SAFE.
Still black -> RunOnce isn't it; next compare = quest priority/alias details or a save-side check.

### Round queued 2026-10-20 (all on SAFE base)
| Profile | Contents | Result |
|---|---|---|
| Test H - SAFE + MouseTracker (try coc) | full Mouse Tracker; load save (expect black) AND, separately, main-menu console `coc Riverwood` (no save) | ? |
| Test F3g - SAFE + MT quest no scriptbind | mod copy `TEST quest no scriptbind` (quest kept, VMAD stripped = like Sam's) | ? |
| Test W3 - SAFE + WeaponArt no quests | mod copy `Elden Rim - Weapon Art 3.2.7 - TEST no quests` (hard-linked, own esp with 3 QUST dropped) | ? |
H coc loads -> save-specific (something in this save blocks new scripted quests; fix there, not in mods).
F3g loads -> script binding on new quest is the trigger; W3 loads -> Weapon Art is the same problem.

### Round queued 2026-10-19 23:30 (user runs all in one sitting, reports results together)
| Profile | Contents | Result |
|---|---|---|
| 1.5.97 SAFE | see above | ? |
| Test G - SAFE + Sam + Mitsunari | both on | ? (loads -> add both to SAFE; black -> split) |
| Test W1 - SAFE + WeaponArt plugin off | Weapon Art 3.2.7 loose files only | ? |
| Test W2 - SAFE + WeaponArt no scripts | mod copy `Elden Rim - Weapon Art 3.2.7 - TEST no scripts` (HARD-LINKED to the original; scripts dir renamed .mohidden) + plugin on | ? |
| Test F3d / F3e / F3f | Mouse Tracker plugin minus IDLE / QUST / ESL flag (on pre-Hokage base) | ? |
W1 black -> loose files; W1 loads + W2 black -> plugin records; W2 loads -> scripts.
Cleanup: deleting the hard-linked TEST copy only removes the links - original is unaffected. Never edit files inside it.

## Profiles (MO2, all share the saves folder via a junction to profiles\1.5.97\saves)
| Profile | Contents | Result |
|---|---|---|
| 1.5.97 pre-Hokage | load order before any Hokage install | WORKS |
| Test A - batch 1 | + NEAE 3.0 (1.6.5 off), Vergil compat, Sam, Mouse Tracker, PIM, AutoCancel, po3 Papyrus Extender | black |
| Test B - batch 2 | + Elden Base 3.7.5 (3.5.6 off), Weapon Art full, Katana, Kagutsuchi, po3 | black |
| Test C - batch 1 no Sam | A without Sam | black |
| Test D - batch 2 no WeaponArt | Elden Base 3.7.5 + Katana + po3 | WORKS |
| 1.5.97 (main) | everything, with the new BDI jsons hidden (see below) | black |
| Test E - NEAE 3.0 only | pre-Hokage + NEAE 3.0 + _Extra + Vergil compat | WORKS (2026-10-19) |
| Test F - MouseTracker PIM AutoCancel | pre-Hokage + those 3 | black (2026-10-19, SKSE logs 21:27 confirm) |
| Test F1 - AutoCancel + PIM | pre-Hokage + AutoCancelTDMLockOn + PIM | WORKS |
| Test F2 - PIM only | pre-Hokage + Papyrus Ini Manipulator 1.9.9 | WORKS |
| Test F3 - MouseTracker + PIM | pre-Hokage + Mouse Tracker V1.5 + PIM | black (SKSE logs 21:41 confirm) |
| Test F3a - MouseTracker no dtry mouse ini | F3 but mod copy `Mouse Tracker V1.5 - TEST no dtry ini` (dtryKeyUtil MouseTracker.ini .mohidden) | black (logs 21:51) -> dTry mouse section CLEARED |
| Test F3b - MouseTracker plugin off | F3 with MouseTracker.esp unticked (loose files only: PIE ChargeAttack.ini, inis, KeyCodes.txt) | WORKS -> loose files cleared |
| Test F3c - MouseTracker no script | F3 but mod copy `Mouse Tracker V1.5 - TEST no script` (mousetracker.pex .mohidden) | black (logs 22:53) -> script cleared, cause is in the PLUGIN |
| Test F3d - MT no script no idle | mod copy `TEST noscript-noidle` (IDLE 0xD7A dropped) | NOT TESTED YET |
| Test F3e - MT no script no quest | mod copy `TEST noscript-noquest` (QUST 0x800 dropped) | NOT TESTED YET |
| Test F3f - MT no script not ESL | mod copy `TEST noscript-noesl` (TES4 ESL flag 0x200 cleared) | NOT TESTED YET |

So: batch 1 culprit is MOUSE TRACKER V1.5 (F1/F2 load, F3 black; NEAE 3.0, PIM, AutoCancel cleared); batch 2 culprit is Weapon Art
and/or Kagutsuchi. Cleared: Sam, Elden Base 3.7.5, Katana Crafting, Papyrus Extender.

## Ruled out so far
- NEAE 1.6.5 -> 3.0 FormID renumbering: the save's formID array has 0 NEAE forms.
- Sam's Ebony Blade model (behaviour-graph nif on Legacy's 6 statues) - hidden as `ebonyblade.mohidden`, still black.
- Player behaviour/skeleton overrides, unconditional OAR/DAR sets, missing masters, fade scripts - none.
- BehaviorDataInjector jsons: failing profiles had extra ones (NEAE 3.0 soundplay/ThrowAttack, Weapon Art
  EldenPayload); hid them (NEAE 3.0 soundplay = 1.6.5's copy, originals *.mohidden) -> main still black.
  (Leave hidden until the real cause is found, then restore.)

## Leads left
- dTry Key Utils configs: both failing batches add one (Mouse Tracker `mousetracker.ini`, NEAE 3.0 `neaehotkey.ini`
  changed vs 1.6.5, Weapon Art `eldenkey.ini`).
- Payload Interpreter configs (both add many), NEAE 3.0's 11 vanilla effect nif replacements (fxemptyobject.nif has a
  NiTransformController), SPID DISTR inis (NEAE perks to all NPCs, Weapon Art keywords).

## Next steps
0000. (2026-10-19 23:00) Cause is MouseTracker.esp itself (not script, not loose files). With no script the only
   records live at load are the start-game QUST (alias PlayerRef, no spells/packages) and the IDLE under PowerAttack;
   plus the plugin is ESL-flagged (1.5.97 + Backported ESL). F3d loads -> IDLE (then check Weapon Art's FallRoot/LandRoot
   overrides + orphan idles); F3e loads -> quest; F3f loads -> ESL flag (then check which Weapon Art/Kagutsuchi plugins
   are ESL-flagged). All black -> spells/MGEF/KYWD (unexpected; drop groups next). Tools: scratchpad esp_edit.py
   (drop records / clear ESL), idle_tree.py, idle_scan.py. Cleanup: delete all `Mouse Tracker V1.5 - TEST *` mods.
000. (old) (2026-10-19 22:00) Cleared inside Mouse Tracker: dTry mouse ini (F3a) and its IDLE PerformPowerAttackMT - the
   working pre-Hokage list has the same first-sibling collision (NEAE 1.6.5 YMDTPowerAttack under PowerAttack) and
   many orphan idles (scratchpad idle_scan.py). Read F3b/F3c: F3b black -> loose files (PIE ChargeAttack.ini or
   MouseTracker.ini/KeyCodes.txt); F3b loads + F3c loads -> the quest script (pex: OnInit/OnPlayerLoadGame TrackOn,
   RegisterForMenu Journal Menu, DrawWeapon/Cast; shipped .psc is OLDER than the pex); F3b loads + F3c black ->
   plugin records (quest/MGEF/SPEL; MGEF scripts AbilityTauntEffect = Elden Rim's, RemoveSpellOnEvent missing).
   Cleanup later: also delete mod copy `Mouse Tracker V1.5 - TEST no script`.
00. (old) LEAD (2026-10-19): only Mouse Tracker and Weapon Art (both black) ship a dTry Key Utils `[KeyTrace_EventID_Mouse]`
   section (Mouse Tracker: RMB_hold=257, LMB_hold=256; Weapon Art's is empty). NEAE 3.0 / Vergil / SDT (load fine) have
   none. Test F3a: black -> the dtry ini is innocent, next suspect is Mouse Tracker's new IDLE PerformPowerAttackMT
   (parent 0x000E8456, no previous sibling) or its quest/PIE config. Loads -> dTry mouse section is the cause: then
   test Weapon Art with its EldenKey.ini `[KeyTrace_EventID_Mouse]` header removed; fix = drop/patch those sections.
   Cleanup later: delete mod copy `Mouse Tracker V1.5 - TEST no dtry ini` + Test profiles.
0. (done) (2026-10-19) User tests F1/F2/F3 (restart MO2 first so new profiles show). F2 black -> PIM itself (DLL/version);
   F2 loads but F1 or F3 black -> that mod. Neither mod's scripts run at load (AutoCancel = anim-event spells,
   MouseTracker = key/control events + OnPlayerLoadGame RegisterForKey), so a PIM-level cause is the top suspect.
   Note: each launch overwrites SKSE logs, check them right after the run you care about.
1. (old) User tests E and F (open-world save). Whichever is black -> split that one further (for E: hide NEAE 3.0's
   dtryKeyUtil ini / DISTR ini / vanilla nifs one group at a time; for F: one mod at a time).
2. Same for batch 2: Weapon Art pieces (eldenkey.ini, DISTR, seq, PIE configs).
3. Once found: apply the fix in main 1.5.97, restore the hidden BDI jsons if innocent, delete Test A-F profiles.
Backups of main's lists: profiles\1.5.97\_backup_* (neae3 = pre batch 1, elden375 = pre batch 2, minimal, po3).
Tools: scratchpad wiz/vfs_diff.py, skse_diff.py, master_check.py, ess_forms.py (Python -I).

# Hokage Obito: moveset prep (2026-10-19)

Three MCO movesets downloaded by the user, scanned (Windows Defender: no threats), surveyed and staged in MO2 as
**new, unenabled** mods. Nothing in the load order changed.

## What each one is

| | Jetstream Sam Remake 1.2.1 | Basara Ishida Mitsunari | Aether Gazer Kagutsuchi |
|---|---|---|---|
| Author | Yong ri ming | Yong ri ming | Serah |
| Animations (hkx) | **390** (Vergil: 396) | 231 | 134 |
| Move condition sets | **61** (OAR) | 23 (OAR) | 42 (DAR) |
| Directional (Keytrace) sets | ~20 | 7 | ~25 |
| Weapon it is tied to | vanilla **Ebony Blade** (Skyrim.esm 0x4A38F, 0xEA29C), player only | **Dai-Katanas** (KatanaCrafting.esp keyword 0x157; its plugin adds 28 Dai-Katanas) | its own weapons (AetherGazer.esp keyword 0x80A; 6 WEAP) |
| Plugin | sam_counter.esp (ESL; masters Skyrim, Dawnguard, Dragonborn, EldenSkyrim, NotEnoughAttackEffect, **MouseTracker**) | MCO Ishida Mitsunari.esp (ESL; masters Skyrim, Dawnguard, Hearthfires, Dragonborn, **KatanaCrafting**, **MouseTracker**, NotEnoughAttackEffect) | AetherGazer.esp (ESL; masters Skyrim, Dragonborn, EldenSkyrim, **EldenSkyrim_RimSkills**) |
| Highlights | basic combos, 4 boss combos, charged attacks, charge and rapid slash skills, throws, counters, block break, air dashes, quick dodges, Zandatsu, 5 killmove sets, taunts | battojutsu, Repentance / Purge / Dirge / Suppression / Annihilation, Pursuit (teleport in front of the enemy), aerial set, perfect block, decapitation | many directional one-off skills, dashes, fire VFX (48 MGEF, 39 SPEL, 18 ARTO, PIE configs) |
| Lore fit (see project notes) | **main moveset**: Uchiha lineage, rebuilt right arm, the rival who passes his blade on, gap-closing speed | a dark-path / vengeful Obito, or a Ronin variant | the **Fire Release** layer (Kagutsuchi = the fire god, Uchiha mythology) |

Because each is tied to a different weapon, all three can be enabled together without overriding Vergil (Yamato
keyword) or each other.

## Missing requirements (need downloads: ask the user first)

| Needed by | Mod | Status |
|---|---|---|
| Sam, Mitsunari | **Mouse Tracker** (MouseTracker.esp + DLL) | missing - a master of both plugins, they will not load without it |
| Sam (its page) | **Papyrus Ini Manipulator** (Nexus SE 65634) | missing - also fixes VergilSDT ignoring its ini |
| Mitsunari | **Katana Crafting** (Nexus SE 5306) + its SE patch (Nexus SE 106441) | missing - a master |
| Mitsunari | **Sprint Start and Stop** | missing (2 condition sets use it) |
| Mitsunari | AutoCancelTDMLockOn | missing (only for Decapitation) |
| Kagutsuchi | **Elden Rim 3.7.0** (EldenSkyrim_RimSkills.esp) | user has 3.5.4 without it - a master; updating means REPLACING an installed mod: ask |

Already installed: Keytrace / dTry's Key Utils, NEAE, TDM, Elden Counter, LotD, BDI, DAC, Modern Stagger Lock, OAR,
Payload Interpreter, IFrame Generator RE, Precision, DMCO, One Click Power Attack, For Honor movesets, Elden Rim base.

## Notes from the survey
- The archives are the authors' working copies: nested .7z backups of animation folders, duplicate plugins in
  scripts/ and skse/, and helper .bat/.ps1 scripts. Staging left out the .bat/.ps1, `backup/` and the duplicate
  ("副本") plugins; the nested .7z files are inert (the game never opens them).
- Sam ships `patch_1.5` folders inside its Killmove sets - likely versions for the 1.5.97 game; check before enabling.
- Mitsunari's skse/ folder also holds a copy of KatanaCrafting.esp (an author backup; it is not loaded from there).

## Staged as (MO2 mods, not enabled)
- `[Staged] MCO Jetstream Sam Remake 1.2.1`
- `[Staged] MCO Ishida Mitsunari`
- `[Staged] Aether Gazer Kagutsuchi`

## Plan for the build session
1. Ask: download Mouse Tracker + Papyrus Ini Manipulator (Sam), and decide on Elden Rim 3.7.0 (Kagutsuchi) and Katana
   Crafting (Mitsunari, later).
2. Enable Sam first (MO2 closed), on an Ebony Blade, and test the raw moveset.
3. Retarget Sam's OAR conditions from the Ebony Blade to a Hokage Obito weapon / mode effect (like Ronin's Yamato
   hooks), so it is Obito's moveset, not the Ebony Blade's.
4. Layer the Hokage kit on top: Kamui Hiraishin (tagged kunai), Copy Wheel, Leaf jutsu, Kamui Shuriken.
5. Kagutsuchi as a Fire Release stance once Elden Rim 3.7 is sorted; Mitsunari kept for a dark-path Obito.

## Download links (2026-10-19)
- Papyrus Ini Manipulator: https://www.nexusmods.com/skyrimspecialedition/mods/65634
- Katana Crafting: https://www.nexusmods.com/skyrimspecialedition/mods/5306 (+ SE patch https://www.nexusmods.com/skyrimspecialedition/mods/106441)
- Elden Rim 3.7.0: https://www.nexusmods.com/skyrimspecialedition/mods/65625 (replaces the installed 3.5.4: ask)
- Mouse Tracker + AutoCancelTDMLockOn: author Patreon https://www.patreon.com/c/yrm708966080/posts; possibly inside the
  dwemermods bundle "Yong Ri Ming Animations" (https://www.dwemermods.com/mods/1529, 358 MB, all his MCO sets) - unconfirmed
- Sprint Start and Stop: exact mod not found (nearest guess Nexus SE 141076, unconfirmed); not a master
- Stances (fallback): https://nexusmods.com/skyrimspecialedition/mods/40484 ; Stances NG https://nexusmods.com/skyrimspecialedition/mods/117986
- Also seen: "MCO Mirage Edge 1.2 by Yong ri ming" (dwemermods 3768) - another possible copied style

## Requirements batch 1 (downloaded 2026-10-19; scanned clean; staged, NOT enabled)
| Staged MO2 mod | What | Notes |
|---|---|---|
| `[Staged] Mouse Tracker V1.5` | MouseTracker.esp (ESL, Skyrim.esm only) + script + PIE/dTry configs | left out: author backup esp/pex in Scripts\, docs, and 5 vanilla effect textures (candleglow01, fxwhiteflare01, fxsmokesub, vaportile01, gradshoutselfarea) that would recolour vanilla effects game-wide |
| `[Staged] Papyrus Ini Manipulator 1.9.9` | DLL (SE 1.5.97 ok: SKSEPlugin_Query + Address Library) | .pdb left out; also lets VergilSDT read its ini |
| `[Staged] AutoCancelTDMLockOn` | CancelTDMLcokOn.esp (full slot, 8 records) | .bat left out; it only copies TDM's lock key into scripts\TDMlockOnKey.ini - set by hand to 258 (your TDM key) |
| `[Staged] NEAE 3.0` | NotEnoughAttackEffect.esp (2244 records) + _Extra.esp (ESL) | REPLACES installed `NEAE 1.6.5 (bundle)` (same esp name): user's OK needed. Sam calls 31/34, Mitsunari 5/5 effects that only 3.0 has |
| `[Staged] NEAE3 Vergil Compat` | our patch (tools: skyrim/neae3_vergil_compat) | 3.0 dropped 5 spells Vergil uses (JudgeCut2/3, drive5/6, MirageEdgeSlashHZLeft) and reused their IDs; patch restores them + repoints Vergil's PIE lines |

NEAE 3.0 vs 1.6.5: masters now Skyrim, Dawnguard, Dragonborn, EldenSkyrim (SummonSwords dropped); every 1.6.5 config
file exists in 3.0; Purple FX files that overlap 3.0 still win (Purple FX is higher priority). NEW in 3.0: a SPID ini
gives every NPC perk CounterDamageResistNPC and non-player NPCs NPC_Hit_Spell_Empty; a HomingProjectiles json (Dante,
DLL not installed - unused by our sets).
Plugin slots: 141 / 254 full used, so no need to ESL-flag CancelTDMLcokOn.esp.

Still missing: Katana Crafting + SE patch (Mitsunari master), Elden Rim 3.7.0 RimSkills (Kagutsuchi), optional:
extaunt.esp (Sam's $Taunt effect), Sprint Start and Stop (2 Mitsunari sets), Homing Projectiles.
Sam's ~10 other undefined PIE names ($test, $SamBladeKillmoveOn, $Repentance...) are defined nowhere: author leftovers,
they do nothing.

Install steps (MO2 closed, after the user OKs replacing NEAE):
1. modlist: untick `NEAE 1.6.5 (bundle)` (keep the folder for rollback), `+NEAE 3.0` in its slot (below Purple FX/Vergil);
   `+NEAE3 Vergil Compat` above Vergil; `+Mouse Tracker`, `+Papyrus Ini Manipulator`, `+AutoCancelTDMLockOn`, `+Sam`.
2. plugins.txt: NotEnoughAttackEffect_Extra.esp after NotEnoughAttackEffect.esp; NEAE3 Vergil Compat.esp after
   ChaosYamato.esp; MouseTracker.esp, CancelTDMLcokOn.esp, sam_counter.esp at the end.
3. Test: Vergil Judgement Cut + overdrive still right; Sam on an Ebony Blade.

DONE 2026-10-19 (user OK): steps 1-2 applied; "[Staged] " dropped from those mod names. Backup of modlist/plugins/
loadorder: profiles/1.5.97/_backup_neae3_20261019. Rollback = restore those 3 files (renamed folders stay harmless).

## Requirements batch 2 (downloaded 2026-10-19; scanned clean; staged, NOT enabled)
- `[Staged] Katana Crafting SE - NoCC 3.19.1`: KatanaCrafting.esp ESL, HEDR 1.71 with ids < 0x800 -> needs BEES
  (installed + enabled). Keyword 0x157 ktn_DaiKatana present = what all 23 Mitsunari sets check. No file conflicts.
  The separate "SE patch" (106441) is not needed for Mitsunari (it only uses the keyword).
- `[Staged] Elden Rim - Base 3.7.5`: replaces the installed `Elden Rim - Weapon Arts 3.5.4` folder (really Base 3.5.6).
  EldenSkyrim.esp: same masters, 1274 -> 1280 records, only 2 renamed (0xBA046/47 NpcEndureArmor -> NpcEndureArmor1/2,
  used only by Elden's own configs); every id used by Vergil, Sam, NEAE 3.0, ADXP Katana, FlamingStrike, Kagutsuchi is
  unchanged. RimImpact esps identical. The author dropped the old EldenNpcSkill OAR folder, ~110 old DAR files and some
  MSL stagger variants, and added Elden Dodge + WarAsh OAR folders -> clean swap (untick old), same priority slot.
  Weapon Art 3.2.7 REQUIRES it (uses 2 records only 3.7.5 has: DisableNpcBlock, EldenNoneBuff).
- `[Staged] Elden Rim - Weapon Art 3.2.7`: EldenSkyrim_RimSkills.esp (full slot, 3341 records) = an Elden Ring
  overhaul: SPID rune/XP + war-ash scroll drops on all NPCs, Elden counter / rune / incantation / skill OAR sets, a HUD
  bar (flask/solvent), Wheeler icons, sprint-key charge (EldenKey.ini). Kagutsuchi uses only 3 of its records:
  KYWD BlockMode 0xC86, MESG EldenBookSuccess 0x1044, SPEL LionFlameSpell 0xBA53 ($longqieFire1).
  Overlaps: 14 files with NEAE 3.0, 48 with Vergil (textures) - Vergil should keep winning.
  Open question to the user: full Weapon Art, or a minimal install (esp + assets only, no drops/anims/key/HUD config).

DONE 2026-10-19 (user chose MINIMAL - they want to keep their Sekiro/Elden Ring/Skyrim mix unchanged):
- `Elden Rim - Weapon Art 3.2.7 (minimal)`: esp + meshes (no actors\*\animations), textures, Sound, scripts,
  Interface; left out SKSE (PIE, BDI, dtry EldenKey, CraftingCategories, InventoryInjector, Wheeler), MCM, Seq,
  EldenWarAshScrolls_DISTR.ini. Plus our patches (skyrim/rimskills_minimal/tools/build_rsm.py):
  `RimSkills Minimal - Quests.esp` (ERBWQuest / EldenUpdate / EldenWeaponPerkAdd2 no longer start-game-enabled) and
  `RimSkills Minimal - Restore.esp` (151 records: every EldenSkyrim.esp record RimSkills rewrites, back to Base 3.7.5,
  + vanilla WardBroken idle). RimSkills + both patches load right after EldenSkyrim.esp (so later mods keep winning
  the Solstheim CELL/WRLD edits; RimImpactOfPlayer still wins FallRoot/LandRoot). Kagutsuchi uses 4 of the restored
  records (small tweaks only: fire enchant 10 vs 20, an extra keyword/conditions) - it runs on the Base versions.
  Mod priority: lowest of the batch (below NEAE 3.0), so NEAE/Vergil/Base win shared files.
- `Elden Rim - Base 3.7.5` enabled in the old slot; `Elden Rim - Weapon Arts 3.5.4` (really Base 3.5.6) UNTICKED, kept.
- `Katana Crafting SE - NoCC 3.19.1`, `MCO Ishida Mitsunari`, `Aether Gazer Kagutsuchi` enabled (no DAR/PIE clashes;
  only clash $EC_Begin Base vs Elden Counter existed before too). The full staged Weapon Art copy is still in mods
  as `[Staged] Elden Rim - Weapon Art 3.2.7` (unused).
- Profile backup: profiles/1.5.97/_backup_elden375_20261019.

## Mixing movesets (user idea 2026-10-19: copy-ninja style switching)
OAR is per move (folder = animations + conditions), so a "Hokage Obito" OAR folder can use Sam as the base and put
Mitsunari / Kagutsuchi animations into chosen slots (e.g. a side-directional skill) at a higher priority.
Caveats: a borrowed move's PIE/DAC effect calls need its own plugin (+ masters) enabled; combo windows travel with each
animation; sheath/scabbard looks may be off. Plan: our own style switching (a style effect that OAR conditions check,
like Ronin's taunt/Issen) driven by the Sharingan copy mechanic / Copy Wheel; Stances NG only as a fallback.

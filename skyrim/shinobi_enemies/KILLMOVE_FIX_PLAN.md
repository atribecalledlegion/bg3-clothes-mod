# Stuck killmoves on small creatures (Serana / Ashe) — fix plan

Prepared 2026-10-19, not started.

## The bug (user report)
- Serana and Ashe start a killmove on a small target: dwarven spiders nearly every time, other small creatures too.
- The paired animation never completes. The victim can't die until it does, so nobody can kill it (not the player
  either), and the companions keep attacking it forever. Combat and their AI are ruined for that fight.
- Spiders are high-armour targets and rarely one-shot, so this comes up constantly.

## Already ruled out or fixed
- 2026-10-17: the dwarven spider SUPPORT repair (SNE_DwemerBrain) healed allies at <= 0 health or mid-killmove,
  which left them unkillable. Fixed with `Repairable()` and a heal guard in every brain. The bug still happens, so
  there is another cause.
- 2026-10-14: Valhalla Combat's killmove tree has no weapon conditions. "Valhalla Unarmed Killmove Fix" added
  weapon-type gates only, nothing for target size.

## Crash 2026-10-19 06:11 (probably the same problem)
- `crash-2026-10-19-10-11-50.log`: EXCEPTION_BREAKPOINT (`int3`, a Havok assertion) in the physics step (stack IDs
  60562-63744, hkpSimulationIsland / ahkpWorld).
- Objects involved: a spawned **Dwarven Spider Worker** (FF000B1D) and its leg bone collision
  (bhkBlendCollisionObject, DwarvenSpiderRLeg20-23), in Mzulft, with Serana nearby. Papyrus logging was off.
- Loaded right where this happens: **Paired Animation Improvements** 1.0.2 (replaces killmove alignment with its own
  smooth repositioning; no ini, defaults) and **Precision** 2.0.4 (weapon collision).

## Cause candidates (unconfirmed — needs one logged test)
1. A killmove meant for a bigger creature, or mismatched with the attacker's weapon, is chosen against a small
   skeleton. The pair fails to align or play, but the engine has already flagged the victim "in killmove".
   - Valhalla has spider / wolf / Spriggan / Centurion / Chaurus Flyer killmove IDLEs, all with 0 conditions on
     the nodes themselves. Check their parents (Val_KillMoveFrontSideRoot 0xA9C7, BackSideRoot 0xAA81).
   - Valhalla has no dwarven spider killmove, so the dwarven spider one comes from vanilla or another mod. Find it.
2. Serana's unarmed (kid era) or MCO/SCAR state interrupts the pair mid-way. KillMoveStart fires, the end event never does.
3. **Paired Animation Improvements** cannot finish its alignment on a small or odd-shaped victim (spider legs), so the
   pair never starts properly. That would also explain the Havok crash. CONTROL TEST: disable PAI (ASK the user,
   it's an installed mod; MO2 closed), fight 3+ dwarven spiders. If killmoves complete and nothing crashes, PAI is the
   cause; then keep it off, or block companion killmoves on small races.

## Early-killmove mods checked (2026-10-19)
- **VioLens** (killmove overhaul): uses the vanilla killmove system (the lethal blow), with chance globals and NPC /
  creature toggles (VL_MeleeNPCs, VL_MeleeCreatures; settings live in the save via its MCM). Overrides the vanilla
  creature roots KillMoveSpiderRoot 0xBD6D9, WolfRoot, SteamCenturionRoot, and adds VL_ ChaurusFlyer and
  DwarvenBallista killmoves. Not "early", but it adds a lot of creature killmoves for NPCs. STRONG SUSPECT for the
  pairing on small creatures; quick test = turn "NPC killmoves on creatures" off in its MCM.
- **Valhalla Combat**: executions on a key (iExecutionKey 49 = N), bAutoExecution 0, and bFriendlyStunToggle 0 (followers
  don't build stun), so its executions are player-driven. It still overrides the creature killmove trees (Val_*).
- **Poisebreaker / POISE**: poise and stagger only, no killmoves. **Elden Parry**: NPC parry only.
- **Paired Animation Improvements**: alignment for every killmove (see the crash).
- The v2 diagnostic (`SNE killmove diag:`) will tell whether the victim is flagged in a killmove, in bleedout, at 0 hp,
  essential, and so on.

## Fix, part 1 — safety net (works whatever the cause; do this first)
Where: `SNE_CompanionBrain.OnUpdate`, fighting branch, before `Think()` (it already ticks every 0.5 s in fights).

`KillmoveWatch()`:
- For each companion (Serana, Ashe) and the player's combat target:
  - If the actor `IsInKillMove()`, start a timer. If it is still true after **4 s** (normal killmoves take about
    2–3 s), it's stuck.
  - Same for a hostile near the companions that `IsInKillMove()`, or has health <= 0 but `!IsDead()`.
- Unstick:
  1. `Debug.SendAnimationEvent(x, "IdleForceDefaultState")` on both the killer and the victim, to break the pair.
  2. `victim.Kill(killer)`. If it still won't die, try `victim.KillEssential(killer)` or `victim.KillSilent()`.
  3. Trace `SNE killmove: unstuck <victim> (<race>) by <killer> after N s`.
- Reset the timers when an actor leaves the killmove.
- Guards: never touch the player's own killmoves (except as a victim?) or Ronin's Annihilation / JCE scenes.

## Fix, part 2 — prevention (once the log shows which killmoves fail)
- Override the failing killmove IDLEs (same approach as valhalla_unarmed_killmove_fix/build_vukf_esp.py). Add
  conditions run on the combat target: `GetIsRace` != DwarvenSpiderRace, skeever, mudcrab, and so on, or a size
  check.
- Alternatively, block companion killmoves on small races only: the attacker is a player teammate AND the target
  race is in the list.

## Diagnosis test (needs Papyrus logging ON — ASK the user first, LotD ini)
- Temporarily register `KillMoveStart`, `KillMoveEnd`, `PairEnd` and `pairedStop` on Serana and Ashe and log:
  - victim name and race,
  - killer weapon type,
  - the time between events.
- The user fights two or three dwarven spiders. Then read the log, and the SCAR / OAR logs for the failing clip.

## Files
- skyrim/shinobi_enemies/Scripts/Source/SNE_CompanionBrain.psc (watchdog)
- skyrim/valhalla_unarmed_killmove_fix/ (IDLE override builder, for part 2)
- MO2 mods: "Shinobi Enemies", "Valhalla Combat", "Valhalla Unarmed Killmove Fix"

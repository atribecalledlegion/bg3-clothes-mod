Scriptname SNE_CompanionBrain extends Quest
{Shinobi Enemies: companion brain for Serana and Ashe (2026-10-15).
Every 0.5 s while the player fights, it reads the battlefield (every hostile actor in the player's cell) and gives each
companion a target:
- player above 50% health: tactician. Enemies are scored: flanking the player (behind them), attacking the player,
  cornering (3+ enemies close), and by role (Rogue Medical Ninja, Anbu Assassin, a vampire elder hanging back,
  archers, mages, anyone casting, staggered or nearly dead). Ashe (greatsword) weighs flankers and melee threats,
  Serana (magic) healers, casters and archers; they split targets instead of doubling up. A target is kept at least
  2 s unless a clearly bigger threat appears.
- 50% or below: both peel the enemy attacking the player.
- 25% or below: Serana is protective: she panics, goes for whoever is hurting the player; a big hit makes her furious.
- 10% or below, once per fight: Serana's rescue: she appears beside the player and staggers every enemy around them.
Callouts are the companions' own recorded lines (topics owned by this quest), max one per category per cooldown.
Followers must be the player's teammates; nothing runs for a companion who is not following. Off: SNE_CompanionTactics 0.
Killmove watchdog (2026-10-19): a killmove on a small creature (dwarven spiders above all) can stall - the victim
cannot die until the paired animation ends, so nobody can kill it and the companions hit it forever. Anyone still in
a killmove after KillmoveStuck s (normal ones take 2-3 s) is freed: the pair is broken on both sides and the victim
is killed (essential / protected actors never). Trace lines start with "SNE killmove:".
v4: a companion's target at 0 health or below is finished at once (FinishAtZero).
Catch-up (2026-10-19): a following companion left more than CatchUpDistance behind, out of combat, for CatchUpSeconds
is moved to a spot behind the player (outdoors only; never while told to wait, sitting or in dialogue). "SNE catch-up:".
Needs SKSE (Cell.GetNthRef, GetDisplayName).}

Actor Property PlayerRef Auto
Spell Property AsheAutomaton Auto
GlobalVariable Property TacticsOn Auto
CombatStyle Property VampElderWait Auto
Topic[] Property SerStart Auto
Topic[] Property SerSurrounded Auto
Topic[] Property SerTough Auto
Topic[] Property SerStagger Auto
Topic[] Property SerWatch Auto
Topic[] Property SerPanic Auto
Topic[] Property SerAngry Auto
Topic[] Property SerRescue Auto
Topic[] Property SerAfterHurt Auto
Topic[] Property AsheStart Auto
Topic[] Property AsheFlanker Auto
Topic[] Property AsheStagger Auto
Topic[] Property AsheWinning Auto
Topic[] Property AsheGuard Auto
Topic[] Property AsheAfterHurt Auto
Topic[] Property AsheShutdown Auto

Float Property FightTick = 0.5 AutoReadOnly
Float Property IdleTick = 2.0 AutoReadOnly
Float Property TargetHold = 2.0 AutoReadOnly
Float Property BigHitDrop = 0.15 AutoReadOnly          ; a health drop this big within one tick makes Serana furious
Float Property ScanRange = 3000.0 AutoReadOnly
Float Property KillmoveStuck = 4.0 AutoReadOnly         ; seconds in a killmove before the watchdog frees it
Float Property CatchUpDistance = 2800.0 AutoReadOnly    ; about 40 m
Float Property CatchUpSeconds = 10.0 AutoReadOnly

; callout categories (index into NextSay)
Int C_SER_START = 0
Int C_SER_SURROUND = 1
Int C_SER_TOUGH = 2
Int C_SER_STAGGER = 3
Int C_SER_WATCH = 4
Int C_SER_PANIC = 5
Int C_SER_ANGRY = 6
Int C_ASHE_START = 7
Int C_ASHE_FLANK = 8
Int C_ASHE_STAGGER = 9
Int C_ASHE_WIN = 10
Int C_ASHE_GUARD = 11

Actor Serana
Actor Ashe
Bool InFight
Bool RescueUsed
Bool ToughSaid
Bool WinSaid
Int StartEnemies
Float LastPlayerHP = 1.0
Float SerHoldUntil
Float AsheHoldUntil
Float NextAnySay
Float[] NextSay
Actor[] Enemies
Int EnemyCount
Float SerFarSince = -1.0  ; catch-up: since when each companion is too far behind (-1 = not)
Float[] CatchLastDist     ; her distance when the clock (re)started
Bool RescueHidden         ; the rescue made Serana invisible and has not shown her again yet
Float AsheFarSince = -1.0
Actor[] StuckWho          ; killmove watchdog: who is in a killmove, and since when
Float[] StuckSince
Int NearPlayer

Event OnInit()
	RegisterForSingleUpdate(IdleTick)
EndEvent

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

Event OnUpdate()
	If !NextSay
		NextSay = new Float[12]
	EndIf
	SNE_JutsuPoseFix tracer = (Self as Quest) as SNE_JutsuPoseFix    ; keep the magicka tracer's loop alive
	If tracer
		tracer.Kick()
	EndIf
	If !Enemies
		Enemies = new Actor[40]
	EndIf
	Resolve()
	CatchUp()
	If TacticsOn.GetValue() < 0.5
		RegisterForSingleUpdate(IdleTick)
		Return
	EndIf
	Bool fighting = PlayerRef.IsInCombat()
	If fighting && !InFight
		FightStarted()
	ElseIf !fighting && InFight
		FightEnded()
	EndIf
	If fighting
		Think()
	EndIf
	Bool companionsFight = (Ready(Serana) && Serana.IsInCombat()) || (Ready(Ashe) && Ashe.IsInCombat())
	If fighting || companionsFight
		KillmoveWatch()    ; v2: also when only the companions fight (a stuck victim may not be fighting the player)
		KillmoveDiag()
		RegisterForSingleUpdate(FightTick)
	Else
		RegisterForSingleUpdate(IdleTick)
	EndIf
EndEvent

Function Resolve()
	If !Serana
		Serana = Game.GetFormFromFile(0x002B74, "Dawnguard.esm") as Actor
	EndIf
	If !Ashe
		Ashe = Game.GetFormFromFile(0x2D4A35, "Ashe - Fire and Blood.esp") as Actor
	EndIf
	If Ashe && AsheAutomaton && !Ashe.HasSpell(AsheAutomaton)
		Ashe.AddSpell(AsheAutomaton, False)
		Debug.Trace("SNE companion: Ashe automaton traits added (shock weakness + shutdown)")
	EndIf
EndFunction

Bool Function Ready(Actor c)
	Return c && !c.IsDead() && !c.IsDisabled() && c.IsPlayerTeammate() && c.GetDistance(PlayerRef) < 4000.0
EndFunction

; ---------- fight start / end ----------
Function FightStarted()
	InFight = True
	RescueUsed = False
	ToughSaid = False
	WinSaid = False
	LastPlayerHP = PlayerRef.GetActorValuePercentage("Health")
	Scan()
	StartEnemies = EnemyCount
	Debug.Trace("SNE companion: fight started, " + EnemyCount + " enemies, Serana " + Ready(Serana) + ", Ashe " + Ready(Ashe))
	If Ready(Ashe) && Utility.RandomInt(0, 1) == 0
		Say(Ashe, AsheStart, C_ASHE_START, 20.0)
	ElseIf Ready(Serana)
		Say(Serana, SerStart, C_SER_START, 20.0)
	EndIf
EndFunction

Function FightEnded()
	InFight = False
	Float p = PlayerRef.GetActorValuePercentage("Health")
	Debug.Trace("SNE companion: fight over, player at " + ((p * 100.0) as Int) + "%")
	If p < 0.6
		Utility.Wait(1.5)
		If Ready(Serana) && (Utility.RandomInt(0, 2) > 0 || !Ready(Ashe))
			Say(Serana, SerAfterHurt, -1, 0.0)
		ElseIf Ready(Ashe)
			Say(Ashe, AsheAfterHurt, -1, 0.0)
		EndIf
	EndIf
EndFunction

; ---------- the battlefield ----------
Function Scan()
	EnemyCount = 0
	NearPlayer = 0
	Cell c = PlayerRef.GetParentCell()
	If !c
		Return
	EndIf
	Int n = c.GetNumRefs(43)
	If n > 120
		n = 120
	EndIf
	Int i = 0
	While i < n && EnemyCount < 40
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && !a.IsDead() && !a.IsDisabled() && a.IsInCombat() && a.IsHostileToActor(PlayerRef) && PlayerRef.GetDistance(a) < ScanRange
			Enemies[EnemyCount] = a
			EnemyCount += 1
			If PlayerRef.GetDistance(a) < 350.0
				NearPlayer += 1
			EndIf
		EndIf
		i += 1
	EndWhile
EndFunction

Bool Function IsStaggered(Actor a)
	Return a && a.GetAnimationVariableBool("IsStaggering")      ; the target can die or unload between checks
EndFunction

Bool Function IsBehindPlayer(Actor a)
	Float ang = PlayerRef.GetHeadingAngle(a)
	If ang < 0.0
		ang = -ang
	EndIf
	Return ang > 100.0 && PlayerRef.GetDistance(a) < 700.0
EndFunction

Float Function Score(Actor e, Actor forWho, Bool asAshe)
	Float s = 0.0
	Float dP = PlayerRef.GetDistance(e)
	If dP < 700.0
		s += (700.0 - dP) / 10.0
	EndIf
	If e.GetCombatTarget() == PlayerRef
		s += 40.0
	EndIf
	If IsBehindPlayer(e)
		If asAshe
			s += 90.0
		Else
			s += 60.0
		EndIf
	EndIf
	If NearPlayer >= 3 && dP < 350.0
		s += 25.0    ; cornering the player
	EndIf
	String nm = e.GetDisplayName()
	If nm == "Rogue Medical Ninja"
		If asAshe
			s += 30.0
		Else
			s += 60.0
		EndIf
	ElseIf nm == "Anbu Assassin"
		s += 35.0
	EndIf
	If e.GetLeveledActorBase().GetCombatStyle() == VampElderWait
		If asAshe
			s += 20.0
		Else
			s += 45.0
		EndIf
	EndIf
	Int r = e.GetEquippedItemType(1)
	If r == 7 || r == 12 || r == 9
		If asAshe
			s += 8.0
		Else
			s += 30.0
		EndIf
	EndIf
	If (r == 9 || e.GetEquippedItemType(0) == 9) && e.HasKeywordString("ActorTypeNPC") && (e.GetAnimationVariableBool("IsCastingRight") || e.GetAnimationVariableBool("IsCastingLeft"))
		s += 30.0
	EndIf
	If IsStaggered(e)
		s += 35.0
	EndIf
	If e.GetActorValuePercentage("Health") < 0.25
		s += 20.0
	EndIf
	s -= forWho.GetDistance(e) / 60.0
	Return s
EndFunction

Actor Function Best(Actor forWho, Bool asAshe, Actor avoid)
	Actor best = None
	Float bestScore = -100000.0
	Int i = 0
	While i < EnemyCount
		Actor e = Enemies[i]
		If e && e != avoid
			Float sc = Score(e, forWho, asAshe)
			If sc > bestScore
				bestScore = sc
				best = e
			EndIf
		EndIf
		i += 1
	EndWhile
	If !best && avoid
		Return avoid    ; only one enemy: both on it
	EndIf
	Return best
EndFunction

Actor Function PlayersAttacker()    ; the enemy hurting the player: targeting them and closest
	Actor best = None
	Float bestDist = 100000.0
	Int i = 0
	While i < EnemyCount
		Actor e = Enemies[i]
		If e
			Float d = PlayerRef.GetDistance(e)
			If e.GetCombatTarget() == PlayerRef
				d -= 300.0
			EndIf
			If d < bestDist
				bestDist = d
				best = e
			EndIf
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction

; ---------- the plan, every tick ----------
; ---------- catch-up ----------
Int Function CatchSlot(Actor c)
	If c == Ashe
		Return 1
	EndIf
	Return 0
EndFunction

Function CatchUp()
	If !CatchLastDist
		CatchLastDist = new Float[2]
	EndIf
	If RescueHidden && Serana                      ; a save/load cut the rescue short: show her again
		Serana.SetAlpha(1.0, True)
		RescueHidden = False
		Debug.Trace("SNE companion: Serana shown again after an interrupted rescue")
	EndIf
	Float t = Now()
	SerFarSince = CatchOne(Serana, SerFarSince, t)
	AsheFarSince = CatchOne(Ashe, AsheFarSince, t)
EndFunction

Float Function CatchOne(Actor c, Float since, Float t)
	If !c || c.IsDead() || c.IsDisabled() || !c.IsPlayerTeammate()
		Return -1.0
	EndIf
	If PlayerRef.IsInCombat() || c.IsInCombat() || c.GetActorValue("WaitingForPlayer") > 0.0 || c.GetSitState() != 0 || c.IsInDialogueWithPlayer() || PlayerRef.IsOnMount()
		Return -1.0
	EndIf
	If PlayerRef.IsInInterior() || c.IsInInterior() || c.GetWorldSpace() != PlayerRef.GetWorldSpace()
		Return -1.0    ; outdoors only: indoors she may be sandboxing (homes, inns), and doors are the game's own travel
	EndIf
	Float far = c.GetDistance(PlayerRef)
	If far < CatchUpDistance
		Return -1.0
	EndIf
	If since < 0.0 || since > t
		CatchLastDist[CatchSlot(c)] = far
		Return t
	EndIf
	If far < CatchLastDist[CatchSlot(c)] - 200.0
		CatchLastDist[CatchSlot(c)] = far
		Return t                                   ; she is on her way: the clock starts over
	EndIf
	If t - since < CatchUpSeconds
		Return since
	EndIf
	Float d = c.GetDistance(PlayerRef)
	; v2 (2026-10-19): onto the player's own spot - always walkable ground. 250 units behind the player could be inside a
	; cliff or wall: she was left embedded there (name and talk prompt showing, no body, unhittable, lost pathing)
	c.MoveTo(PlayerRef, 0.0, 0.0, 0.0, True)
	Debug.Trace("SNE catch-up: " + c.GetDisplayName() + " was " + (d as Int) + " units behind for " + ((t - since) as Int) + " s - moved to the player")
	Return -1.0
EndFunction

; ---------- killmove watchdog ----------
Function KillmoveWatch()
	If KmOff && !InUnstick                                     ; a save/load cut an unstick short: killmoves back on
		GlobalVariable km = Game.GetFormFromFile(0x00100F19, "Skyrim.esm") as GlobalVariable
		If km
			km.SetValue(KmSaved)
		EndIf
		KmOff = False
		Debug.Trace("SNE killmove: KillMove global restored to " + KmSaved + " after an interrupted unstick")
	EndIf
	If !StuckWho
		StuckWho = new Actor[10]
		StuckSince = new Float[10]
	EndIf
	Float t = Now()
	Int i = 0
	While i < StuckWho.Length                                  ; forget whoever got out by themselves
		Actor a = StuckWho[i]
		If a && (a.IsDead() || !Limbo(a) || StuckSince[i] > t)
			StuckWho[i] = None
		EndIf
		i += 1
	EndWhile
	If Ready(Serana)
		If FinishAtZero(Serana)
			Return
		EndIf
		Watch(Serana, t)
		Watch(Serana.GetCombatTarget(), t)
	EndIf
	If Ready(Ashe)
		If FinishAtZero(Ashe)
			Return
		EndIf
		Watch(Ashe, t)
		Watch(Ashe.GetCombatTarget(), t)
	EndIf
	i = 0
	While i < EnemyCount
		Watch(Enemies[i], t)
		i += 1
	EndWhile
EndFunction

Bool Function Limbo(Actor a)
	; v3 (log 2026-10-19 07:28): a stuck spider sat at -10000 health, not dead, between killmoves
	Return a.IsInKillMove() || (a.GetActorValue("Health") <= 0.0 && !a.IsPlayerTeammate() && !a.IsEssential() && !a.IsBleedingOut())
EndFunction

; v4 (user, 2026-10-19: "reaching a negative number should auto kill it without needing a kill move"): a companion's
; target at 0 health or below that is not dead is finished at once (killmoves switched off meanwhile), so a killmove
; never gets the chance to stall. Costs most companion killmoves; the player's own killmoves are left alone.
Bool Function FinishAtZero(Actor c)
	Actor x = c.GetCombatTarget()
	If !x || x == PlayerRef || x.IsDead() || x.GetActorValue("Health") > 0.0
		Return False
	EndIf
	If x.IsPlayerTeammate() || x.IsEssential() || x.IsBleedingOut() || PlayerRef.IsInKillMove()
		Return False
	EndIf
	Actor killer = None
	If c.IsInKillMove()
		killer = c
	EndIf
	Unstick(x, killer, 0.0)
	Return True
EndFunction

Function Watch(Actor a, Float t)
	If !a || a == PlayerRef || a.IsDead() || !Limbo(a)
		Return
	EndIf
	Int k = StuckWho.Find(a)
	If k < 0
		k = StuckWho.Find(None)
		If k >= 0
			StuckWho[k] = a
			StuckSince[k] = t
		EndIf
		Return
	EndIf
	If t - StuckSince[k] < KillmoveStuck
		Return
	EndIf
	StuckWho[k] = None
	If a == Serana || a == Ashe
		Unstick(a.GetCombatTarget(), a, t - StuckSince[k])
	Else
		Unstick(a, None, t - StuckSince[k])
	EndIf
EndFunction

; diagnostics (2026-10-19, Papyrus logging on for the stuck-victim hunt): every DiagEvery s while companions fight
Float LastDiag = -100.0
Float Property DiagEvery = 1.5 AutoReadOnly
Bool Property KillmoveDiagOn = False AutoReadOnly

Function KillmoveDiag()
	If !KillmoveDiagOn
		Return
	EndIf
	Float t = Now()
	If t - LastDiag < DiagEvery && t >= LastDiag
		Return
	EndIf
	LastDiag = t
	DiagOne("Serana", Serana)
	DiagOne("Ashe", Ashe)
EndFunction

Function DiagOne(String label, Actor c)
	If !Ready(c)
		Return
	EndIf
	Actor x = c.GetCombatTarget()
	String me = label + " [combat " + c.IsInCombat() + ", killmove " + c.IsInKillMove() + ", attacking " + c.GetAnimationVariableBool("IsAttacking") + ", hp " + (c.GetActorValuePercentage("Health") * 100.0) as Int + "%]"
	If !x
		Debug.Trace("SNE killmove diag: " + me + " -> no combat target (player combat " + PlayerRef.IsInCombat() + ")")
		Return
	EndIf
	Debug.Trace("SNE killmove diag: " + me + " -> " + x.GetDisplayName() + " (" + x.GetRace().GetName() + ", base " + x.GetActorBase().GetName() + ") hp " + x.GetActorValue("Health") as Int + " / " + (x.GetActorValuePercentage("Health") * 100.0) as Int + "%, dead " + x.IsDead() + ", killmove " + x.IsInKillMove() + ", bleedout " + x.IsBleedingOut() + ", essential " + x.IsEssential() + ", protected " + x.GetActorBase().IsProtected() + ", ghost " + x.IsGhost() + ", unconscious " + x.IsUnconscious() + ", combat " + x.IsInCombat() + ", hostile " + x.IsHostileToActor(PlayerRef) + ", dist " + c.GetDistance(x) as Int + ", ai " + x.IsAIEnabled() + ", stagger " + x.GetAnimationVariableBool("IsStaggering") + ", ragdoll " + x.GetAnimationVariableBool("bIsRagdoll"))
EndFunction

; victim: the one who cannot die; killer: the companion stuck in the pair, if known
; v3 (2026-10-19): Kill() and even -10000 health did nothing - every hit on a victim below 0 health is "lethal", so
; the next companion hit starts a new killmove and the death waits for it again. So killmoves are switched off (the
; vanilla KillMove global, Skyrim.esm 0x100F19, the one VioLens uses) for KillmoveOffSeconds while the pair is
; broken and the victim is killed, then switched back to what it was.
Float Property KillmoveOffSeconds = 1.0 AutoReadOnly    ; after the kill (the waits before it are on top)
Bool KmOff                 ; the KillMove global is switched off by us right now (restored on the next tick if a save
Float KmSaved = 1.0        ; or load cut the unstick short)
Bool InUnstick

Function WaitKillmoveClear(Actor a, Float limit)
	Float waited = 0.0
	While a.IsInKillMove() && waited < limit
		Utility.Wait(0.2)
		waited += 0.2
	EndWhile
EndFunction

Function Unstick(Actor victim, Actor killer, Float stuckFor)
	GlobalVariable km = Game.GetFormFromFile(0x00100F19, "Skyrim.esm") as GlobalVariable    ; KillMove
	Float was = 1.0
	InUnstick = True
	If km
		was = km.GetValue()
		If KmOff
			was = KmSaved
		EndIf
		KmSaved = was
		KmOff = True
		km.SetValue(0.0)
	EndIf
	If killer
		Debug.SendAnimationEvent(killer, "IdleForceDefaultState")
	EndIf
	If Ready(Serana) && Serana != killer && Serana.IsInKillMove()
		Debug.SendAnimationEvent(Serana, "IdleForceDefaultState")
	EndIf
	If Ready(Ashe) && Ashe != killer && Ashe.IsInKillMove()
		Debug.SendAnimationEvent(Ashe, "IdleForceDefaultState")
	EndIf
	String how = "none"
	If !victim || victim == PlayerRef || victim.IsDead()
		how = "no victim"
	ElseIf victim.IsPlayerTeammate() || victim.IsEssential() || victim.GetActorBase().IsProtected()
		Debug.SendAnimationEvent(victim, "IdleForceDefaultState")
		how = "essential/teammate: freed, not killed"
	Else
		Debug.SendAnimationEvent(victim, "IdleForceDefaultState")
		Actor credit = killer
		If !credit
			credit = PlayerRef
		EndIf
		; v5 (log 07:38): the victim's killmove flag outlives the broken pair, and no kill lands while it is set -
		; wait for it to clear (killmoves stay off meanwhile), then kill; never heal it back to full
		WaitKillmoveClear(victim, 3.0)
		how = "Kill"
		victim.Kill(credit)
		Utility.Wait(0.3)
		If !victim.IsDead()
			how = "KillEssential"
			victim.KillEssential(credit)
			Utility.Wait(0.3)
		EndIf
		If !victim.IsDead()
			how = "1 hp + Kill"    ; out of the below-zero limbo, but one hit from death
			Float hp = victim.GetActorValue("Health")
			If hp < 1.0
				victim.RestoreActorValue("Health", 1.0 - hp)
			EndIf
			WaitKillmoveClear(victim, 2.0)
			victim.Kill(credit)
			Utility.Wait(0.3)
		EndIf
	EndIf
	If km
		Utility.Wait(KillmoveOffSeconds)
		km.SetValue(was)
		KmOff = False
	EndIf
	InUnstick = False
	If victim
		Debug.Trace("SNE killmove: unstuck " + victim.GetDisplayName() + " (" + victim.GetRace().GetName() + ") after " + (stuckFor as Int) + " s by " + how + ", dead " + victim.IsDead() + ", hp " + victim.GetActorValue("Health") as Int + ", killmove " + victim.IsInKillMove() + " (KillMove global back to " + was + ")")
	ElseIf killer
		Debug.Trace("SNE killmove: freed " + killer.GetDisplayName() + " after " + (stuckFor as Int) + " s (" + how + ")")
	EndIf
EndFunction

Function Think()
	Scan()
	Float p = PlayerRef.GetActorValuePercentage("Health")
	Bool bigHit = (LastPlayerHP - p) >= BigHitDrop
	LastPlayerHP = p
	If EnemyCount == 0
		Return
	EndIf
	Bool serOk = Ready(Serana)
	Bool asheOk = Ready(Ashe)
	Actor attacker = PlayersAttacker()

	If p <= 0.10 && !RescueUsed && serOk
		Rescue(attacker)
	EndIf

	If p <= 0.5
		; guard: both peel the player's attacker (Serana always; Ashe unless something flanks the player)
		If serOk
			SetTarget(Serana, attacker, True, p <= 0.25)
		EndIf
		If asheOk
			Actor flanker = None
			If p > 0.25
				flanker = FindFlanker()
			EndIf
			If flanker
				SetTarget(Ashe, flanker, False, False)
			Else
				SetTarget(Ashe, attacker, False, False)
				Say(Ashe, AsheGuard, C_ASHE_GUARD, 25.0)
			EndIf
		EndIf
		If serOk
			If p <= 0.25
				Say(Serana, SerPanic, C_SER_PANIC, 18.0)
			Else
				Say(Serana, SerWatch, C_SER_WATCH, 40.0)
			EndIf
		EndIf
	Else
		; tactician: split the targets
		Actor asheT = None
		If asheOk
			asheT = Best(Ashe, True, None)
			SetTarget(Ashe, asheT, False, False)
		EndIf
		If serOk
			SetTarget(Serana, Best(Serana, False, asheT), True, False)
		EndIf
	EndIf

	If bigHit && serOk
		SetTarget(Serana, attacker, True, True)
		Say(Serana, SerAngry, C_SER_ANGRY, 9.0)
	EndIf

	; read the fight
	If NearPlayer >= 4 && serOk
		Say(Serana, SerSurrounded, C_SER_SURROUND, 30.0)
	EndIf
	If !ToughSaid && serOk && (EnemyCount >= 5 || ToughEnemyPresent())
		ToughSaid = True
		Say(Serana, SerTough, C_SER_TOUGH, 60.0)
	EndIf
	If !WinSaid && asheOk && StartEnemies >= 4 && EnemyCount * 2 <= StartEnemies && p > 0.5
		WinSaid = True
		Say(Ashe, AsheWinning, C_ASHE_WIN, 60.0)
	EndIf
	CalloutStagger(serOk, asheOk)
EndFunction

Actor Function FindFlanker()
	Int i = 0
	While i < EnemyCount
		Actor e = Enemies[i]
		If e && IsBehindPlayer(e)
			Return e
		EndIf
		i += 1
	EndWhile
	Return None
EndFunction

Bool Function ToughEnemyPresent()
	Int i = 0
	While i < EnemyCount
		Actor e = Enemies[i]
		If e
			String nm = e.GetDisplayName()
			If nm == "Anbu Assassin" || e.GetLeveledActorBase().GetCombatStyle() == VampElderWait || e.GetLevel() >= PlayerRef.GetLevel() + 5
				Return True
			EndIf
		EndIf
		i += 1
	EndWhile
	Return False
EndFunction

Function CalloutStagger(Bool serOk, Bool asheOk)
	Actor t = None
	If asheOk && Ashe.GetCombatTarget() && IsStaggered(Ashe.GetCombatTarget())
		Say(Ashe, AsheStagger, C_ASHE_STAGGER, 12.0)
	ElseIf serOk && Serana.GetCombatTarget() && IsStaggered(Serana.GetCombatTarget())
		Say(Serana, SerStagger, C_SER_STAGGER, 15.0)
	EndIf
EndFunction

Function SetTarget(Actor c, Actor t, Bool isSerana, Bool force)
	If !c || !t || t.IsDead()
		Return
	EndIf
	Actor cur = c.GetCombatTarget()
	If cur == t
		Return
	EndIf
	Float n = Now()
	Float holdUntil = AsheHoldUntil
	If isSerana
		holdUntil = SerHoldUntil
	EndIf
	If holdUntil > n + 30.0
		holdUntil = 0.0
	EndIf
	If !force && cur && !cur.IsDead() && n < holdUntil
		Return    ; keep the current target a little while
	EndIf
	If !t || t.IsDead()
		Return    ; it died between choosing and ordering
	EndIf
	c.StartCombat(t)
	If isSerana
		SerHoldUntil = n + TargetHold
	Else
		AsheHoldUntil = n + TargetHold
		If IsBehindPlayer(t)
			Say(Ashe, AsheFlanker, C_ASHE_FLANK, 12.0)
		EndIf
	EndIf
	Debug.Trace("SNE companion: " + c.GetDisplayName() + " -> " + t.GetDisplayName() + " " + t + " (player " + ((PlayerRef.GetActorValuePercentage("Health") * 100.0) as Int) + "%, behind player " + IsBehindPlayer(t) + ", force " + force + ")")
EndFunction

; ---------- Serana's rescue (once per fight, player at 10% or less) ----------
Function Rescue(Actor attacker)
	RescueUsed = True
	RescueHidden = True
	Serana.SetAlpha(0.0, True)
	Utility.Wait(0.25)
	Serana.MoveTo(PlayerRef, 0.0, 0.0, 0.0)    ; v2: the player's own spot (an offset could be inside a wall)
	Serana.SetAlpha(1.0, True)
	RescueHidden = False
	Int staggered = 0
	Int i = 0
	While i < EnemyCount
		Actor e = Enemies[i]
		If e && !e.IsDead() && PlayerRef.GetDistance(e) < 450.0
			e.SetAnimationVariableFloat("staggerMagnitude", 1.0)
			Debug.SendAnimationEvent(e, "staggerStart")
			staggered += 1
		EndIf
		i += 1
	EndWhile
	If attacker
		Serana.StartCombat(attacker)
		SerHoldUntil = Now() + 4.0
	EndIf
	NextAnySay = 0.0
	Say(Serana, SerRescue, -1, 0.0)
	Debug.Trace("SNE companion: SERANA RESCUE at player " + ((PlayerRef.GetActorValuePercentage("Health") * 100.0) as Int) + "%, staggered " + staggered)
EndFunction

; ---------- callouts ----------
Function Say(Actor c, Topic[] lines, Int category, Float cooldown)
	If !c || !lines || lines.Length == 0
		Return
	EndIf
	Float n = Now()
	If NextAnySay > n + 30.0
		NextAnySay = 0.0
	EndIf
	If n < NextAnySay
		Return
	EndIf
	If category >= 0
		If NextSay[category] > n + cooldown + 1.0
			NextSay[category] = 0.0
		EndIf
		If n < NextSay[category]
			Return
		EndIf
		NextSay[category] = n + cooldown
	EndIf
	NextAnySay = n + 3.0
	Topic t = lines[Utility.RandomInt(0, lines.Length - 1)]
	c.Say(t)
	Debug.Trace("SNE companion: " + c.GetDisplayName() + " says " + t)
EndFunction

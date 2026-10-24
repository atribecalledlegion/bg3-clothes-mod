Scriptname SNE_ThalmorBrain extends ActiveMagicEffect
{Shinobi Enemies, Thalmor (2026-10-16). SPID gives this ability to ThalmorFaction (modded Thalmor in it get it too).
Lore (UESP): the Aldmeri Dominion's ruling party - Altmer supremacists, Great War veterans, Justiciars as magical
secret police (Root-like). Far better trained than bandits; their superiority is their biggest weakness.
- SUPERIORITY meter: starts at 100 + 15 per tier (higher Thalmor are more arrogant). While it is 60+, they hold you
  in CONTEMPT: sloppy, lone, unguarded styles, taunts, Justiciars hardly bother with jutsu. Damage taken, power and
  sneak hits, and dead Thalmor (a dead Justiciar most of all) wear it down. Below 60 they get SERIOUS: disciplined
  line, flanking archers, wards, focus, every jutsu, and they read how you fight (melee: they kite; magic: they
  seal and ward).
- PANIC: Thalmor are not used to being put in their place. Superiority under 25 and health under half: 35% (+15%
  without a Justiciar) they break and flee for 8 s ("Mercy!"), once per fight.
- SELFISH Justiciars: a hurt soldier falls back to its Justiciar for healing; the Justiciar may just buff itself
  instead (25% + 12% per tier). Higher Justiciars are more selfish - the fall-back is often wasted time.
- Bodyguards: a Justiciar hit in melee calls the nearest soldier to it. No leader, no cohesion: when the Justiciar
  dies, soldiers and archers lose formation (their own vanilla styles) and their superiority drops.
- Highborn: an Altmer low on magicka gets half of it back, once per fight.
- Heretic hunt: Amulet of Talos worn or the Talos shrine blessing on you: no contempt, no panic, zealous.
- Justiciar jutsu (no Uchiha): Wind Release: Vacuum Bullet (Danzo, t1+), Silencing Seal (t2+: 60% of your magicka
  and no regen for 6 s), Body Flicker (t2+, hit in melee: reappears by another Thalmor), Adamantine Sealing Chains
  (t3+, you under 30%: bound 3 s "for questioning"), Eight Trigrams Palm Rotation (t3+, Hyuga: crowded or you on
  top of it: pushes everyone away and wards), Mind Transfer (t4: freezes one of your followers 4 s; hitting the
  Justiciar breaks it).
Everything works against whoever they fight (you, the Legion, anyone): the jutsu hit their combat target.
Off: console "set SNE_ThalmorTactics to 0". Needs SKSE.}

CombatStyle Property StyleContempt Auto
CombatStyle Property StyleSoldier Auto
CombatStyle Property StyleArcher Auto
CombatStyle Property StyleJusticiar Auto
CombatStyle Property StyleJusticiarContempt Auto
GlobalVariable Property TacticsOn Auto
GlobalVariable Property IntelMelee Auto
GlobalVariable Property IntelMagic Auto
GlobalVariable Property IntelTime Auto
GlobalVariable Property VoiceLock Auto
Actor Property PlayerRef Auto
Faction Property ThalmorFaction Auto
Class Property ClassWizard Auto
Class Property ClassMissile Auto
Race Property HighElfRace Auto
FormList Property HaughtyVoices Auto
Armor Property TalosAmulet Auto
Armor Property TalosAmulet2 Auto
Spell Property TalosBlessing Auto
Spell Property ThalmorWard Auto
Spell Property SilencingSeal Auto
Spell Property SealingChains Auto
Spell Property SpellFus Auto
Spell Property SpellHealOther Auto
Spell Property SpellStoneflesh Auto
Spell Property SpellEbonyflesh Auto
EffectShader Property WardFX Auto
Topic[] Property ThalContempt Auto
Topic[] Property ThalFlea Auto
Topic[] Property ThalSerious Auto
Topic[] Property ThalPanic Auto
Topic[] Property ThalHeretic Auto

Float Property ContemptLine = 60.0 AutoReadOnly
Float Property PanicLine = 25.0 AutoReadOnly

Int R_SOLDIER = 1
Int R_ARCHER = 2
Int R_JUSTICIAR = 3

Actor Me
Int Role
CombatStyle OriginalStyle
Bool Done
Bool Busy
Float Sup
Bool Serious
Bool Panicked
Float FleeUntil
Float SavedConfidence
Bool Leaderless
Bool Heretic
Bool HighbornUsed
Float LastHp
Float NextHealRequest
Float NextFlea
Float NextBullet
Float NextSeal
Float NextFlicker
Float NextChains
Float NextKaiten
Float NextMind
Bool MindHit
Actor Target          ; current combat target

; ---------- setup ----------
Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	Init()
	ApplyStyle()
	Debug.Trace("SNE thalmor: start " + Me + " " + Me.GetDisplayName() + " role " + RoleName() + " tier " + Tier() + " (level " + Me.GetLevel() + ")")
	If Me.IsInCombat()
		StartFight()
		RegisterForSingleUpdate(1.0)
	EndIf
EndEvent

Function Init()
	If Role != 0 || !Me
		Return
	EndIf
	ActorBase b = Me.GetLeveledActorBase()
	If b
		OriginalStyle = b.GetCombatStyle()
	EndIf
	Class c = None
	If b
		c = b.GetClass()
	EndIf
	; the class and the hands decide: vanilla patrols name their soldiers "Thalmor Justiciar" too (log 2026-10-16:
	; a whole patrol was taken for Justiciars). The name only counts for an unarmed one.
	Int r = Me.GetEquippedItemType(1)
	Int l = Me.GetEquippedItemType(0)
	If c == ClassWizard || r == 9 || l == 9 || r == 8
		Role = R_JUSTICIAR
	ElseIf c == ClassMissile || r == 7 || r == 12
		Role = R_ARCHER
	ElseIf r >= 1 && r <= 6
		Role = R_SOLDIER
	ElseIf StringUtil.Find(Me.GetDisplayName(), "Justiciar") >= 0
		Role = R_JUSTICIAR
	Else
		Role = R_SOLDIER
	EndIf
EndFunction

String Function RoleName()
	If Role == R_JUSTICIAR
		Return "Justiciar"
	ElseIf Role == R_ARCHER
		Return "archer"
	EndIf
	Return "soldier"
EndFunction

Int Function Tier()
	Int lv = Me.GetLevel()
	If lv < 15
		Return 1
	ElseIf lv < 30
		Return 2
	ElseIf lv < 45
		Return 3
	EndIf
	Return 4
EndFunction

Bool Function Active()
	Return TacticsOn.GetValue() >= 0.5 && !Me.IsPlayerTeammate()
EndFunction

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Done = True
EndEvent

Event OnLoad()
	If !Done
		ApplyStyle()
	EndIf
EndEvent

Event OnDying(Actor akKiller)
	Done = True
	If Active()
		Me.SendModEvent("SNE_ThalmorFell", RoleName(), Role as Float)
	EndIf
EndEvent

Event OnCombatStateChanged(Actor akTarget, Int aeCombatState)
	If Done
		Return
	EndIf
	If !Me
		Me = GetTargetActor()
	EndIf
	Init()
	If aeCombatState == 1
		StartFight()
		ApplyStyle()
		PushCPR()
		RegisterForSingleUpdate(1.0)
	ElseIf aeCombatState == 0 && !Me.IsDead()
		Serious = False
		Sup = 0.0
		ApplyStyle()
	EndIf
EndEvent

Function StartFight()
	If Sup > 0.0
		Return    ; already fighting
	EndIf
	RegisterForModEvent("SNE_ThalmorFell", "OnThalmorFell")
	RegisterForModEvent("SNE_ThalmorHealMe", "OnHealMe")
	RegisterForModEvent("SNE_JusticiarThreat", "OnJusticiarThreat")
	Float t = Now()
	Float it = IntelTime.GetValue()
	If it > t + 1.0 || t - it > 60.0
		IntelMelee.SetValue(0.0)    ; a new fight: fresh intelligence
		IntelMagic.SetValue(0.0)
	EndIf
	IntelTime.SetValue(t)
	LastHp = Me.GetActorValuePercentage("Health")
	Heretic = Me.GetCombatTarget() == PlayerRef && (PlayerRef.IsEquipped(TalosAmulet) || PlayerRef.IsEquipped(TalosAmulet2) || PlayerRef.HasMagicEffect(TalosBlessing.GetNthEffectMagicEffect(0)))
	Panicked = False
	Leaderless = False
	HighbornUsed = False
	If Heretic
		Sup = ContemptLine - 1.0
		Serious = True
		Speak(ThalHeretic)
		Debug.Trace("SNE thalmor: " + RoleName() + " " + Me + " - a Talos worshipper: HERETIC HUNT (no contempt, no panic)")
	Else
		Sup = 100.0 + 15.0 * Tier()
		Serious = False
		Speak(ThalContempt)
		Debug.Trace("SNE thalmor: " + RoleName() + " " + Me + " fight starts in CONTEMPT (superiority " + (Sup as Int) + ")")
	EndIf
EndFunction

Event OnUpdate()
	If Done || !Me || Me.IsDead()
		Return
	EndIf
	Float t = Now()
	If FleeUntil > t + 30.0
		FleeUntil = t
	EndIf
	If FleeUntil > 0.0 && t >= FleeUntil
		FleeUntil = 0.0
		Me.SetActorValue("Confidence", SavedConfidence)
		Sup = 45.0
		Debug.Trace("SNE thalmor: " + RoleName() + " " + Me + " collects itself and comes back")
	EndIf
	If !Me.IsInCombat()
		If FleeUntil > 0.0
			RegisterForSingleUpdate(1.0)
		EndIf
		Return
	EndIf
	Target = Me.GetCombatTarget()
	If Active() && !Busy
		; damage taken wears the superiority down
		Float hp = Me.GetActorValuePercentage("Health")
		If hp < LastHp
			Lower((LastHp - hp) * 90.0, "")
		EndIf
		LastHp = hp
		If Me.GetActorValuePercentage("Magicka") < 0.25 && !HighbornUsed && Me.GetRace() == HighElfRace
			HighbornUsed = True
			Me.RestoreActorValue("Magicka", Me.GetBaseActorValue("Magicka") * 0.5)
			Debug.Trace("SNE thalmor: " + Me + " HIGHBORN (magicka back)")
		EndIf
		If !Panicked && !Heretic && Sup < PanicLine && hp < 0.5 && FleeUntil <= 0.0
			Panicked = True
			Float chance = 0.35
			If Leaderless
				chance += 0.15
			EndIf
			If Utility.RandomFloat() < chance
				Panic()
			Else
				Debug.Trace("SNE thalmor: " + RoleName() + " " + Me + " is shaken but holds (superiority " + (Sup as Int) + ")")
			EndIf
		EndIf
		If Role == R_JUSTICIAR
			JusticiarTick(t)
		ElseIf Role == R_SOLDIER && Serious
			SoldierTick(t)
		EndIf
	EndIf
	ApplyStyle()
	PushCPR()
	If !Done && !Me.IsDead()
		RegisterForSingleUpdate(1.0)
	EndIf
EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If Busy
		MindHit = True
	EndIf
	If Done || !Me || Me.IsDead() || !Active()
		Return
	EndIf
	Actor att = akAggressor as Actor
	If att && att != Me && !att.IsInFaction(ThalmorFaction)
		If akSource as Spell
			IntelMagic.Mod(1.0)
		Else
			IntelMelee.Mod(1.0)
		EndIf
		IntelTime.SetValue(Now())
		If abPowerAttack || abSneakAttack
			Lower(8.0, "put in its place")
		EndIf
	EndIf
	If !Serious && att && !att.IsInFaction(ThalmorFaction) && Now() >= NextFlea
		NextFlea = Now() + 8.0
		Speak(ThalFlea)
	EndIf
	If Role == R_JUSTICIAR && att && !att.IsInFaction(ThalmorFaction) && !akProjectile && !(akSource as Spell)
		Me.SendModEvent("SNE_JusticiarThreat")
		If Serious && Tier() >= 2 && Now() >= NextFlicker
			BodyFlicker()
		EndIf
	EndIf
EndEvent

; ---------- superiority ----------
Function Lower(Float amount, String why)
	If amount <= 0.0 || Heretic
		Return
	EndIf
	Sup -= amount
	If !Serious && Sup < ContemptLine
		Serious = True
		Speak(ThalSerious)
		Debug.Trace("SNE thalmor: " + RoleName() + " " + Me + " takes you SERIOUSLY now (superiority " + (Sup as Int) + ")")
	ElseIf why != ""
		Debug.Trace("SNE thalmor: " + RoleName() + " " + Me + " " + why + " (superiority " + (Sup as Int) + ")")
	EndIf
EndFunction

Function Panic()
	SavedConfidence = Me.GetActorValue("Confidence")
	Me.SetActorValue("Confidence", 0.0)
	FleeUntil = Now() + 8.0
	Speak(ThalPanic)
	Debug.Trace("SNE thalmor: " + RoleName() + " " + Me + " PANICS and flees (superiority " + (Sup as Int) + ")")
EndFunction

Function Speak(Topic[] lines)
	If !lines || lines.Length == 0 || !HaughtyVoices.HasForm(Me.GetVoiceType())
		Return
	EndIf
	Float t = Now()
	Float lock = VoiceLock.GetValue()
	If lock > t + 10.0
		lock = 0.0
	EndIf
	If lock > t
		Return    ; one voice at a time
	EndIf
	VoiceLock.SetValue(t + 4.0)
	Me.Say(lines[Utility.RandomInt(0, lines.Length - 1)])
EndFunction

Event OnThalmorFell(String eventName, String strArg, Float numArg, Form sender)
	Actor dead = sender as Actor
	If Done || !Me || Me.IsDead() || !Me.IsInCombat() || !dead || dead == Me || Me.GetDistance(dead) > 3000.0
		Return
	EndIf
	If (numArg as Int) == R_JUSTICIAR && Role != R_JUSTICIAR
		If !Leaderless && !AnyJusticiar()
			Leaderless = True
			Lower(35.0, "lost its Justiciar - NO LEADER")
		EndIf
	Else
		Lower(20.0, "saw " + strArg + " " + dead + " fall")
	EndIf
EndEvent

Bool Function AnyJusticiar()
	Cell c = Me.GetParentCell()
	If !c
		Return False
	EndIf
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a != Me && !a.IsDead() && a.IsInFaction(ThalmorFaction) && IsJusticiar(a) && Me.GetDistance(a) < 3000.0
			Return True
		EndIf
		i += 1
	EndWhile
	Return False
EndFunction

Bool Function IsJusticiar(Actor a)
	ActorBase b = a.GetLeveledActorBase()
	Int r = a.GetEquippedItemType(1)
	Return (b && b.GetClass() == ClassWizard) || r == 9 || r == 8 || a.GetEquippedItemType(0) == 9
EndFunction

Actor Function NearestJusticiar()
	Cell c = Me.GetParentCell()
	If !c
		Return None
	EndIf
	Actor best = None
	Float bestD = 2000.0
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a != Me && !a.IsDead() && a.IsInFaction(ThalmorFaction) && !a.IsPlayerTeammate() && IsJusticiar(a) && Me.GetDistance(a) < bestD
			bestD = Me.GetDistance(a)
			best = a
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction

; ---------- soldiers ----------
Function SoldierTick(Float t)
	If NextHealRequest > t + 30.0
		NextHealRequest = 0.0
	EndIf
	If Me.GetActorValuePercentage("Health") >= 0.4 || t < NextHealRequest || Leaderless
		Return
	EndIf
	Actor j = NearestJusticiar()
	If !j
		Return
	EndIf
	NextHealRequest = t + 20.0
	Actor foe = Target
	Busy = True
	Debug.Trace("SNE thalmor: soldier " + Me + " falls back to Justiciar " + j + " for healing")
	Me.StopCombat()
	Me.PathToReference(j, 1.0)
	Me.SendModEvent("SNE_ThalmorHealMe")
	Utility.Wait(2.0)
	If !Me.IsDead() && foe && !foe.IsDead()
		Me.StartCombat(foe)
	EndIf
	Busy = False
EndFunction

Event OnJusticiarThreat(String eventName, String strArg, Float numArg, Form sender)
	Actor j = sender as Actor
	If Done || !Me || Me.IsDead() || Role != R_SOLDIER || !Serious || Busy || !j || Me.GetDistance(j) > 1500.0
		Return
	EndIf
	Actor threat = j.GetCombatTarget()
	If threat && !threat.IsDead() && Me.GetDistance(threat) > 400.0 && Utility.RandomFloat() < 0.5
		Me.StartCombat(threat)
		Debug.Trace("SNE thalmor: soldier " + Me + " moves to guard its Justiciar from " + threat)
	EndIf
EndEvent

; ---------- Justiciars ----------
Event OnHealMe(String eventName, String strArg, Float numArg, Form sender)
	Actor s = sender as Actor
	If Done || !Me || Me.IsDead() || Role != R_JUSTICIAR || !s || s.IsDead() || Me.GetDistance(s) > 600.0
		Return
	EndIf
	Float selfish = 0.25 + 0.12 * Tier()
	If Utility.RandomFloat() < selfish
		If Tier() >= 3
			SpellEbonyflesh.Cast(Me, Me)
		Else
			SpellStoneflesh.Cast(Me, Me)
		EndIf
		ThalmorWard.Cast(Me, Me)
		Debug.Trace("SNE thalmor: Justiciar " + Me + " REFUSES to heal " + s + " and buffs itself instead (selfish " + ((selfish * 100.0) as Int) + "%)")
	Else
		If !s.IsInKillMove() && !s.IsBleedingOut() && s.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
			SpellHealOther.Cast(Me, s)
		EndIf
		Debug.Trace("SNE thalmor: Justiciar " + Me + " heals " + s)
	EndIf
EndEvent

Bool Function MagicUser()
	Return IntelMagic.GetValue() > IntelMelee.GetValue() * 1.2 && IntelMagic.GetValue() >= 3.0
EndFunction

Function JusticiarTick(Float t)
	If NextBullet > t + 30.0
		NextBullet = 0.0
	EndIf
	If NextSeal > t + 30.0
		NextSeal = 0.0
	EndIf
	If NextChains > t + 40.0
		NextChains = 0.0
	EndIf
	If NextKaiten > t + 30.0
		NextKaiten = 0.0
	EndIf
	If NextMind > t + 50.0
		NextMind = 0.0
	EndIf
	If !Target || Target.IsDead()
		Return
	EndIf
	Float d = Me.GetDistance(Target)
	Int tier = Tier()
	If !Serious
		; contempt: you are hardly worth a jutsu
		If t >= NextBullet && d > 300.0 && Me.HasLOS(Target)
			NextBullet = t + 20.0
			VacuumBullet()
		EndIf
		Return
	EndIf
	If tier >= 3 && t >= NextKaiten && (d < 180.0 || EnemiesNear(250.0) >= 2)
		NextKaiten = t + 15.0
		Kaiten()
		Return
	EndIf
	If tier >= 3 && t >= NextChains && Target.GetActorValuePercentage("Health") < 0.3 && d < 1500.0 && Me.HasLOS(Target)
		NextChains = t + 30.0
		If Utility.RandomFloat() < 0.4
			SealingChains.Cast(Me, Target)
			If Target == PlayerRef
				Debug.Notification("Adamantine Sealing Chains - you are bound for questioning!")
			EndIf
			Debug.Trace("SNE thalmor: Justiciar " + Me + " ADAMANTINE SEALING CHAINS on " + Target)
			Return
		EndIf
	EndIf
	If tier >= 2 && t >= NextSeal && Target.GetActorValuePercentage("Magicka") > 0.3 && Target.GetBaseActorValue("Magicka") > 60.0 && d < 1800.0 && (MagicUser() || Utility.RandomFloat() < 0.25)
		NextSeal = t + 20.0
		SilenceSeal()
		Return
	EndIf
	If tier >= 4 && t >= NextMind && Target == PlayerRef
		Actor f = NearestFollower()
		If f
			NextMind = t + 40.0
			MindTransfer(f)
			Return
		EndIf
	EndIf
	If t >= NextBullet && d > 250.0 && Me.HasLOS(Target)
		NextBullet = t + 10.0
		VacuumBullet()
		Return
	EndIf
	; ward discipline against a mage
	If MagicUser() && !Me.HasMagicEffect(ThalmorWard.GetNthEffectMagicEffect(0))
		ThalmorWard.Cast(Me, Me)
		WardFX.Play(Me, 1.0)
	EndIf
EndFunction

Function VacuumBullet()
	SpellFus.Cast(Me, Target)
	Target.DamageActorValue("Health", 5.0 + 5.0 * Tier())
	Debug.Trace("SNE thalmor: Justiciar " + Me + " WIND RELEASE: VACUUM BULLET at " + Target)
EndFunction

Function SilenceSeal()
	Target.DamageActorValue("Magicka", Target.GetActorValue("Magicka") * 0.6)
	SilencingSeal.Cast(Target, Target)
	WardFX.Play(Target, 1.5)
	If Target == PlayerRef
		Debug.Notification("Your magic has been sealed!")
	EndIf
	Debug.Trace("SNE thalmor: Justiciar " + Me + " SILENCING SEAL on " + Target + " (magic user " + MagicUser() + ")")
EndFunction

Function BodyFlicker()
	NextFlicker = Now() + 10.0
	Actor ally = None
	Float bestD = 0.0
	Cell c = Me.GetParentCell()
	If c
		Int n = c.GetNumRefs(43)
		If n > 80
			n = 80
		EndIf
		Int i = 0
		While i < n
			Actor a = c.GetNthRef(i, 43) as Actor
			If a && a != Me && !a.IsDead() && a.IsInFaction(ThalmorFaction) && !a.IsPlayerTeammate() && Me.GetDistance(a) < 2000.0
				Float dd = a.GetDistance(Target)
				If dd > bestD
					bestD = dd
					ally = a
				EndIf
			EndIf
			i += 1
		EndWhile
	EndIf
	If !ally || bestD < 500.0
		Return
	EndIf
	WardFX.Play(Me, 0.5)
	Me.MoveTo(ally, Utility.RandomFloat(-100.0, 100.0), Utility.RandomFloat(-100.0, 100.0), 0.0)
	Debug.Trace("SNE thalmor: Justiciar " + Me + " BODY FLICKER - reappears by " + ally)
EndFunction

Int Function EnemiesNear(Float r)
	Int k = 0
	Cell c = Me.GetParentCell()
	If c
		Int n = c.GetNumRefs(43)
		If n > 80
			n = 80
		EndIf
		Int i = 0
		While i < n
			Actor a = c.GetNthRef(i, 43) as Actor
			If a && !a.IsDead() && a.IsHostileToActor(Me) && Me.GetDistance(a) < r
				k += 1
			EndIf
			i += 1
		EndWhile
	EndIf
	Return k
EndFunction

; Hyuga's Eight Trigrams Palm Rotation: a spinning ward that throws everyone back
Function Kaiten()
	WardFX.Play(Me, 1.5)
	ThalmorWard.Cast(Me, Me)
	Cell c = Me.GetParentCell()
	If c
		Int n = c.GetNumRefs(43)
		If n > 80
			n = 80
		EndIf
		Int i = 0
		While i < n
			Actor a = c.GetNthRef(i, 43) as Actor
			If a && !a.IsDead() && a.IsHostileToActor(Me) && Me.GetDistance(a) < 350.0
				Me.PushActorAway(a, 3.0)
			EndIf
			i += 1
		EndWhile
	EndIf
	Debug.Trace("SNE thalmor: Justiciar " + Me + " EIGHT TRIGRAMS PALM ROTATION")
EndFunction

Actor Function NearestFollower()
	Cell c = Me.GetParentCell()
	If !c
		Return None
	EndIf
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && !a.IsDead() && a.IsPlayerTeammate() && a.IsInCombat() && Me.GetDistance(a) < 1500.0
			Return a
		EndIf
		i += 1
	EndWhile
	Return None
EndFunction

; Yamanaka Mind Transfer: the Justiciar stands still and holds your follower's mind; hit it to break the hold
Function MindTransfer(Actor f)
	Busy = True
	MindHit = False
	Me.SetDontMove(True)
	f.SetRestrained(True)
	WardFX.Play(f, 4.0)
	Debug.Notification(f.GetDisplayName() + "'s mind is seized!")
	Debug.Trace("SNE thalmor: Justiciar " + Me + " MIND TRANSFER on " + f)
	Float waited = 0.0
	While waited < 4.0 && !MindHit && !Me.IsDead()
		Utility.Wait(0.5)
		waited += 0.5
	EndWhile
	f.SetRestrained(False)
	WardFX.Stop(f)
	Me.SetDontMove(False)
	Debug.Trace("SNE thalmor: Justiciar " + Me + " mind transfer ends (broken by a hit " + MindHit + ")")
	Busy = False
EndFunction

; ---------- styles and CPR ----------
Function ApplyStyle()
	If !Me || Me.IsPlayerTeammate()
		Return
	EndIf
	ActorBase b = Me.GetLeveledActorBase()
	If !b
		Return
	EndIf
	CombatStyle want = OriginalStyle
	If TacticsOn.GetValue() >= 0.5 && Me.IsInCombat()
		If Role == R_JUSTICIAR && Serious
			want = StyleJusticiar
		ElseIf Role == R_JUSTICIAR
			want = StyleJusticiarContempt
		ElseIf !Serious
			want = StyleContempt
		ElseIf Leaderless
			want = OriginalStyle    ; no leader, no cohesion
		ElseIf Role == R_ARCHER
			want = StyleArcher
		Else
			want = StyleSoldier
		EndIf
	EndIf
	If want && b.GetCombatStyle() != want
		b.SetCombatStyle(want)
	EndIf
EndFunction

Function PushCPR()
	If !Active() || Busy
		Return
	EndIf
	Bool kite = !MagicUser() && IntelMelee.GetValue() >= 3.0    ; a melee fighter: keep it at arm's length
	If !Serious
		SetCPR(False, 0.0, False, 0.0, 0.0, 0.0, 0.0, False)       ; contempt: stands its ground
	ElseIf Role == R_JUSTICIAR && kite
		SetCPR(True, 0.9, True, 500.0, 1300.0, 30.0, 60.0, True)
	ElseIf Role == R_JUSTICIAR
		SetCPR(True, 0.6, True, 400.0, 1000.0, 30.0, 60.0, True)
	ElseIf Role == R_ARCHER
		SetCPR(True, 0.7, True, 400.0, 1200.0, 40.0, 90.0, kite)
	ElseIf Leaderless
		SetCPR(True, 0.3, True, 100.0, 300.0, 20.0, 60.0, False)
	Else
		SetCPR(True, 0.2, True, 100.0, 300.0, 40.0, 120.0, False)  ; a disciplined line that also works the flanks
	EndIf
EndFunction

Function SetCPR(Bool backoff, Float backoffChance, Bool circle, Float circleMin, Float circleMax, Float angleMin, Float angleMax, Bool fallback)
	Me.SetAnimationVariableBool("CPR_EnableBackoff", backoff)
	Me.SetAnimationVariableFloat("CPR_BackoffChance", backoffChance)
	Me.SetAnimationVariableBool("CPR_EnableCircling", circle)
	Me.SetAnimationVariableFloat("CPR_CirclingDistMin", circleMin)
	Me.SetAnimationVariableFloat("CPR_CirclingDistMax", circleMax)
	Me.SetAnimationVariableFloat("CPR_CirclingAngleMin", angleMin)
	Me.SetAnimationVariableFloat("CPR_CirclingAngleMax", angleMax)
	Me.SetAnimationVariableBool("CPR_EnableFallback", fallback)
	If fallback
		Me.SetAnimationVariableFloat("CPR_FallbackDistMin", 400.0)
		Me.SetAnimationVariableFloat("CPR_FallbackDistMax", 1000.0)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", 0.3)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", 0.7)
	EndIf
EndFunction

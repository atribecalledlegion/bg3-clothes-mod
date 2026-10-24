Scriptname CTOB_RinneganQuestScript extends Quest
{Rinnegan rework for the combat setup (third script on CTOB_Quest). Watches the player's Uchiha Clan Rinnegan casts
(SKSE actor action "Spell Fire") and builds on them without changing the Uchiha Clan's own spells:
 R1 Shinra Tensei: cast while an enemy close by is mid-swing at you = perfect repulsion: the chakra is returned, the
    5 s interval is skipped and the attacker is Exposed. Otherwise a "Shinra Tensei ready" note when the interval ends.
 R2 Bansho Tenin: the pulled enemy lands Exposed in front of you. Pulling one pinned by receiver rods tears at the rods:
    extra damage and a short hold.
 R3 Human Path: Remove Soul on an Exposed, held or badly wounded enemy tears the soul out at once (kill + soul trap).
 R4 Outer Path: Chakra Receivers (hand-cast spell, like the Uchiha Clan's chakra blade): a black rod shot from your
    palm. Each rod hurts, drains chakra and pins (slows); three in one target within RodWindow hold it in place.
 R5 Tengai Shinsei no longer hurts your followers (they are untouchable while it falls and burns), Great Missile grows
    with your level, and Chibaku Tensei's fatigue lasts half as long.
Valhalla Combat has no script hook for its stun meter, so "Exposed" (armour broken, open to the Human Path) is used.}

Float Property PerfectReach = 450.0 AutoReadOnly
{Shinra Tensei: enemies this close and mid-swing at you make it a perfect repulsion.}
Float Property BanshoReach = 3000.0 AutoReadOnly
Float Property AimCone = 10.0 AutoReadOnly
Float Property SoulRipReach = 350.0 AutoReadOnly
Float Property SoulRipHealth = 0.25 AutoReadOnly
{Remove Soul tears the soul out at once below this share of health (Uchiha bosses: BossSoulRipHealth).}
Float Property BossSoulRipHealth = 0.15 AutoReadOnly
Int Property RodCount = 3 AutoReadOnly
{Rods in one target within RodWindow seconds that hold it in place.}
Float Property RodWindow = 4.0 AutoReadOnly
Float Property RodMagickaDrain = 25.0 AutoReadOnly
Float Property FollowerShieldSeconds = 30.0 AutoReadOnly
Int Property ChibakuFatigueSeconds = 45 AutoReadOnly

Actor RodVictim = None
Int RodHits = 0
Float RodVolley = -100.0
Bool WatchingInterval = False

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

Form Function Own(Int id)
	Return Game.GetFormFromFile(id, "Obito Tobi Path Additions.esp")
EndFunction

Form Function Uchiha(Int id)
	Return Game.GetFormFromFile(id, "UchihaClan.esp")
EndFunction

Bool Function RinneganActive()
	Spell r = Uchiha(0x04144E) as Spell      ; aaaRinneganAbility
	Return r && Game.GetPlayer().HasSpell(r)
EndFunction

Bool Function UchihaBoss(Actor a)
	Keyword k = Uchiha(0x02E8C9) as Keyword
	Return k && a.HasKeyword(k)
EndFunction

; Cooldowns are kept in real time, which restarts every launch: clear stale values.
Float Function Ready(Float last, Float cooldown)
	Float t = Now()
	If last > t
		Return 0.0
	EndIf
	Float left = cooldown - (t - last)
	If left < 0.0
		Return 0.0
	EndIf
	Return left
EndFunction

Bool Function Exposed(Actor a)
	Return a.HasMagicEffect(Own(0x824) as MagicEffect)
EndFunction

Bool Function Pinned(Actor a)
	Return a.HasMagicEffect(Own(0x826) as MagicEffect)
EndFunction

Function Expose(Actor a)
	(Own(0x825) as Spell).Cast(Game.GetPlayer(), a)
EndFunction

Function Hold(Actor a, Int seconds)
	Spell paralysis = Own(0x812) as Spell
	paralysis.SetNthEffectDuration(0, seconds)
	paralysis.Cast(Game.GetPlayer(), a)
EndFunction

; Called by CTOB_TobiPathQuestScript's poll while on the Tobi path.
Function Tick(Actor p)
	RegisterForActorAction(2)                               ; Spell Fire (kept with the save; re-registering is harmless)
	; R5: Great Missile grows with your level (runtime values are not saved, so they are set again every poll)
	Spell missile = Uchiha(0x03A663) as Spell
	If missile
		Float dmg = 100.0 + 5.0 * p.GetLevel()
		If dmg > 450.0
			dmg = 450.0
		EndIf
		If missile.GetNthEffectMagnitude(0) != dmg
			missile.SetNthEffectMagnitude(0, dmg)
		EndIf
	EndIf
	Spell fatigue = Uchiha(0x1C15FA) as Spell
	If fatigue && fatigue.GetNthEffectDuration(0) != ChibakuFatigueSeconds
		Int i = 0
		While i < fatigue.GetNumEffects()
			fatigue.SetNthEffectDuration(i, ChibakuFatigueSeconds)
			i += 1
		EndWhile
	EndIf
	; R4: the Outer Path power follows the Rinnegan, like the Preta Path
	Spell rods = Own(0x82E) as Spell
	If rods
		If RinneganActive()
			If !p.HasSpell(rods)
				p.AddSpell(rods, False)
				Debug.Notification("Rinnegan: Outer Path unlocked: Chakra Receivers (spell).")
			EndIf
		ElseIf p.HasSpell(rods)
			p.RemoveSpell(rods)
		EndIf
	EndIf
EndFunction

Event OnActorAction(Int actionType, Actor akActor, Form source, Int slot)
	If actionType != 2 || !source || akActor != Game.GetPlayer()
		Return
	EndIf
	If source == Uchiha(0x0385E6) || source == Uchiha(0x038B53)        ; Shinra Tensei, Shinra Tensei (Area)
		ShinraTensei(source as Spell)
	ElseIf source == Uchiha(0x0385EB)                                 ; Bansho Tenin
		BanshoTenin()
	ElseIf source == Uchiha(0x03A0FB)                                 ; Remove Soul
		RemoveSoul()
	ElseIf source == Uchiha(0x05F398)                                 ; Tengai Shinsei
		ShieldFollowers()
	EndIf
EndEvent

; ---------------- R1: Shinra Tensei ----------------
Function ShinraTensei(Spell s)
	Actor p = Game.GetPlayer()
	Actor[] around = MiscUtil.ScanCellNPCs(p, PerfectReach, None, True)
	Int caught = 0
	Int k = 0
	While around && k < around.Length
		Actor a = around[k]
		If a && a != p && !a.IsDead() && a.IsHostileToActor(p) && a.GetCombatTarget() == p && a.GetAnimationVariableBool("IsAttacking")
			Expose(a)
			caught += 1
		EndIf
		k += 1
	EndWhile
	If caught == 0
		Debug.Trace("CTOB rinnegan: Shinra Tensei (normal)")
		WatchInterval()
		Return
	EndIf
	; perfect repulsion: chakra back and no interval (the Uchiha effect adds its cooldown perk when it lands, so keep
	; clearing it for a moment)
	p.RestoreActorValue("Magicka", s.GetMagickaCost())
	Debug.Notification("Shinra Tensei: perfect repulsion.")
	Debug.Trace("CTOB rinnegan: perfect Shinra Tensei, " + caught + " exposed")
	Perk interval = Uchiha(0x0385EA) as Perk
	Int n = 0
	While n < 8
		Utility.Wait(0.25)
		If p.HasPerk(interval)
			p.RemovePerk(interval)
		EndIf
		n += 1
	EndWhile
EndFunction

; Shinra Tensei and Bansho Tenin share the Uchiha interval perk: say when it is over.
Function WatchInterval()
	If WatchingInterval
		Return
	EndIf
	WatchingInterval = True
	Actor p = Game.GetPlayer()
	Perk interval = Uchiha(0x0385EA) as Perk
	Utility.Wait(1.0)
	Int n = 0
	While n < 60 && p.HasPerk(interval)
		Utility.Wait(0.5)
		n += 1
	EndWhile
	If n > 0
		Debug.Notification("Shinra Tensei ready.")
	EndIf
	WatchingInterval = False
EndFunction

; ---------------- targeting ----------------
; The actor under the crosshair, else the one closest to where you aim (within AimCone degrees) up to range,
; enemies first. The crosshair alone only reaches activation distance.
Actor Function AimTarget(Float range)
	Actor p = Game.GetPlayer()
	Actor c = Game.GetCurrentCrosshairRef() as Actor
	If c && c != p && !c.IsDead() && p.GetDistance(c) <= range && p.HasLOS(c)
		Return c
	EndIf
	Actor[] around = MiscUtil.ScanCellNPCs(p, range, None, True)
	Actor aimed = None
	Float bestScore = 1000.0
	Int k = 0
	While around && k < around.Length
		Actor x = around[k]
		If x && x != p && !x.IsPlayerTeammate() && !x.IsDead()
			Float ang = Math.Abs(p.GetHeadingAngle(x))
			If ang < AimCone && p.HasLOS(x)
				Float score = ang
				If !x.IsHostileToActor(p)
					score += AimCone
				EndIf
				If score < bestScore
					aimed = x
					bestScore = score
				EndIf
			EndIf
		EndIf
		k += 1
	EndWhile
	Return aimed
EndFunction

; ---------------- R2: Bansho Tenin ----------------
Function BanshoTenin()
	Actor p = Game.GetPlayer()
	Actor a = AimTarget(BanshoReach)
	WatchInterval()
	If !a
		Return
	EndIf
	Bool wasPinned = Pinned(a)
	Utility.Wait(0.9)                                        ; the pull
	If a.IsDead() || p.GetDistance(a) > 500.0
		Return
	EndIf
	Expose(a)
	If wasPinned
		; the rods are still in them: the pull tears at them
		a.DamageActorValue("Health", 40.0 + p.GetLevel())
		Hold(a, 2)
		Debug.Notification("Bansho Tenin: the receivers tear at " + a.GetDisplayName() + ".")
	EndIf
	Debug.Trace("CTOB rinnegan: Bansho Tenin pulled " + a + " pinned=" + wasPinned)
EndFunction

; ---------------- R3: Human Path ----------------
Actor Function TouchTarget()
	Actor p = Game.GetPlayer()
	Actor c = Game.GetCurrentCrosshairRef() as Actor
	If c && c != p && !c.IsDead() && p.GetDistance(c) <= SoulRipReach
		Return c
	EndIf
	Actor[] around = MiscUtil.ScanCellNPCs(p, SoulRipReach, None, True)
	Actor best = None
	Float bestDist = SoulRipReach
	Int k = 0
	While around && k < around.Length
		Actor x = around[k]
		If x && x != p && !x.IsDead() && x.IsHostileToActor(p) && Math.Abs(p.GetHeadingAngle(x)) < 50.0
			Float d = p.GetDistance(x)
			If d < bestDist
				best = x
				bestDist = d
			EndIf
		EndIf
		k += 1
	EndWhile
	Return best
EndFunction

Function RemoveSoul()
	Actor p = Game.GetPlayer()
	Actor a = TouchTarget()
	If !a
		Return
	EndIf
	Keyword noSoul = Game.GetFormFromFile(0x103AD2, "Skyrim.esm") as Keyword    ; NoSoulTrap (also blocks Remove Soul)
	If a.HasKeyword(noSoul)
		Return
	EndIf
	Float hp = a.GetActorValuePercentage("Health")
	Bool isOpen = False
	If UchihaBoss(a)
		isOpen = hp < BossSoulRipHealth
	Else
		isOpen = Exposed(a) || a.GetActorValue("Paralysis") > 0 || hp < SoulRipHealth
	EndIf
	If !isOpen
		Return                                               ; the slow Uchiha drain carries on as before
	EndIf
	(Game.GetFormFromFile(0x04DBA4, "Skyrim.esm") as Spell).Cast(p, a)      ; vanilla Soul Trap
	Utility.Wait(0.3)
	a.Kill(p)
	Debug.Notification("Human Path: " + a.GetDisplayName() + "'s soul is torn out.")
	Debug.Trace("CTOB rinnegan: Human Path soul rip on " + a)
EndFunction

; ---------------- R4: Outer Path: Chakra Receivers ----------------
; Called by CTOB_ReceiverRodEffect when a rod lands.
Function RodHit(Actor a, Actor caster)
	If !a || a.IsDead()
		Return
	EndIf
	Float dmg = 15.0 + Game.GetPlayer().GetLevel()
	If a.GetActorValue("Health") <= dmg
		a.Kill(caster)
		Return
	EndIf
	a.DamageActorValue("Health", dmg)
	a.DamageActorValue("Magicka", RodMagickaDrain)
	(Own(0x827) as Spell).Cast(Game.GetPlayer(), a)          ; Pinned: slowed, marked for Bansho Tenin
	a.ModActorValue("CarryWeight", 0.1)                      ; make the speed change take effect now
	a.ModActorValue("CarryWeight", -0.1)
	If a == RodVictim && Now() - RodVolley < RodWindow
		RodHits += 1
	Else
		RodVictim = a
		RodHits = 1
		RodVolley = Now()
	EndIf
	If RodHits == RodCount
		RodHits = 0
		Hold(a, 2)
		Debug.Notification(a.GetDisplayName() + " is pinned by the receivers.")
	EndIf
EndFunction

; ---------------- R5: Tengai Shinsei spares your followers ----------------
Function ShieldFollowers()
	Actor p = Game.GetPlayer()
	Actor[] around = MiscUtil.ScanCellNPCs(p, 8000.0, None, True)
	Actor[] shielded = new Actor[16]
	Int count = 0
	Int k = 0
	While around && k < around.Length && count < 16
		Actor a = around[k]
		If a && a != p && a.IsPlayerTeammate() && !a.IsGhost()
			a.SetGhost(True)
			shielded[count] = a
			count += 1
		EndIf
		k += 1
	EndWhile
	Debug.Trace("CTOB rinnegan: Tengai Shinsei, " + count + " followers shielded")
	Utility.Wait(FollowerShieldSeconds)
	k = 0
	While k < count
		If shielded[k]
			shielded[k].SetGhost(False)
		EndIf
		k += 1
	EndWhile
EndFunction

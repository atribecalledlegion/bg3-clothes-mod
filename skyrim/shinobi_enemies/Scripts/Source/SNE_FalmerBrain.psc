Scriptname SNE_FalmerBrain extends ActiveMagicEffect
{Shinobi Enemies, Falmer (2026-10-15). SPID gives this ability to FalmerFaction. Lore (UESP): blinded Snow Elves who
hunt by sound, stalk intruders in the dark, breed chaurus, poison their blades; shamans carry healing and wards.
- Hive screech: the first Falmer to engage alerts the hive (loud detection event at the player, once a minute).
- Release the chaurus: entering combat, it sets idle chaurus within 2000 on the player.
- Hunters: strike and fade (back off and circle in the dark). Bosses: steady and punishing.
- Casters (csFalmerMagic: shamans, spellswords): heal hurt Falmer and chaurus (< 50%), Ironflesh on the boss.
Naruto (no Uchiha), fitted to the lore:
- Hidden Mist + Silent Killing (Zabuza): level 30+ hunters/bosses, once per fight: the player's sight is clouded for
  8 s, the Falmer turns invisible and strikes; killing it clears the mist.
- Insect summoning (Aburame / chaurus husbandry): casters level 15+, once per fight: a 1.5 s call (a hit stops it)
  brings a chaurus to their side.
Blindness is their biggest weakness (user, 2026-10-15): Blindness is set to 100 (vanilla 80), so the engine finds
the player only by sound, and in combat each Falmer checks every second whether it can still HEAR the player:
  hearing range = 500 walking in light/no armour, 1000 in heavy armour; x0.35 sneaking; x0.5 muffled;
  +250 running, +700 sprinting; casting 1500 (2000 casting on the move); attacking 1200; never under 200.
Two quiet seconds (and no hit from the player in 3 s) and it LOSES you: it stops fighting, goes to where it last
heard you and listens and searches there for 25 s (they take a long time to stop looking); any sound, it is back.
That is also their bad aim: archers and casters only shoot what they can hear. Their spells are x1.15 (SNE_FalmerPerk).
A living Falmer caster (shaman/spellsword) within 1500 sharpens the hearing of the Falmer around it: range x1.5.
The moment that caster dies, they lose it (user, 2026-10-15).
Heavy armour: years of fighting men taught them that sound - they rush and swarm a heavy-armoured player (rush style).
Savage: non-casters swing 15% faster, pile on staggered prey, and go for the weakest (a bleeding-out follower).
Off: console "set SNE_FalmerTactics to 0". Needs SKSE.}

CombatStyle Property StyleHunter Auto
CombatStyle Property StyleBoss Auto
GlobalVariable Property TacticsOn Auto
GlobalVariable Property ScreechLock Auto
Actor Property PlayerRef Auto
CombatStyle Property VanillaMagic Auto
CombatStyle Property VanillaMissile Auto
CombatStyle Property VanillaBoss Auto
Faction Property FalmerFaction Auto
Faction Property ChaurusFaction Auto
Spell Property SpellHealOther Auto
Spell Property SpellIronflesh Auto
Spell Property SpellInvisibility Auto
ImageSpaceModifier Property MistImod Auto
LeveledActor Property ChaurusSummon Auto
EffectShader Property SummonFX Auto
CombatStyle Property StyleRush Auto
Static Property XMarkerBase Auto
Keyword Property ArmorHeavy Auto
MagicEffect Property Muffle1 Auto
MagicEffect Property Muffle2 Auto
MagicEffect Property Muffle3 Auto
MagicEffect Property Muffle4 Auto
MagicEffect Property Muffle5 Auto

Float Property MistSeconds = 8.0 AutoReadOnly
Float Property SearchSeconds = 25.0 AutoReadOnly
Float Property CasterHearingMult = 1.5 AutoReadOnly
Float Property CasterRange = 1500.0 AutoReadOnly
Int Property QuietTicksToLose = 2 AutoReadOnly

Int R_HUNTER = 1
Int R_ARCHER = 2
Int R_CASTER = 3
Int R_BOSS = 4

Actor Me
Int Role
CombatStyle OriginalStyle
Bool Done
Bool Busy
Bool BusyHit
Bool Released
Bool MistUsed
Bool Summoned
Bool MistOn
Float MistUntil
Float NextHeal
Bool Searching
Float SearchUntil
ObjectReference LastHeard
Float LastHitByPlayer
Int QuietTicks
Bool Rushing
Float NextPrey
Actor Attuner         ; the nearby caster sharpening this one's hearing
Float NextAttunerScan

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	Init()
	ApplyStyle()
	Debug.Trace("SNE falmer: start " + Me + " " + Me.GetDisplayName() + " role " + RoleName() + " (level " + Me.GetLevel() + ")")
	If Me.IsInCombat()
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
	Me.SetActorValue("Blindness", 100.0)    ; they find you by sound only
	If OriginalStyle == VanillaBoss
		Role = R_BOSS
	ElseIf OriginalStyle == VanillaMagic
		Role = R_CASTER
	ElseIf OriginalStyle == VanillaMissile || Me.GetEquippedItemType(1) == 7
		Role = R_ARCHER
	Else
		Role = R_HUNTER
	EndIf
	If Role != R_CASTER && Me.GetActorValue("WeaponSpeedMult") < 1.1
		Me.SetActorValue("WeaponSpeedMult", 1.15)        ; savage: faster swings
		Me.SetActorValue("LeftWeaponSpeedMult", 1.15)
	EndIf
EndFunction

String Function RoleName()
	If Role == R_BOSS
		Return "boss"
	ElseIf Role == R_CASTER
		Return "caster"
	ElseIf Role == R_ARCHER
		Return "archer"
	EndIf
	Return "hunter"
EndFunction

Bool Function Active()
	Return TacticsOn.GetValue() >= 0.5 && !Me.IsPlayerTeammate() && Me.IsHostileToActor(PlayerRef)
EndFunction

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Done = True
	ClearMist()
EndEvent

Event OnDying(Actor akKiller)
	Done = True
	ClearMist()    ; killing the mist-maker clears the mist
	If LastHeard
		LastHeard.Delete()
	EndIf
EndEvent

Event OnLoad()
	If !Done
		ApplyStyle()
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
		Searching = False
		QuietTicks = 0
		ApplyStyle()
		PushCPR()
		If Active()
			Screech()
			ReleaseChaurus()
		EndIf
		RegisterForSingleUpdate(1.0)
	ElseIf aeCombatState == 0 && !Me.IsDead()
		ClearMist()
		If !Searching
			UnregisterForUpdate()
		EndIf
	EndIf
EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If Busy
		BusyHit = True
	EndIf
	If akAggressor == PlayerRef
		LastHitByPlayer = Now()
		If Searching && !Done
			Searching = False
			Me.StartCombat(PlayerRef)    ; it felt that
		EndIf
	EndIf
EndEvent

Event OnUpdate()
	If Done || !Me || Me.IsDead()
		Return
	EndIf
	If Searching
		SearchTick()
		Return
	EndIf
	If !Me.IsInCombat()
		Return
	EndIf
	Float t = Now()
	If Active() && Me.GetCombatTarget() == PlayerRef && !Busy
		If Listen(t)
			Return    ; lost you: searching now
		EndIf
	EndIf
	If Active() && Role != R_CASTER && t >= NextPrey
		NextPrey = t + 3.0
		HuntTheWeak()
	EndIf
	If MistOn && (t >= MistUntil || MistUntil > t + MistSeconds + 1.0)
		ClearMist()
	EndIf
	If Active() && !Busy
		Float dist = Me.GetDistance(PlayerRef)
		If (Role == R_HUNTER || Role == R_BOSS) && !MistUsed && Me.GetLevel() >= 30 && dist < 1500.0
			HiddenMist()
		ElseIf Role == R_CASTER
			If !Summoned && Me.GetLevel() >= 15 && dist > 250.0
				InsectSummon()
			ElseIf t >= NextHeal
				ShamanCare(t)
			EndIf
		EndIf
	EndIf
	ApplyStyle()
	PushCPR()
	If !Done && !Me.IsDead()
		RegisterForSingleUpdate(1.0)
	EndIf
EndEvent

; ---------- blindness: hearing ----------
Float Function PlayerNoise()
	Bool heavy = PlayerRef.WornHasKeyword(ArmorHeavy)
	Float r = 500.0
	If heavy
		r = 1000.0
	EndIf
	If PlayerRef.IsSneaking()
		r *= 0.35
	EndIf
	If Muffled()
		r *= 0.5
	EndIf
	Bool moving = PlayerRef.IsRunning() || PlayerRef.IsSprinting()
	If PlayerRef.IsSprinting()
		r += 700.0
	ElseIf PlayerRef.IsRunning()
		r += 250.0
	EndIf
	If PlayerRef.GetAnimationVariableBool("IsCastingRight") || PlayerRef.GetAnimationVariableBool("IsCastingLeft")
		If moving
			r = MaxF(r, 2000.0)
		Else
			r = MaxF(r, 1500.0)
		EndIf
	EndIf
	If PlayerRef.GetAnimationVariableBool("IsAttacking") || PlayerRef.GetAnimationVariableBool("IsShouting")
		r = MaxF(r, 1200.0)
	EndIf
	Return MaxF(r, 200.0)
EndFunction

Float Function MaxF(Float a, Float b)
	If a > b
		Return a
	EndIf
	Return b
EndFunction

Bool Function Muffled()
	Return PlayerRef.HasMagicEffect(Muffle1) || PlayerRef.HasMagicEffect(Muffle2) || PlayerRef.HasMagicEffect(Muffle3) || PlayerRef.HasMagicEffect(Muffle4) || PlayerRef.HasMagicEffect(Muffle5)
EndFunction

Bool Function HearsPlayer()
	Return Me.GetDistance(PlayerRef) <= HearingRange()
EndFunction

Float Function HearingRange()
	Float r = PlayerNoise()
	If HasAttuner()
		r *= CasterHearingMult
	EndIf
	Return r
EndFunction

; a living Falmer caster nearby sharpens its hearing; the bonus is gone the moment that caster dies
Bool Function HasAttuner()
	If Role == R_CASTER
		Return False
	EndIf
	If Attuner && (Attuner.IsDead() || Attuner.IsDisabled() || Me.GetDistance(Attuner) > CasterRange)
		Debug.Trace("SNE falmer: " + Me + " loses the caster's sharpened hearing (" + Attuner + " dead " + Attuner.IsDead() + ")")
		Attuner = None
	EndIf
	Float t = Now()
	If NextAttunerScan > t + 10.0
		NextAttunerScan = 0.0
	EndIf
	If !Attuner && t >= NextAttunerScan
		NextAttunerScan = t + 3.0
		Cell c = Me.GetParentCell()
		If c
			Int n = c.GetNumRefs(43)
			If n > 80
				n = 80
			EndIf
			Int i = 0
			While i < n && !Attuner
				Actor a = c.GetNthRef(i, 43) as Actor
				If a && a != Me && !a.IsDead() && !a.IsDisabled() && a.IsInFaction(FalmerFaction) && a.GetLeveledActorBase().GetCombatStyle() == VanillaMagic && Me.GetDistance(a) <= CasterRange
					Attuner = a
					Debug.Trace("SNE falmer: " + Me + " hearing sharpened by caster " + a)
				EndIf
				i += 1
			EndWhile
		EndIf
	EndIf
	Return Attuner != None
EndFunction

; returns True if it lost the player this tick
Bool Function Listen(Float t)
	If LastHitByPlayer > t + 10.0
		LastHitByPlayer = 0.0
	EndIf
	If HearsPlayer() || t - LastHitByPlayer < 3.0
		QuietTicks = 0
		If !LastHeard
			LastHeard = PlayerRef.PlaceAtMe(XMarkerBase)
		Else
			LastHeard.MoveTo(PlayerRef)
		EndIf
		Rushing = PlayerRef.WornHasKeyword(ArmorHeavy) && Role != R_CASTER && Role != R_ARCHER
		Return False
	EndIf
	QuietTicks += 1
	If QuietTicks < QuietTicksToLose
		Return False
	EndIf
	; lost you
	QuietTicks = 0
	Searching = True
	SearchUntil = t + SearchSeconds
	Rushing = False
	Me.StopCombat()
	Debug.Trace("SNE falmer: " + Me + " LOST YOU (" + (Me.GetDistance(PlayerRef) as Int) + " away, hearing range " + (HearingRange() as Int) + ", caster " + (Attuner != None) + ") - searching for " + SearchSeconds + " s")
	RegisterForSingleUpdate(0.5)
	Return True
EndFunction

Function SearchTick()
	Float t = Now()
	If SearchUntil > t + SearchSeconds + 1.0
		SearchUntil = 0.0
	EndIf
	If Me.IsInCombat()
		Searching = False    ; the engine heard you
		RegisterForSingleUpdate(1.0)
		Return
	EndIf
	If HearsPlayer()
		Searching = False
		Me.StartCombat(PlayerRef)
		Debug.Trace("SNE falmer: " + Me + " HEARS YOU again (" + (Me.GetDistance(PlayerRef) as Int) + " away)")
		RegisterForSingleUpdate(1.0)
		Return
	EndIf
	If t >= SearchUntil
		Searching = False
		Debug.Trace("SNE falmer: " + Me + " gives up the search")
		Return
	EndIf
	; listen around the spot it last heard you
	If LastHeard
		If Me.GetDistance(LastHeard) > 250.0
			Me.PathToReference(LastHeard, 0.5)
		Else
			ObjectReference m = LastHeard.PlaceAtMe(XMarkerBase)
			m.MoveTo(LastHeard, Utility.RandomFloat(-300.0, 300.0), Utility.RandomFloat(-300.0, 300.0), 0.0)
			Me.PathToReference(m, 0.3)
			m.Delete()
		EndIf
	EndIf
	If !Done && !Me.IsDead()
		RegisterForSingleUpdate(0.5)
	EndIf
EndFunction

; savage: go for the weakest - a bleeding-out or badly hurt follower close by
Function HuntTheWeak()
	Cell c = Me.GetParentCell()
	If !c
		Return
	EndIf
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a != Me && !a.IsDead() && a.IsPlayerTeammate() && Me.GetDistance(a) < 700.0 && (a.IsBleedingOut() || a.GetActorValuePercentage("Health") < 0.3)
			If Me.GetCombatTarget() != a
				Me.StartCombat(a)
				Debug.Trace("SNE falmer: " + Me + " goes for the weak one: " + a)
			EndIf
			Return
		EndIf
		i += 1
	EndWhile
EndFunction

; ---------- lore ----------
Function Screech()
	Float t = Now()
	Float lock = ScreechLock.GetValue()
	If lock > t + 61.0
		lock = 0.0
	EndIf
	If t < lock
		Return
	EndIf
	ScreechLock.SetValue(t + 60.0)
	PlayerRef.CreateDetectionEvent(PlayerRef, 100)
	Debug.Trace("SNE falmer: " + Me + " screeches - the hive hears you")
EndFunction

Function ReleaseChaurus()
	If Released
		Return
	EndIf
	Released = True
	Cell c = Me.GetParentCell()
	If !c
		Return
	EndIf
	Int sent = 0
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && !a.IsDead() && a.IsInFaction(ChaurusFaction) && !a.IsInCombat() && Me.GetDistance(a) < 2000.0
			a.StartCombat(PlayerRef)
			sent += 1
		EndIf
		i += 1
	EndWhile
	If sent > 0
		Debug.Trace("SNE falmer: " + Me + " releases " + sent + " chaurus on you")
	EndIf
EndFunction

Function ShamanCare(Float t)
	Cell c = Me.GetParentCell()
	If !c
		Return
	EndIf
	Actor hurt = None
	Float worst = 0.5
	Actor boss = None
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a != Me && !a.IsDead() && a.IsInCombat() && (a.IsInFaction(FalmerFaction) || a.IsInFaction(ChaurusFaction)) && Me.GetDistance(a) < 1800.0
			Float pct = a.GetActorValuePercentage("Health")
			If pct < worst
				worst = pct
				hurt = a
			EndIf
			If !boss && a.GetLeveledActorBase().GetCombatStyle() == StyleBoss
				boss = a
			EndIf
		EndIf
		i += 1
	EndWhile
	If hurt
		If !hurt.IsInKillMove() && !hurt.IsBleedingOut() && hurt.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
			SpellHealOther.Cast(Me, hurt)
		EndIf
		NextHeal = t + 5.0
		Debug.Trace("SNE falmer: caster " + Me + " heals " + hurt + " at " + ((worst * 100.0) as Int) + "%")
	ElseIf boss && !boss.HasMagicEffect(SpellIronflesh.GetNthEffectMagicEffect(0))
		SpellIronflesh.Cast(boss, boss)
		NextHeal = t + 5.0
		Debug.Trace("SNE falmer: caster " + Me + " armours the boss " + boss)
	Else
		NextHeal = t + 2.0
	EndIf
EndFunction

; ---------- Naruto ----------
Function HiddenMist()
	MistUsed = True
	MistOn = True
	MistUntil = Now() + MistSeconds
	MistImod.Apply(1.0)
	SpellInvisibility.Cast(Me, Me)
	Debug.Trace("SNE falmer: " + Me + " HIDDEN MIST - your sight is clouded, it hunts by sound (" + MistSeconds + " s)")
EndFunction

Function ClearMist()
	If MistOn
		MistOn = False
		MistImod.Remove()
		Debug.Trace("SNE falmer: " + Me + " mist clears")
	EndIf
EndFunction

Function InsectSummon()
	Summoned = True
	Busy = True
	BusyHit = False
	SummonFX.Play(Me, 1.5)
	Debug.Trace("SNE falmer: caster " + Me + " calls a chaurus (1.5 s, hit it to stop it)")
	Utility.Wait(1.5)
	If BusyHit || Me.IsDead()
		Debug.Trace("SNE falmer: caster " + Me + " chaurus call STOPPED by a hit")
	Else
		Actor beast = Me.PlaceAtMe(ChaurusSummon) as Actor
		If beast
			beast.StartCombat(PlayerRef)
		EndIf
		Debug.Trace("SNE falmer: caster " + Me + " INSECT SUMMONING: " + beast)
	EndIf
	Busy = False
EndFunction

; ---------- style and pathing ----------
Function ApplyStyle()
	If !Me || Me.IsPlayerTeammate()
		Return
	EndIf
	ActorBase b = Me.GetLeveledActorBase()
	If !b
		Return
	EndIf
	CombatStyle want = OriginalStyle
	If TacticsOn.GetValue() >= 0.5
		If Rushing
			want = StyleRush
		ElseIf Role == R_HUNTER
			want = StyleHunter
		ElseIf Role == R_BOSS
			want = StyleBoss
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
	If Rushing
		SetCPR(False, 0.0, True, 90.0, 300.0, 60.0, 140.0, False)   ; swarm the tank from the sides
	ElseIf Role == R_HUNTER
		SetCPR(True, 0.6, True, 150.0, 700.0, 70.0, 140.0, True)     ; strike, fade, circle back in
	ElseIf Role == R_BOSS
		SetCPR(True, 0.1, True, 90.0, 300.0, 20.0, 50.0, False)
	Else
		SetCPR(True, 0.8, True, 400.0, 1200.0, 30.0, 60.0, True)
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
		Me.SetAnimationVariableFloat("CPR_FallbackDistMin", 300.0)
		Me.SetAnimationVariableFloat("CPR_FallbackDistMax", 800.0)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", 0.5)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", 1.2)
	EndIf
EndFunction

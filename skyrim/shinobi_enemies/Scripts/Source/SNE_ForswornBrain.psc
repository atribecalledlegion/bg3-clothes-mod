Scriptname SNE_ForswornBrain extends ActiveMagicEffect
{Shinobi Enemies, Forsworn and hagravens (2026-10-16). SPID gives this ability to ForswornFaction + HagravenFaction.
Lore (UESP): Reachmen who rose against Skyrim; savage dual-wielders, expert hunters, old nature and blood magic;
hagravens lead the Forsworn and make Briarhearts by replacing a warrior's heart with a briar heart.
- Fanatic (melee): wild, dual-wielding, circles and darts in. They do the dirty work.
- Archer: the most evasive archers in the game. Ranger + Quick Shot perks (SPID), faster on foot, back off while
  shooting (CPR fallback), take high ground when they hear you, sprint to a new spot when an ally falls, and scatter
  when every fanatic is dead. Level 25+ archers dodge (DMCO "Dodge" event, 6 s cooldown) when you get on them.
- Shaman: half medical ninja, half battlemage. Quicker support casts than the bandit medics (heal, flesh, cloaks),
  tankier (SNE_ForswornPerk: incoming damage x0.8) but weaker spells (x0.85). Wild magic: fire at range, frost up
  close, an atronach at tier 2+, and MELODY ARM (Dosu, Sound Village): get in its face and a sound burst staggers you
  and blurs your sight; then it backs off.
- Briarheart: the champion. CURSE MARK (Orochimaru): once, below 35%, the briar heart surges for 12 s (red glow,
  attack damage x1.5, faster swings, +100 armour, 20% health back), then EXHAUSTION for 8 s (slow, no stamina).
- Briar hearts are plant matter (2026-10-16): Briarhearts have -50 fire resistance, and one killed by fire (a fire
  hit in the last 3 s) is burned: SNE_BurnedFaction, and no Briar Rite can raise it.
- Hagraven: the ultimate support. Stays back and stacks Hagraven's Blessing on the team (Briarhearts first, then the
  strongest): 4 tiers, each +19% attack damage (x2 at full), +40 armour, +8% attack speed, +25 health, 30 s, kept up.
  Heals the hurt. BRIAR RITE: revives a dead Briarheart (3 s channel; hitting her cancels it; taking the heart from
  the body stops it for good) - once, or up to 10 times for a powerful hagraven (level 28+).
  BLOOD MAGIC: after 60 s of fighting, every 6 s the Forsworn within 3000 grow stronger (5 steps: +30 health and
  +8% attack damage each). Killing her strips her Blessing and Blood magic at once.
  She only fights herself when cornered or when most of her allies are dead; then MURDER OF CROWS: in melee she
  scatters and reappears beside another Forsworn (12 s cooldown).
- Matriarch morale: when a hagraven dies, low-level Forsworn nearby may break and flee for 10 s; Briarhearts turn
  vengeful (a Blessing of their own).
Off: console "set SNE_ForswornTactics to 0". Needs SKSE.}

CombatStyle Property StyleFanatic Auto
CombatStyle Property StyleArcher Auto
CombatStyle Property StyleShaman Auto
CombatStyle Property StyleBriarheart Auto
CombatStyle Property StyleHagravenSupport Auto
CombatStyle Property VanillaMissile Auto
CombatStyle Property VanillaMagic Auto
CombatStyle Property VanillaBossMagic Auto
CombatStyle Property VanillaHagraven Auto
GlobalVariable Property TacticsOn Auto
Actor Property PlayerRef Auto
Static Property XMarkerBase Auto
Faction Property ForswornFaction Auto
Faction Property HagravenFaction Auto
Race Property HagravenRace Auto
Ingredient Property BriarHeart Auto
EffectShader Property CurseFX Auto
EffectShader Property ReviveFX Auto
ImageSpaceModifier Property MelodyImod Auto
Spell Property ShamanMark Auto
Spell[] Property Blessing Auto       ; tiers 1-4; effect 0 of each is that tier's marker
Spell[] Property BloodTide Auto      ; tiers 1-5
Spell Property CurseMark Auto
Spell Property Exhaustion Auto
Spell Property SpellHealOther Auto
Spell Property SpellCloseWounds Auto
Spell Property SpellOakflesh Auto
Spell Property SpellStoneflesh Auto
Spell Property SpellIronflesh Auto
Spell Property SpellFlameCloak Auto
Spell Property SpellFrostCloak Auto
Spell Property SpellFirebolt Auto
Spell Property SpellFrostbite Auto
Spell Property SpellIceSpike Auto
Spell Property SpellFlameAtronach Auto
Spell Property SpellFrostAtronach Auto
Faction Property BurnedFaction Auto

Float Property Range = 3000.0 AutoReadOnly
Float Property BloodAfter = 60.0 AutoReadOnly
Float Property BloodStep = 6.0 AutoReadOnly
Float Property RiteSeconds = 3.0 AutoReadOnly
Int Property PowerfulHagLevel = 28 AutoReadOnly
Int Property DodgeLevel = 25 AutoReadOnly
Float Property SprintBonus = 60.0 AutoReadOnly
Float Property BurnWindow = 3.0 AutoReadOnly

Int R_FANATIC = 1
Int R_ARCHER = 2
Int R_SHAMAN = 3
Int R_BRIAR = 4
Int R_HAG = 5

Actor Me
Int Role
CombatStyle OriginalStyle
Bool Done
Bool Busy
Bool Prepared         ; one-time stat changes made (saved with the script)
Bool FireWeak
Float LastFireHit
Bool Sprinting
Bool Repositioning
Bool HeardTried
Float NextMove
Float NextDodge
Float NextSupport
Float NextAttack
Float NextMelody
Bool AtronachDone
Bool CurseUsed
Float CurseEnds
Float FleeUntil
Float SavedConfidence
; hagraven
Float FightStart
Float NextBlood
Int BloodLevel
Int RevivesLeft
Float NextRite
Bool RiteHit
Bool FightMode
Int CorneredTicks
Int StartAllies
Float NextCrows
Int RefreshIndex
Actor[] Allies
Int AllyCount

; ---------- setup ----------
Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	Init()
	ApplyStyle()
	Debug.Trace("SNE forsworn: start " + Me + " " + Me.GetDisplayName() + " role " + RoleName() + " tier " + Tier() + " (level " + Me.GetLevel() + ")")
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
	If Me.GetRace() == HagravenRace
		Role = R_HAG
	ElseIf Me.GetItemCount(BriarHeart) > 0 || StringUtil.Find(Me.GetDisplayName(), "Briarheart") >= 0
		Role = R_BRIAR
	ElseIf OriginalStyle == VanillaMissile || Me.GetEquippedItemType(1) == 7
		Role = R_ARCHER
	ElseIf OriginalStyle == VanillaMagic || OriginalStyle == VanillaBossMagic || Me.GetEquippedItemType(1) == 9 || Me.GetEquippedItemType(0) == 9
		Role = R_SHAMAN
	Else
		Role = R_FANATIC
	EndIf
	If Role == R_HAG
		If Me.GetLevel() >= PowerfulHagLevel
			RevivesLeft = 10
		Else
			RevivesLeft = 1
		EndIf
	EndIf
	If Role == R_BRIAR && !FireWeak
		FireWeak = True
		Me.ModActorValue("FireResist", -50.0)    ; the briar heart burns
	EndIf
	If !Prepared
		Prepared = True
		If Role == R_ARCHER
			Me.ModActorValue("SpeedMult", 15.0)    ; light on their feet
			Nudge()
		ElseIf Role == R_SHAMAN
			Me.AddSpell(ShamanMark, False)        ; perk: tankier, weaker spells
		EndIf
	EndIf
EndFunction

String Function RoleName()
	If Role == R_ARCHER
		Return "archer"
	ElseIf Role == R_SHAMAN
		Return "shaman"
	ElseIf Role == R_BRIAR
		Return "Briarheart"
	ElseIf Role == R_HAG
		Return "hagraven"
	EndIf
	Return "fanatic"
EndFunction

Int Function Tier()
	Int lv = Me.GetLevel()
	If lv < 12
		Return 1
	ElseIf lv < 25
		Return 2
	ElseIf lv < 40
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
	If Sprinting
		Me.ModActorValue("SpeedMult", -SprintBonus)
	EndIf
	If !Active()
		Return
	EndIf
	If Role == R_BRIAR && LastFireHit > 0.0 && Now() - LastFireHit < BurnWindow
		Me.AddToFaction(BurnedFaction)
		Debug.Notification("The briar heart burns away.")
		Debug.Trace("SNE forsworn: Briarheart " + Me + " died by fire - its briar heart is burned, no Briar Rite")
	EndIf
	If Role == R_HAG
		StripBuffs()
		Me.SendModEvent("SNE_MatriarchFell")    ; sent from the actor: this effect ends with the death
		Debug.Trace("SNE forsworn: hagraven " + Me + " is dead - her blessing and blood magic fade")
	EndIf
	Me.SendModEvent("SNE_ForswornFell", RoleName(), Role as Float)
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
		HeardTried = False
		RegisterForModEvent("SNE_ForswornFell", "OnForswornFell")
		RegisterForModEvent("SNE_MatriarchFell", "OnMatriarchFell")
		If Role == R_HAG && FightStart <= 0.0
			FightStart = Now()
			BloodLevel = 0
			NextBlood = 0.0
			StartAllies = ScanAllies(Range)
			If StartAllies < 1
				StartAllies = 1
			EndIf
			Debug.Trace("SNE forsworn: hagraven " + Me + " leads " + StartAllies + " Forsworn, " + RevivesLeft + " Briar Rite(s)")
		EndIf
		ApplyStyle()
		PushCPR()
		If Active() && (Role == R_ARCHER || Role == R_SHAMAN) && !HeardTried && Me.GetDistance(PlayerRef) > 900.0
			HeardTried = True
			TryReposition("takes the high ground", False)
		EndIf
		RegisterForSingleUpdate(1.0)
	ElseIf aeCombatState == 2
		If Active() && (Role == R_ARCHER || Role == R_SHAMAN) && !HeardTried && akTarget == PlayerRef
			HeardTried = True
			TryReposition("heard you - takes the high ground", False)
		EndIf
	ElseIf aeCombatState == 0 && !Me.IsDead()
		FightStart = 0.0
		FightMode = False
		CorneredTicks = 0
		ApplyStyle()
	EndIf
EndEvent

Event OnUpdate()
	If Done || !Me || Me.IsDead()
		Return
	EndIf
	Float t = Now()
	If FleeUntil > t + 30.0
		FleeUntil = t    ; stale value from an earlier launch
	EndIf
	If FleeUntil > 0.0 && t >= FleeUntil
		FleeUntil = 0.0
		Me.SetActorValue("Confidence", SavedConfidence)
		Debug.Trace("SNE forsworn: " + Me + " regains its nerve")
	EndIf
	If CurseEnds > t + 30.0
		CurseEnds = t
	EndIf
	If CurseEnds > 0.0 && t >= CurseEnds
		CurseEnds = 0.0
		Exhaustion.Cast(Me, Me)
		Me.DamageActorValue("Stamina", Me.GetActorValue("Stamina"))
		Debug.Trace("SNE forsworn: Briarheart " + Me + " Curse Mark burns out - EXHAUSTED for 8 s")
	EndIf
	If !Me.IsInCombat()
		If FleeUntil > 0.0 || CurseEnds > 0.0
			RegisterForSingleUpdate(1.0)
		EndIf
		Return
	EndIf
	If Active() && !Busy
		If Role == R_ARCHER
			ArcherTick(t)
		ElseIf Role == R_SHAMAN
			ShamanTick(t)
		ElseIf Role == R_BRIAR
			CurseCheck()
		ElseIf Role == R_HAG
			HagTick(t)
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
		RiteHit = True
	EndIf
	If Role == R_BRIAR && IsFire(akSource)
		LastFireHit = Now()
	EndIf
	If Done || !Me || !Active()
		Return
	EndIf
	If Role == R_ARCHER && akAggressor == PlayerRef && !akProjectile
		TryDodge("hit in melee")    ; get out before the follow-up
	ElseIf Role == R_BRIAR
		CurseCheck()
	EndIf
EndEvent

Bool Function IsFire(Form src)
	Spell s = src as Spell
	If s
		Int i = 0
		While i < s.GetNumEffects()
			MagicEffect m = s.GetNthEffectMagicEffect(i)
			If m && m.GetResistance() == "FireResist"
				Return True
			EndIf
			i += 1
		EndWhile
		Return False
	EndIf
	Enchantment e
	Weapon w = src as Weapon
	If w
		e = w.GetEnchantment()
	Else
		e = src as Enchantment
	EndIf
	If e
		Int j = 0
		While j < e.GetNumEffects()
			MagicEffect m2 = e.GetNthEffectMagicEffect(j)
			If m2 && m2.GetResistance() == "FireResist"
				Return True
			EndIf
			j += 1
		EndWhile
	EndIf
	Return False
EndFunction

; ---------- allies ----------
Bool Function IsAlly(Actor a, Float within)
	Return a && a != Me && !a.IsDead() && !a.IsDisabled() && (a.IsInFaction(ForswornFaction) || a.IsInFaction(HagravenFaction)) && !a.IsPlayerTeammate() && Me.GetDistance(a) < within
EndFunction

Int Function ScanAllies(Float within)
	If !Allies
		Allies = new Actor[32]
	EndIf
	AllyCount = 0
	Cell c = Me.GetParentCell()
	If !c
		Return 0
	EndIf
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n && AllyCount < 32
		Actor a = c.GetNthRef(i, 43) as Actor
		If IsAlly(a, within)
			Allies[AllyCount] = a
			AllyCount += 1
		EndIf
		i += 1
	EndWhile
	Return AllyCount
EndFunction

Bool Function IsBriarheart(Actor a)
	Return a.GetItemCount(BriarHeart) > 0
EndFunction

Int Function FanaticsLeft()
	ScanAllies(Range)
	Int k = 0
	Int i = 0
	While i < AllyCount
		Int r = Allies[i].GetEquippedItemType(1)
		If r >= 1 && r <= 6 && Allies[i].GetRace() != HagravenRace
			k += 1
		EndIf
		i += 1
	EndWhile
	Return k
EndFunction

Event OnForswornFell(String eventName, String strArg, Float numArg, Form sender)
	Actor dead = sender as Actor
	If Done || !Me || Me.IsDead() || !Me.IsInCombat() || !Active() || Role != R_ARCHER || !dead || dead == Me
		Return
	EndIf
	If Me.GetDistance(dead) > Range
		Return
	EndIf
	Utility.Wait(Utility.RandomFloat(0.1, 0.5))
	If FanaticsLeft() == 0
		TryReposition("every fanatic is dead - scatters", True)
	ElseIf Utility.RandomFloat() < 0.45 + 0.1 * Tier()
		TryReposition("saw " + strArg + " " + dead + " fall", False)
	Else
		Debug.Trace("SNE forsworn: archer " + Me + " saw " + strArg + " fall, holds its spot")
	EndIf
EndEvent

Event OnMatriarchFell(String eventName, String strArg, Float numArg, Form sender)
	Actor hag = sender as Actor
	If Done || !Me || Me.IsDead() || !Me.IsInCombat() || !Active() || Role == R_HAG || !hag
		Return
	EndIf
	If Me.GetDistance(hag) > Range
		Return
	EndIf
	If Role == R_BRIAR
		Blessing[0].Cast(Me, Me)
		Debug.Trace("SNE forsworn: Briarheart " + Me + " - the matriarch is dead: VENGEFUL")
	ElseIf Me.GetLevel() < 25 && Utility.RandomFloat() < 0.4 && FleeUntil <= 0.0
		SavedConfidence = Me.GetActorValue("Confidence")
		Me.SetActorValue("Confidence", 0.0)
		FleeUntil = Now() + 10.0
		Debug.Trace("SNE forsworn: " + RoleName() + " " + Me + " - the matriarch is dead: it BREAKS and flees")
	EndIf
EndEvent

; ---------- archers ----------
Function ArcherTick(Float t)
	Float d = Me.GetDistance(PlayerRef)
	If d < 260.0
		TryDodge("you are on it")
	EndIf
	; caught up close and could not dodge: break away for a better spot now and then
	If d < 400.0 && t >= NextMove && Utility.RandomFloat() < 0.15 + 0.05 * Tier()
		TryReposition("you closed in", False)
	EndIf
EndFunction

Function TryDodge(String reason)
	If Me.GetLevel() < DodgeLevel || Repositioning
		Return
	EndIf
	Float t = Now()
	If NextDodge > t + 30.0
		NextDodge = 0.0
	EndIf
	If t < NextDodge
		Return
	EndIf
	NextDodge = t + 6.0
	Float angle = 180.0
	Float r = Utility.RandomFloat()
	If r < 0.3
		angle = 90.0
	ElseIf r < 0.6
		angle = 270.0
	EndIf
	Me.SetAnimationVariableFloat("Dodge_Angle", angle)
	Debug.SendAnimationEvent(Me, "Dodge")
	Debug.Trace("SNE forsworn: archer " + Me + " DODGES (" + reason + ", angle " + (angle as Int) + ")")
EndFunction

Function TryReposition(String reason, Bool scatter)
	If Done || Repositioning || Me.IsDead()
		Return
	EndIf
	Float t = Now()
	If NextMove > t + 30.0
		NextMove = 0.0
	EndIf
	If t < NextMove
		Return
	EndIf
	NextMove = t + 5.0
	Repositioning = True
	ObjectReference spot = None
	If !scatter
		spot = FindPerch()
	EndIf
	Bool made = False
	If !spot
		spot = AwayMarker(scatter)
		made = True
	EndIf
	Bool fighting = Me.IsInCombat()
	Debug.Trace("SNE forsworn: " + RoleName() + " " + Me + " " + reason + ", sprinting to " + spot + " (perch " + !made + ", " + (Me.GetDistance(spot) as Int) + " away, " + ((spot.GetPositionZ() - PlayerRef.GetPositionZ()) as Int) + " above you)")
	SetSprint(True)
	If fighting
		Me.StopCombat()
	EndIf
	Bool reached = Me.PathToReference(spot, 1.0)
	SetSprint(False)
	If fighting && !Me.IsDead()
		Me.StartCombat(PlayerRef)
	EndIf
	Debug.Trace("SNE forsworn: " + RoleName() + " " + Me + " reposition reached " + reached + ", now " + (Me.GetDistance(PlayerRef) as Int) + " from you")
	If made
		spot.Delete()
	EndIf
	Repositioning = False
EndFunction

; furniture or idle marker above the player and further from them: the closest thing to high ground Papyrus can find
ObjectReference Function FindPerch()
	Cell c = Me.GetParentCell()
	If !c
		Return None
	EndIf
	Float myDist = Me.GetDistance(PlayerRef)
	Float pz = PlayerRef.GetPositionZ()
	ObjectReference best = None
	Float bestScore = -100000.0
	Int[] types = new Int[2]
	types[0] = 40
	types[1] = 47
	Int k = 0
	While k < 2
		Int n = c.GetNumRefs(types[k])
		If n > 80
			n = 80
		EndIf
		Int i = 0
		While i < n
			ObjectReference r = c.GetNthRef(i, types[k])
			If r && !r.IsDisabled()
				Float dA = Me.GetDistance(r)
				Float dP = PlayerRef.GetDistance(r)
				If dA > 250.0 && dA < 1800.0 && dP > 800.0 && dP > myDist + 200.0
					Float score = (r.GetPositionZ() - pz) * 2.0 + dP * 0.5 - dA * 0.3
					If score > bestScore
						bestScore = score
						best = r
					EndIf
				EndIf
			EndIf
			i += 1
		EndWhile
		k += 1
	EndWhile
	Return best
EndFunction

; away from the player; a scatter spreads them out (a random turn of up to 70 degrees each way, further)
ObjectReference Function AwayMarker(Bool scatter)
	Float dx = Me.GetPositionX() - PlayerRef.GetPositionX()
	Float dy = Me.GetPositionY() - PlayerRef.GetPositionY()
	Float len = Math.sqrt(dx * dx + dy * dy)
	If len < 1.0
		dx = 1.0
		dy = 0.0
		len = 1.0
	EndIf
	dx /= len
	dy /= len
	Float dist = 900.0
	If scatter
		Float a = Utility.RandomFloat(-70.0, 70.0)
		Float cs = Math.cos(a)
		Float sn = Math.sin(a)
		Float nx = dx * cs - dy * sn
		dy = dx * sn + dy * cs
		dx = nx
		dist = Utility.RandomFloat(900.0, 1400.0)
	EndIf
	ObjectReference m = Me.PlaceAtMe(XMarkerBase)
	m.SetPosition(Me.GetPositionX() + dx * dist, Me.GetPositionY() + dy * dist, Me.GetPositionZ())
	Return m
EndFunction

Function SetSprint(Bool on)
	If on == Sprinting || !Me
		Return
	EndIf
	Sprinting = on
	If on
		Me.ModActorValue("SpeedMult", SprintBonus)
	Else
		Me.ModActorValue("SpeedMult", -SprintBonus)
	EndIf
	Nudge()
EndFunction

Function Nudge()    ; a SpeedMult change only takes effect after a carry weight change
	Me.ModActorValue("CarryWeight", 0.1)
	Me.ModActorValue("CarryWeight", -0.1)
EndFunction

; ---------- shamans ----------
Float Function SupportCooldown()
	Int t = Tier()
	If t == 1
		Return 2.5
	ElseIf t == 2
		Return 2.0
	ElseIf t == 3
		Return 1.6
	EndIf
	Return 1.3
EndFunction

Bool Function HasFlesh(Actor a)
	Return a.HasMagicEffect(SpellOakflesh.GetNthEffectMagicEffect(0)) || a.HasMagicEffect(SpellStoneflesh.GetNthEffectMagicEffect(0)) || a.HasMagicEffect(SpellIronflesh.GetNthEffectMagicEffect(0))
EndFunction

Bool Function HasCloak(Actor a)
	Return a.HasMagicEffect(SpellFlameCloak.GetNthEffectMagicEffect(0)) || a.HasMagicEffect(SpellFrostCloak.GetNthEffectMagicEffect(0))
EndFunction

Function ShamanTick(Float t)
	Float d = Me.GetDistance(PlayerRef)
	If NextMelody > t + 30.0
		NextMelody = 0.0
	EndIf
	If d < 220.0 && t >= NextMelody
		MelodyArm()
		Return
	EndIf
	If !AtronachDone && Tier() >= 2
		AtronachDone = True
		If d < 600.0
			SpellFrostAtronach.Cast(Me, Me)
		Else
			SpellFlameAtronach.Cast(Me, Me)
		EndIf
		Debug.Trace("SNE forsworn: shaman " + Me + " calls an atronach")
		Return
	EndIf
	If NextSupport > t + 30.0
		NextSupport = 0.0
	EndIf
	If t >= NextSupport
		NextSupport = t + SupportCooldown()
		If Support()
			Return
		EndIf
	EndIf
	; wild magic: fire at range, frost up close
	If NextAttack > t + 30.0
		NextAttack = 0.0
	EndIf
	If t >= NextAttack && Me.HasLOS(PlayerRef)
		NextAttack = t + 5.0
		If d < 500.0
			If Tier() >= 3
				SpellIceSpike.Cast(Me, PlayerRef)
			Else
				SpellFrostbite.Cast(Me, PlayerRef)
			EndIf
		Else
			SpellFirebolt.Cast(Me, PlayerRef)
		EndIf
	EndIf
EndFunction

Bool Function Support()
	If Me.GetActorValuePercentage("Health") < 0.4
		SpellCloseWounds.Cast(Me, Me)
		Debug.Trace("SNE forsworn: shaman " + Me + " heals itself")
		Return True
	EndIf
	ScanAllies(1500.0)
	Actor hurt = None
	Float hurtPct = 0.5
	Actor needFlesh = None
	Actor needCloak = None
	Int i = 0
	While i < AllyCount
		Actor a = Allies[i]
		Float p = a.GetActorValuePercentage("Health")
		If p < hurtPct
			hurtPct = p
			hurt = a
		EndIf
		If !needFlesh && a.IsInCombat() && !HasFlesh(a)
			needFlesh = a
		EndIf
		Int r = a.GetEquippedItemType(1)
		If !needCloak && a.IsInCombat() && r >= 1 && r <= 6 && !HasCloak(a)
			needCloak = a
		EndIf
		i += 1
	EndWhile
	If hurt
		If !hurt.IsInKillMove() && !hurt.IsBleedingOut() && hurt.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
			SpellHealOther.Cast(Me, hurt)
		EndIf
		Debug.Trace("SNE forsworn: shaman " + Me + " heals " + hurt + " at " + ((hurtPct * 100.0) as Int) + "%")
	ElseIf needFlesh
		Spell f = SpellOakflesh
		If Tier() >= 3
			f = SpellIronflesh
		ElseIf Tier() == 2
			f = SpellStoneflesh
		EndIf
		f.Cast(needFlesh, needFlesh)
		Debug.Trace("SNE forsworn: shaman " + Me + " armours " + needFlesh)
	ElseIf needCloak
		If Me.GetDistance(PlayerRef) < 600.0 || Tier() >= 3
			SpellFrostCloak.Cast(needCloak, needCloak)
		Else
			SpellFlameCloak.Cast(needCloak, needCloak)
		EndIf
		Debug.Trace("SNE forsworn: shaman " + Me + " cloaks " + needCloak)
	ElseIf !HasFlesh(Me)
		SpellOakflesh.Cast(Me, Me)
	Else
		Return False
	EndIf
	Return True
EndFunction

; Dosu's Melody Arm: a sound burst at close range
Function MelodyArm()
	NextMelody = Now() + 12.0
	Busy = True
	PlayerRef.SetAnimationVariableFloat("staggerMagnitude", 0.6)
	Debug.SendAnimationEvent(PlayerRef, "staggerStart")
	PlayerRef.DamageActorValue("Health", 6.0 + 4.0 * Tier())
	Game.ShakeCamera(None, 0.6, 1.0)
	If MelodyImod
		MelodyImod.Apply(1.0)
	EndIf
	Debug.Trace("SNE forsworn: shaman " + Me + " MELODY ARM - you are staggered, ears ringing")
	Utility.Wait(2.5)
	If MelodyImod
		MelodyImod.Remove()
	EndIf
	Busy = False
EndFunction

; ---------- Briarhearts ----------
Function CurseCheck()
	If CurseUsed || Busy
		Return
	EndIf
	Float hp = Me.GetActorValuePercentage("Health")
	If hp < 0.35 && hp > 0.0 && !Me.IsDead()
		CurseUsed = True
		CurseMark.Cast(Me, Me)
		CurseFX.Play(Me, 12.0)
		If !Me.IsInKillMove() && !Me.IsBleedingOut() && Me.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
			Me.RestoreActorValue("Health", Me.GetBaseActorValue("Health") * 0.2)
		EndIf
		CurseEnds = Now() + 12.0
		Debug.Trace("SNE forsworn: Briarheart " + Me + " CURSE MARK at " + ((hp * 100.0) as Int) + "%")
	EndIf
EndFunction

; ---------- hagravens ----------
Function HagTick(Float t)
	Float d = Me.GetDistance(PlayerRef)
	Int alive = ScanAllies(Range)
	If d < 300.0
		CorneredTicks += 1
	Else
		CorneredTicks = 0
	EndIf
	Bool wasFighting = FightMode
	FightMode = CorneredTicks >= 2 || alive == 0 || (alive as Float) < (StartAllies as Float) * 0.35
	If FightMode != wasFighting
		Debug.Trace("SNE forsworn: hagraven " + Me + " fight mode " + FightMode + " (" + alive + "/" + StartAllies + " allies, you " + (d as Int) + " away)")
	EndIf
	; murder of crows
	If NextCrows > t + 30.0
		NextCrows = 0.0
	EndIf
	If FightMode && d < 250.0 && t >= NextCrows && alive > 0
		NextCrows = t + 12.0
		MurderOfCrows()
		Return
	EndIf
	; blood magic
	If FightStart > t + 1.0
		FightStart = t    ; stale value from an earlier launch
	EndIf
	If FightStart > 0.0 && t - FightStart >= BloodAfter && t >= NextBlood
		NextBlood = t + BloodStep
		BloodMagic()
	EndIf
	; briar rite
	If NextRite > t + 30.0
		NextRite = 0.0
	EndIf
	If RevivesLeft > 0 && t >= NextRite
		Actor body = FindBriarBody()
		If body
			BriarRite(body)
			Return
		EndIf
	EndIf
	; heal, then bless
	If NextSupport > t + 30.0
		NextSupport = 0.0
	EndIf
	If t >= NextSupport && alive > 0
		If Tier() >= 4
			NextSupport = t + 1.5
		Else
			NextSupport = t + 2.0
		EndIf
		HagSupport()
	EndIf
EndFunction

Function HagSupport()
	Actor hurt = None
	Float hurtPct = 0.45
	Actor best = None
	Int bestNext = 99
	Float bestScore = -1.0
	Int i = 0
	While i < AllyCount
		Actor a = Allies[i]
		Float p = a.GetActorValuePercentage("Health")
		If p < hurtPct
			hurtPct = p
			hurt = a
		EndIf
		Int nt = NextTier(a)
		If nt < 4
			Float score = a.GetLevel() as Float
			If IsBriarheart(a)
				score += 1000.0
			EndIf
			If nt < bestNext || (nt == bestNext && score > bestScore)
				bestNext = nt
				bestScore = score
				best = a
			EndIf
		EndIf
		i += 1
	EndWhile
	If hurt
		If !hurt.IsInKillMove() && !hurt.IsBleedingOut() && hurt.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
			SpellHealOther.Cast(Me, hurt)
		EndIf
		Debug.Trace("SNE forsworn: hagraven " + Me + " heals " + hurt + " at " + ((hurtPct * 100.0) as Int) + "%")
	ElseIf best
		; strongest first: a Briarheart gets every tier before the rest get their next one
		Actor pick = best
		Int k = 0
		While k < AllyCount
			If IsBriarheart(Allies[k]) && NextTier(Allies[k]) < 4
				pick = Allies[k]
				k = AllyCount
			EndIf
			k += 1
		EndWhile
		Int tier = NextTier(pick)
		Blessing[tier].Cast(pick, pick)
		Debug.Trace("SNE forsworn: hagraven " + Me + " BLESSES " + pick + " (tier " + (tier + 1) + "/4)")
	ElseIf AllyCount > 0
		; everyone is at full blessing: keep it up, one ally per tick
		RefreshIndex += 1
		If RefreshIndex >= AllyCount
			RefreshIndex = 0
		EndIf
		Actor r = Allies[RefreshIndex]
		Int j = 0
		While j < 4
			Blessing[j].Cast(r, r)
			j += 1
		EndWhile
	EndIf
EndFunction

Int Function NextTier(Actor a)    ; first blessing tier (0-3) the ally lacks, 4 = full
	Int i = 0
	While i < 4
		If !a.HasMagicEffect(Blessing[i].GetNthEffectMagicEffect(0))
			Return i
		EndIf
		i += 1
	EndWhile
	Return 4
EndFunction

Function BloodMagic()
	If BloodLevel < 5
		BloodLevel += 1
		If BloodLevel == 1
			Debug.Notification("The hagraven's blood magic is empowering the Forsworn...")
		EndIf
		Debug.Trace("SNE forsworn: hagraven " + Me + " BLOOD MAGIC step " + BloodLevel + "/5 on " + AllyCount + " Forsworn")
	EndIf
	Int i = 0
	While i < AllyCount
		Int k = 0
		While k < BloodLevel
			BloodTide[k].Cast(Allies[i], Allies[i])
			k += 1
		EndWhile
		i += 1
	EndWhile
	Int s = 0
	While s < BloodLevel
		BloodTide[s].Cast(Me, Me)
		s += 1
	EndWhile
EndFunction

Actor Function FindBriarBody()
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
		If a && a.IsDead() && !a.IsDisabled() && a.IsInFaction(ForswornFaction) && a.GetItemCount(BriarHeart) > 0 && !a.IsInFaction(BurnedFaction) && Me.GetDistance(a) < 2000.0
			Return a
		EndIf
		i += 1
	EndWhile
	Return None
EndFunction

Function BriarRite(Actor body)
	Busy = True
	RiteHit = False
	Debug.Trace("SNE forsworn: hagraven " + Me + " begins the BRIAR RITE on " + body + " (" + RevivesLeft + " left)")
	Me.SetDontMove(True)
	ReviveFX.Play(body, RiteSeconds + 0.5)
	Float waited = 0.0
	While waited < RiteSeconds && !RiteHit && !Me.IsDead()
		Utility.Wait(0.5)
		waited += 0.5
	EndWhile
	Me.SetDontMove(False)
	ReviveFX.Stop(body)
	If Me.IsDead()
		Busy = False
		Return
	EndIf
	If RiteHit
		NextRite = Now() + 5.0
		Debug.Trace("SNE forsworn: hagraven " + Me + " Briar Rite INTERRUPTED")
	ElseIf body.GetItemCount(BriarHeart) <= 0
		Debug.Trace("SNE forsworn: hagraven " + Me + " Briar Rite fails - the heart is gone")
	Else
		body.Resurrect()
		RevivesLeft -= 1
		NextRite = Now() + 4.0
		Utility.Wait(0.5)
		body.StartCombat(PlayerRef)
		Debug.Trace("SNE forsworn: hagraven " + Me + " Briar Rite: " + body + " RISES (" + RevivesLeft + " left)")
	EndIf
	Busy = False
EndFunction

; cornered: she bursts into crows and comes back beside the Forsworn furthest from you
Function MurderOfCrows()
	Actor far = None
	Float farD = 0.0
	Int i = 0
	While i < AllyCount
		Float dd = Allies[i].GetDistance(PlayerRef)
		If dd > farD
			farD = dd
			far = Allies[i]
		EndIf
		i += 1
	EndWhile
	If !far || farD < 500.0
		Return
	EndIf
	ReviveFX.Play(Me, 1.0)
	Utility.Wait(0.3)
	Me.MoveTo(far, Utility.RandomFloat(-120.0, 120.0), Utility.RandomFloat(-120.0, 120.0), 0.0)
	ReviveFX.Play(Me, 1.0)
	Debug.Trace("SNE forsworn: hagraven " + Me + " MURDER OF CROWS - reappears by " + far + " (" + (farD as Int) + " from you)")
EndFunction

Function StripBuffs()
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
		If a && a != Me && !a.IsDead() && (a.IsInFaction(ForswornFaction) || a.IsInFaction(HagravenFaction)) && Me.GetDistance(a) < 4000.0
			Int k = 0
			While k < 4
				a.DispelSpell(Blessing[k])
				k += 1
			EndWhile
			k = 0
			While k < 5
				a.DispelSpell(BloodTide[k])
				k += 1
			EndWhile
		EndIf
		i += 1
	EndWhile
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
	If TacticsOn.GetValue() >= 0.5
		If Role == R_FANATIC
			want = StyleFanatic
		ElseIf Role == R_ARCHER
			want = StyleArcher
		ElseIf Role == R_SHAMAN
			want = StyleShaman
		ElseIf Role == R_BRIAR
			want = StyleBriarheart
		ElseIf Role == R_HAG && FightMode
			want = VanillaHagraven
		ElseIf Role == R_HAG
			want = StyleHagravenSupport
		EndIf
	EndIf
	If want && b.GetCombatStyle() != want
		b.SetCombatStyle(want)
	EndIf
EndFunction

Function PushCPR()
	If !Active() || Busy || Repositioning
		Return
	EndIf
	If Role == R_FANATIC
		SetCPR(True, 0.25, True, 100.0, 320.0, 40.0, 120.0, False, 0.0, 0.0)     ; wild: dart in, circle, dart in
	ElseIf Role == R_ARCHER
		SetCPR(True, 0.9, True, 400.0, 1200.0, 30.0, 70.0, True, 500.0, 1300.0)  ; keep the gap while shooting
	ElseIf Role == R_SHAMAN
		SetCPR(True, 0.6, True, 300.0, 900.0, 30.0, 60.0, True, 400.0, 900.0)
	ElseIf Role == R_BRIAR
		SetCPR(True, 0.1, True, 80.0, 250.0, 30.0, 90.0, False, 0.0, 0.0)
	ElseIf FightMode
		SetCPR(True, 0.3, True, 150.0, 400.0, 30.0, 90.0, False, 0.0, 0.0)
	Else
		SetCPR(True, 1.0, True, 700.0, 1500.0, 20.0, 50.0, True, 700.0, 1500.0) ; the matriarch stays back
	EndIf
EndFunction

Function SetCPR(Bool backoff, Float backoffChance, Bool circle, Float circleMin, Float circleMax, Float angleMin, Float angleMax, Bool fallback, Float fallMin, Float fallMax)
	Me.SetAnimationVariableBool("CPR_EnableBackoff", backoff)
	Me.SetAnimationVariableFloat("CPR_BackoffChance", backoffChance)
	Me.SetAnimationVariableBool("CPR_EnableCircling", circle)
	Me.SetAnimationVariableFloat("CPR_CirclingDistMin", circleMin)
	Me.SetAnimationVariableFloat("CPR_CirclingDistMax", circleMax)
	Me.SetAnimationVariableFloat("CPR_CirclingAngleMin", angleMin)
	Me.SetAnimationVariableFloat("CPR_CirclingAngleMax", angleMax)
	Me.SetAnimationVariableBool("CPR_EnableFallback", fallback)
	If fallback
		Me.SetAnimationVariableFloat("CPR_FallbackDistMin", fallMin)
		Me.SetAnimationVariableFloat("CPR_FallbackDistMax", fallMax)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", 0.2)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", 0.5)
	EndIf
EndFunction

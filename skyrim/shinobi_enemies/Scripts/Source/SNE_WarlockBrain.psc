Scriptname SNE_WarlockBrain extends ActiveMagicEffect
{Shinobi Enemies, warlocks (2026-10-15). SPID gives this ability to WarlockFaction and NecromancerFaction.
Kinds: necromancer (class CombatMageNecro / NecromancerFaction), conjurer (CombatMageConjurer), elementals by their
spells (fire, frost, storm). Tier by level (1 < 10, 2 < 25, 3 < 40, 4).
Lore: they hear you -> prepare (Flesh by tier + their element's cloak); melee hits break their casts; necromancers
raise the nearest fresh corpse, and a badly hurt necromancer may lose its binding (its thrall turns on it).
Naruto (no Uchiha), fitted to the lore:
- Necromancer (tier 3+): phylactery / Orochimaru's immortality: a black soul gem glows in its lair; while it is
  there, the necromancer rises from it once after death (SNE_WarlockQuest). Take it first.
- Conjurer (tier 2+): Reverse Summoning: cornered, it swaps places with its summon.
- Storm mage (tier 2+): Lightning Release Armour (Raikage): cornered, +30 speed, +60 armor, lightning cloak, 10 s.
- Frost mage (tier 2+): Haku's ice mirrors: cornered, two ice-shimmer blinks, an Ice Spike after each.
- Fire mage (tier 2+): Ash Pile Burning (Asuma): 1.5 s charge, then two Fireballs; a hit during the charge stops it.
Arrogance (user, 2026-10-15): powerful magic, powerful egos. Each time an allied warlock hits this one, its
arrogance rises; the chance it snaps is 6% per point of arrogance plus 2% per tier (max 45%). Snapping: it shouts
"How dare you!" (or similar, real vanilla lines), attacks the warlock that hit it for 10 s, then turns back on the
player (who stays its enemy the whole time). Below the snap it just warns ("Hey, watch it!").
Off: console "set SNE_WarlockTactics to 0". Needs SKSE.}

CombatStyle Property StyleSummoner Auto
CombatStyle Property StyleElemental Auto
CombatStyle Property StyleArmour Auto
SNE_WarlockQuest Property WQ Auto
GlobalVariable Property TacticsOn Auto
Actor Property PlayerRef Auto
Static Property XMarkerBase Auto
Spell Property LightningArmour Auto
Faction Property RevivedFaction Auto
Class Property ClassNecro Auto
Class Property ClassConjurer Auto
Faction Property NecromancerFaction Auto
Keyword Property KwUndead Auto
Keyword Property KwDaedra Auto
Spell Property SpellRaiseZombie Auto
Spell Property SpellRevenant Auto
Spell Property SpellDreadZombie Auto
Spell Property SpellFireball Auto
Spell Property SpellIceSpike Auto
Spell Property SpellFlameCloak Auto
Spell Property SpellFrostCloak Auto
Spell Property SpellLightningCloak Auto
Spell Property SpellOakflesh Auto
Spell Property SpellStoneflesh Auto
Spell Property SpellIronflesh Auto
Spell Property SpellEbonyflesh Auto
SoulGem Property Phylactery Auto
EffectShader Property FrostFX Auto
EffectShader Property SummonFX Auto
Faction Property WarlockFaction Auto
Topic[] Property WarlockWarn Auto
Topic[] Property WarlockSnap Auto

Float Property CornerDistance = 260.0 AutoReadOnly
Float Property GrudgeSeconds = 10.0 AutoReadOnly

Int K_NECRO = 1
Int K_CONJURER = 2
Int K_FIRE = 3
Int K_FROST = 4
Int K_STORM = 5

Actor Me
Int Kind
CombatStyle OriginalStyle
ObjectReference Phyl
Bool Done
Bool Busy
Bool BusyHit
Bool Prepared
Bool BindingBroken
Float NextAbility
Float NextRaise
Float ArmourUntil
Int Arrogance
Actor GrudgeTarget
Float GrudgeUntil
Float NextWarn

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	Init()
	ApplyStyle()
	Debug.Trace("SNE warlock: start " + Me + " " + Me.GetDisplayName() + " kind " + KindName() + " tier " + Tier() + " (level " + Me.GetLevel() + ")" + PhylNote())
	If Me.IsInCombat()
		RegisterForSingleUpdate(1.0)
	EndIf
EndEvent

String Function PhylNote()
	If Phyl
		Return ", phylactery " + Phyl
	EndIf
	Return ""
EndFunction

Function Init()
	If Kind != 0 || !Me
		Return
	EndIf
	ActorBase b = Me.GetLeveledActorBase()
	If b
		OriginalStyle = b.GetCombatStyle()
	EndIf
	Class cls = None
	If b
		cls = b.GetClass()
	EndIf
	If cls == ClassNecro || Me.IsInFaction(NecromancerFaction)
		Kind = K_NECRO
	ElseIf cls == ClassConjurer
		Kind = K_CONJURER
	Else
		Kind = ElementFromSpells(b)
	EndIf
	; lore + Orochimaru: a strong necromancer keeps a phylactery in its lair
	If Kind == K_NECRO && Tier() >= 3 && !Me.IsInFaction(RevivedFaction) && Me.IsHostileToActor(PlayerRef) && !Phyl
		Cell c = Me.GetParentCell()
		If c && c.IsInterior()
			Phyl = Me.PlaceAtMe(Phylactery)
		EndIf
	EndIf
EndFunction

Int Function ElementFromSpells(ActorBase b)
	Int e = ElementOf(Me.GetEquippedSpell(1))
	If e == 0
		e = ElementOf(Me.GetEquippedSpell(0))
	EndIf
	If e == 0 && b
		Int i = 0
		Int n = b.GetSpellCount()
		While i < n && e == 0
			e = ElementOf(b.GetNthSpell(i))
			i += 1
		EndWhile
	EndIf
	If e == 0
		e = K_FIRE
	EndIf
	Return e
EndFunction

Int Function ElementOf(Spell s)
	If !s
		Return 0
	EndIf
	Int i = 0
	While i < s.GetNumEffects()
		MagicEffect m = s.GetNthEffectMagicEffect(i)
		If m && m.GetAssociatedSkill() == "Destruction"
			String r = m.GetResistance()
			If r == "FireResist"
				Return K_FIRE
			ElseIf r == "FrostResist"
				Return K_FROST
			ElseIf r == "ElectricResist"
				Return K_STORM
			EndIf
		EndIf
		i += 1
	EndWhile
	Return 0
EndFunction

String Function KindName()
	If Kind == K_NECRO
		Return "necromancer"
	ElseIf Kind == K_CONJURER
		Return "conjurer"
	ElseIf Kind == K_FROST
		Return "frost mage"
	ElseIf Kind == K_STORM
		Return "storm mage"
	EndIf
	Return "fire mage"
EndFunction

Int Function Tier()
	Int l = Me.GetLevel()
	If l < 10
		Return 1
	ElseIf l < 25
		Return 2
	ElseIf l < 40
		Return 3
	EndIf
	Return 4
EndFunction

Float Function Cooldown(Float base)    ; higher tiers act more often
	Int t = Tier()
	If t == 1
		Return base * 2.0
	ElseIf t == 2
		Return base * 1.4
	ElseIf t == 4
		Return base * 0.75
	EndIf
	Return base
EndFunction

Bool Function Active()
	Return TacticsOn.GetValue() >= 0.5 && !Me.IsPlayerTeammate() && Me.IsHostileToActor(PlayerRef)
EndFunction

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Done = True
EndEvent

Event OnDying(Actor akKiller)
	Done = True
	If Kind == K_NECRO && Phyl
		WQ.NecromancerFell(Me, Phyl)
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
	If aeCombatState == 2 || aeCombatState == 1
		Prepare()
	EndIf
	If aeCombatState == 1
		ApplyStyle()
		PushCPR()
		RegisterForSingleUpdate(1.0)
	ElseIf aeCombatState == 0 && !Me.IsDead()
		Prepared = False
		UnregisterForUpdate()
	EndIf
EndEvent

; lore: battle-mages armour themselves before the fight
Function Prepare()
	If Prepared || !Active()
		Return
	EndIf
	Prepared = True
	Int t = Tier()
	Spell flesh = SpellOakflesh
	If t == 2
		flesh = SpellStoneflesh
	ElseIf t == 3
		flesh = SpellIronflesh
	ElseIf t >= 4
		flesh = SpellEbonyflesh
	EndIf
	flesh.Cast(Me, Me)
	If Kind == K_FIRE
		SpellFlameCloak.Cast(Me, Me)
	ElseIf Kind == K_FROST
		SpellFrostCloak.Cast(Me, Me)
	ElseIf Kind == K_STORM
		SpellLightningCloak.Cast(Me, Me)
	EndIf
	Debug.Trace("SNE warlock: " + KindName() + " " + Me + " prepares (" + flesh + ")")
EndFunction

Event OnUpdate()
	If Done || !Me || Me.IsDead() || !Me.IsInCombat()
		Return
	EndIf
	GrudgeCheck()
	If Active() && !Busy && !GrudgeTarget
		Float t = Now()
		If NextAbility > t + 60.0
			NextAbility = 0.0
		EndIf
		If NextRaise > t + 60.0
			NextRaise = 0.0
		EndIf
		If ArmourUntil > t + 20.0
			ArmourUntil = 0.0
		EndIf
		Float dist = Me.GetDistance(PlayerRef)
		If Kind == K_NECRO
			If t >= NextRaise
				RaiseDead(t)
			EndIf
			If !BindingBroken && Me.GetActorValuePercentage("Health") < 0.25
				BindingBreaks()
			EndIf
		ElseIf t >= NextAbility && Tier() >= 2
			If Kind == K_CONJURER && dist < CornerDistance
				ReverseSummon(t)
			ElseIf Kind == K_STORM && dist < CornerDistance + 60.0
				LightningReleaseArmour(t)
			ElseIf Kind == K_FROST && dist < CornerDistance
				IceMirrors(t)
			ElseIf Kind == K_FIRE && dist > 300.0 && dist < 1500.0 && Me.HasLOS(PlayerRef)
				AshPileBurning(t)
			EndIf
		EndIf
	EndIf
	ApplyStyle()
	PushCPR()
	If !Done && !Me.IsDead()
		RegisterForSingleUpdate(1.0)
	EndIf
EndEvent

; melee is still the counter: any melee hit breaks the cast; a hit during a charged jutsu spoils it
Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If Busy
		BusyHit = True
	EndIf
	If Done || !Me
		Return
	EndIf
	Actor ally = akAggressor as Actor
	If ally && ally != Me && ally != PlayerRef && !GrudgeTarget && Active() && IsFellowWarlock(ally)
		Insulted(ally)
	EndIf
	If akProjectile
		Return
	EndIf
	Weapon w = akSource as Weapon
	If w && w.GetWeaponType() != 7 && w.GetWeaponType() != 9
		Me.InterruptCast()
	EndIf
EndEvent

; ---------- arrogance ----------
Bool Function IsFellowWarlock(Actor a)
	Return !a.IsDead() && !a.IsPlayerTeammate() && (a.IsInFaction(WarlockFaction) || a.IsInFaction(NecromancerFaction))
EndFunction

Function Insulted(Actor ally)
	Arrogance += 1
	Float chance = 0.06 * Arrogance + 0.02 * Tier()
	If chance > 0.45
		chance = 0.45
	EndIf
	Float t = Now()
	If Utility.RandomFloat() < chance
		GrudgeTarget = ally
		GrudgeUntil = t + GrudgeSeconds
		Arrogance = 0
		SayOne(WarlockSnap)
		Me.StartCombat(ally)
		Debug.Trace("SNE warlock: " + KindName() + " " + Me + " SNAPS at " + ally + " for hitting it (" + ((chance * 100.0) as Int) + "% roll) - " + GrudgeSeconds + " s")
	Else
		If NextWarn > t + 20.0
			NextWarn = 0.0
		EndIf
		If t >= NextWarn
			NextWarn = t + 8.0
			SayOne(WarlockWarn)
		EndIf
		Debug.Trace("SNE warlock: " + KindName() + " " + Me + " hit by ally " + ally + ", arrogance " + Arrogance + " (snap chance was " + ((chance * 100.0) as Int) + "%)")
	EndIf
EndFunction

Function GrudgeCheck()
	If !GrudgeTarget
		Return
	EndIf
	Float t = Now()
	If GrudgeUntil > t + GrudgeSeconds + 1.0
		GrudgeUntil = 0.0
	EndIf
	If t >= GrudgeUntil || GrudgeTarget.IsDead()
		Debug.Trace("SNE warlock: " + KindName() + " " + Me + " is done with " + GrudgeTarget + ", back to you")
		GrudgeTarget = None
		Me.StopCombat()
		Me.StartCombat(PlayerRef)
	EndIf
EndFunction

Function SayOne(Topic[] lines)
	If lines && lines.Length > 0
		Me.Say(lines[Utility.RandomInt(0, lines.Length - 1)])
	EndIf
EndFunction

; ---------- necromancers ----------
Function RaiseDead(Float t)
	Cell c = Me.GetParentCell()
	If !c
		Return
	EndIf
	Actor corpse = None
	Float best = 1500.0
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a.IsDead() && !a.IsDisabled() && a != PlayerRef && !a.HasKeyword(KwUndead) && !a.HasKeyword(KwDaedra)
			Float d = Me.GetDistance(a)
			If d < best
				best = d
				corpse = a
			EndIf
		EndIf
		i += 1
	EndWhile
	If !corpse
		Return
	EndIf
	NextRaise = t + Cooldown(12.0)
	Spell raise = SpellRaiseZombie
	If Tier() >= 4
		raise = SpellDreadZombie
	ElseIf Tier() >= 3
		raise = SpellRevenant
	EndIf
	raise.Cast(Me, corpse)
	Debug.Trace("SNE warlock: necromancer " + Me + " raises " + corpse + " with " + raise)
EndFunction

; lore: a bad binding breaks and the undead turns on its master
Function BindingBreaks()
	BindingBroken = True
	If Utility.RandomFloat() >= 0.35
		Return
	EndIf
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
		If a && !a.IsDead() && a.IsCommandedActor() && a.HasKeyword(KwUndead) && Me.GetDistance(a) < 1500.0
			a.StopCombat()
			a.StartCombat(Me)
			Debug.Trace("SNE warlock: necromancer " + Me + " loses its binding: " + a + " turns on it")
			Return
		EndIf
		i += 1
	EndWhile
EndFunction

; ---------- conjurer: Reverse Summoning ----------
Function ReverseSummon(Float t)
	Cell c = Me.GetParentCell()
	If !c
		Return
	EndIf
	Actor summon = None
	Float best = 1500.0
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a != Me && !a.IsDead() && a.IsCommandedActor() && a.HasKeyword(KwDaedra) && a.IsHostileToActor(PlayerRef)
			Float d = Me.GetDistance(a)
			If d < best && d > 300.0
				best = d
				summon = a
			EndIf
		EndIf
		i += 1
	EndWhile
	If !summon
		Return
	EndIf
	NextAbility = t + Cooldown(20.0)
	ObjectReference mine = Me.PlaceAtMe(XMarkerBase)
	ObjectReference theirs = summon.PlaceAtMe(XMarkerBase)
	SummonFX.Play(Me, 1.0)
	SummonFX.Play(summon, 1.0)
	Me.MoveTo(theirs)
	summon.MoveTo(mine)
	mine.Delete()
	theirs.Delete()
	Debug.Trace("SNE warlock: conjurer " + Me + " REVERSE SUMMONING: swapped with " + summon + ", now " + (Me.GetDistance(PlayerRef) as Int) + " from you")
EndFunction

; ---------- storm mage: Lightning Release Armour ----------
Function LightningReleaseArmour(Float t)
	NextAbility = t + Cooldown(25.0)
	ArmourUntil = t + 10.0
	LightningArmour.Cast(Me, Me)
	SpellLightningCloak.Cast(Me, Me)
	Debug.Trace("SNE warlock: storm mage " + Me + " LIGHTNING RELEASE ARMOUR (10 s)")
EndFunction

; ---------- frost mage: ice mirrors ----------
Function IceMirrors(Float t)
	NextAbility = t + Cooldown(18.0)
	Int jumps = 0
	Int i = 0
	While i < 2 && !Me.IsDead()
		ObjectReference spot = FindPerch()
		If spot
			FrostFX.Play(Me, 0.6)
			Me.SetAlpha(0.2, True)
			Utility.Wait(0.25)
			Me.MoveTo(spot)
			Me.SetAlpha(1.0, True)
			FrostFX.Play(Me, 0.6)
			SpellIceSpike.Cast(Me, PlayerRef)
			jumps += 1
			Utility.Wait(0.5)
		EndIf
		i += 1
	EndWhile
	Debug.Trace("SNE warlock: frost mage " + Me + " ICE MIRRORS: " + jumps + " blinks")
EndFunction

; ---------- fire mage: Ash Pile Burning ----------
Function AshPileBurning(Float t)
	NextAbility = t + Cooldown(25.0)
	Busy = True
	BusyHit = False
	Debug.Trace("SNE warlock: fire mage " + Me + " charges ASH PILE BURNING (1.5 s, hit it to stop it)")
	Utility.Wait(1.5)
	If BusyHit || Me.IsDead()
		Debug.Trace("SNE warlock: fire mage " + Me + " Ash Pile Burning STOPPED by a hit")
	Else
		SpellFireball.Cast(Me, PlayerRef)
		Utility.Wait(0.4)
		SpellFireball.Cast(Me, PlayerRef)
		Debug.Trace("SNE warlock: fire mage " + Me + " Ash Pile Burning released")
	EndIf
	Busy = False
EndFunction

; furniture/idle marker in the cell: further from the player, a short jump away, higher is better
ObjectReference Function FindPerch()
	Cell c = Me.GetParentCell()
	If !c
		Return None
	EndIf
	Float myDist = Me.GetDistance(PlayerRef)
	Float pz = PlayerRef.GetPositionZ()
	ObjectReference best = None
	Float bestScore = -100000.0
	Int t = 0
	While t < 2
		Int ft = 40
		If t == 1
			ft = 47
		EndIf
		Int n = c.GetNumRefs(ft)
		If n > 80
			n = 80
		EndIf
		Int i = 0
		While i < n
			ObjectReference r = c.GetNthRef(i, ft)
			If r && !r.IsDisabled()
				Float dA = Me.GetDistance(r)
				Float dP = PlayerRef.GetDistance(r)
				If dA > 300.0 && dA < 1200.0 && dP > 500.0 && dP > myDist + 150.0
					Float score = (r.GetPositionZ() - pz) * 1.5 + dP * 0.5 - dA * 0.3
					If score > bestScore
						bestScore = score
						best = r
					EndIf
				EndIf
			EndIf
			i += 1
		EndWhile
		t += 1
	EndWhile
	Return best
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
		If Kind == K_NECRO || Kind == K_CONJURER
			want = StyleSummoner
		ElseIf Kind == K_STORM && Now() < ArmourUntil
			want = StyleArmour
		Else
			want = StyleElemental
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
	If Kind == K_STORM && Now() < ArmourUntil
		SetCPR(False, 0.0, True, 90.0, 300.0, 60.0, 120.0, False)    ; armoured: in your face
	ElseIf Kind == K_NECRO || Kind == K_CONJURER
		SetCPR(True, 0.95, True, 700.0, 1500.0, 20.0, 45.0, True)    ; behind the summons
	Else
		SetCPR(True, 0.8, True, 400.0, 1300.0, 30.0, 60.0, True)
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
		Me.SetAnimationVariableFloat("CPR_FallbackDistMin", 500.0)
		Me.SetAnimationVariableFloat("CPR_FallbackDistMax", 1100.0)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", 0.3)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", 0.7)
	EndIf
EndFunction

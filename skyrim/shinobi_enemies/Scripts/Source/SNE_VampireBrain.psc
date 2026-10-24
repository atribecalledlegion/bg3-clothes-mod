Scriptname SNE_VampireBrain extends ActiveMagicEffect
{Shinobi Enemies, vampire tactics (2026-10-15). SPID gives this ability to VampireFaction and VampireThrallFaction.
Roles: thrall (enslaved fodder), fledgling (lesser vampire: hungry, reckless, flanks), elder (csVampireBoss or level
35+: selfish). Unique to vampires:
- Selfish elders: while their lessers still stand, an elder stays back (drain, necromancy) and only engages when
  they are dead or wounded, when you corner it, or when you turn your back on it to fight one of them (ambush,
  with Vampiric Invisibility).
- Desperate feeding: a vampire below half health runs to a thrall (or a bleeding-out non-vampire) and tries to
  feed (Dawnguard standing feed animation). It works only half the time, and any hit during the feed spoils it:
  a last gamble, not an exit plan (user, 2026-10-15).
- Prepared feeding (elders, once): an elder that hears a fight but is not being fought runs to a thrall (or a
  fledgling) and feeds; the benefit (Blood Empowered: +100 health, +75 armor, 300 s, full heal) lands only after a
  3 s feeding window, so you can stop it by hitting the elder.
- Necromancy: elders raise the dead around them (Raise Zombie / Revenant / Dread Zombie by level).
- Lairs: the first hostile vampire to load in an interior brings 1-3 extra thralls/fledglings (once per cell).
- Serana's thrall (user, 2026-10-16): a low-level fledgling (level 20 or less) that sees Serana fighting at your side
  has a 10% chance (rolled once) to fall under her spell: it says "My Lady." (or "Whatever you say!" when its voice
  type never recorded that line), leaves its kind and fights them for her. When the fight is over it turns to dust.
Followers (Serana) and non-hostile vampires are left alone. Off switch: console "set SNE_VampireTactics to 0".
Needs SKSE (Get/SetCombatStyle, Cell.GetNthRef, PlayIdleWithTarget).}

CombatStyle Property StyleFledgling Auto
CombatStyle Property StyleElderWait Auto
CombatStyle Property StyleElderStrike Auto
CombatStyle Property StyleThrall Auto
GlobalVariable Property TacticsOn Auto
FormList Property ReinforcedCells Auto
Actor Property PlayerRef Auto
Static Property XMarkerBase Auto
CombatStyle Property VanillaVampireBoss Auto
Faction Property VampireThrallFaction Auto
Faction Property VampireFaction Auto
Keyword Property VampireKeyword Auto
Spell Property SpellRaiseZombie Auto
Spell Property SpellRevenant Auto
Spell Property SpellDreadZombie Auto
Spell Property SpellInvisibility Auto
Spell Property SpellVampireDrain Auto
Spell Property BloodEmpowered Auto
ActorBase Property ThrallMelee Auto
ActorBase Property ThrallMissile Auto
ActorBase Property LesserVampire Auto

Float Property UpdateInterval = 1.0 AutoReadOnly
Int Property ElderLevel = 35 AutoReadOnly
Float Property FeedBelow = 0.5 AutoReadOnly          ; health fraction that sends a vampire to feed
Float Property FeedCooldown = 30.0 AutoReadOnly
Float Property RaiseCooldown = 15.0 AutoReadOnly
Float Property StrikeSeconds = 8.0 AutoReadOnly      ; an elder's ambush window
Float Property StrikeCooldown = 12.0 AutoReadOnly
Float Property ConfrontDistance = 300.0 AutoReadOnly ; closer than this, the elder has to fight
Float Property Range = 2000.0 AutoReadOnly
Float Property DesperateFeedChance = 0.5 AutoReadOnly
Float Property PrepareWindow = 3.0 AutoReadOnly     ; seconds of feeding before Blood Empowered lands
Float Property PrepareDistance = 1000.0 AutoReadOnly ; the player must be further than this ("not engaged yet")
Float Property TurncoatChance = 0.0 AutoReadOnly   ; was 0.1; turned off 2026-10-17 at the user's request (companions fought the thrall)
Int Property TurncoatMaxLevel = 20 AutoReadOnly
Faction Property PlayerFaction Auto
FormList Property MyLadyVoices Auto
Topic[] Property TurnMyLady Auto
Topic[] Property TurnObey Auto
EffectShader Property DustFX Auto
Activator Property AshPile Auto

Int ROLE_THRALL = 1
Int ROLE_FLEDGLING = 2
Int ROLE_ELDER = 3

Actor Me
Int Role
CombatStyle OriginalStyle
Bool Done
Bool Busy             ; feeding or casting a scripted action
Bool Striking
Float StrikeUntil
Float NextStrikeTime
Float NextFeedTime
Float NextRaiseTime
Idle FeedIdle         ; Dawnguard IdleVampireStandingFeedFront_Loose (looked up at runtime)
Bool FeedHit          ; set by OnHit while feeding: the feed is spoiled
Bool Prepared         ; an elder feeds to prepare only once
Bool TurnRolled
Bool Turned           ; Serana's thrall now
Int QuietTicks

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	Init()
	ApplyStyle()
	If Me.IsPlayerTeammate()
		Debug.Trace("SNE vampire: " + Me + " is your follower, left alone")
	EndIf
	Debug.Trace("SNE vampire: start " + Me + " role " + RoleName() + " (level " + Me.GetLevel() + "), style " + OriginalStyle + " -> " + Me.GetLeveledActorBase().GetCombatStyle())
	Reinforce()
	If Me.IsInCombat()
		RegisterForSingleUpdate(UpdateInterval)
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
	If Me.IsInFaction(VampireThrallFaction) && !Me.HasKeyword(VampireKeyword)
		Role = ROLE_THRALL
	ElseIf OriginalStyle == VanillaVampireBoss || Me.GetLevel() >= ElderLevel
		Role = ROLE_ELDER
	Else
		Role = ROLE_FLEDGLING
	EndIf
	FeedIdle = Game.GetFormFromFile(0x00E6A8, "Dawnguard.esm") as Idle
EndFunction

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Done = True
EndEvent

Event OnDying(Actor akKiller)
	Done = True
EndEvent

Event OnLoad()
	If Done
		Return
	EndIf
	ApplyStyle()
EndEvent

Event OnCombatStateChanged(Actor akTarget, Int aeCombatState)
	If Done
		Return
	EndIf
	If !Me
		Me = GetTargetActor()
	EndIf
	Init()
	If aeCombatState == 2 && akTarget == PlayerRef
		TryPrepareFeed("heard the fight")
	EndIf
	If Turned
		RegisterForSingleUpdate(1.0)
		Return
	EndIf
	If aeCombatState == 1 && !TurnRolled && Active()
		TurnRolled = True
		If TryTurncoat()
			Return
		EndIf
	EndIf
	If aeCombatState == 1
		ApplyStyle()
		PushCPR()
		If Me.GetDistance(PlayerRef) > PrepareDistance
			TryPrepareFeed("fight started far away")
		EndIf
		Debug.Trace("SNE vampire: combat " + Me + " role " + RoleName() + " target " + akTarget + " style " + Me.GetLeveledActorBase().GetCombatStyle())
		RegisterForSingleUpdate(UpdateInterval)
	ElseIf aeCombatState == 0
		If !Me.IsDead()
			UnregisterForUpdate()
		EndIf
		Striking = False
	EndIf
EndEvent

Event OnUpdate()
	If Done || !Me || Me.IsDead()
		Return
	EndIf
	If Turned
		TurncoatTick()
		Return
	EndIf
	If !Me.IsInCombat()
		Return
	EndIf
	If Active() && !Busy
		If Role == ROLE_ELDER
			If Me.GetDistance(PlayerRef) > PrepareDistance
				TryPrepareFeed("not engaged yet")
			EndIf
			ElderThink()
			TryRaiseDead()
		EndIf
		Float hp = Me.GetActorValuePercentage("Health")
		If Role != ROLE_THRALL && hp < FeedBelow && hp > 0.1
			TryFeed()
		EndIf
	EndIf
	ApplyStyle()
	PushCPR()
	If !Done && !Me.IsDead()
		RegisterForSingleUpdate(UpdateInterval)
	EndIf
EndEvent

; hunger check right when it is hurt (the 1 s tick was too slow: a fledgling was already dying when it decided)
Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If Busy
		FeedHit = True    ; hit while feeding: the feed is spoiled
		Return
	EndIf
	If Done || Role == ROLE_THRALL || !Me || !Active()
		Return
	EndIf
	Float hp = Me.GetActorValuePercentage("Health")
	If hp < FeedBelow && hp > 0.1
		TryFeed()
	EndIf
EndEvent

; ---------- Serana's thrall ----------
Bool Function TryTurncoat()
	If Role != ROLE_FLEDGLING || Me.GetLevel() > TurncoatMaxLevel
		Return False
	EndIf
	Actor serana = Game.GetFormFromFile(0x002B74, "Dawnguard.esm") as Actor
	If !serana || serana.IsDead() || !serana.IsPlayerTeammate() || !serana.HasKeyword(VampireKeyword) || Me.GetDistance(serana) > 3000.0
		Return False
	EndIf
	If Utility.RandomFloat() >= TurncoatChance
		Debug.Trace("SNE vampire: " + Me + " resists Serana's pull")
		Return False
	EndIf
	Turned = True
	Me.StopCombat()
	Me.RemoveFromAllFactions()
	Me.AddToFaction(PlayerFaction)
	Me.SetPlayerTeammate(True, False)
	Topic line
	If MyLadyVoices.HasForm(Me.GetVoiceType())
		line = TurnMyLady[0]
	Else
		line = TurnObey[0]
	EndIf
	Me.Say(line)
	Debug.Notification(Me.GetDisplayName() + " falls under Serana's spell")
	Debug.Trace("SNE vampire: " + Me + " TURNS for Serana (voice " + Me.GetVoiceType() + ", says " + line + ")")
	CallOffFriends()
	Utility.Wait(1.5)
	CallOffFriends()
	Actor foe = NearestVampireFoe()
	If foe
		Me.StartCombat(foe)
	EndIf
	RegisterForSingleUpdate(1.0)
	Return True
EndFunction

; Your companions (Ashe) were already fighting it before it turned, and the game keeps that target: they would
; keep attacking their new ally, and Serana would defend it against them. So anyone on your side still aimed at it
; is told to stand down, right after the turn and every second while it serves.
Function CallOffFriends()
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
		If a && a != Me && !a.IsDead() && a.IsPlayerTeammate() && a.GetCombatTarget() == Me
			a.StopCombat()
			Debug.Trace("SNE vampire: " + a.GetDisplayName() + " told to leave Serana's thrall " + Me + " alone")
		EndIf
		i += 1
	EndWhile
EndFunction

Actor Function NearestVampireFoe()
	Cell c = Me.GetParentCell()
	If !c
		Return None
	EndIf
	Actor best = None
	Float bestD = 2500.0
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a != Me && !a.IsDead() && !a.IsDisabled() && !a.IsPlayerTeammate() && (a.IsInFaction(VampireFaction) || a.IsInFaction(VampireThrallFaction)) && Me.GetDistance(a) < bestD
			bestD = Me.GetDistance(a)
			best = a
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction

; it fights while you fight; three quiet seconds and Serana's hold on it ends: it turns to dust
Function TurncoatTick()
	If PlayerRef.IsInCombat() || Me.IsInCombat()
		QuietTicks = 0
		CallOffFriends()
		If !Me.IsInCombat()
			Actor foe = NearestVampireFoe()
			If foe
				Me.StartCombat(foe)
			EndIf
		EndIf
		RegisterForSingleUpdate(1.0)
		Return
	EndIf
	QuietTicks += 1
	If QuietTicks < 3
		RegisterForSingleUpdate(1.0)
		Return
	EndIf
	Debug.Trace("SNE vampire: Serana's thrall " + Me + " turns to dust")
	Done = True
	DustFX.Play(Me, 3.0)
	Utility.Wait(1.0)
	Me.Kill()
	Me.SetCriticalStage(Me.CritStage_DisintegrateStart)
	Me.AttachAshPile(AshPile)
	Utility.Wait(1.5)
	Me.SetAlpha(0.0, True)
	Me.SetCriticalStage(Me.CritStage_DisintegrateEnd)
EndFunction

Bool Function Active()
	Return TacticsOn.GetValue() >= 0.5 && !Me.IsPlayerTeammate() && Me.IsHostileToActor(PlayerRef)
EndFunction

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

; ---------- selfish elders ----------
Bool Function ElderWaiting()
	Return Role == ROLE_ELDER && !Striking && Active() && LessersStanding() > 0 && Me.GetDistance(PlayerRef) > ConfrontDistance && Me.GetActorValuePercentage("Health") > 0.6
EndFunction

Function ElderThink()
	Float t = Now()
	If StrikeUntil > t + StrikeSeconds + 1.0 || NextStrikeTime > t + StrikeCooldown + StrikeSeconds + 1.0
		StrikeUntil = 0.0    ; stale real-time values from an earlier launch
		NextStrikeTime = 0.0
	EndIf
	If Striking && t > StrikeUntil
		Striking = False
		Debug.Trace("SNE vampire: elder " + Me + " pulls back again")
	EndIf
	If Striking || !ElderWaiting() || t < NextStrikeTime
		Return
	EndIf
	; you are busy with one of its lessers and have your back to it: strike
	Float behind = PlayerRef.GetHeadingAngle(Me)
	If behind < 0.0
		behind = -behind
	EndIf
	If behind > 100.0 && LesserEngagingPlayer() && Me.GetDistance(PlayerRef) < 1800.0
		Striking = True
		StrikeUntil = t + StrikeSeconds
		NextStrikeTime = t + StrikeSeconds + StrikeCooldown
		SpellInvisibility.Cast(Me, Me)
		Debug.Trace("SNE vampire: elder " + Me + " strikes while your back is turned (" + (behind as Int) + " deg)")
	EndIf
EndFunction

Bool Function IsLesser(Actor a)
	If !a || a == Me || a.IsDead() || a.IsDisabled() || a.IsPlayerTeammate() || Me.GetDistance(a) > Range
		Return False
	EndIf
	If a.IsInFaction(VampireThrallFaction)
		Return True
	EndIf
	Return a.IsInFaction(VampireFaction) && a.GetLevel() < ElderLevel && a.GetLeveledActorBase().GetCombatStyle() != StyleElderWait && a.GetLeveledActorBase().GetCombatStyle() != StyleElderStrike
EndFunction

Int Function LessersStanding()    ; lessers still fighting at more than half health
	Int count = 0
	Cell c = Me.GetParentCell()
	If !c
		Return 0
	EndIf
	Int n = c.GetNumRefs(43)
	If n > 60
		n = 60
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If IsLesser(a) && a.IsInCombat() && a.GetActorValuePercentage("Health") > 0.5
			count += 1
		EndIf
		i += 1
	EndWhile
	Return count
EndFunction

Bool Function LesserEngagingPlayer()
	Cell c = Me.GetParentCell()
	If !c
		Return False
	EndIf
	Int n = c.GetNumRefs(43)
	If n > 60
		n = 60
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If IsLesser(a) && a.IsInCombat() && a.GetDistance(PlayerRef) < 250.0
			Return True
		EndIf
		i += 1
	EndWhile
	Return False
EndFunction

; ---------- feeding ----------
Function TryFeed()
	Float t = Now()
	If NextFeedTime > t + FeedCooldown + 1.0
		NextFeedTime = 0.0
	EndIf
	If t < NextFeedTime || Me.IsBleedingOut() || Me.IsDead()
		Return
	EndIf
	Actor victim = FindVictim()
	If !victim
		Return
	EndIf
	NextFeedTime = t + FeedCooldown
	Busy = True
	Float before = Me.GetActorValuePercentage("Health")
	Debug.Trace("SNE vampire: " + RoleName() + " " + Me + " at " + ((before * 100.0) as Int) + "% goes to feed on " + victim + " (" + (Me.GetDistance(victim) as Int) + " away)")
	Bool inCombat = Me.IsInCombat()
	If Me.GetDistance(victim) > 180.0
		If inCombat
			Me.StopCombat()
		EndIf
		Me.PathToReference(victim, 1.0)
	EndIf
	If !Me.IsDead() && !victim.IsDead() && Me.GetDistance(victim) < 220.0
		Bool played = False
		FeedHit = False
		If FeedIdle
			played = Me.PlayIdleWithTarget(FeedIdle, victim)
		EndIf
		Utility.Wait(2.0)
		If FeedHit || Me.IsDead()
			Debug.Trace("SNE vampire: " + Me + " desperate feed on " + victim + " SPOILED by a hit")
		ElseIf Utility.RandomFloat() >= DesperateFeedChance
			Debug.Trace("SNE vampire: " + Me + " desperate feed on " + victim + " FAILED (it broke free), animation " + played)
		Else
			If victim.IsInFaction(VampireThrallFaction)
				victim.Kill(Me)
			Else
				victim.DamageActorValue("Health", 60.0)    ; a bleeding-out follower is drained, not killed
			EndIf
			If !Me.IsInKillMove() && !Me.IsBleedingOut() && Me.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
				Me.RestoreActorValue("Health", Me.GetBaseActorValue("Health") * 0.5)
			EndIf
			Debug.Trace("SNE vampire: " + Me + " desperate feed on " + victim + " WORKED (animation " + played + "), health " + ((Me.GetActorValuePercentage("Health") * 100.0) as Int) + "%")
		EndIf
	ElseIf !Me.IsDead() && !victim.IsDead()
		SpellVampireDrain.Cast(Me, victim)    ; could not reach it: drain from range
		Debug.Trace("SNE vampire: " + Me + " could not reach " + victim + ", drained it from range")
	Else
		Debug.Trace("SNE vampire: " + Me + " feed interrupted (vampire dead " + Me.IsDead() + ", victim dead " + victim.IsDead() + ")")
	EndIf
	If inCombat && !Me.IsDead()
		Me.StartCombat(PlayerRef)
	EndIf
	Busy = False
EndFunction

; an elder with time to prepare feeds on one of its own: thrall first, else a fledgling
Function TryPrepareFeed(String reason)
	If Role != ROLE_ELDER || Prepared || Busy || Done || !Active() || Me.IsDead()
		Return
	EndIf
	Actor victim = FindTeammate()
	If !victim
		Return
	EndIf
	Prepared = True
	Busy = True
	Debug.Trace("SNE vampire: elder " + Me + " (" + reason + ") goes to feed on its own " + victim + " to prepare (" + (Me.GetDistance(victim) as Int) + " away)")
	Bool inCombat = Me.IsInCombat()
	If Me.GetDistance(victim) > 180.0
		If inCombat
			Me.StopCombat()
		EndIf
		Me.PathToReference(victim, 1.0)
	EndIf
	If !Me.IsDead() && !victim.IsDead() && Me.GetDistance(victim) < 220.0
		FeedHit = False
		Bool played = False
		If FeedIdle
			played = Me.PlayIdleWithTarget(FeedIdle, victim)
		EndIf
		Debug.Trace("SNE vampire: elder " + Me + " is feeding (animation " + played + "): " + PrepareWindow + " s to stop it")
		Utility.Wait(PrepareWindow)
		If FeedHit || Me.IsDead() || victim.IsDead()
			Debug.Trace("SNE vampire: elder " + Me + " prepared feed STOPPED (hit " + FeedHit + ")")
		Else
			victim.Kill(Me)
			If !Me.IsInKillMove() && !Me.IsBleedingOut() && Me.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
				Me.RestoreActorValue("Health", Me.GetBaseActorValue("Health"))
			EndIf
			BloodEmpowered.Cast(Me, Me)
			Debug.Trace("SNE vampire: elder " + Me + " is BLOOD EMPOWERED (fed on " + victim + ")")
		EndIf
	Else
		Debug.Trace("SNE vampire: elder " + Me + " could not reach " + victim + " to feed")
	EndIf
	If inCombat && !Me.IsDead()
		Me.StartCombat(PlayerRef)
	EndIf
	Busy = False
EndFunction

Actor Function FindTeammate()
	Cell c = Me.GetParentCell()
	If !c
		Return None
	EndIf
	Actor thrall = None
	Actor fledgling = None
	Float thrallDist = 1500.0
	Float fledgDist = 1500.0
	Int n = c.GetNumRefs(43)
	If n > 60
		n = 60
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If IsLesser(a)
			Float d = Me.GetDistance(a)
			If a.IsInFaction(VampireThrallFaction)
				If d < thrallDist
					thrallDist = d
					thrall = a
				EndIf
			ElseIf d < fledgDist
				fledgDist = d
				fledgling = a
			EndIf
		EndIf
		i += 1
	EndWhile
	If thrall
		Return thrall
	EndIf
	Return fledgling
EndFunction

Actor Function FindVictim()     ; nearest living thrall, or a bleeding-out non-vampire, within 1500
	Cell c = Me.GetParentCell()
	If !c
		Return None
	EndIf
	Actor best = None
	Float bestDist = 1500.0
	Int n = c.GetNumRefs(43)
	If n > 60
		n = 60
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a != Me && a != PlayerRef && !a.IsDead() && !a.IsDisabled() && !a.HasKeyword(VampireKeyword)
			If a.IsInFaction(VampireThrallFaction) || a.IsBleedingOut()
				Float d = Me.GetDistance(a)
				If d < bestDist
					bestDist = d
					best = a
				EndIf
			EndIf
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction

; ---------- necromancy (elders) ----------
Function TryRaiseDead()
	Float t = Now()
	If NextRaiseTime > t + RaiseCooldown + 1.0
		NextRaiseTime = 0.0
	EndIf
	If t < NextRaiseTime
		Return
	EndIf
	Cell c = Me.GetParentCell()
	If !c
		Return
	EndIf
	Actor corpse = None
	Float bestDist = 1500.0
	Int n = c.GetNumRefs(43)
	If n > 60
		n = 60
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a.IsDead() && !a.IsDisabled() && !a.HasKeyword(VampireKeyword) && a != PlayerRef
			Float d = Me.GetDistance(a)
			If d < bestDist
				bestDist = d
				corpse = a
			EndIf
		EndIf
		i += 1
	EndWhile
	If !corpse
		Return
	EndIf
	NextRaiseTime = t + RaiseCooldown
	Spell raise = SpellRaiseZombie
	If Me.GetLevel() >= 45
		raise = SpellDreadZombie
	ElseIf Me.GetLevel() >= 25
		raise = SpellRevenant
	EndIf
	raise.Cast(Me, corpse)
	Debug.Trace("SNE vampire: elder " + Me + " raises " + corpse + " with " + raise)
EndFunction

; ---------- lairs get more numbers (canon: vampires keep thralls as fodder) ----------
Function Reinforce()
	If Role == ROLE_THRALL || TacticsOn.GetValue() < 0.5 || Me.IsPlayerTeammate() || !Me.IsHostileToActor(PlayerRef)
		Return
	EndIf
	Cell c = Me.GetParentCell()
	If !c || !c.IsInterior() || ReinforcedCells.HasForm(c)
		Return
	EndIf
	ReinforcedCells.AddForm(c)
	Int count = 1 + Utility.RandomInt(0, 1)
	If Role == ROLE_ELDER
		count += 1
	EndIf
	Int i = 0
	While i < count
		ActorBase base = ThrallMelee
		Int pick = Utility.RandomInt(0, 9)
		If pick < 3
			base = ThrallMissile
		ElseIf pick < 5
			base = LesserVampire
		EndIf
		Me.PlaceAtMe(base)
		i += 1
	EndWhile
	Debug.Trace("SNE vampire: lair " + c + " reinforced with " + count + " extra (thralls/fledglings) by " + Me)
EndFunction

; ---------- style and pathing ----------
String Function RoleName()
	If Role == ROLE_THRALL
		Return "thrall"
	ElseIf Role == ROLE_ELDER
		Return "elder"
	EndIf
	Return "fledgling"
EndFunction

CombatStyle Function RoleStyle()
	If Role == ROLE_THRALL
		Return StyleThrall
	ElseIf Role == ROLE_ELDER
		If ElderWaiting()
			Return StyleElderWait
		EndIf
		Return StyleElderStrike
	EndIf
	Return StyleFledgling
EndFunction

Function ApplyStyle()
	If !Me
		Return
	EndIf
	ActorBase b = Me.GetLeveledActorBase()
	If !b
		Return
	EndIf
	If Me.IsPlayerTeammate()
		Return    ; followers (Serana) are never touched: her Taekwondo toggle manages her combat style
	EndIf
	CombatStyle want = RoleStyle()
	If TacticsOn.GetValue() < 0.5
		want = OriginalStyle
	EndIf
	If want && b.GetCombatStyle() != want
		b.SetCombatStyle(want)
	EndIf
EndFunction

Function PushCPR()
	If !Active() || Busy
		Return
	EndIf
	If Role == ROLE_THRALL
		SetCPR(False, 0.0, 0.8, False, 0.0, 0.0, 0.0, 0.0, False)    ; straight at you
	ElseIf Role == ROLE_ELDER && ElderWaiting()
		SetCPR(True, 1.0, 1.0, True, 900.0, 1600.0, 20.0, 45.0, True)    ; hangs back
	ElseIf Role == ROLE_ELDER
		SetCPR(True, 0.1, 0.85, True, 100.0, 400.0, 90.0, 150.0, False)  ; circles in behind you
	Else
		SetCPR(True, 0.2, 0.8, True, 120.0, 600.0, 60.0, 120.0, False)   ; fledgling: flanks
	EndIf
EndFunction

Function SetCPR(Bool backoff, Float backoffChance, Float backoffDistMult, Bool circle, Float circleMin, Float circleMax, Float angleMin, Float angleMax, Bool fallback)
	Me.SetAnimationVariableBool("CPR_EnableBackoff", backoff)
	Me.SetAnimationVariableFloat("CPR_BackoffChance", backoffChance)
	Me.SetAnimationVariableFloat("CPR_BackoffMinDistMult", backoffDistMult)
	Me.SetAnimationVariableBool("CPR_EnableCircling", circle)
	Me.SetAnimationVariableFloat("CPR_CirclingDistMin", circleMin)
	Me.SetAnimationVariableFloat("CPR_CirclingDistMax", circleMax)
	Me.SetAnimationVariableFloat("CPR_CirclingAngleMin", angleMin)
	Me.SetAnimationVariableFloat("CPR_CirclingAngleMax", angleMax)
	Me.SetAnimationVariableBool("CPR_EnableFallback", fallback)
	If fallback
		Me.SetAnimationVariableFloat("CPR_FallbackDistMin", 800.0)
		Me.SetAnimationVariableFloat("CPR_FallbackDistMax", 1500.0)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", 0.3)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", 0.6)
	EndIf
EndFunction

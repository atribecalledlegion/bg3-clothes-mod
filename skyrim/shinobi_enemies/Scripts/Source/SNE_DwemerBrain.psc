Scriptname SNE_DwemerBrain extends ActiveMagicEffect
{Shinobi Enemies, Dwemer automatons (2026-10-16). SPID gives this ability to DwarvenAutomatonFaction.
Lore (UESP): animunculi - soul-gem and steam machines that still guard the ruins on their makers' last orders.
- MASTER LINK: every 2 s each automaton counts the automatons fighting within 2000 (a living Centurion counts as the
  controller, Kankuro/Sasori-style). More of them = smarter (linked combat styles: flanking, group offence) and
  tougher: Link tier 1-4, each incoming weapon damage x0.9 (SNE_DwemerPerk), capped at tier 4 (x0.66) - never
  invulnerable. Thin their numbers and the link falls apart.
- Plating: slashing weapons (swords, daggers, axes, greatswords, battleaxes) x0.7; impact (maces, warhammers) x1.25.
  Magic resistance 25 -> 40, but shock resistance -150: shock is their kryptonite (net about x1.5).
- GLITCH: spiders, spheres and any automaton at or below your level can glitch from one big shock hit (>= 10% of
  its health or 40+ damage): 60%, frozen 1.5 s, 6 s cooldown. OVERLOAD (all, Centurions too): shock adding up to 30%
  of its health within 4 s freezes it 2 s (12 s cooldown).
- Spiders: half shock troops, half support. Many spiders = they swarm (flanking, tight circling). Few (2 or less), or
  far weaker than you, and a damaged ally nearby = they go and REPAIR it (4%/s up to 90%; a hit stops it).
  A badly hurt swarming spider may rush you and SELF-DESTRUCT.
- Spheres: shield wall, block and bash; linked, they flank.
- Centurions: below 30%, once: OVERDRIVE 12 s (attack damage x1.4, faster swings, steam), then OVERHEAT 5 s: stuck
  venting steam, taking x1.5 damage. The window.
- Ballistas: stay back.
- Ruin alarm: the first to fight raises the alarm (a loud detection event at you; 30 s lock).
- More spiders: the first automaton to load in a Dwemer ruin cell brings 2-3 extra spiders (once per cell).
Off: console "set SNE_DwemerTactics to 0". Needs SKSE.}

CombatStyle Property StyleSpiderSwarm Auto
CombatStyle Property StyleSpiderSupport Auto
CombatStyle Property StyleSphereGuard Auto
CombatStyle Property StyleSphereLinked Auto
CombatStyle Property StyleCenturionLinked Auto
GlobalVariable Property TacticsOn Auto
GlobalVariable Property AlarmLock Auto
FormList Property ReinforcedCells Auto
Actor Property PlayerRef Auto
Faction Property AutomatonFaction Auto
Race Property SpiderRace Auto
Race Property SphereRace Auto
Race Property CenturionRace Auto
Keyword Property LocDwarven Auto
Form Property LvlSpider Auto
Explosion Property SpiderBlast Auto
EffectShader Property ShockFX Auto
EffectShader Property SteamFX Auto
Spell[] Property Link Auto          ; tiers 1-4; effect 0 is the tier marker
Spell Property Overdrive Auto
Spell Property Overheat Auto

Float Property LinkRange = 2000.0 AutoReadOnly

Int R_SPIDER = 1
Int R_SPHERE = 2
Int R_CENTURION = 3
Int R_BALLISTA = 4

Actor Me
Int Role
CombatStyle OriginalStyle
Bool Done
Bool Busy
Bool Prepared
Int LinkTier
Bool Supporting
Bool RepairHit
Float NextRepair
Bool Exploded
Bool OverdriveUsed
Float OverheatAt
Float NextGlitch
Float NextOverload
Float ShockWindowStart
Float ShockSum
Float NextScan

; ---------- setup ----------
Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	Init()
	ApplyStyle()
	Debug.Trace("SNE dwemer: start " + Me + " " + Me.GetDisplayName() + " role " + RoleName() + " (level " + Me.GetLevel() + ")")
	Reinforce()
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
	Race r = Me.GetRace()
	If r == SpiderRace
		Role = R_SPIDER
	ElseIf r == SphereRace
		Role = R_SPHERE
	ElseIf r == CenturionRace
		Role = R_CENTURION
	ElseIf StringUtil.Find(Me.GetDisplayName(), "Ballista") >= 0
		Role = R_BALLISTA
	Else
		Role = R_SPHERE
	EndIf
	If !Prepared
		Prepared = True
		Me.ModActorValue("MagicResist", 15.0)
		Me.ModActorValue("ElectricResist", -150.0)    ; shock is their kryptonite
	EndIf
EndFunction

String Function RoleName()
	If Role == R_SPIDER
		Return "spider"
	ElseIf Role == R_CENTURION
		Return "Centurion"
	ElseIf Role == R_BALLISTA
		Return "ballista"
	EndIf
	Return "sphere"
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

Event OnDying(Actor akKiller)
	Done = True
EndEvent

Event OnLoad()
	If !Done
		ApplyStyle()
		Reinforce()
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
		If Active()
			RaiseAlarm()
		EndIf
		ApplyStyle()
		PushCPR()
		RegisterForSingleUpdate(1.0)
	ElseIf aeCombatState == 0 && !Me.IsDead()
		LinkTier = 0
		Supporting = False
		ApplyStyle()
	EndIf
EndEvent

Event OnUpdate()
	If Done || !Me || Me.IsDead()
		Return
	EndIf
	Float t = Now()
	If OverheatAt > t + 30.0
		OverheatAt = t
	EndIf
	If OverheatAt > 0.0 && t >= OverheatAt && !Busy
		OverheatAt = 0.0
		OverheatVent()
	EndIf
	If !Me.IsInCombat()
		Return
	EndIf
	If Active() && !Busy
		If NextScan > t + 30.0
			NextScan = 0.0
		EndIf
		If t >= NextScan
			NextScan = t + 2.0
			MasterLink()
		EndIf
		If Role == R_SPIDER
			SpiderTick(t)
		ElseIf Role == R_CENTURION
			CenturionCheck()
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
		RepairHit = True
	EndIf
	If Done || !Me || Me.IsDead() || !Active()
		Return
	EndIf
	Float mag = ShockMagnitude(akSource)
	If mag > 0.0
		ShockHit(mag, akSource)
	EndIf
	If Role == R_CENTURION
		CenturionCheck()
	EndIf
EndEvent

; ---------- shock ----------
Float Function ShockMagnitude(Form src)
	Float best = 0.0
	Spell s = src as Spell
	If s
		Int i = 0
		While i < s.GetNumEffects()
			MagicEffect m = s.GetNthEffectMagicEffect(i)
			If m && m.GetResistance() == "ElectricResist" && s.GetNthEffectMagnitude(i) > best
				best = s.GetNthEffectMagnitude(i)
			EndIf
			i += 1
		EndWhile
		Return best
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
			If m2 && m2.GetResistance() == "ElectricResist" && e.GetNthEffectMagnitude(j) > best
				best = e.GetNthEffectMagnitude(j)
			EndIf
			j += 1
		EndWhile
	EndIf
	Return best
EndFunction

Function ShockHit(Float mag, Form src)
	Float t = Now()
	Float maxHp = Me.GetBaseActorValue("Health")
	If maxHp < 1.0
		maxHp = 1.0
	EndIf
	If NextGlitch > t + 30.0
		NextGlitch = 0.0
	EndIf
	If NextOverload > t + 30.0
		NextOverload = 0.0
	EndIf
	; overload: shock adding up within 4 s
	If t - ShockWindowStart > 4.0 || ShockWindowStart > t
		ShockWindowStart = t
		ShockSum = 0.0
	EndIf
	ShockSum += mag
	If ShockSum >= maxHp * 0.3 && t >= NextOverload
		NextOverload = t + 12.0
		ShockSum = 0.0
		Freeze(2.0, "OVERLOAD (" + src + ")")
		Return
	EndIf
	; glitch: one big hit on a lesser machine
	Bool lesser = Role == R_SPIDER || Role == R_SPHERE || Me.GetLevel() <= PlayerRef.GetLevel()
	If lesser && t >= NextGlitch && (mag >= maxHp * 0.1 || mag >= 40.0) && Utility.RandomFloat() < 0.6
		NextGlitch = t + 6.0
		Freeze(1.5, "GLITCH (" + src + ", " + (mag as Int) + " shock)")
	EndIf
EndFunction

Function Freeze(Float seconds, String why)
	If Busy
		Return
	EndIf
	Busy = True
	ShockFX.Play(Me, seconds)
	Me.SetAnimationVariableFloat("staggerMagnitude", 1.0)
	Debug.SendAnimationEvent(Me, "staggerStart")
	Me.SetRestrained(True)
	Debug.Trace("SNE dwemer: " + RoleName() + " " + Me + " " + why + " - frozen " + seconds + " s")
	Utility.Wait(seconds)
	Me.SetRestrained(False)
	Busy = False
EndFunction

; ---------- master link ----------
Bool Function IsAutomaton(Actor a)
	Return a && !a.IsDead() && !a.IsDisabled() && a.IsInFaction(AutomatonFaction) && !a.IsPlayerTeammate()
EndFunction

Function MasterLink()
	Cell c = Me.GetParentCell()
	Int n = 1
	Bool controller = Role == R_CENTURION
	If c
		Int k = c.GetNumRefs(43)
		If k > 80
			k = 80
		EndIf
		Int i = 0
		While i < k
			Actor a = c.GetNthRef(i, 43) as Actor
			If a != Me && IsAutomaton(a) && a.IsInCombat() && Me.GetDistance(a) < LinkRange
				n += 1
				If a.GetRace() == CenturionRace
					controller = True
				EndIf
			EndIf
			i += 1
		EndWhile
	EndIf
	Int score = n - 1
	If controller
		score += 2
	EndIf
	Int tier = score / 2
	If tier > 4
		tier = 4
	EndIf
	If tier != LinkTier
		Debug.Trace("SNE dwemer: " + RoleName() + " " + Me + " MASTER LINK tier " + tier + " (" + n + " linked, controller " + controller + ")")
	EndIf
	LinkTier = tier
	Int j = 0
	While j < 4
		If j < tier
			Link[j].Cast(Me, Me)    ; 5 s, refreshed every 2 s while the link holds
		Else
			Me.DispelSpell(Link[j])
		EndIf
		j += 1
	EndWhile
EndFunction

Function RaiseAlarm()
	Float t = Now()
	Float lock = AlarmLock.GetValue()
	If lock > t + 31.0
		lock = 0.0
	EndIf
	If lock > t
		Return
	EndIf
	AlarmLock.SetValue(t + 30.0)
	PlayerRef.CreateDetectionEvent(PlayerRef, 100)
	Debug.Trace("SNE dwemer: " + RoleName() + " " + Me + " raises the RUIN ALARM")
EndFunction

; ---------- spiders ----------
Function SpiderTick(Float t)
	Cell c = Me.GetParentCell()
	If !c
		Return
	EndIf
	Int spiders = 1
	Actor hurt = None
	Float hurtPct = 0.75
	Int k = c.GetNumRefs(43)
	If k > 80
		k = 80
	EndIf
	Int i = 0
	While i < k
		Actor a = c.GetNthRef(i, 43) as Actor
		If a != Me && IsAutomaton(a) && Me.GetDistance(a) < 1500.0 && Repairable(a)
			If a.GetRace() == SpiderRace && a.IsInCombat()
				spiders += 1
			EndIf
			Float p = a.GetActorValuePercentage("Health")
			If p < hurtPct
				hurtPct = p
				hurt = a
			EndIf
		EndIf
		i += 1
	EndWhile
	Bool weak = Me.GetLevel() + 15 < PlayerRef.GetLevel()
	Bool want = hurt && (spiders <= 2 || weak)
	If want != Supporting
		Supporting = want
		Debug.Trace("SNE dwemer: spider " + Me + " " + ModeName() + " (" + spiders + " spiders, weak " + weak + ", hurt ally " + hurt + ")")
	EndIf
	If NextRepair > t + 30.0
		NextRepair = 0.0
	EndIf
	If Supporting && t >= NextRepair
		Repair(hurt)
		Return
	EndIf
	; a badly hurt swarming spider may go out with a bang
	Float hp = Me.GetActorValuePercentage("Health")
	If !Supporting && !Exploded && hp < 0.25 && hp > 0.0
		Exploded = True
		If Utility.RandomFloat() < 0.6
			SelfDestruct()
		EndIf
	EndIf
EndFunction

String Function ModeName()
	If Supporting
		Return "SUPPORT: repairing"
	EndIf
	Return "SWARM"
EndFunction

; Never repair what is already going down: an automaton at (or below) zero health, bleeding out or caught in a
; killmove. Healing it there left it stuck between dying and alive: no killmove or hit could finish it
; (user, 2026-10-17: a spider at -15% kept fighting; killmoves on small automatons kept failing).
Bool Function Repairable(Actor a)
	Return a && !a.IsDead() && !a.IsInKillMove() && !a.IsBleedingOut() && a.GetActorValuePercentage("Health") > 0.05
EndFunction

Function Repair(Actor ally)
	Busy = True
	RepairHit = False
	Bool fighting = Me.IsInCombat()
	If Me.GetDistance(ally) > 180.0
		If fighting
			Me.StopCombat()
		EndIf
		Me.PathToReference(ally, 1.0)
	EndIf
	Int ticks = 0
	Float maxHp = ally.GetBaseActorValue("Health")
	While ticks < 6 && !RepairHit && !Me.IsDead() && Repairable(ally) && Me.GetDistance(ally) < 300.0 && ally.GetActorValuePercentage("Health") < 0.9
		ShockFX.Play(ally, 0.8)
		ally.RestoreActorValue("Health", maxHp * 0.04)
		Utility.Wait(1.0)
		ticks += 1
	EndWhile
	Debug.Trace("SNE dwemer: spider " + Me + " repaired " + ally + " for " + ticks + " s (hit " + RepairHit + "), now " + ((ally.GetActorValuePercentage("Health") * 100.0) as Int) + "%")
	NextRepair = Now() + 4.0
	If !Me.IsDead() && !Me.IsInCombat()
		Me.StartCombat(PlayerRef)
	EndIf
	Busy = False
EndFunction

Function SelfDestruct()
	Busy = True
	Debug.Trace("SNE dwemer: spider " + Me + " SELF-DESTRUCT run")
	Me.ModActorValue("SpeedMult", 80.0)
	Me.ModActorValue("CarryWeight", 0.1)
	Me.ModActorValue("CarryWeight", -0.1)
	ShockFX.Play(Me, 4.0)
	Float waited = 0.0
	While waited < 4.0 && !Me.IsDead() && Me.GetDistance(PlayerRef) > 160.0
		Utility.Wait(0.25)
		waited += 0.25
	EndWhile
	If Me.IsDead()
		Busy = False
		Return
	EndIf
	Me.PlaceAtMe(SpiderBlast)
	If Me.GetDistance(PlayerRef) < 250.0
		PlayerRef.DamageActorValue("Health", 15.0 + Me.GetLevel())
		PlayerRef.SetAnimationVariableFloat("staggerMagnitude", 0.5)
		Debug.SendAnimationEvent(PlayerRef, "staggerStart")
	EndIf
	Debug.Trace("SNE dwemer: spider " + Me + " EXPLODES (" + (Me.GetDistance(PlayerRef) as Int) + " from you)")
	Busy = False
	Me.Kill()
EndFunction

; ---------- Centurions ----------
Function CenturionCheck()
	If OverdriveUsed || Busy
		Return
	EndIf
	Float hp = Me.GetActorValuePercentage("Health")
	If hp < 0.3 && hp > 0.0
		OverdriveUsed = True
		Overdrive.Cast(Me, Me)
		SteamFX.Play(Me, 12.0)
		OverheatAt = Now() + 12.0
		Debug.Trace("SNE dwemer: Centurion " + Me + " OVERDRIVE at " + ((hp * 100.0) as Int) + "%")
	EndIf
EndFunction

Function OverheatVent()
	If Me.IsDead()
		Return
	EndIf
	Busy = True
	Overheat.Cast(Me, Me)
	SteamFX.Play(Me, 5.0)
	Me.SetRestrained(True)
	Debug.Trace("SNE dwemer: Centurion " + Me + " OVERHEATS - venting steam for 5 s (x1.5 damage)")
	Utility.Wait(5.0)
	Me.SetRestrained(False)
	Busy = False
	If !Done && !Me.IsDead()
		RegisterForSingleUpdate(0.5)
	EndIf
EndFunction

; ---------- more spiders ----------
Function Reinforce()
	If TacticsOn.GetValue() < 0.5 || Me.IsPlayerTeammate() || Me.IsInCombat() || Me.IsDead()
		Return
	EndIf
	Cell c = Me.GetParentCell()
	If !c || !c.IsInterior() || ReinforcedCells.HasForm(c)
		Return
	EndIf
	Location loc = Me.GetCurrentLocation()
	If !loc || !loc.HasKeyword(LocDwarven)
		Return
	EndIf
	If Me.GetSitState() != 0 || !Me.Is3DLoaded() || Me.GetActorValue("Paralysis") > 0.0
		Return    ; dormant in a pipe or a vent: let an awake one place them
	EndIf
	ReinforcedCells.AddForm(c)
	Int count = 2 + Utility.RandomInt(0, 1)
	Int i = 0
	While i < count
		Me.PlaceAtMe(LvlSpider)
		i += 1
	EndWhile
	Debug.Trace("SNE dwemer: ruin cell " + c + " gets " + count + " extra spiders (by " + Me + ")")
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
		If Role == R_SPIDER && Supporting
			want = StyleSpiderSupport
		ElseIf Role == R_SPIDER
			want = StyleSpiderSwarm
		ElseIf Role == R_SPHERE && LinkTier >= 2
			want = StyleSphereLinked
		ElseIf Role == R_SPHERE
			want = StyleSphereGuard
		ElseIf Role == R_CENTURION && LinkTier >= 2
			want = StyleCenturionLinked
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
	If Role == R_SPIDER && Supporting
		SetCPR(True, 0.8, True, 400.0, 900.0, 30.0, 60.0, True)
	ElseIf Role == R_SPIDER
		SetCPR(False, 0.0, True, 80.0, 200.0, 90.0, 180.0, False)    ; swarm round the sides and back
	ElseIf Role == R_SPHERE && LinkTier >= 2
		SetCPR(True, 0.2, True, 120.0, 350.0, 60.0, 140.0, False)
	ElseIf Role == R_SPHERE
		SetCPR(True, 0.2, True, 100.0, 250.0, 20.0, 50.0, False)
	ElseIf Role == R_BALLISTA
		SetCPR(True, 0.9, True, 600.0, 1400.0, 20.0, 50.0, True)
	Else
		SetCPR(False, 0.0, LinkTier >= 2, 120.0, 300.0, 30.0, 80.0, False)
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

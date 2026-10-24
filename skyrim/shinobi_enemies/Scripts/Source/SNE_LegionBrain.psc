Scriptname SNE_LegionBrain extends ActiveMagicEffect
{Shinobi Enemies, Imperial Legion (2026-10-16). SPID gives this ability to CWImperialFaction + PenitusOculatusFaction
(every Legion soldier; it only acts in combat). Works against whoever they fight - you, Thalmor, anyone.
Lore (UESP): a professional army of drill, formation and chain of command; Imperial sword and shield rather than the
Nord greataxe; combined arms (line, archers, battlemages). Good at everything, great at nothing.
- Shield wall: shield-bearers hold a tight, guarded line (block, bash, no wandering). In FORMATION (another Legion
  soldier within 400): +25 block, +25 armour, incoming weapon damage x0.9 (SNE_LegionPerk). Alone, just competent.
- PARRY: a blocked melee hit has 5% + 2.5% per tier (+8% once they have adapted to power attacks) to stagger the
  attacker (5 s cooldown); never on an attacker already recoiling/staggered (Elden Parry's NPC parry or Valhalla's
  perfect block got there first). Halved 2026-10-16 so it does not stack with Elden Parry.
- LINE ROTATION: a front-liner under 40% steps back behind the line (if two other front-liners hold it), patches up
  (25% health over 3 s) and asks the battlemages for healing, then steps back in. Focus one soldier to break it.
- A heavy power attack that staggers a front-liner breaks its place in the line for 3 s (no formation bonus).
- NEVER BREAK: no fleeing. When the commander falls, the highest-level survivor TAKES COMMAND.
- Commander: every 6 s orders the squad to FOCUS the most dangerous enemy (casters first, then the strongest).
- SQUAD INTELLIGENCE: every hit they take is reported (power attacks, magic, arrows, melee, sneak attacks). The squad
  adapts faster the bigger it is (squad size x 5% a second, x1.5 with a commander), and counters the enemy's main
  style - moderately (jack of all trades): power -> parry more, +40 armour; magic -> +30 magic resistance, wards,
  rush the caster; arrows -> raised shields (arrows x0.8), press in; melee -> +30 armour, work in pairs; sneak
  attacks -> the noise gives the attacker away.
- Battlemages (placeholder for the future Leaf Ninja / Leaf Medical Ninja): heal the hurt and rotated, armour and
  ward the line.
- MAGE HUNTERS (user, 2026-10-16): the Thalmor's spellcasters are the Legion's priority. A Thalmor caster in sight
  (within 2000) and every melee legionary within 1500 goes after it: it is the commander's first focus (+100), they
  press with no backing off and run faster (+25% speed), and a legionary within 250 of a casting Thalmor breaks the
  cast (InterruptCast + shield-bash stagger, 3 s cooldown each). No breathing room to cast.
- LEAF NINJA (2026-10-16): some rank-and-file soldiers (not commanders or unique NPCs) are Leaf ninja - about 8%
  Leaf Jonin, 5% Leaf Medical Ninja, rare Leaf Medical Captains (picked once from the form ID). They get SNE_LeafNinja,
  which owns their style, outfit and jutsu; this script still gives them formation, intel and focus orders.
- No damage bonus: their strength is defence and teamwork.
Off: console "set SNE_LegionTactics to 0". Needs SKSE.}

CombatStyle Property StyleLine Auto
CombatStyle Property StyleSoldier Auto
CombatStyle Property StyleArcher Auto
CombatStyle Property StyleMage Auto
CombatStyle Property StylePress Auto
CombatStyle Property VanillaMagic Auto
CombatStyle Property VanillaMissile Auto
CombatStyle Property VanillaCWMissile Auto
GlobalVariable Property TacticsOn Auto
GlobalVariable Property IntelPower Auto
GlobalVariable Property IntelMagic Auto
GlobalVariable Property IntelRanged Auto
GlobalVariable Property IntelMelee Auto
GlobalVariable Property IntelTime Auto
GlobalVariable Property Adapt Auto          ; 0..1 shared squad adaptation
Actor Property PlayerRef Auto
Faction Property LegionFaction Auto
Faction Property OculatusFaction Auto
Faction Property FieldCOFaction Auto
Faction Property ThalmorFaction Auto
Spell Property LeafAbility Auto
Spell Property Formation Auto
Spell Property AdaptPower Auto
Spell Property AdaptMagic Auto
Spell Property AdaptRanged Auto
Spell Property AdaptMelee Auto
Spell Property LegionWard Auto
Spell Property SpellHealOther Auto
Spell Property SpellCloseWounds Auto
Spell Property SpellOakflesh Auto
Spell Property SpellStoneflesh Auto
Spell Property SpellIronflesh Auto

Int R_LINE = 1
Int R_SOLDIER = 2
Int R_ARCHER = 3
Int R_MAGE = 4

Int S_NONE = 0
Int S_POWER = 1
Int S_MAGIC = 2
Int S_RANGED = 3
Int S_MELEE = 4

Actor Me
Int Role
CombatStyle OriginalStyle
Bool Done
Bool Busy
Bool Prepared
Bool Commander
Bool InFormation
Int SquadSize
Float LineBrokenUntil
Float NextParry
Float NextRotate
Float NextOrder
Float NextSupport
Float LastLearn
Actor Target
Int LeafRank          ; 0 none, 1 jonin, 2 medic, 3 medical captain
Actor Prey            ; the Thalmor caster this legionary is hunting
Bool Hunting
Float NextInterrupt

; ---------- setup ----------
Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	Init()
	Debug.Trace("SNE legion: start " + Me + " " + Me.GetDisplayName() + " role " + RoleName() + " tier " + Tier() + " commander " + Commander + " leaf rank " + LeafRank + " (level " + Me.GetLevel() + ")")
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
	Bool armed = Me.Is3DLoaded() && Me.IsAIEnabled()     ; actors with no AI (wounded-soldier props) can't report weapons
	If OriginalStyle == VanillaMagic || (armed && (Me.GetEquippedItemType(1) == 9 || Me.GetEquippedItemType(0) == 9))
		Role = R_MAGE
	ElseIf OriginalStyle == VanillaMissile || OriginalStyle == VanillaCWMissile || (armed && Me.GetEquippedItemType(1) == 7)
		Role = R_ARCHER
	ElseIf Me.GetEquippedShield()
		Role = R_LINE
	Else
		Role = R_SOLDIER
	EndIf
	String nm = Me.GetDisplayName()
	Commander = Me.IsInFaction(FieldCOFaction) || StringUtil.Find(nm, "Legate") >= 0 || StringUtil.Find(nm, "Captain") >= 0 || StringUtil.Find(nm, "Tribune") >= 0 || StringUtil.Find(nm, "General") >= 0 || StringUtil.Find(nm, "Commander") >= 0
	If !Prepared
		Prepared = True
		Me.SetActorValue("Confidence", 4.0)    ; the Legion does not break
	EndIf
	If !Commander && b && !b.IsUnique() && Role != R_MAGE && !Me.IsPlayerTeammate()
		LeafRank = SNE_LeafNinja.LeafRank(Me)
		If LeafRank > 0 && !Me.HasSpell(LeafAbility)
			Me.AddSpell(LeafAbility, False)
		EndIf
	EndIf
EndFunction

String Function RoleName()
	If Role == R_LINE
		Return "shield line"
	ElseIf Role == R_ARCHER
		Return "archer"
	ElseIf Role == R_MAGE
		Return "battlemage"
	EndIf
	Return "soldier"
EndFunction

Int Function Tier()
	Int lv = Me.GetLevel()
	Int t = 4
	If lv < 12
		t = 1
	ElseIf lv < 25
		t = 2
	ElseIf lv < 40
		t = 3
	EndIf
	If Me.IsInFaction(OculatusFaction) && t < 4
		t += 1    ; Penitus Oculatus: the Emperor's elite
	EndIf
	Return t
EndFunction

Bool Function Active()
	Return TacticsOn.GetValue() >= 0.5 && !Me.IsPlayerTeammate()
EndFunction

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

Bool Function IsLegion(Actor a)
	Return a && !a.IsDead() && !a.IsDisabled() && (a.IsInFaction(LegionFaction) || a.IsInFaction(OculatusFaction)) && !a.IsPlayerTeammate()
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
	If Hunting
		Hunting = False
		Me.ModActorValue("SpeedMult", -25.0)
	EndIf
	If Commander && Active()
		Me.SendModEvent("SNE_LegionCommanderFell")
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
		Prey = None
		SetHunting(False)
		ApplyStyle()
	EndIf
EndEvent

Function StartFight()
	RegisterForModEvent("SNE_LegionCommanderFell", "OnCommanderFell")
	RegisterForModEvent("SNE_LegionFocus", "OnLegionFocus")
	RegisterForModEvent("SNE_LegionHealMe", "OnHealMe")
	Float t = Now()
	Float it = IntelTime.GetValue()
	If it > t + 1.0 || t - it > 60.0
		IntelPower.SetValue(0.0)    ; a new fight: fresh intelligence
		IntelMagic.SetValue(0.0)
		IntelRanged.SetValue(0.0)
		IntelMelee.SetValue(0.0)
		Adapt.SetValue(0.0)
	EndIf
	IntelTime.SetValue(t)
	LastLearn = t
EndFunction

Event OnUpdate()
	If Done || !Me || Me.IsDead() || !Me.IsInCombat()
		Return
	EndIf
	Float t = Now()
	Target = Me.GetCombatTarget()
	If Active() && !Busy
		Squad(t)
		Learn(t)
		ApplyAdaptation()
		If (Role == R_LINE || Role == R_SOLDIER) && LeafRank <= 1
			HuntMages(t)
		EndIf
		If Commander && t >= NextOrder
			NextOrder = t + 6.0
			OrderFocus()
		EndIf
		If Role == R_MAGE
			MageTick(t)
		ElseIf (Role == R_LINE || Role == R_SOLDIER) && LeafRank == 0 && Me.GetActorValuePercentage("Health") < 0.4
			TryRotate(t)
		EndIf
	EndIf
	ApplyStyle()
	PushCPR()
	If !Done && !Me.IsDead()
		RegisterForSingleUpdate(1.0)
	EndIf
EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If Done || !Me || Me.IsDead() || !Active()
		Return
	EndIf
	Actor att = akAggressor as Actor
	If !att || IsLegion(att)
		Return
	EndIf
	; report it to the squad
	If akSource as Spell
		IntelMagic.Mod(1.0)
	ElseIf akProjectile
		IntelRanged.Mod(1.0)
	ElseIf abPowerAttack
		IntelPower.Mod(1.0)
	Else
		IntelMelee.Mod(1.0)
	EndIf
	IntelTime.SetValue(Now())
	If abSneakAttack
		att.CreateDetectionEvent(att, 100)    ; the squad hears where it came from
	EndIf
	Float t = Now()
	; parry (2026-10-16: halved, Elden Parry already gives NPCs real timed parries; skip when the attacker is
	; already recoiling or staggered - Elden Parry or Valhalla got there first - so the two never stack)
	If abHitBlocked && !akProjectile && !(akSource as Spell) && t >= NextParry && !AlreadyReeling(att)
		Float chance = 0.05 + 0.025 * Tier()
		If DominantStyle() == S_POWER && Adapt.GetValue() >= 0.5
			chance += 0.08
		EndIf
		If Utility.RandomFloat() < chance
			NextParry = t + 5.0
			att.SetAnimationVariableFloat("staggerMagnitude", 0.6)
			Debug.SendAnimationEvent(att, "staggerStart")
			Debug.Trace("SNE legion: " + RoleName() + " " + Me + " PARRIES " + att)
		EndIf
	EndIf
	; a heavy blow through the guard breaks this soldier's place in the line
	If abPowerAttack && !abHitBlocked && Role == R_LINE
		LineBrokenUntil = t + 3.0
	EndIf
EndEvent

Bool Function AlreadyReeling(Actor a)
	If !a.HasKeywordString("ActorTypeNPC")
		Return False
	EndIf
	Return a.GetAnimationVariableBool("IsRecoiling") || a.GetAnimationVariableBool("IsStaggering")
EndFunction

; ---------- squad ----------
Function Squad(Float t)
	Int n = 1
	Bool near = False
	Cell c = Me.GetParentCell()
	If c
		Int k = c.GetNumRefs(43)
		If k > 80
			k = 80
		EndIf
		Int i = 0
		While i < k
			Actor a = c.GetNthRef(i, 43) as Actor
			If a != Me && IsLegion(a) && a.IsInCombat()
				Float d = Me.GetDistance(a)
				If d < 2000.0
					n += 1
				EndIf
				If d < 400.0
					near = True
				EndIf
			EndIf
			i += 1
		EndWhile
	EndIf
	SquadSize = n
	If LineBrokenUntil > t + 10.0
		LineBrokenUntil = 0.0
	EndIf
	Bool was = InFormation
	InFormation = near && t >= LineBrokenUntil
	If InFormation
		Formation.Cast(Me, Me)    ; 4 s, refreshed every second while in formation
	EndIf
	If InFormation != was
		Debug.Trace("SNE legion: " + RoleName() + " " + Me + " formation " + InFormation + " (squad " + n + ")")
	EndIf
EndFunction

Int Function DominantStyle()
	Float p = IntelPower.GetValue()
	Float m = IntelMagic.GetValue()
	Float r = IntelRanged.GetValue()
	Float e = IntelMelee.GetValue()
	If p + m + r + e < 3.0
		Return S_NONE
	EndIf
	Int best = S_MELEE
	Float bv = e
	If p >= bv
		best = S_POWER
		bv = p
	EndIf
	If m >= bv
		best = S_MAGIC
		bv = m
	EndIf
	If r >= bv
		best = S_RANGED
	EndIf
	Return best
EndFunction

; the squad learns together: bigger squads (and a commander) adapt faster
Function Learn(Float t)
	Float dt = t - LastLearn
	LastLearn = t
	If dt <= 0.0 || dt > 5.0 || DominantStyle() == S_NONE
		Return
	EndIf
	Float rate = 0.05    ; every soldier in the fight adds this each second, so the squad learns at size x 5%/s
	If Commander
		rate *= 1.5
	EndIf
	Float a = Adapt.GetValue()
	If a < 1.0
		Float na = a + rate * dt
		If na > 1.0
			na = 1.0
		EndIf
		Adapt.SetValue(na)
		If a < 0.5 && na >= 0.5
			Debug.Trace("SNE legion: the squad has ADAPTED to " + StyleName(DominantStyle()) + " (squad " + SquadSize + ")")
		EndIf
	EndIf
EndFunction

String Function StyleName(Int s)
	If s == S_POWER
		Return "power attacks"
	ElseIf s == S_MAGIC
		Return "magic"
	ElseIf s == S_RANGED
		Return "archery"
	ElseIf s == S_MELEE
		Return "fast melee"
	EndIf
	Return "nothing yet"
EndFunction

Function ApplyAdaptation()
	If Adapt.GetValue() < 0.5
		Return
	EndIf
	Int s = DominantStyle()
	If s == S_POWER
		AdaptPower.Cast(Me, Me)
	ElseIf s == S_MAGIC
		AdaptMagic.Cast(Me, Me)
	ElseIf s == S_RANGED
		AdaptRanged.Cast(Me, Me)
	ElseIf s == S_MELEE
		AdaptMelee.Cast(Me, Me)
	EndIf
EndFunction

Event OnCommanderFell(String eventName, String strArg, Float numArg, Form sender)
	Actor dead = sender as Actor
	If Done || !Me || Me.IsDead() || Commander || !Me.IsInCombat() || !dead || Me.GetDistance(dead) > 2500.0
		Return
	EndIf
	Utility.Wait(Utility.RandomFloat(0.2, 1.0))
	; the highest-ranked survivor takes command
	Cell c = Me.GetParentCell()
	If c
		Int k = c.GetNumRefs(43)
		If k > 80
			k = 80
		EndIf
		Int i = 0
		While i < k
			Actor a = c.GetNthRef(i, 43) as Actor
			If a != Me && IsLegion(a) && a.IsInCombat() && Me.GetDistance(a) < 2500.0 && a.GetLevel() > Me.GetLevel()
				Return
			EndIf
			i += 1
		EndWhile
	EndIf
	Commander = True
	Debug.Trace("SNE legion: " + RoleName() + " " + Me + " TAKES COMMAND (level " + Me.GetLevel() + ")")
EndEvent

; commander: the squad focuses the most dangerous enemy - casters first, then the strongest
Function OrderFocus()
	Actor best = None
	Float bestScore = -1.0
	Cell c = Me.GetParentCell()
	If !c
		Return
	EndIf
	Int k = c.GetNumRefs(43)
	If k > 80
		k = 80
	EndIf
	Int i = 0
	While i < k
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && !a.IsDead() && a.IsInCombat() && a.IsHostileToActor(Me) && Me.GetDistance(a) < 2500.0
			Float score = a.GetLevel() as Float
			If a.GetEquippedItemType(1) == 9 || a.GetEquippedItemType(0) == 9
				score += 30.0
				If a.IsInFaction(ThalmorFaction)
					score += 100.0    ; Thalmor casters first, always
				EndIf
			EndIf
			If a.GetActorValuePercentage("Health") < 0.3
				score += 15.0    ; finish it
			EndIf
			If score > bestScore
				bestScore = score
				best = a
			EndIf
		EndIf
		i += 1
	EndWhile
	If !best
		Return
	EndIf
	Int h = ModEvent.Create("SNE_LegionFocus")
	If h
		ModEvent.PushForm(h, best)
		ModEvent.PushForm(h, Me)
		ModEvent.Send(h)
	EndIf
	Debug.Trace("SNE legion: commander " + Me + " orders FOCUS on " + best)
EndFunction

Event OnLegionFocus(Form akTarget, Form akCommander)
	Actor tgt = akTarget as Actor
	Actor cmd = akCommander as Actor
	If Done || !Me || Me.IsDead() || Busy || !tgt || tgt.IsDead() || !cmd || cmd == Me || !Me.IsInCombat()
		Return
	EndIf
	If Me.GetDistance(cmd) > 2500.0 || Me.GetDistance(tgt) > 1500.0 || Me.GetCombatTarget() == tgt
		Return
	EndIf
	If Utility.RandomFloat() < 0.6
		Me.StartCombat(tgt)
	EndIf
EndEvent

; ---------- mage hunting ----------
Bool Function IsThalmorCaster(Actor a)
	Return a && !a.IsDead() && a.IsInFaction(ThalmorFaction) && (a.GetEquippedItemType(1) == 9 || a.GetEquippedItemType(0) == 9 || StringUtil.Find(a.GetDisplayName(), "Justiciar") >= 0)
EndFunction

Function HuntMages(Float t)
	If Prey && (Prey.IsDead() || Me.GetDistance(Prey) > 2000.0)
		Prey = None
	EndIf
	If !Prey
		If IsThalmorCaster(Target) && Me.GetDistance(Target) < 1500.0
			Prey = Target
		Else
			Cell c = Me.GetParentCell()
			Float bestD = 1500.0
			If c
				Int k = c.GetNumRefs(43)
				If k > 80
					k = 80
				EndIf
				Int i = 0
				While i < k
					Actor a = c.GetNthRef(i, 43) as Actor
					If IsThalmorCaster(a) && a.IsHostileToActor(Me) && Me.GetDistance(a) < bestD
						bestD = Me.GetDistance(a)
						Prey = a
					EndIf
					i += 1
				EndWhile
			EndIf
		EndIf
		If Prey
			Debug.Trace("SNE legion: " + RoleName() + " " + Me + " HUNTS Thalmor caster " + Prey)
		EndIf
	EndIf
	SetHunting(Prey != None)
	If !Prey
		Return
	EndIf
	If Me.GetCombatTarget() != Prey
		Me.StartCombat(Prey)
	EndIf
	; no breathing room: break the cast when close
	If NextInterrupt > t + 10.0
		NextInterrupt = 0.0
	EndIf
	If t >= NextInterrupt && Me.GetDistance(Prey) < 250.0 && (Prey.GetAnimationVariableBool("IsCastingRight") || Prey.GetAnimationVariableBool("IsCastingLeft") || Prey.GetAnimationVariableBool("IsCastingDual"))
		NextInterrupt = t + 3.0
		Prey.InterruptCast()
		Prey.SetAnimationVariableFloat("staggerMagnitude", 0.5)
		Debug.SendAnimationEvent(Prey, "staggerStart")
		Debug.Trace("SNE legion: " + RoleName() + " " + Me + " BREAKS " + Prey + "'s cast")
	EndIf
EndFunction

Function SetHunting(Bool on)
	If on == Hunting
		Return
	EndIf
	Hunting = on
	If on
		Me.ModActorValue("SpeedMult", 25.0)
	Else
		Me.ModActorValue("SpeedMult", -25.0)
	EndIf
	Me.ModActorValue("CarryWeight", 0.1)
	Me.ModActorValue("CarryWeight", -0.1)
EndFunction

; ---------- line rotation ----------
Function TryRotate(Float t)
	If NextRotate > t + 40.0
		NextRotate = 0.0
	EndIf
	If t < NextRotate || !Target
		Return
	EndIf
	; only if two other front-liners hold the line
	Int holders = 0
	Cell c = Me.GetParentCell()
	If c
		Int k = c.GetNumRefs(43)
		If k > 80
			k = 80
		EndIf
		Int i = 0
		While i < k
			Actor a = c.GetNthRef(i, 43) as Actor
			If a != Me && IsLegion(a) && a.IsInCombat() && a.GetEquippedItemType(1) >= 1 && a.GetEquippedItemType(1) <= 6 && a.GetDistance(Target) < 600.0 && a.GetActorValuePercentage("Health") > 0.5
				holders += 1
			EndIf
			i += 1
		EndWhile
	EndIf
	If holders < 2
		Return
	EndIf
	NextRotate = t + 25.0
	Busy = True
	Actor foe = Target
	Debug.Trace("SNE legion: " + RoleName() + " " + Me + " ROTATES out of the line at " + ((Me.GetActorValuePercentage("Health") * 100.0) as Int) + "% (" + holders + " hold it)")
	ObjectReference spot = BehindMarker(foe)
	Me.StopCombat()
	Me.PathToReference(spot, 1.0)
	spot.Delete()
	Me.SendModEvent("SNE_LegionHealMe")
	Int i2 = 0
	While i2 < 3 && !Me.IsDead()
		If !Me.IsInKillMove() && !Me.IsBleedingOut() && Me.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
			Me.RestoreActorValue("Health", Me.GetBaseActorValue("Health") * 0.083)
		EndIf
		Utility.Wait(1.0)
		i2 += 1
	EndWhile
	If !Me.IsDead() && foe && !foe.IsDead()
		Me.StartCombat(foe)
	EndIf
	Debug.Trace("SNE legion: " + RoleName() + " " + Me + " back in the line at " + ((Me.GetActorValuePercentage("Health") * 100.0) as Int) + "%")
	Busy = False
EndFunction

ObjectReference Function BehindMarker(Actor foe)
	Float dx = Me.GetPositionX() - foe.GetPositionX()
	Float dy = Me.GetPositionY() - foe.GetPositionY()
	Float len = Math.sqrt(dx * dx + dy * dy)
	If len < 1.0
		dx = 1.0
		dy = 0.0
		len = 1.0
	EndIf
	ObjectReference m = Me.PlaceAtMe(Game.GetFormFromFile(0x3B, "Skyrim.esm"))
	m.SetPosition(Me.GetPositionX() + dx / len * 450.0, Me.GetPositionY() + dy / len * 450.0, Me.GetPositionZ())
	Return m
EndFunction

; ---------- battlemages ----------
Event OnHealMe(String eventName, String strArg, Float numArg, Form sender)
	Actor s = sender as Actor
	If Done || !Me || Me.IsDead() || Role != R_MAGE || !s || s.IsDead() || Me.GetDistance(s) > 1200.0
		Return
	EndIf
	If !s.IsInKillMove() && !s.IsBleedingOut() && s.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
		SpellHealOther.Cast(Me, s)
	EndIf
	Debug.Trace("SNE legion: battlemage " + Me + " heals rotated " + s)
EndEvent

Function MageTick(Float t)
	If NextSupport > t + 30.0
		NextSupport = 0.0
	EndIf
	If t < NextSupport
		Return
	EndIf
	NextSupport = t + 3.0
	If Me.GetActorValuePercentage("Health") < 0.4
		SpellCloseWounds.Cast(Me, Me)
		Return
	EndIf
	Bool wardUp = DominantStyle() == S_MAGIC && Adapt.GetValue() >= 0.5
	Actor hurt = None
	Float hurtPct = 0.5
	Actor bare = None
	Cell c = Me.GetParentCell()
	If c
		Int k = c.GetNumRefs(43)
		If k > 80
			k = 80
		EndIf
		Int i = 0
		While i < k
			Actor a = c.GetNthRef(i, 43) as Actor
			If a != Me && IsLegion(a) && a.IsInCombat() && Me.GetDistance(a) < 1500.0
				Float p = a.GetActorValuePercentage("Health")
				If p < hurtPct
					hurtPct = p
					hurt = a
				EndIf
				If !bare && a.GetEquippedItemType(1) >= 1 && a.GetEquippedItemType(1) <= 6
					If wardUp && !a.HasMagicEffect(LegionWard.GetNthEffectMagicEffect(0))
						bare = a
					ElseIf !wardUp && !a.HasMagicEffect(SpellOakflesh.GetNthEffectMagicEffect(0)) && !a.HasMagicEffect(SpellStoneflesh.GetNthEffectMagicEffect(0)) && !a.HasMagicEffect(SpellIronflesh.GetNthEffectMagicEffect(0))
						bare = a
					EndIf
				EndIf
			EndIf
			i += 1
		EndWhile
	EndIf
	If hurt
		If !hurt.IsInKillMove() && !hurt.IsBleedingOut() && hurt.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
			SpellHealOther.Cast(Me, hurt)
		EndIf
		Debug.Trace("SNE legion: battlemage " + Me + " heals " + hurt + " at " + ((hurtPct * 100.0) as Int) + "%")
	ElseIf bare && wardUp
		LegionWard.Cast(bare, bare)
		Debug.Trace("SNE legion: battlemage " + Me + " wards " + bare)
	ElseIf bare
		Spell f = SpellOakflesh
		If Tier() >= 3
			f = SpellIronflesh
		ElseIf Tier() == 2
			f = SpellStoneflesh
		EndIf
		f.Cast(bare, bare)
		Debug.Trace("SNE legion: battlemage " + Me + " armours " + bare)
	EndIf
EndFunction

; ---------- styles and CPR ----------
Bool Function Pressing()    ; hunting a Thalmor caster, or adapted to archers or casters: close the distance
	Int s = DominantStyle()
	Return Hunting || (Adapt.GetValue() >= 0.5 && (s == S_RANGED || s == S_MAGIC))
EndFunction

Function ApplyStyle()
	If !Me || Me.IsPlayerTeammate() || LeafRank > 0
		Return    ; Leaf ninja: SNE_LeafNinja owns the style
	EndIf
	ActorBase b = Me.GetLeveledActorBase()
	If !b
		Return
	EndIf
	CombatStyle want = OriginalStyle
	If TacticsOn.GetValue() >= 0.5 && Me.IsInCombat()
		If Role == R_MAGE
			want = StyleMage
		ElseIf Role == R_ARCHER
			want = StyleArcher
		ElseIf Pressing()
			want = StylePress
		ElseIf Role == R_LINE
			want = StyleLine
		Else
			want = StyleSoldier
		EndIf
	EndIf
	If want && b.GetCombatStyle() != want
		b.SetCombatStyle(want)
	EndIf
EndFunction

Function PushCPR()
	If !Active() || Busy || LeafRank > 0
		Return
	EndIf
	If Role == R_MAGE
		SetCPR(True, 0.7, True, 400.0, 1000.0, 20.0, 50.0, True)
	ElseIf Role == R_ARCHER
		SetCPR(True, 0.6, True, 500.0, 1200.0, 20.0, 50.0, True)
	ElseIf Pressing()
		SetCPR(False, 0.0, True, 100.0, 250.0, 40.0, 100.0, False)
	ElseIf Role == R_LINE
		SetCPR(True, 0.15, False, 0.0, 0.0, 0.0, 0.0, False)              ; hold the line
	ElseIf DominantStyle() == S_MELEE && Adapt.GetValue() >= 0.5
		SetCPR(True, 0.2, True, 100.0, 250.0, 70.0, 150.0, False)         ; work in pairs from the sides
	Else
		SetCPR(True, 0.2, True, 100.0, 250.0, 30.0, 80.0, False)
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

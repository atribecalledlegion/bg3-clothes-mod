Scriptname SNE_DraugrBrain extends ActiveMagicEffect
{Shinobi Enemies, draugr (2026-10-15). SPID gives this ability to DraugrFaction. Lore (UESP): draugr are the Dragon
Cult's dead, bound to their Priest or lord; they rise in shifts to give their life force to the master, return to
their graves to regenerate, keep the skills they had in life (many still use the Thu'um), and guard the barrow.
- Common draugr: relentless (no fear, no backing off). Badly hurt (< 35%), once: back to the spot it rose from to
  regenerate for 4 s; any hit spoils it.
- Lords (named "...Lord", or a draugr boss style): patient duelists. Entering combat, a lord calls the barrow
  (a loud detection event at the player wakes the sleepers).
- On death: the life force goes to the nearest living lord or Dragon Priest (SNE_DraugrQuest).
- Edo Tensei: a lord may rise again after death (15%, Deathlords/Death Overlords 20%, once), unless the body was
  cleansed: the killing blow (last 3 s) was fire or Restoration magic. Handled by SNE_DraugrQuest, because this
  effect ends with the death.
- Swarm (user, 2026-10-16): they overwhelm you in the barrow's tight halls. Every 2 s each common counts the
  draugr already closer to its target; the front two press straight in (relentless), everyone else wraps round the
  sides and back (swarm style + tight CPR circling) and piles on when you stagger. They hit x1.3 (SNE_DraugrPerk).
Off: console "set SNE_DraugrTactics to 0". Needs SKSE (Get/SetCombatStyle, StringUtil, MagicEffect info).}

CombatStyle Property StyleRelentless Auto
CombatStyle Property StyleLord Auto
SNE_DraugrQuest Property DQ Auto
GlobalVariable Property TacticsOn Auto
Actor Property PlayerRef Auto
Static Property XMarkerBase Auto
Faction Property RevivedFaction Auto
CombatStyle Property VanillaBoss1 Auto
CombatStyle Property VanillaBoss2 Auto
CombatStyle Property VanillaMissile Auto
CombatStyle Property VanillaMagic Auto
CombatStyle Property StyleSwarm Auto
Faction Property DraugrFaction Auto

Float Property RegenBelow = 0.35 AutoReadOnly
Float Property CleanseWindow = 3.0 AutoReadOnly

Int ROLE_COMMON = 1
Int ROLE_ARCHER = 2
Int ROLE_MAGE = 3
Int ROLE_LORD = 4

Actor Me
Int Role
CombatStyle OriginalStyle
ObjectReference Home      ; where it rose from (its grave)
Bool Done
Bool Busy
Bool Regenerated
Bool RegenHit
Bool Called
Float LastCleanseHit
Bool Swarming
Float NextSwarmScan

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	Init()
	ApplyStyle()
	Debug.Trace("SNE draugr: start " + Me + " " + Me.GetDisplayName() + " role " + RoleName() + " (level " + Me.GetLevel() + ")" + RevivedNote())
	If Me.IsInCombat()
		RegisterForSingleUpdate(1.0)
	EndIf
EndEvent

String Function RevivedNote()
	If Me.IsInFaction(RevivedFaction)
		Return " [risen again]"
	EndIf
	Return ""
EndFunction

Function Init()
	If Role != 0 || !Me
		Return
	EndIf
	ActorBase b = Me.GetLeveledActorBase()
	If b
		OriginalStyle = b.GetCombatStyle()
	EndIf
	String nm = Me.GetDisplayName()
	If StringUtil.Find(nm, "Lord") >= 0 || OriginalStyle == VanillaBoss1 || OriginalStyle == VanillaBoss2
		Role = ROLE_LORD
	ElseIf OriginalStyle == VanillaMissile || Me.GetEquippedItemType(1) == 7
		Role = ROLE_ARCHER
	ElseIf OriginalStyle == VanillaMagic || Me.GetEquippedItemType(1) == 9
		Role = ROLE_MAGE
	Else
		Role = ROLE_COMMON
	EndIf
	If Role == ROLE_COMMON && !Home
		Home = Me.PlaceAtMe(XMarkerBase)    ; its grave: where it was when the barrow loaded
	EndIf
EndFunction

String Function RoleName()
	If Role == ROLE_LORD
		Return "lord"
	ElseIf Role == ROLE_ARCHER
		Return "archer"
	ElseIf Role == ROLE_MAGE
		Return "mage"
	EndIf
	Return "common"
EndFunction

Bool Function Active()
	Return TacticsOn.GetValue() >= 0.5 && !Me.IsPlayerTeammate()
EndFunction

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Done = True
EndEvent

Event OnDying(Actor akKiller)
	Done = True
	If !Active()
		Return
	EndIf
	Bool cleansed = Utility.GetCurrentRealTime() - LastCleanseHit < CleanseWindow
	DQ.DraugrFell(Me, Role == ROLE_LORD, cleansed)
	If Home
		Home.Delete()
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
		ApplyStyle()
		PushCPR()
		If Role == ROLE_LORD && !Called && Active()
			Called = True
			PlayerRef.CreateDetectionEvent(PlayerRef, 100)
			Debug.Trace("SNE draugr: lord " + Me + " " + Me.GetDisplayName() + " calls the barrow")
		EndIf
		RegisterForSingleUpdate(1.0)
	ElseIf aeCombatState == 0 && !Me.IsDead()
		UnregisterForUpdate()
	EndIf
EndEvent

Event OnUpdate()
	If Done || !Me || Me.IsDead() || !Me.IsInCombat()
		Return
	EndIf
	If Active() && !Busy && Role == ROLE_COMMON && !Regenerated
		Float hp = Me.GetActorValuePercentage("Health")
		If hp < RegenBelow && hp > 0.05
			ReturnToGrave()
		EndIf
	EndIf
	If Active() && !Busy && Role == ROLE_COMMON && !Me.IsDead()
		SwarmCheck()
	EndIf
	ApplyStyle()
	PushCPR()
	If !Done && !Me.IsDead()
		RegisterForSingleUpdate(1.0)
	EndIf
EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If Busy
		RegenHit = True
	EndIf
	If IsCleansing(akSource)
		LastCleanseHit = Utility.GetCurrentRealTime()
	EndIf
EndEvent

; fire burns the body, Restoration (Turn Undead, Sun) purifies it: either one stops the Edo Tensei revival
Bool Function IsCleansing(Form src)
	Spell s = src as Spell
	If s
		Int i = 0
		While i < s.GetNumEffects()
			MagicEffect m = s.GetNthEffectMagicEffect(i)
			If m && (m.GetResistance() == "FireResist" || m.GetAssociatedSkill() == "Restoration")
				Return True
			EndIf
			i += 1
		EndWhile
		Return False
	EndIf
	Weapon w = src as Weapon
	If w && w.GetEnchantment()
		Enchantment e = w.GetEnchantment()
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

; the swarm: the front two press in, the rest go round the sides and back
Function SwarmCheck()
	Float t = Utility.GetCurrentRealTime()
	If NextSwarmScan > t + 10.0
		NextSwarmScan = 0.0
	EndIf
	If t < NextSwarmScan
		Return
	EndIf
	NextSwarmScan = t + 2.0
	Actor tgt = Me.GetCombatTarget()
	Bool want = False
	Int ahead = 0
	Int pack = 0
	If tgt && Me.GetDistance(tgt) < 1500.0
		Float mine = Me.GetDistance(tgt)
		Cell c = Me.GetParentCell()
		If c
			Int n = c.GetNumRefs(43)
			If n > 80
				n = 80
			EndIf
			Int i = 0
			While i < n
				Actor a = c.GetNthRef(i, 43) as Actor
				If a && a != Me && !a.IsDead() && a.IsInCombat() && a.IsInFaction(DraugrFaction) && !a.IsPlayerTeammate()
					Float d = a.GetDistance(tgt)
					If d < 900.0
						pack += 1
						If d < mine
							ahead += 1
						EndIf
					EndIf
				EndIf
				i += 1
			EndWhile
		EndIf
		want = ahead >= 2
	EndIf
	If want != Swarming
		Swarming = want
		Debug.Trace("SNE draugr: " + Me + " swarm " + want + " (" + ahead + " ahead, pack of " + (pack + 1) + ")")
	EndIf
EndFunction

; lore: draugr return to their graves to regenerate
Function ReturnToGrave()
	If !Home || Me.GetDistance(Home) > 2500.0
		Regenerated = True
		Return
	EndIf
	Regenerated = True
	Busy = True
	RegenHit = False
	Debug.Trace("SNE draugr: " + Me + " at " + ((Me.GetActorValuePercentage("Health") * 100.0) as Int) + "% returns to its grave to regenerate (" + (Me.GetDistance(Home) as Int) + " away)")
	Me.StopCombat()
	Me.PathToReference(Home, 1.0)
	Int healed = 0
	If !Me.IsDead() && Me.GetDistance(Home) < 200.0
		Int i = 0
		While i < 4 && !RegenHit && !Me.IsDead()
			Utility.Wait(1.0)
			If !RegenHit
				If !Me.IsInKillMove() && !Me.IsBleedingOut() && Me.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
					Me.RestoreActorValue("Health", Me.GetBaseActorValue("Health") * 0.15)
				EndIf
				healed += 1
			EndIf
			i += 1
		EndWhile
	EndIf
	Debug.Trace("SNE draugr: " + Me + " regeneration " + healed + "/4 (interrupted " + RegenHit + "), health " + ((Me.GetActorValuePercentage("Health") * 100.0) as Int) + "%")
	If !Me.IsDead()
		Me.StartCombat(PlayerRef)
	EndIf
	Busy = False
EndFunction

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
		If Role == ROLE_LORD
			want = StyleLord
		ElseIf Role == ROLE_COMMON && Swarming
			want = StyleSwarm
		ElseIf Role == ROLE_COMMON
			want = StyleRelentless
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
	If Role == ROLE_COMMON && Swarming
		SetCPR(False, 0.0, True, 90.0, 220.0, 90.0, 180.0, False)     ; close in from the sides and behind
	ElseIf Role == ROLE_COMMON
		SetCPR(False, 0.0, False, 0.0, 0.0, 0.0, 0.0, False)          ; straight at you, never gives ground
	ElseIf Role == ROLE_LORD
		SetCPR(True, 0.15, True, 100.0, 350.0, 20.0, 50.0, False)     ; measured duelist
	ElseIf Role == ROLE_ARCHER
		SetCPR(True, 0.7, True, 300.0, 1100.0, 30.0, 60.0, True)
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
		Me.SetAnimationVariableFloat("CPR_FallbackDistMin", 300.0)
		Me.SetAnimationVariableFloat("CPR_FallbackDistMax", 800.0)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", 0.4)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", 0.9)
	EndIf
EndFunction

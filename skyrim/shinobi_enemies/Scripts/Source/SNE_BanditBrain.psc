Scriptname SNE_BanditBrain extends ActiveMagicEffect
{Shinobi Enemies, bandit tactics. SPID gives this ability to every bandit.
Picks a role (thug, tank, archer, mage, chief), swaps in the role's combat style (SKSE SetCombatStyle on the
leveled base, so no NPC record is edited and nothing stays changed after uninstall), and while the bandit fights
it keeps Combat Pathing Revolution's per-actor variables set for that role (CPR is off unless something sets them).
Tiers by level: thugs 25+ use a patient veteran style; archers reposition more often the higher their level.
Archer repositioning: when an archer sees the player kill a bandit while 2+ bandit archers are fighting, or hears
the player before the fight (combat state "searching"), it may sprint to a better spot (higher furniture/idle
marker further from the player, else straight away from the player). One archer at a time (SNE_RepositionLock).
An archer the player is already on top of (< 350 units) does not try: it is caught.
Off switch for A/B testing: console "set SNE_BanditTactics to 0" (restores the original style at the next update).
Needs SKSE (Get/SetCombatStyle, Cell.GetNthRef, mod events).}

Keyword Property KwThug Auto
Keyword Property KwTank Auto
Keyword Property KwArcher Auto
Keyword Property KwMage Auto
Keyword Property KwChief Auto
CombatStyle Property StyleThug Auto
CombatStyle Property StyleTank Auto
CombatStyle Property StyleArcher Auto
CombatStyle Property StyleMage Auto
CombatStyle Property StyleChief Auto
CombatStyle Property VanillaMissile Auto
CombatStyle Property VanillaMagic Auto
CombatStyle Property VanillaBoss1H Auto
CombatStyle Property VanillaBoss2H Auto
CombatStyle Property VanillaTank Auto
CombatStyle Property VanillaForswornBossMagic Auto
CombatStyle Property VanillaWarlock Auto
GlobalVariable Property TacticsOn Auto
CombatStyle Property StyleThugVeteran Auto
GlobalVariable Property ArchersInCombat Auto
GlobalVariable Property RepositionLock Auto
Actor Property PlayerRef Auto
Static Property XMarkerBase Auto
Spell Property MageMark Auto              ; turns on the glass-cannon entries of SNE_BanditPerk
Spell Property SpellFrostbite Auto
Spell Property SpellIceSpike Auto
Spell Property SpellFrostRune Auto
Spell Property SpellFireRune Auto
Spell Property SpellIceStorm Auto
Spell Property SpellChainLightning Auto
Spell Property SpellParalyzeShort Auto
Spell Property SpellFus Auto              ; VoiceUnrelentingForce1, a tier 4 mage's way out of melee
CombatStyle Property StyleBattlemage Auto
Faction Property BanditFaction Auto
Spell Property SpellHealOther Auto        ; support: heal an ally (projectile from the mage)
Spell Property SpellCloseWounds Auto      ; support: heal self
Spell Property SpellOakflesh Auto         ; support armor buffs by tier (cast with the ally as source)
Spell Property SpellStoneflesh Auto
Spell Property SpellIronflesh Auto
Spell Property SpellEbonyflesh Auto
Spell Property SpellFlameCloak Auto       ; support elemental buffs (melee allies only)
Spell Property SpellFrostCloak Auto
Spell Property SpellLightningCloak Auto
Spell Property SpellGrandHealing Auto

Float Property UpdateInterval = 3.0 AutoReadOnly
Int Property VeteranLevel = 25 AutoReadOnly
Float Property CaughtDistance = 350.0 AutoReadOnly     ; closer than this, an archer does not try to get away
Float Property LockSeconds = 6.0 AutoReadOnly          ; no other archer starts repositioning for this long
Float Property SprintSpeedBonus = 40.0 AutoReadOnly    ; SpeedMult while repositioning
Float Property MageUpdateInterval = 1.0 AutoReadOnly   ; mages watch for the player closing in
Float Property EscapeDistance = 260.0 AutoReadOnly     ; a tier 3+ mage tries to escape when the player is this close
Float Property SupportChance = 0.55 AutoReadOnly       ; share of bandit mages that are support (the rest battlemages)
Float Property SupportRange = 2000.0 AutoReadOnly      ; allies a support mage looks after
Float Property HealBelow = 0.6 AutoReadOnly            ; heal allies under this health fraction
Float Property StaggerCooldown = 1.5 AutoReadOnly

Int ROLE_THUG = 1
Int ROLE_TANK = 2
Int ROLE_ARCHER = 3
Int ROLE_MAGE = 4
Int ROLE_CHIEF = 5

Actor Me
Int Role
CombatStyle OriginalStyle
String RoleSource = "keyword"
Bool Done    ; the ability ends when the bandit dies; events that arrive after that must not touch the effect
Bool Counted          ; this archer is in SNE_ArchersInCombat
Bool Repositioning
Bool HeardTried       ; one "heard you" attempt per alert
Bool SpeedBoosted
Float NextEscapeTime  ; real time; reset when greater than now + cooldown (real time restarts each launch)
Bool IsSupport        ; mage kind, picked once in SetupMage
Armor AnbuMask        ; the Anbu Assassin's mask (naruto overhaul.esp, looked up at runtime)
Float NextSupportTime ; real time of the next support cast
Float NextStaggerTime ; real time; melee hits stagger a mage at most once per StaggerCooldown

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	Init()
	ApplyStyle()
	Debug.Trace("SNE bandit: start " + Me + " role " + RoleName() + " tier " + Tier() + " (level " + Me.GetLevel() + ") via " + RoleSource + ", original style " + OriginalStyle + ", now " + Me.GetLeveledActorBase().GetCombatStyle())
	If Me.IsInCombat()
		PushCPR()
		RegisterForSingleUpdate(Interval())
	EndIf
EndEvent

Function Init()
	; the first combat event can arrive before OnEffectStart has run (seen in the 2026-10-15 log)
	If Role != 0 || !Me
		Return
	EndIf
	ActorBase b = Me.GetLeveledActorBase()
	If b
		OriginalStyle = b.GetCombatStyle()
	EndIf
	Role = PickRole()
	If Role == ROLE_MAGE
		SetupMage()
	EndIf
EndFunction

Float Function Interval()
	If Role == ROLE_MAGE
		Return MageUpdateInterval
	EndIf
	Return UpdateInterval
EndFunction

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Done = True
	CountOut()
	SetSprint(False)
EndEvent

Event OnDying(Actor akKiller)
	CountOut()
	If akKiller == PlayerRef || (akKiller && akKiller.IsPlayerTeammate())
		Me.SendModEvent("SNE_BanditKilled")    ; archers who saw it may reposition (sent from the actor: this effect may already be gone)
		Debug.Trace("SNE bandit: " + RoleName() + " " + Me + " killed by " + akKiller + ", archers in combat " + (ArchersInCombat.GetValue() as Int))
	EndIf
	Done = True
EndEvent

Event OnLoad()
	If Done
		Return
	EndIf
	; base changes made through SKSE are not saved, so put the style back whenever the bandit loads in
	ApplyStyle()
	If AnbuMask
		EquipAnbuMask()
	EndIf
	Debug.Trace("SNE bandit: load " + Me + " role " + RoleName())
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
		If Role == ROLE_ARCHER
			CountIn()
			RegisterForModEvent("SNE_BanditKilled", "OnBanditKilled")
		EndIf
		ApplyStyle()
		PushCPR()
		Debug.Trace("SNE bandit: combat " + Me + " role " + RoleName() + " target " + akTarget + " style " + Me.GetLeveledActorBase().GetCombatStyle() + " CPR circling " + Me.GetAnimationVariableBool("CPR_EnableCircling") + " backoff " + Me.GetAnimationVariableFloat("CPR_BackoffChance") + " on " + (TacticsOn.GetValue() as Int))
		RegisterForSingleUpdate(Interval())
	ElseIf aeCombatState == 2
		; searching: heard or glimpsed the player, no fight yet
		If Role == ROLE_ARCHER && !HeardTried && !Repositioning && akTarget == PlayerRef && TacticsOn.GetValue() >= 0.5
			HeardTried = True
			If Utility.RandomFloat() < HeardChance()
				TryReposition("heard you")
			Else
				Debug.Trace("SNE bandit: archer " + Me + " heard you, stayed (tier " + Tier() + ")")
			EndIf
		ElseIf Role == ROLE_MAGE && IsSupport && !HeardTried && akTarget == PlayerRef && TacticsOn.GetValue() >= 0.5
			HeardTried = True
			If Utility.RandomFloat() < SenseChance()
				MageSense()
			Else
				Debug.Trace("SNE bandit: medical ninja " + Me + " heard you, no mage sense (tier " + Tier() + ")")
			EndIf
		EndIf
	ElseIf aeCombatState == 0
		UnregisterForUpdate()
		If Role == ROLE_ARCHER
			CountOut()
			UnregisterForModEvent("SNE_BanditKilled")
		EndIf
		Debug.Trace("SNE bandit: combat end " + Me + " role " + RoleName() + " dead " + Me.IsDead() + " health " + Me.GetActorValuePercentage("Health"))
	EndIf
EndEvent

Event OnUpdate()
	If Done || !Me || Me.IsDead() || !Me.IsInCombat()
		Return
	EndIf
	ApplyStyle()
	PushCPR()    ; moveset idles can rewrite the CPR variables, so keep re-pushing ours
	If Role == ROLE_MAGE
		CheckEscape()
		If IsSupport && !Done
			SupportTick()
		EndIf
	EndIf
	If !Done
		RegisterForSingleUpdate(Interval())
	EndIf
EndEvent

; ---------- bandit mages ----------
; Two kinds (2026-10-15): battlemages fight directly (glass cannon: tier attack spells, spells x1.3, damage taken
; x1.25 through the mage mark + SNE_BanditPerk); support mages stay at the back healing and buffing their allies,
; and have "mage sense" (they hear you -> alert everyone, buff the group, run to the back).
; Both: a melee hit interrupts their cast and staggers them; tier 3+ escape when cornered (CheckEscape).
Function SetupMage()
	If !Me.HasSpell(MageMark)
		Me.AddSpell(MageMark, False)
	EndIf
	IsSupport = (ActorSeed() % 100) < ((SupportChance * 100.0) as Int)    ; same NPC, same kind, even after reloads
	Int t = Tier()
	If IsSupport
		GiveSpell(SpellFrostRune)    ; covers its retreat
	Else
		; battlemage tier spells: 1 Frostbite | 2 + Ice Spike, Frost Rune | 3 + Ice Storm, Fire Rune | 4 + Chain Lightning, Paralysis Bolt (3 s)
		GiveSpell(SpellFrostbite)
		If t >= 2
			GiveSpell(SpellIceSpike)
			GiveSpell(SpellFrostRune)
		EndIf
		If t >= 3
			GiveSpell(SpellIceStorm)
			GiveSpell(SpellFireRune)
		EndIf
		If t >= 4
			GiveSpell(SpellChainLightning)
			GiveSpell(SpellParalyzeShort)
		EndIf
	EndIf
	If IsSupport
		Me.SetDisplayName("Rogue Medical Ninja", True)
	Else
		Me.SetDisplayName("Anbu Assassin", True)
		EquipAnbuMask()
	EndIf
	Debug.Trace("SNE bandit: mage " + Me + " is a " + RoleName() + ", tier " + t + " (mark " + Me.HasSpell(MageMark) + ", mask " + AnbuMask + ")")
EndFunction

; Anbu Assassins wear a random Anbu mask from the Naruto overhaul: Haku, Raiga or Jutsu Master, mask or mask + hood.
; Unenchanted versions; GetFormFromFile, so the Naruto plugin is not a master (no mask if it is missing).
Int Function ActorSeed()
	Int id = Me.GetFormID()
	If id < 0
		id = -(id + 1)    ; FF... runtime refs are negative as Int
	EndIf
	Return id
EndFunction

Function EquipAnbuMask()
	If !AnbuMask
		Int[] ids = new Int[6]
		ids[0] = 0x0D94B9    ; A0MaskHaku
		ids[1] = 0x0D94BF    ; A0MaskRaiga
		ids[2] = 0x0D94BE    ; A0MaskJutsuMaster
		ids[3] = 0x0D94BA    ; A0MaskHoodHaku
		ids[4] = 0x0D94BC    ; A0MaskHoodRaiga
		ids[5] = 0x0D94BB    ; A0MaskHoodJutsuMaster
		AnbuMask = Game.GetFormFromFile(ids[(ActorSeed() / 7) % 6], "naruto overhaul.esp") as Armor
		If !AnbuMask
			Return
		EndIf
		Me.AddItem(AnbuMask, 1, True)
	EndIf
	If !Me.IsEquipped(AnbuMask)
		Me.EquipItem(AnbuMask, False, True)
	EndIf
EndFunction

; ---------- support mages ----------
Float Function SenseChance()
	Int t = Tier()
	If t == 1
		Return 0.5
	ElseIf t == 2
		Return 0.7
	ElseIf t == 3
		Return 0.85
	EndIf
	Return 1.0
EndFunction

Float Function SupportCooldown()    ; seconds between support casts; killing the mage first is the counter
	Int t = Tier()
	If t == 1
		Return 4.0
	ElseIf t == 2
		Return 3.0
	ElseIf t == 3
		Return 2.5
	EndIf
	Return 2.0
EndFunction

Spell Function FleshSpell()
	Int t = Tier()
	If t == 1
		Return SpellOakflesh
	ElseIf t == 2
		Return SpellStoneflesh
	ElseIf t == 3
		Return SpellIronflesh
	EndIf
	Return SpellEbonyflesh
EndFunction

Spell Function CloakSpell()         ; tier 2 fire; tier 3 fire or frost; tier 4 any of the three
	Int t = Tier()
	If t < 2
		Return None
	ElseIf t == 2
		Return SpellFlameCloak
	EndIf
	Int pick = Utility.RandomInt(0, t - 2)
	If pick == 0
		Return SpellFlameCloak
	ElseIf pick == 1
		Return SpellFrostCloak
	EndIf
	Return SpellLightningCloak
EndFunction

Bool Function HasFlesh(Actor a)
	Return a.HasMagicEffect(SpellOakflesh.GetNthEffectMagicEffect(0)) || a.HasMagicEffect(SpellStoneflesh.GetNthEffectMagicEffect(0)) || a.HasMagicEffect(SpellIronflesh.GetNthEffectMagicEffect(0)) || a.HasMagicEffect(SpellEbonyflesh.GetNthEffectMagicEffect(0))
EndFunction

Bool Function HasCloak(Actor a)
	Return a.HasMagicEffect(SpellFlameCloak.GetNthEffectMagicEffect(0)) || a.HasMagicEffect(SpellFrostCloak.GetNthEffectMagicEffect(0)) || a.HasMagicEffect(SpellLightningCloak.GetNthEffectMagicEffect(0))
EndFunction

Bool Function IsMeleeFighter(Actor a)
	Int r = a.GetEquippedItemType(1)
	Return r <= 6    ; fists (0) or a melee weapon (1-6)
EndFunction

Bool Function IsAlly(Actor a)
	Return a && a != Me && !a.IsDead() && !a.IsDisabled() && a.IsInFaction(BanditFaction) && !a.IsPlayerTeammate() && Me.GetDistance(a) < SupportRange
EndFunction

; one support action per cooldown: heal self < 50% -> heal the most hurt ally -> armor an unarmored ally ->
; elemental cloak on a melee ally -> armor self
Function SupportTick()
	Float now = Utility.GetCurrentRealTime()
	If NextSupportTime > now + 30.0
		NextSupportTime = 0.0    ; stale value from an earlier launch
	EndIf
	If now < NextSupportTime || Repositioning || TacticsOn.GetValue() < 0.5
		Return
	EndIf
	NextSupportTime = now + SupportCooldown()
	If Me.GetActorValuePercentage("Health") < 0.5
		SpellCloseWounds.Cast(Me, Me)
		Debug.Trace("SNE bandit: medical ninja " + Me + " healed itself")
		Return
	EndIf
	Actor hurt = None
	Float hurtPct = HealBelow
	Int hurtCount = 0
	Actor needArmor = None
	Actor needCloak = None
	Spell cloak = CloakSpell()
	Cell c = Me.GetParentCell()
	If c
		Int n = c.GetNumRefs(43)    ; actors
		If n > 60
			n = 60
		EndIf
		Int i = 0
		While i < n
			Actor a = c.GetNthRef(i, 43) as Actor
			If IsAlly(a)
				Float pct = a.GetActorValuePercentage("Health")
				If pct < HealBelow
					hurtCount += 1
				EndIf
				If pct < hurtPct
					hurtPct = pct
					hurt = a
				EndIf
				If !needArmor && a.IsInCombat() && !HasFlesh(a)
					needArmor = a
				EndIf
				If cloak && !needCloak && a.IsInCombat() && IsMeleeFighter(a) && !HasCloak(a)
					needCloak = a
				EndIf
			EndIf
			i += 1
		EndWhile
	EndIf
	If hurt
		If Tier() >= 4 && hurtCount >= 2 && Me.GetDistance(hurt) < 400.0
			SpellGrandHealing.Cast(Me, Me)
			Debug.Trace("SNE bandit: medical ninja " + Me + " Grand Healing (" + hurtCount + " hurt)")
		Else
			If !hurt.IsInKillMove() && !hurt.IsBleedingOut() && hurt.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
				SpellHealOther.Cast(Me, hurt)
			EndIf
			Debug.Trace("SNE bandit: medical ninja " + Me + " healed " + hurt + " at " + ((hurtPct * 100.0) as Int) + "%")
		EndIf
	ElseIf needArmor
		FleshSpell().Cast(needArmor, needArmor)
		Debug.Trace("SNE bandit: medical ninja " + Me + " armored " + needArmor + " (" + FleshSpell() + ")")
	ElseIf needCloak
		cloak.Cast(needCloak, needCloak)
		Debug.Trace("SNE bandit: medical ninja " + Me + " gave " + needCloak + " " + cloak)
	ElseIf !HasFlesh(Me)
		FleshSpell().Cast(Me, Me)
	Else
		NextSupportTime = now + 0.5    ; nothing to do: look again soon
	EndIf
EndFunction

; heard you before the fight: raise the alarm, buff self and every ally in range, then run to the back
Function MageSense()
	Debug.Trace("SNE bandit: medical ninja " + Me + " MAGE SENSE (tier " + Tier() + ")")
	PlayerRef.CreateDetectionEvent(PlayerRef, 100)    ; loud noise where you are: nearby bandits come looking
	Spell flesh = FleshSpell()
	flesh.Cast(Me, Me)
	Int buffed = 0
	Cell c = Me.GetParentCell()
	If c
		Int n = c.GetNumRefs(43)
		If n > 60
			n = 60
		EndIf
		Int i = 0
		While i < n
			Actor a = c.GetNthRef(i, 43) as Actor
			If IsAlly(a)
				If !HasFlesh(a)
					flesh.Cast(a, a)
				EndIf
				Spell cloak = CloakSpell()
				If cloak && IsMeleeFighter(a) && !HasCloak(a)
					cloak.Cast(a, a)
				EndIf
				buffed += 1
				Utility.Wait(0.2)
			EndIf
			i += 1
		EndWhile
	EndIf
	Debug.Trace("SNE bandit: medical ninja " + Me + " alerted and buffed " + buffed + " allies")
	TryReposition("mage sense")
EndFunction

Function GiveSpell(Spell s)
	If s && !Me.HasSpell(s)
		Me.AddSpell(s, False)
	EndIf
EndFunction

; Melee is the counter: any melee hit interrupts the cast, and an unblocked one staggers the mage.
Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If Done || Role != ROLE_MAGE || akProjectile || TacticsOn.GetValue() < 0.5
		Return
	EndIf
	Weapon w = akSource as Weapon
	If !w
		Return    ; spells, potions, explosions
	EndIf
	Int wt = w.GetWeaponType()
	If wt == 7 || wt == 9
		Return    ; bow / crossbow
	EndIf
	Bool casting = Me.GetAnimationVariableBool("IsCastingRight") || Me.GetAnimationVariableBool("IsCastingLeft")
	Me.InterruptCast()
	If abHitBlocked || (!casting && !abPowerAttack && !abBashAttack)
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If NextStaggerTime > now + StaggerCooldown + 1.0
		NextStaggerTime = 0.0
	EndIf
	If now < NextStaggerTime
		Return
	EndIf
	NextStaggerTime = now + StaggerCooldown
	Me.SetAnimationVariableFloat("staggerMagnitude", 0.4)
	Debug.SendAnimationEvent(Me, "staggerStart")
	Debug.Trace("SNE bandit: " + RoleName() + " " + Me + " hit in melee by " + akAggressor + " (casting " + casting + ", power " + abPowerAttack + "): cast broken, staggered")
EndEvent

; tier 3+: when the player gets into melee range, get out: tier 3 blinks to a perch; tier 4 also uses Fus (50/50).
; Cooldown 25 s (tier 3) / 15 s (tier 4), so a fast melee fighter still gets the mage.
Function CheckEscape()
	Int t = Tier()
	If t < 3 || Repositioning || Me.GetCombatTarget() != PlayerRef || TacticsOn.GetValue() < 0.5
		Return
	EndIf
	If Me.GetDistance(PlayerRef) > EscapeDistance
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	Float cooldown = 25.0
	If t >= 4
		cooldown = 15.0
	EndIf
	If NextEscapeTime > now + cooldown + 1.0
		NextEscapeTime = 0.0    ; stale value from an earlier launch
	EndIf
	If now < NextEscapeTime
		Return
	EndIf
	NextEscapeTime = now + cooldown
	If t >= 4 && Utility.RandomFloat() < 0.5
		Fus()
	ElseIf !Blink()
		If t >= 4
			Fus()
		Else
			Debug.Trace("SNE bandit: mage " + Me + " cornered, no perch to blink to")
		EndIf
	EndIf
EndFunction

Function Fus()
	SpellFus.Cast(Me, PlayerRef)
	Debug.Trace("SNE bandit: mage " + Me + " used Fus to push you away")
EndFunction

Bool Function Blink()
	ObjectReference spot = FindPerch()
	If !spot
		Return False
	EndIf
	Repositioning = True
	Me.SetAlpha(0.0, True)
	Utility.Wait(0.35)
	Me.MoveTo(spot)
	Me.SetAlpha(1.0, True)
	Repositioning = False
	Debug.Trace("SNE bandit: mage " + Me + " blinked to " + spot + ", now " + (Me.GetDistance(PlayerRef) as Int) + " from you")
	Return True
EndFunction

; ---------- tiers ----------
Int Function Tier()
	Int lvl = Me.GetLevel()
	If lvl < 10
		Return 1
	ElseIf lvl < VeteranLevel
		Return 2
	ElseIf lvl < 40
		Return 3
	EndIf
	Return 4
EndFunction

Float Function KillChance()     ; saw the player kill a bandit
	Int t = Tier()
	If t == 1
		Return 0.25
	ElseIf t == 2
		Return 0.45
	ElseIf t == 3
		Return 0.65
	EndIf
	Return 0.85
EndFunction

Float Function HeardChance()    ; heard the player before the fight
	Int t = Tier()
	If t == 1
		Return 0.2
	ElseIf t == 2
		Return 0.35
	ElseIf t == 3
		Return 0.55
	EndIf
	Return 0.75
EndFunction

; ---------- archer repositioning ----------
Function CountIn()
	If !Counted
		Counted = True
		ArchersInCombat.Mod(1.0)
	EndIf
EndFunction

Function CountOut()
	If Counted
		Counted = False
		Float v = ArchersInCombat.GetValue() - 1.0
		If v < 0.0
			v = 0.0
		EndIf
		ArchersInCombat.SetValue(v)
	EndIf
EndFunction

Event OnBanditKilled(String eventName, String strArg, Float numArg, Form sender)
	If Done || Role != ROLE_ARCHER || Repositioning || !Me || Me.IsDead() || !Me.IsInCombat() || TacticsOn.GetValue() < 0.5
		Return
	EndIf
	If ArchersInCombat.GetValue() < 2.0
		Debug.Trace("SNE bandit: archer " + Me + " saw a kill, stayed: only " + (ArchersInCombat.GetValue() as Int) + " archer(s) fighting")
		Return
	EndIf
	If !Me.HasLOS(PlayerRef)
		Debug.Trace("SNE bandit: archer " + Me + " missed the kill (no line of sight to you)")
		Return
	EndIf
	If Utility.RandomFloat() >= KillChance()
		Debug.Trace("SNE bandit: archer " + Me + " saw a kill, stayed (tier " + Tier() + ")")
		Return
	EndIf
	Utility.Wait(Utility.RandomFloat(0.1, 0.6))    ; spread the archers out so the lock picks one
	TryReposition("saw a kill")
EndEvent

Function TryReposition(String reason)
	If Done || Repositioning || Me.IsDead()
		Return
	EndIf
	Float dist = Me.GetDistance(PlayerRef)
	If dist < CaughtDistance
		Debug.Trace("SNE bandit: " + RoleName() + " " + Me + " " + reason + " but you are on top of it (" + (dist as Int) + "), caught")
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	Float lock = RepositionLock.GetValue()
	If lock > now + LockSeconds + 1.0
		lock = 0.0    ; real time restarts each launch: a saved lock from an earlier session is stale
	EndIf
	If lock > now
		Return    ; another archer is moving
	EndIf
	RepositionLock.SetValue(now + LockSeconds)
	Repositioning = True

	ObjectReference spot = FindPerch()
	Bool madeMarker = False
	If !spot
		spot = AwayMarker()
		madeMarker = True
	EndIf
	Float startZ = Me.GetPositionZ()
	Bool inCombat = Me.IsInCombat()
	Debug.Trace("SNE bandit: " + RoleName() + " " + Me + " " + reason + ", tier " + Tier() + ", sprinting to " + spot + " (perch " + !madeMarker + ", " + (Me.GetDistance(spot) as Int) + " away, " + ((spot.GetPositionZ() - PlayerRef.GetPositionZ()) as Int) + " above you)")
	SetSprint(True)
	If inCombat
		Me.StopCombat()    ; combat AI would override the path
	EndIf
	Bool reached = Me.PathToReference(spot, 1.0)
	SetSprint(False)
	If inCombat && !Me.IsDead()
		Me.StartCombat(PlayerRef)
	EndIf
	Debug.Trace("SNE bandit: " + RoleName() + " " + Me + " reposition reached " + reached + ", now " + (Me.GetDistance(PlayerRef) as Int) + " from you, climbed " + ((Me.GetPositionZ() - startZ) as Int))
	If madeMarker
		spot.Delete()
	EndIf
	Repositioning = False
EndFunction

; best furniture or idle marker in the archer's cell: higher than the player, further from the player than the archer,
; within a short sprint. Cover cannot be tested from Papyrus, so height and distance stand in for "a better position".
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
	types[0] = 40    ; furniture (chairs, benches, archer perches)
	types[1] = 47    ; idle markers
	Int t = 0
	While t < 2
		Int n = c.GetNumRefs(types[t])
		If n > 80
			n = 80
		EndIf
		Int i = 0
		While i < n
			ObjectReference r = c.GetNthRef(i, types[t])
			If r && !r.IsDisabled()
				Float dA = Me.GetDistance(r)
				Float dP = PlayerRef.GetDistance(r)
				If dA > 250.0 && dA < 1800.0 && dP > 700.0 && dP > myDist + 200.0
					Float score = (r.GetPositionZ() - pz) * 2.0 + dP * 0.5 - dA * 0.3
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

ObjectReference Function AwayMarker()
	Float dx = Me.GetPositionX() - PlayerRef.GetPositionX()
	Float dy = Me.GetPositionY() - PlayerRef.GetPositionY()
	Float len = Math.sqrt(dx * dx + dy * dy)
	If len < 1.0
		dx = 1.0
		dy = 0.0
		len = 1.0
	EndIf
	ObjectReference m = Me.PlaceAtMe(XMarkerBase)
	m.SetPosition(Me.GetPositionX() + dx / len * 900.0, Me.GetPositionY() + dy / len * 900.0, Me.GetPositionZ())
	Return m
EndFunction

Function SetSprint(Bool on)
	If on == SpeedBoosted || !Me
		Return
	EndIf
	SpeedBoosted = on
	If on
		Me.ModActorValue("SpeedMult", SprintSpeedBonus)
	Else
		Me.ModActorValue("SpeedMult", -SprintSpeedBonus)
	EndIf
	Me.ModActorValue("CarryWeight", 0.1)    ; a SpeedMult change only takes effect after a carry weight change
	Me.ModActorValue("CarryWeight", -0.1)
EndFunction

Int Function PickRole()
	If Me.HasKeyword(KwChief)
		Return ROLE_CHIEF
	ElseIf Me.HasKeyword(KwMage)
		Return ROLE_MAGE
	ElseIf Me.HasKeyword(KwArcher)
		Return ROLE_ARCHER
	ElseIf Me.HasKeyword(KwTank)
		Return ROLE_TANK
	EndIf
	; no specific role keyword (SPID did not see the style through the NPC's template): use the vanilla style.
	; The thug keyword is SPID's catch-all, so it is checked only after this (a csHumanMagic bandit got it on 2026-10-15)
	RoleSource = "style"
	If OriginalStyle == VanillaBoss1H || OriginalStyle == VanillaBoss2H
		Return ROLE_CHIEF
	ElseIf OriginalStyle == VanillaMagic || OriginalStyle == VanillaForswornBossMagic || OriginalStyle == VanillaWarlock
		Return ROLE_MAGE
	ElseIf OriginalStyle == VanillaMissile
		Return ROLE_ARCHER
	ElseIf OriginalStyle == VanillaTank
		Return ROLE_TANK
	EndIf
	If Me.HasKeyword(KwThug)
		RoleSource = "keyword"
		Return ROLE_THUG
	EndIf
	; then the gear: 7 bow, 12 crossbow, 9 spell, 10 shield (left hand)
	RoleSource = "gear"
	Int right = Me.GetEquippedItemType(1)
	If right == 7 || right == 12
		Return ROLE_ARCHER
	ElseIf right == 9
		Return ROLE_MAGE
	ElseIf Me.GetEquippedItemType(0) == 10
		Return ROLE_TANK
	EndIf
	Return ROLE_THUG
EndFunction

String Function RoleName()
	If Role == ROLE_CHIEF
		Return "chief"
	ElseIf Role == ROLE_MAGE && IsSupport
		Return "medical ninja"
	ElseIf Role == ROLE_MAGE
		Return "anbu assassin"
	ElseIf Role == ROLE_ARCHER
		Return "archer"
	ElseIf Role == ROLE_TANK
		Return "tank"
	EndIf
	Return "thug"
EndFunction

CombatStyle Function RoleStyle()
	If Role == ROLE_CHIEF
		Return StyleChief
	ElseIf Role == ROLE_MAGE && IsSupport
		Return StyleMage
	ElseIf Role == ROLE_MAGE
		Return StyleBattlemage
	ElseIf Role == ROLE_ARCHER
		Return StyleArcher
	ElseIf Role == ROLE_TANK
		Return StyleTank
	ElseIf Me.GetLevel() >= VeteranLevel
		Return StyleThugVeteran
	EndIf
	Return StyleThug
EndFunction

Function ApplyStyle()
	If !Me
		Return
	EndIf
	ActorBase b = Me.GetLeveledActorBase()
	If !b
		Return
	EndIf
	CombatStyle want = RoleStyle()
	If TacticsOn.GetValue() < 0.5 || Me.IsPlayerTeammate()
		want = OriginalStyle    ; switched off, or a bandit who became a follower: leave them vanilla
	EndIf
	If want && b.GetCombatStyle() != want
		b.SetCombatStyle(want)
	EndIf
EndFunction

; Combat Pathing Revolution: per-actor graph variables (they only exist while the actor is in combat).
; Defaults and meanings: Combat Pathing Revolution/SKSE/Plugins/BehaviorDataInjector/MaxsuCPR_BDI.json
Function PushCPR()
	If TacticsOn.GetValue() < 0.5 || Me.IsPlayerTeammate() || Repositioning
		Return
	EndIf
	If Role == ROLE_THUG && Me.GetLevel() >= VeteranLevel
		; veteran: wide circling to flank; backs off a little (0.4 -> 0.2 on 2026-10-15: dodged power attacks too well)
		SetCPR(True, 0.2, 0.8, True, 150.0, 800.0, 60.0, 120.0, False, 0.0, 0.0, 0.0, 0.0)
	ElseIf Role == ROLE_THUG
		; untrained: wide circling (60-120 deg) so a pair ends up on both your sides, rarely gives ground
		SetCPR(True, 0.15, 0.8, True, 120.0, 700.0, 60.0, 120.0, False, 0.0, 0.0, 0.0, 0.0)
	ElseIf Role == ROLE_TANK
		; holds the front: little circling, rarely gives ground
		SetCPR(True, 0.1, 0.9, True, 90.0, 300.0, 15.0, 35.0, False, 0.0, 0.0, 0.0, 0.0)
	ElseIf Role == ROLE_ARCHER
		; if you reach them: back off and fall back behind the others, then shoot again
		SetCPR(True, 0.85, 1.0, True, 300.0, 1200.0, 30.0, 60.0, True, 300.0, 700.0, 0.5, 1.0)
	ElseIf Role == ROLE_MAGE && IsSupport
		; support: always backs off, keeps far behind, falls back quickly
		SetCPR(True, 1.0, 1.0, True, 900.0, 1600.0, 20.0, 45.0, True, 800.0, 1500.0, 0.2, 0.5)
	ElseIf Role == ROLE_MAGE
		SetCPR(True, 0.9, 1.0, True, 400.0, 1400.0, 30.0, 60.0, True, 400.0, 900.0, 0.3, 0.8)
	Else
		; chief: tight, patient circling; rarely backs off (0.15 -> 0.1 on 2026-10-15)
		SetCPR(True, 0.1, 0.85, True, 90.0, 350.0, 30.0, 60.0, False, 0.0, 0.0, 0.0, 0.0)
	EndIf
EndFunction

Function SetCPR(Bool backoff, Float backoffChance, Float backoffDistMult, Bool circle, Float circleMin, Float circleMax, Float angleMin, Float angleMax, Bool fallback, Float fallMin, Float fallMax, Float waitMin, Float waitMax)
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
		Me.SetAnimationVariableFloat("CPR_FallbackDistMin", fallMin)
		Me.SetAnimationVariableFloat("CPR_FallbackDistMax", fallMax)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", waitMin)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", waitMax)
	EndIf
EndFunction

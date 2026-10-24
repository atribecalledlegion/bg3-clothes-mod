Scriptname CTKD_QuestScript extends Quest
{Serana Taekwondo Toggle. Holds the state and does the work for the toggle power.
On: Serana's weapons go into a hidden chest, her unarmed damage is raised from her best sword or dagger,
and her AI becomes an aggressive brawler (combat style + no CPR circling/backing off), so she fights with
the Taekwondo moveset. Off: everything is put back.
Juri Mastery (0-100) grows with every Taekwondo hit she lands and unlocks Juri Han's abilities.
Needs SKSE (GetNumItems, GetNthForm, GetBaseDamage, GetWeaponType, Get/SetCombatStyle).
Supers use the Juri animations from Cheeky Girl Taekwondo (SFJuriMoves.esp), copied into her MCO power
attack slots 9 (Sakkai Fuhazan) and 10 (Feng Shui Engine).}

Actor Property PlayerRef Auto
Spell Property TogglePower Auto
Container Property StorageBase Auto
{Empty, non-respawning container. One disabled copy is placed to hold Serana's weapons.}
GlobalVariable Property PowerMult Auto
{CTKD_UnarmedPowerMult: multiplier on her blade damage for Taekwondo (default 3).}
CombatStyle Property BrawlerStyle Auto
{CTKD_JuriStyle: aggressive unarmed fighter, magic only as a fallback. Swapped in while in Taekwondo mode.}
GlobalVariable Property SetMasteryGlobal Auto
{CTKD_SetMastery: test hook. 'set CTKD_SetMastery to <0-100>' in the console sets her rank; -1 = idle.}
Float Property UpkeepSeconds = 2.0 Auto
Float Property ComboReach = 300.0 AutoReadOnly
{Combo driver: keep chaining while her target is this close (units).}
Float Property FinisherStaminaPct = 0.15 AutoReadOnly
{Combo driver: the power-attack finisher needs this much stamina left.}
Float Property OpenerHeavyChance = 0.35 AutoReadOnly
{Combo driver: chance that the first follow-up of a string is the heavy string instead of the light one.}

; --- Juri Mastery tuning ---
Float Property HitReach = 170.0 AutoReadOnly
{A HitFrame counts as a landed hit when her target is this close and in front of her.}
Float Property RankCostBase = 15.0 AutoReadOnly
Float Property RankCostStep = 0.3 AutoReadOnly
{Hits needed for the next rank = base + step x rank (about 3000 hits for rank 100).}
Float Property MasteryDamageMax = 0.5 AutoReadOnly
{Unarmed damage bonus at rank 100, on top of her damage formula (+50%).}
Float Property SakkaiChance = 0.5 AutoReadOnly
{Chance per upkeep tick to queue Sakkai Fuhazan when it is ready.}
Float Property SmallTargetHeight = 75.0 AutoReadOnly
{Mudcrabs, skeevers, foxes...: Juri's kicks travel over targets shorter than this, so a strike in range that
does no damage is applied by the script instead.}

ObjectReference Storage
Float LastComboTime = 0.0
Float LastWinOpenTime = 0.0
Bool TaekwondoOn = false
Float UnarmedBonus = 0.0
Weapon BestWeapon
CombatStyle SavedStyle
Float BestDamage = 0.0

Float MasteryPoints = 0.0
Int Mastery = 0
Int FuhaStock = 0
Float FengShuiTime = 0.0
Int PendingSuper = 0
Bool WasFighting = False
Float AppliedSpeed = 0.0
Float AppliedArmor = 0.0
Float AppliedHealth = 0.0
Float AppliedStaminaRate = 0.0

Event OnInit()
	PlayerRef.AddSpell(TogglePower)
EndEvent

Actor Function Serana()
	Return Game.GetFormFromFile(0x00002B74, "Dawnguard.esm") as Actor
EndFunction

Function Toggle()
	Actor s = Serana()
	If !s || s.IsDead() || s.IsDisabled()
		Debug.Notification("Serana isn't available.")
		Return
	EndIf
	WOTW_QuestScript witch = Witch()
	If TaekwondoOn
		WeaponsOn(s)
	Else
		If witch && witch.IsOn()
			witch.Toggle()    ; one mode at a time: the Witch of the Wilds puts the staff away first
		EndIf
		SNJ_QuestScript ninja = Game.GetFormFromFile(0x00000800, "Serana Ninja Mode.esp") as SNJ_QuestScript
		If ninja && ninja.IsOn()
			ninja.Toggle()    ; and Ninja Mode its Kusanagi
		EndIf
		TaekwondoStance(s)
	EndIf
	If witch
		witch.Wake()    ; its dodge reflex also runs in Taekwondo mode
	EndIf
EndFunction

Bool Function IsOn()
	Return TaekwondoOn
EndFunction

; Witch of the Wilds.esp (optional): the staff mode, and the dodge reflex both modes share.
WOTW_QuestScript Function Witch()
	Return Game.GetFormFromFile(0x00000800, "Witch of the Wilds.esp") as WOTW_QuestScript
EndFunction

Function TaekwondoStance(Actor s)
	If !Storage
		Storage = PlayerRef.PlaceAtMe(StorageBase, 1, True, True)
	EndIf
	; best one-handed blade (sword = 1, dagger = 2) decides her unarmed damage
	BestDamage = 0.0
	BestWeapon = None
	Int i = s.GetNumItems()
	While i > 0
		i -= 1
		Weapon w = s.GetNthForm(i) as Weapon
		If w
			Int wtype = w.GetWeaponType()
			If (wtype == 1 || wtype == 2) && w.GetBaseDamage() > BestDamage
				BestDamage = w.GetBaseDamage()
				BestWeapon = w
			EndIf
			s.RemoveItem(w, s.GetItemCount(w), True, Storage)
		EndIf
	EndWhile
	TaekwondoOn = True
	RefreshDamage(s)
	Aggressive(s)
	RegisterForSingleUpdate(UpkeepSeconds)
	Debug.Notification("Serana: Taekwondo. Unarmed damage " + (s.GetActorValue("UnarmedDamage") as Int) + ", Juri Mastery " + Mastery + ".")
EndFunction

; Matching the blade's base damage alone left her weak: her sword/dagger moveset (Daughter of Coldharbour)
; adds its own damage, and several Juri strikes deal reduced damage per hit (fast multi-hit jabs).
; So: blade damage x One-Handed bonus x PowerMult, never below 10 + 1.5 x her level, then + Juri Mastery bonus.
; PowerMult is a global, tunable in game: set CTKD_UnarmedPowerMult to <n>, then recast the power twice.
Function RefreshDamage(Actor s)
	If UnarmedBonus != 0.0
		s.ModActorValue("UnarmedDamage", -UnarmedBonus)
		UnarmedBonus = 0.0
	EndIf
	If BestDamage <= 0.0 && BestWeapon
		BestDamage = BestWeapon.GetBaseDamage()    ; saves from before BestDamage was stored
	EndIf
	Float target = 0.0
	If BestDamage > 0.0
		target = BestDamage * (1.0 + s.GetActorValue("OneHanded") * 0.005) * PowerMult.GetValue()
	EndIf
	Float floor = 10.0 + 1.5 * s.GetLevel()
	If target < floor
		target = floor
	EndIf
	target = target * (1.0 + MasteryDamageMax * Mastery / 100.0)
	Float current = s.GetActorValue("UnarmedDamage")
	If target > current
		UnarmedBonus = target - current
		s.ModActorValue("UnarmedDamage", UnarmedBonus)
	EndIf
EndFunction

; Taekwondo AI: her own combat style is a caster's (magic 10, melee 0.5), so swap in the Juri style, and
; tell Combat Pathing Revolution not to circle, back off or fall back (SCAR's fist-draw animation turns those on).
; Base-form combat style changes are not saved, so this is re-applied every few seconds while the mode is on.
Function Aggressive(Actor s)
	ActorBase b = s.GetActorBase()
	CombatStyle cur = b.GetCombatStyle()
	If cur != BrawlerStyle
		If !SavedStyle
			SavedStyle = cur    ; keep her real style even if an older Taekwondo style is still applied
		EndIf
		b.SetCombatStyle(BrawlerStyle)
	EndIf
	If !s.Is3DLoaded() || !s.IsWeaponDrawn()
		Return    ; the CPR variables and MCO events only exist while she is fighting (errors in the log otherwise)
	EndIf
	s.SetAnimationVariableBool("CPR_EnableBackoff", True)
	s.SetAnimationVariableFloat("CPR_BackoffChance", 0.0)
	s.SetAnimationVariableBool("CPR_EnableCircling", True)
	s.SetAnimationVariableFloat("CPR_CirclingDistMin", 0.0)
	s.SetAnimationVariableFloat("CPR_CirclingDistMax", 1.0)
	s.SetAnimationVariableBool("CPR_EnableFallback", True)
	s.SetAnimationVariableFloat("CPR_FallbackDistMin", 0.0)
	s.SetAnimationVariableFloat("CPR_FallbackDistMax", 1.0)
	s.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", 0.0)
	s.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", 0.0)
	; combo driver + mastery (registrations drop when her 3D reloads, so they are renewed here)
	RegisterForAnimationEvent(s, "MCO_WinOpen")
	RegisterForAnimationEvent(s, "MCO_PowerWinOpen")
	RegisterForAnimationEvent(s, "SCAR_ComboStart")
	RegisterForAnimationEvent(s, "HitFrame")
EndFunction

; Combo driver. SCAR only ever reads one follow-up (the power attack) from her Juri attack clips, so she
; stopped after a hit or two. Instead, when a Juri attack opens its MCO combo window, send the next attack
; ourselves: attacks 1-5 chain into the next light attack, attack 6 (power window only) into the finisher.
Bool Function TargetInReach(Actor s)
	Actor t = s.GetCombatTarget()
	Return t && !t.IsDead() && s.GetDistance(t) <= ComboReach && Math.Abs(s.GetHeadingAngle(t)) < 90.0
EndFunction

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If !TaekwondoOn
		Return
	EndIf
	Actor s = akSource as Actor
	If !s || !s.IsInCombat() || s.IsDead()
		Return
	EndIf
	If asEventName == "HitFrame"
		OnStrike(s)
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	; real time restarts at 0 every game launch, but these are saved: a value from an earlier session would
	; block every combo until the clock caught up
	If LastComboTime > now
		LastComboTime = 0.0
	EndIf
	If LastWinOpenTime > now
		LastWinOpenTime = 0.0
	EndIf
	If asEventName == "MCO_WinOpen" || asEventName == "SCAR_ComboStart"
		LastWinOpenTime = now
		If now - LastComboTime < 0.25 || !TargetInReach(s)
			Return    ; already sent for this window (both events fire together), or nobody to hit
		EndIf
		; the first window of a string (her up-kick opener, or jab 1; both lead to light 2 / heavy 2)
		; sometimes branches into the heavy string 2-3-4 instead of the light string
		Bool opener = now - LastComboTime > 1.5
		LastComboTime = now
		If s.GetActorValuePercentage("Stamina") >= FinisherStaminaPct && FireSuper(s)
			Return
		EndIf
		If opener && Utility.RandomFloat() < OpenerHeavyChance && s.GetActorValuePercentage("Stamina") >= FinisherStaminaPct
			Debug.SendAnimationEvent(s, "attackPowerStartForwardH2HRightHand")
			Debug.Trace("CTKD combo: " + asEventName + " -> heavy string")
		Else
			Debug.SendAnimationEvent(s, "AttackStartH2HRight")
			Debug.Trace("CTKD combo: " + asEventName + " -> next light attack")
		EndIf
	ElseIf asEventName == "MCO_PowerWinOpen"
		; light attacks 1-5 and the up kick open both windows at once (the light handler covers those);
		; a power window alone means light attack 6 (finisher) or a heavy string's next hit
		Utility.Wait(0.1)
		If Utility.GetCurrentRealTime() - LastWinOpenTime < 0.3 || now - LastComboTime < 0.25
			Return
		EndIf
		If TargetInReach(s) && s.GetActorValuePercentage("Stamina") >= FinisherStaminaPct
			LastComboTime = Utility.GetCurrentRealTime()
			; Fuhajin: her finishers gather wind ki (Fuha stock, max 3); Sakkai Fuhazan spends one
			If Mastery >= 20 && FuhaStock < 3
				FuhaStock += 1
			EndIf
			If FireSuper(s)
				Return
			EndIf
			Debug.SendAnimationEvent(s, "attackPowerStartForwardH2HRightHand")
			Debug.Trace("CTKD combo: finisher")
		EndIf
	EndIf
EndEvent

; ---------------- Juri Mastery ----------------

Float Function RankCost(Int rank)
	Return RankCostBase + RankCostStep * rank
EndFunction

Function GainMastery(Actor s, Float pts)
	If Mastery >= 100
		Return
	EndIf
	MasteryPoints += pts
	Bool ranked = False
	While Mastery < 100 && MasteryPoints >= RankCost(Mastery)
		MasteryPoints -= RankCost(Mastery)
		Mastery += 1
		ranked = True
		AnnounceRank(Mastery)
	EndWhile
	If ranked
		RefreshDamage(s)
	EndIf
EndFunction

; Test hook: the console sets CTKD_SetMastery, this applies it once and resets the global to -1.
; Also fills her Fuha stock so Sakkai Fuhazan can be tried straight away.
Function CheckSetMastery(Actor s)
	If !SetMasteryGlobal
		SetMasteryGlobal = Game.GetFormFromFile(0x00000806, "Serana Taekwondo Toggle.esp") as GlobalVariable
		If !SetMasteryGlobal
			Return
		EndIf
	EndIf
	Int want = SetMasteryGlobal.GetValue() as Int
	If want < 0
		Return
	EndIf
	SetMasteryGlobal.SetValue(-1.0)
	If want > 100
		want = 100
	EndIf
	Mastery = want
	MasteryPoints = 0.0
	FuhaStock = 3
	RefreshDamage(s)
	ApplyBuffs(s)
	Debug.Notification("Serana: Juri Mastery set to " + Mastery + ". Unarmed damage " + (s.GetActorValue("UnarmedDamage") as Int) + ".")
EndFunction

Function AnnounceRank(Int r)
	String unlock = ""
	If r == 10
		unlock = " Unlocked: Light on Her Feet (move speed)."
	ElseIf r == 15
		unlock = " Unlocked: Unarmored Defense."
	ElseIf r == 20
		unlock = " Unlocked: Fuha Stock and Sakkai Fuhazan."
	ElseIf r == 25
		unlock = " Unlocked: Restless Spirit (stamina regen in combat)."
	ElseIf r == 30
		unlock = " Unlocked: Sadistic Pleasure (her hits steal stamina)."
	ElseIf r == 40
		unlock = " Unlocked: Ankensatsu (staggering kicks)."
	ElseIf r == 50
		unlock = " Unlocked: Endurance (health in combat)."
	ElseIf r == 55
		unlock = " Unlocked: Feng Shui Engine."
	ElseIf r == 100
		unlock = " Feng Shui Engine recharges twice as fast, Sakkai Fuhazan no longer needs a stock."
	EndIf
	If r % 5 == 0 || unlock != ""
		Debug.Notification("Serana: Juri Mastery " + r + "." + unlock)
	EndIf
EndFunction

; Rank tier of a three-step ability: 0 below a, 1 from a, 2 from b, 3 from c.
Int Function Tier(Int a, Int b, Int c)
	If Mastery >= c
		Return 3
	ElseIf Mastery >= b
		Return 2
	ElseIf Mastery >= a
		Return 1
	EndIf
	Return 0
EndFunction

; Juri fights in her own light outfit, so it counts as unarmored; any other armor does not.
Bool Function Unarmored(Actor s)
	If s.WornHasKeyword(Game.GetFormFromFile(0x0006BBD2, "Skyrim.esm") as Keyword)    ; ArmorHeavy
		Return False
	EndIf
	If !s.WornHasKeyword(Game.GetFormFromFile(0x0006BBD3, "Skyrim.esm") as Keyword)   ; ArmorLight
		Return True
	EndIf
	Armor juriTop = Game.GetFormFromFile(0x0000080E, "Juri Han Outfit.esp") as Armor
	Return juriTop && s.IsEquipped(juriTop)
EndFunction

; A HitFrame with her target close and in front counts as a landed Taekwondo strike.
Function OnStrike(Actor s)
	Actor t = s.GetCombatTarget()
	If !t || t.IsDead() || s.GetDistance(t) > HitReach || Math.Abs(s.GetHeadingAngle(t)) > 60.0
		Return
	EndIf
	GainMastery(s, 1.0)
	If t.GetHeight() < SmallTargetHeight
		CheckLowHit(s, t)
	EndIf
	; Sadistic Pleasure: Juri feeds on her opponent's pain
	If Mastery >= 30
		Float steal = 10.0
		If Mastery >= 60
			steal = 20.0
		EndIf
		t.DamageActorValue("Stamina", steal)
		s.RestoreActorValue("Stamina", steal)
	EndIf
	; Ankensatsu: crushing kicks that stagger
	If Mastery >= 40
		Int chance = 15
		If Mastery >= 70
			chance = 25
		EndIf
		If Utility.RandomInt(1, 100) <= chance
			t.SetAnimationVariableFloat("staggerMagnitude", 0.6)
			Debug.SendAnimationEvent(t, "staggerStart")
		EndIf
	EndIf
EndFunction

; Small targets: if her strike in range did not actually connect (no health lost), land it for her.
Function CheckLowHit(Actor s, Actor t)
	Float before = t.GetActorValue("Health")
	Utility.Wait(0.2)
	If t.IsDead() || t.GetActorValue("Health") < before
		Return    ; it connected
	EndIf
	t.DamageActorValue("Health", s.GetActorValue("UnarmedDamage"))
	Debug.Trace("CTKD combo: low hit landed on " + t.GetDisplayName())
EndFunction

; Passive buffs, re-evaluated every upkeep tick. Each is applied as a delta against what is already applied,
; so nothing stacks, and ClearBuffs takes them all back off.
Function ApplyBuffs(Actor s)
	Bool bare = Unarmored(s)
	Bool fighting = s.IsInCombat()
	Float speed = 0.0
	Float armorBonus = 0.0
	Float health = 0.0
	Float stamRate = 0.0
	If bare
		speed = 10.0 * Tier(10, 40, 70)       ; Light on Her Feet
		armorBonus = 20.0 * Tier(15, 45, 75)       ; Unarmored Defense
		If fighting
			stamRate = 20.0 * Tier(25, 55, 85)    ; Restless Spirit
			health = 20.0 * Tier(50, 70, 90)      ; Endurance
		EndIf
	EndIf
	If speed != AppliedSpeed
		s.ModActorValue("SpeedMult", speed - AppliedSpeed)
		AppliedSpeed = speed
		s.ModActorValue("CarryWeight", 0.1)     ; SpeedMult only takes effect when carry weight changes
		s.ModActorValue("CarryWeight", -0.1)
	EndIf
	If armorBonus != AppliedArmor
		s.ModActorValue("DamageResist", armorBonus - AppliedArmor)
		AppliedArmor = armorBonus
	EndIf
	If health != AppliedHealth
		s.ModActorValue("Health", health - AppliedHealth)
		AppliedHealth = health
	EndIf
	If stamRate != AppliedStaminaRate
		s.ModActorValue("StaminaRateMult", stamRate - AppliedStaminaRate)
		AppliedStaminaRate = stamRate
	EndIf
EndFunction

Function ClearBuffs(Actor s)
	s.ModActorValue("SpeedMult", -AppliedSpeed)
	s.ModActorValue("DamageResist", -AppliedArmor)
	s.ModActorValue("Health", -AppliedHealth)
	s.ModActorValue("StaminaRateMult", -AppliedStaminaRate)
	If AppliedSpeed != 0.0
		s.ModActorValue("CarryWeight", 0.1)
		s.ModActorValue("CarryWeight", -0.1)
	EndIf
	AppliedSpeed = 0.0
	AppliedArmor = 0.0
	AppliedHealth = 0.0
	AppliedStaminaRate = 0.0
EndFunction

; Supers. Hot Key Skill's start events are ignored in most of her combat states (event not processed by
; the graph), so Juri's two super animations were copied into MCO power attack slots her strings never reach
; (Base mco_powerattack9 = Sakkai Fuhazan, mco_powerattack10 = Feng Shui Engine; only the player-only weapon
; art led there). The upkeep tick queues a super; the next combo window sets MCO_nextpowerattack to that slot
; and fires a power attack, exactly like the heavy strings. Each animation casts its own effects, Magicka cost
; and cooldown, so the cooldown effect showing up means it really played.

Bool Function SakkaiReady(Actor s)
	If Mastery < 20 || (FuhaStock < 1 && Mastery < 100) || s.GetActorValue("Magicka") < 50.0
		Return False
	EndIf
	MagicEffect cd = Game.GetFormFromFile(0x00000832, "SFJuriMoves.esp") as MagicEffect
	Return cd && !s.HasMagicEffect(cd)
EndFunction

; Feng Shui Engine: when the fight turns against her (hurt, or facing a strong enemy), she unleashes it.
; 20 s of the 9-hit Feng Shui string; the animation applies the mod's own 10 minute cooldown.
Bool Function FengShuiReady(Actor s)
	If Mastery < 55 || s.GetActorValue("Magicka") < 80.0
		Return False
	EndIf
	MagicEffect active = Game.GetFormFromFile(0x00000804, "SFJuriMoves.esp") as MagicEffect
	MagicEffect cd = Game.GetFormFromFile(0x00000833, "SFJuriMoves.esp") as MagicEffect
	Return cd && !s.HasMagicEffect(cd) && !s.HasMagicEffect(active)
EndFunction

Function QueueSuper(Actor s)
	If PendingSuper != 0
		Return
	EndIf
	Actor t = s.GetCombatTarget()
	If !t || t.IsDead()
		Return
	EndIf
	If FengShuiReady(s) && (s.GetActorValuePercentage("Health") < 0.6 || (t.GetLevel() >= s.GetLevel() && Utility.RandomFloat() < 0.15))
		PendingSuper = 10
	ElseIf SakkaiReady(s) && Utility.RandomFloat() < SakkaiChance
		PendingSuper = 9
	EndIf
EndFunction

; Called from a combo window that is about to send her next attack. True if a super was fired instead.
Bool Function FireSuper(Actor s)
	Int slot = PendingSuper
	If slot == 0
		Return False
	EndIf
	PendingSuper = 0
	MagicEffect cd
	String superName
	If slot == 10
		If !FengShuiReady(s)
			Return False
		EndIf
		cd = Game.GetFormFromFile(0x00000833, "SFJuriMoves.esp") as MagicEffect
		superName = "Feng Shui Engine"
	Else
		If !SakkaiReady(s)
			Return False
		EndIf
		cd = Game.GetFormFromFile(0x00000832, "SFJuriMoves.esp") as MagicEffect
		superName = "Sakkai Fuhazan"
	EndIf
	s.SetAnimationVariableInt("MCO_nextpowerattack", slot)
	Debug.SendAnimationEvent(s, "attackPowerStartForwardH2HRightHand")
	; the super can start a little late (she finishes her current move first), so keep checking for 1.5 s
	Int tries = 6
	While tries > 0 && !s.HasMagicEffect(cd)
		Utility.Wait(0.25)
		tries -= 1
	EndWhile
	If !s.HasMagicEffect(cd)
		Debug.Trace("CTKD combo: " + superName + " did not start")
		Return True    ; the power attack event was still sent this window
	EndIf
	If slot == 10
		FengShuiTime = Utility.GetCurrentRealTime()
	ElseIf Mastery < 100
		FuhaStock -= 1
	EndIf
	Debug.Trace("CTKD combo: " + superName + " (Fuha stock " + FuhaStock + ")")
	Return True
EndFunction

; Rank 100: Feng Shui Engine recharges in 5 minutes instead of 10.
Function FastFengShuiRecharge(Actor s)
	If Mastery < 100 || FengShuiTime <= 0.0
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If FengShuiTime > now
		FengShuiTime = 0.0    ; saved from an earlier session
		Return
	EndIf
	If now - FengShuiTime >= 300.0
		s.DispelSpell(Game.GetFormFromFile(0x00000D97, "SFJuriMoves.esp") as Spell)
		FengShuiTime = 0.0
	EndIf
EndFunction

Event OnUpdate()
	If !TaekwondoOn
		Return
	EndIf
	Actor s = Serana()
	If s && !s.IsDead()
		CheckSetMastery(s)
		Aggressive(s)
		ApplyBuffs(s)
		If s.IsInCombat()
			WasFighting = True
			QueueSuper(s)
		ElseIf WasFighting
			WasFighting = False
			PendingSuper = 0
			FuhaStock = 0    ; wind ki fades after the fight
		EndIf
		FastFengShuiRecharge(s)
	EndIf
	RegisterForSingleUpdate(UpkeepSeconds)
EndEvent

Function WeaponsOn(Actor s)
	If UnarmedBonus != 0.0
		s.ModActorValue("UnarmedDamage", -UnarmedBonus)
		UnarmedBonus = 0.0
	EndIf
	ClearBuffs(s)
	If Storage
		Storage.RemoveAllItems(s, False, True)
	EndIf
	If BestWeapon && s.GetItemCount(BestWeapon) > 0
		s.EquipItem(BestWeapon, False, True)
	EndIf
	TaekwondoOn = False
	FuhaStock = 0
	UnregisterForAnimationEvent(s, "MCO_WinOpen")
	UnregisterForAnimationEvent(s, "MCO_PowerWinOpen")
	UnregisterForAnimationEvent(s, "SCAR_ComboStart")
	UnregisterForAnimationEvent(s, "HitFrame")
	If SavedStyle
		s.GetActorBase().SetCombatStyle(SavedStyle)
		SavedStyle = None
	EndIf
	s.EvaluatePackage()
	Debug.Notification("Serana: weapons back. Juri Mastery " + Mastery + ".")
EndFunction

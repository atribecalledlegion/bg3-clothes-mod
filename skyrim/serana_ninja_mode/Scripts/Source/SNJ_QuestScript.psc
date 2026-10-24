Scriptname SNJ_QuestScript extends Quest
{Serana: Way of the Shinobi (Ninja Mode). The middle path between Taekwondo (CTKD) and Witch of the Wilds (WOTW):
Sasuke's style, Serana's elements. She fights with the Kusanagi (naruto overhaul.esp) on the "Shinobi Normal and
Power" MCO moveset, copied per tier into OAR folders only she uses; her jutsu are Payload Interpreter casts added
to those clips (SKSE/PayloadInterpreter/Config/SeranaNinjaMode.ini): lightning first, frost where an Uchiha would
use fire. This script chains her kenjutsu combos, picks her jutsu, and throws lightning from range while she closes.
Ninja Mastery (0-100) grows with every strike that lands, and only mastery awakens her Sharingan:
tier 1 Genin, 2 one tomoe (rank 20), 3 two tomoe (45), 4 three tomoe (75), 5 awakened (100).
Defence is the heart of this mode: a dodge-and-parry rogue with quick, Sharingan-sharpened reflexes. Every swing,
spell or arrow aimed at her is offered to Defend() (called from the shared watcher in WOTW_QuestScript): she parries
(a timed block; Elden Parry turns it into a parry that staggers the attacker) and ripostes, or dodges (DMCO). Chances
and cooldowns grow with each Sharingan stage but never reach certainty, dodges cost stamina, and she cannot defend
while committed to her own attack (the game refuses the block or dodge then). Her eyes show the Sharingan from the
moment the mode starts (one tomoe even at Genin), with the activation sound from Naruto Overhaul.
Needs SKSE (GetNthForm, Get/SetCombatStyle).}

Actor Property PlayerRef Auto
Spell Property TogglePower Auto
Container Property StorageBase Auto
CombatStyle Property ShinobiStyle Auto
GlobalVariable Property SetMasteryGlobal Auto
{SNJ_SetMastery: test hook. 'set SNJ_SetMastery to <0-100>' in the console sets her rank; -1 = idle.}

Float Property UpkeepSeconds = 1.0 AutoReadOnly
Float Property ComboReach = 320.0 AutoReadOnly
Float Property OpenerMinDistance = 500.0 AutoReadOnly
Float Property OpenerMaxDistance = 1800.0 AutoReadOnly
Float Property OpenerIdleSeconds = 1.5 AutoReadOnly
{Closing in: if she has not attacked for this long and her target is between min and max, she throws a jutsu.}
Float Property OpenerHeavyChance = 0.35 AutoReadOnly
Float Property HitReach = 220.0 AutoReadOnly
Float Property RankCostBase = 10.0 AutoReadOnly
Float Property RankCostStep = 0.2 AutoReadOnly
{Strikes needed for the next rank = base + step x rank (about 2000 for rank 100; was 15 + 0.3, about 3000).}
Float Property BigJutsuCooldown = 40.0 AutoReadOnly
Float Property NagashiCooldown = 10.0 AutoReadOnly
Float Property StormCooldown = 25.0 AutoReadOnly
Float Property ChidoriCooldown = 9.0 AutoReadOnly
Float Property KirinCooldown = 60.0 AutoReadOnly
Float Property DodgeStamina = 8.0 AutoReadOnly
{A dodge's stamina cost (was 15): the Sharingan moves her only as much as she needs to.}
Float Property KirinFinaleHealth = 0.5 AutoReadOnly
{Kirin is her finale: only on bosses and mini bosses, once they are at or below this much health (or she is in trouble).}
Float Property KirinSeedHealth = 0.65 AutoReadOnly
{She raises the clouds a little before the finale, so they are there when the moment comes.}

ObjectReference Storage
Bool NinjaOn = False
Weapon PrevWeapon
Weapon Blade
CombatStyle SavedStyle
Float MasteryPoints = 0.0
Int Mastery = 0
Int CurTier = 0
Bool WasFighting = False
Float AppliedSpeed = 0.0
Float AppliedDamage = 0.0
; real-time stamps (reset when from an earlier session: GetCurrentRealTime restarts every launch)
Float LastWindow = 0.0
Float LastCombo = 0.0
Float LastKidWin = 0.0
Float LastKidChidori = 0.0
Float LastRibcage = 0.0
Float LastBow = 0.0
Float LastSusBlade = 0.0
Float LastAmeno = 0.0
Float SusBladeSince = 0.0
Bool SusBladeOn = False
Enchantment SavedBladeEnch
Float SavedBladeCharge = 0.0
Float BaseBladeReach = 0.0
Float RibcageSince = 0.0    ; when the ribcage was last raised (a flash or the bow): the stuck-state cleanup measures from it
Bool RibcageUp = False
Float LastBig = 0.0
Float LastNagashi = 0.0
Float LastStorm = 0.0
Int PendingCounter = 0
Float LastHyoton = 0.0
Float LastKidFireball = 0.0
Float LastKirin = 0.0
Float LastChidori = 0.0
Float LastKirinPick = 0.0
Bool WantKirin = False
Bool KunaiOut = False
Bool AddedKunai = False
Int GearEra = 0
Float PendingChidoriHit = 0.0
Bool CurseOn = False
Int CurseStage = 0
Float CurseUntil = 0.0
Float LastCurse = 0.0
Float CurseSpeed = 0.0
Float CurseDmg = 0.0
Float CurseUnarmedBonus = 0.0
Float AppliedUnarmed = 0.0
Float LastBlackFrost = 0.0
Float LastDimhollow = 0.0
Int FrostHops = 0
Actor SealedActor
Float SealedSince = 0.0
Actor PendingThrall
Float PendingThrallSince = 0.0
Actor[] Thralls
Bool KirinQueued = False
; Sharingan reads (six enemies at a time)
Actor[] RActor
Int[] RMelee
Int[] RCast
Int[] RArrow
Int[] RStrike
Int[] RBlock
Int[] RFire
Int[] RFrostUser
Int[] RPlan
Int[] RFrost
Int[] RSeen
Float LastInterrupt = 0.0
Float AppliedMagRate = 0.0
Float AppliedStamRate = 0.0
Float LastDefend = 0.0
Float LastGenjutsu = 0.0
Bool Defending = False
HeadPart OrigEyes
HeadPart MeshEyes      ; the eye part on her loaded head right now
Bool BaseRepaired = False
Int EyesShown = 0      ; tomoe count her eyes show now (0 = her own eyes)
Bool WasLoaded = False
Float LastTickReal = 0.0

Event OnInit()
	PlayerRef.AddSpell(TogglePower)
EndEvent

Actor Function Serana()
	Return Game.GetFormFromFile(0x00002B74, "Dawnguard.esm") as Actor
EndFunction

CTKD_QuestScript Function Juri()
	Return Game.GetFormFromFile(0x00000800, "Serana Taekwondo Toggle.esp") as CTKD_QuestScript
EndFunction

WOTW_QuestScript Function Witch()
	Return Game.GetFormFromFile(0x00000800, "Witch of the Wilds.esp") as WOTW_QuestScript
EndFunction

Bool Function IsOn()
	Return NinjaOn
EndFunction

Function Toggle()
	Actor s = Serana()
	If !s || s.IsDead() || s.IsDisabled()
		Debug.Notification("Serana isn't available.")
		Return
	EndIf
	WOTW_QuestScript w = Witch()
	If NinjaOn
		BladeOff(s)
	Else
		; one mode at a time: the others give her weapons back first
		CTKD_QuestScript j = Juri()
		If j && j.IsOn()
			j.Toggle()
		EndIf
		If w && w.IsOn()
			w.Toggle()
		EndIf
		BladeOn(s)
	EndIf
	If w
		w.Wake()    ; the dodge reflex and loyalty guard live there
	EndIf
	RegisterForSingleUpdate(0.5)
EndFunction

Function BladeOn(Actor s)
	Blade = Game.GetFormFromFile(0x0002C0A5, "naruto overhaul.esp") as Weapon    ; Kusanagi
	If !Storage
		Storage = PlayerRef.PlaceAtMe(StorageBase, 1, True, True)
	EndIf
	PrevWeapon = s.GetEquippedWeapon()
	If !Blade
		Blade = PrevWeapon    ; no Naruto Overhaul: she keeps the sword in her hand
	EndIf
	If !Blade || Blade.GetWeaponType() != 1
		Debug.Notification("Way of the Shinobi needs a one-handed sword (the Kusanagi from Naruto Overhaul).")
		Return
	EndIf
	Int i = s.GetNumItems()
	While i > 0
		i -= 1
		Weapon w = s.GetNthForm(i) as Weapon
		If w && w != Blade
			s.RemoveItem(w, s.GetItemCount(w), True, Storage)
		EndIf
	EndWhile
	If s.GetItemCount(Blade) == 0
		s.AddItem(Blade, 1, True)
	EndIf
	NinjaOn = True
	KunaiOut = False
	EraGear(s)    ; kid era: bare hands; Hebi on: the Kusanagi
	UpdateTier(s, False)
	Shinobi(s)
	ApplyBuffs(s)
	PlaySound(s, 0x00003E10)    ; Naruto Overhaul A0SharinganMarker
	ShowEyes(s, True)
	Debug.Notification("Serana: Way of the Shinobi. Ninja Mastery " + Mastery + " (" + EraName() + ", " + TierName(CurTier) + ").")
EndFunction

Function BladeOff(Actor s)
	NinjaOn = False
	CurseEnd(s)
	If RibcageUp
		RibcageClear(s)
	EndIf
	SusanooBladeEnd(s)
	If AddedKunai && Kunai()
		s.UnequipItem(Kunai(), False, True)
		s.RemoveItem(Kunai(), s.GetItemCount(Kunai()), True)
		AddedKunai = False
	EndIf
	KunaiOut = False
	RestoreEyes(s)
	PlaySound(s, 0x00003E12)    ; A0SharinganendMarker
	ClearBuffs(s)
	SetTierAbility(s, 0)
	Weapon kusanagi = Game.GetFormFromFile(0x0002C0A5, "naruto overhaul.esp") as Weapon
	If kusanagi && Blade == kusanagi && PrevWeapon != kusanagi
		s.UnequipItem(kusanagi, False, True)
		s.RemoveItem(kusanagi, s.GetItemCount(kusanagi), True)
	EndIf
	If Storage
		Storage.RemoveAllItems(s, False, True)
	EndIf
	If PrevWeapon && s.GetItemCount(PrevWeapon) > 0
		s.EquipItem(PrevWeapon, False, True)
	EndIf
	UnregisterForAnimationEvent(s, "MCO_WinOpen")
	UnregisterForAnimationEvent(s, "MCO_PowerWinOpen")
	UnregisterForAnimationEvent(s, "SCAR_ComboStart")
	UnregisterForAnimationEvent(s, "HitFrame")
	If SavedStyle
		s.GetActorBase().SetCombatStyle(SavedStyle)
		SavedStyle = None
	EndIf
	s.EvaluatePackage()
	Debug.Notification("Serana sheathes the Kusanagi. Ninja Mastery " + Mastery + ".")
EndFunction

; Shinobi AI: her own style is a hand caster's; swap in the swordswoman's, and let Combat Pathing Revolution
; circle her in close (flanking) without backing off. Re-applied every tick (base-form styles are not saved).
Function Shinobi(Actor s)
	ActorBase b = s.GetActorBase()
	CombatStyle cur = b.GetCombatStyle()
	CombatStyle juri = Game.GetFormFromFile(0x00000805, "Serana Taekwondo Toggle.esp") as CombatStyle    ; CTKD_JuriStyle
	CombatStyle want = ShinobiStyle
	If Era() == 1 && juri
		want = juri    ; the kid is a brawler: aggressive, unarmed, magic only as a fallback
	EndIf
	If cur != want
		If !SavedStyle && cur != ShinobiStyle && cur != juri
			SavedStyle = cur
		EndIf
		b.SetCombatStyle(want)
	EndIf
	If !s.Is3DLoaded() || !s.IsWeaponDrawn()
		Return
	EndIf
	s.SetAnimationVariableBool("CPR_EnableBackoff", True)
	s.SetAnimationVariableFloat("CPR_BackoffChance", 0.3)
	s.SetAnimationVariableBool("CPR_EnableCircling", True)
	s.SetAnimationVariableFloat("CPR_CirclingDistMin", 200.0)
	s.SetAnimationVariableFloat("CPR_CirclingDistMax", 420.0)
	s.SetAnimationVariableBool("CPR_EnableFallback", True)
	s.SetAnimationVariableFloat("CPR_FallbackDistMin", 0.0)
	s.SetAnimationVariableFloat("CPR_FallbackDistMax", 1.0)
	s.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", 0.0)
	s.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", 0.0)
	EraMovement(s)
	Int plan = PlanFor(s.GetCombatTarget())
	If plan != PLAN_NONE
		PlanMovement(s, plan)
	EndIf
	RegisterForAnimationEvent(s, "MCO_WinOpen")
	RegisterForAnimationEvent(s, "MCO_PowerWinOpen")
	RegisterForAnimationEvent(s, "SCAR_ComboStart")
	RegisterForAnimationEvent(s, "HitFrame")
EndFunction

Function GuardClocks(Float now)
	If LastWindow > now
		LastWindow = 0.0
	EndIf
	If LastCombo > now
		LastCombo = 0.0
	EndIf
	If LastBig > now
		LastBig = 0.0
	EndIf
	If LastNagashi > now
		LastNagashi = 0.0
	EndIf
	If LastStorm > now
		LastStorm = 0.0
	EndIf
	If LastDefend > now
		LastDefend = 0.0
	EndIf
	If LastChidori > now
		LastChidori = 0.0
	EndIf
	If LastKirinPick > now
		LastKirinPick = 0.0
	EndIf
	If LastGenjutsu > now
		LastGenjutsu = 0.0
	EndIf
EndFunction

; ---------------- kenjutsu + jutsu driver ----------------

Int Function EnemiesNear(Actor s, Float reach)
	Int n = 0
	Int k = 0
	While k < 6
		Actor a = Game.FindRandomActorFromRef(s, reach)
		If a && a != s && a != PlayerRef && !a.IsDead() && !a.IsPlayerTeammate() && a.IsHostileToActor(PlayerRef)
			n += 1
		EndIf
		k += 1
	EndWhile
	Return n    ; a rough count (random picks can repeat); enough to tell one foe from a crowd
EndFunction

; Power attack slots of the Shinobi clips (Chidori kit, tools/make_oar.py): 1 Chidori (thrust), 2 Hyoton (frost),
; 3 Chidori Nagashi, 4 Chidori Eiso (spear), 5 Chidori Senbon (needles), 6 Kirin (three tomoe; Eiso before),
; 7 Hyoton storm (seeds the clouds Kirin needs). 0 = keep cutting (light attack; Chidori Katana arcs from one tomoe).
; Unlock order follows canon: Chidori from the start, Nagashi and Katana with one tomoe, Eiso and Senbon with two,
; Kirin with three.
Int Function PickJutsu(Actor s, Actor t, Float now, Bool opener)
	Return PlanJutsu(s, t, PickJutsuBase(s, t, now, opener), opener, now)
EndFunction

Int Function PickJutsuBase(Actor s, Actor t, Float now, Bool opener)
	Float m = s.GetActorValue("Magicka")
	Float hp = s.GetActorValuePercentage("Health")
	Float d = s.GetDistance(t)
	Bool big = t.GetLevel() >= s.GetLevel() || hp < 0.5 || EnemiesNear(s, 1500.0) >= 3
	; Kirin is her finale: bosses and mini bosses only, when they are worn down (or she is). The dragon needs
	; clouds; she raises them with her Hyoton storm a little before the moment comes.
	If CurTier >= 4 && IsBoss(s, t) && now - LastKirinPick > KirinCooldown
		Float th = t.GetActorValuePercentage("Health")
		If (th <= KirinFinaleHealth || hp < 0.35) && KirinReady(s, now) && m >= 45.0
			LastKirinPick = now
			LastBig = now
			WantKirin = False
			KirinQueued = True
			Debug.Trace("SNJ: Kirin, the finale, on " + t.GetDisplayName() + " (" + ((th * 100.0) as Int) + "% health)")
			Return 6
		ElseIf th <= KirinSeedHealth && !KirinReady(s, now) && !s.IsInInterior() && m >= 85.0 && now - LastStorm > 10.0
			LastStorm = now
			WantKirin = True
			Debug.Trace("SNJ: Hyoton storm to seed the clouds for Kirin")
			Return 7
		EndIf
	EndIf
	; the big jutsu everywhere else: Chidori Eiso, twice
	If CurTier >= 3 && m >= 60.0 && now - LastBig > BigJutsuCooldown && big
		LastBig = now
		KirinQueued = False
		Return 6
	EndIf
	If CurTier >= 2 && m >= 25.0 && now - LastNagashi > NagashiCooldown && d < 260.0 && EnemiesNear(s, 400.0) >= 2
		LastNagashi = now
		Return 3
	EndIf
	If m >= 40.0 && now - LastStorm > StormCooldown && EnemiesNear(s, 1500.0) >= 2
		LastStorm = now
		Return 7
	EndIf
	Float roll = Utility.RandomFloat()
	If opener
		; at range: spear, needles or frost (lightning bolt and frost before two tomoe)
		If CurTier >= 3 && m >= 25.0 && d <= 1150.0 && roll < 0.4
			Return 4
		ElseIf CurTier >= 3 && m >= 25.0 && roll < 0.65
			Return 5
		ElseIf m >= 15.0 && roll < 0.85
			Return 2
		ElseIf m >= 20.0
			Return 4
		EndIf
		Return 0
	EndIf
	If CurTier >= 3 && m >= 25.0 && roll < 0.12
		Return 5
	ElseIf CurTier >= 3 && m >= 25.0 && roll < 0.22
		Return 4
	ElseIf m >= 20.0 && roll < 0.3
		Return 1    ; Chidori straight from the combo (the clip charges it on the way in)
	EndIf
	Return 0
EndFunction

Function SendAttack(Actor s, Int slot, String why)
	If Era() == 1
		If slot != 1 && slot != 3
			slot = 0    ; no ranged jutsu in the kid kit: taijutsu, and Chidori for the big hit
		EndIf
		Actor kt = s.GetCombatTarget()
		If slot > 0 && kt
			KidJutsu(s, kt, slot)
		EndIf
		Bool bare = Unarmed(s)
		If slot == 1 || slot == 3 || (slot == 0 && Utility.RandomFloat() < 0.25)
			If bare
				Debug.SendAnimationEvent(s, "attackPowerStartForwardH2HRightHand")
			Else
				Debug.SendAnimationEvent(s, "attackPowerStartInPlace")
			EndIf
		ElseIf slot == 0
			If bare
				Debug.SendAnimationEvent(s, "AttackStartH2HRight")
			Else
				Debug.SendAnimationEvent(s, "attackStart")
			EndIf
		EndIf
		Debug.Trace("SNJ: kid " + why + " -> " + SlotName(slot) + " (bare " + bare + ", magicka " + (s.GetActorValue("Magicka") as Int) + ", mastery " + Mastery + ")")
		Return
	EndIf
	If slot > 0
		If slot == 7
			LastHyoton = Utility.GetCurrentRealTime()
		EndIf
		s.SetAnimationVariableInt("MCO_nextpowerattack", slot)
		Debug.SendAnimationEvent(s, "attackPowerStartInPlace")
	Else
		Debug.SendAnimationEvent(s, "attackStart")
	EndIf
	Debug.Trace("SNJ: " + why + " -> " + SlotName(slot) + " (magicka " + (s.GetActorValue("Magicka") as Int) + ", mastery " + Mastery + ")")
EndFunction

String Function SlotName(Int slot)
	If slot == 1
		Return "Chidori"
	ElseIf slot == 2
		Return "Hyoton (frost)"
	ElseIf slot == 3
		Return "Chidori Nagashi"
	ElseIf slot == 4
		Return "Chidori Eiso"
	ElseIf slot == 5
		Return "Chidori Senbon"
	ElseIf slot == 6
		If KirinQueued
			Return "Kirin"    ; the boss finale (SNJ_KirinCallEffect asks TakeKirin; otherwise it throws Eiso)
		EndIf
		Return "Chidori Eiso (big)"
	ElseIf slot == 7
		Return "Hyoton storm"
	EndIf
	Return "cut"
EndFunction

; ---------------- Kirin ----------------

; Bosses and mini bosses: the game's boss markers (Boss / Dragonborn boss and miniboss location ref types,
; dragons, Dawnguard's boss keyword, the vanilla boss combat styles), or anything with at least twice her health.
Bool Function IsBoss(Actor s, Actor t)
	If !t || t.IsDead()
		Return False
	EndIf
	If t.HasRefType(Game.GetFormFromFile(0x000130F7, "Skyrim.esm") as LocationRefType)
		Return True
	EndIf
	If t.HasRefType(Game.GetFormFromFile(0x000206B5, "Dragonborn.esm") as LocationRefType) || t.HasRefType(Game.GetFormFromFile(0x000206B4, "Dragonborn.esm") as LocationRefType) || t.HasRefType(Game.GetFormFromFile(0x0001D4CC, "Dragonborn.esm") as LocationRefType)
		Return True
	EndIf
	If t.HasKeyword(Game.GetFormFromFile(0x00035D59, "Skyrim.esm") as Keyword) || t.HasKeyword(Game.GetFormFromFile(0x0001269F, "Dawnguard.esm") as Keyword)
		Return True    ; dragons, Dawnguard bosses
	EndIf
	ActorBase b = t.GetLeveledActorBase()
	If b
		CombatStyle cs = b.GetCombatStyle()
		If cs
			Int id = cs.GetFormID()
			; csHumanBoss1H/2H, csForswornBossMelee/Magic, csVampireBoss, csDraugrBoss, csDraugr02Boss, csFalmerMeleeBoss, csDragonPriest
			If id == 0x0003DECE || id == 0x0003DECF || id == 0x000442D0 || id == 0x000442D1 || id == 0x0002DFB6 || id == 0x00052197 || id == 0x000DDDA3 || id == 0x00052389 || id == 0x000BB365
				Return True
			EndIf
		EndIf
	EndIf
	Return t.GetBaseActorValue("Health") >= 2.0 * s.GetBaseActorValue("Health")    ; a mini boss by sheer toughness
EndFunction

; Clouds above her: her own Hyoton storm in the last 30 s, or a storm already raging (rain or snow). Outdoors only.
Bool Function KirinReady(Actor s, Float now)
	If CurTier < 4 || Era() < 2 || s.IsInInterior()
		Return False
	EndIf
	If LastHyoton > now
		LastHyoton = 0.0
	EndIf
	If LastHyoton > 0.0 && now - LastHyoton < 30.0
		Return True
	EndIf
	Weather w = Weather.GetCurrentWeather()
	Return w && w.GetClassification() >= 2
EndFunction

; Called by SNJ_KirinCallEffect when her big jutsu reaches its cast frame:
; 1 = bring the dragon down, 2 = it already came down for this jutsu, 0 = no clouds (she throws Eiso instead).
Int Function TakeKirin(Actor s)
	Float now = Utility.GetCurrentRealTime()
	If LastKirin > now
		LastKirin = 0.0
	EndIf
	If now - LastKirin < 3.0
		Return 2
	EndIf
	If !KirinQueued
		Return 0    ; not the finale: her big jutsu is Chidori Eiso
	EndIf
	If !KirinReady(s, now)
		KirinQueued = False
		Debug.Trace("SNJ: no clouds for Kirin, Chidori Eiso instead")
		Return 0
	EndIf
	KirinQueued = False
	LastKirin = now
	Return 1
EndFunction

; ---------------- Chidori: the charged thrust ----------------
; Up close, with a breath of space, she gathers it (her body crackles, the chirping sound) and drives it in.
Function ChidoriTick(Actor s, Float now)
	Actor t = s.GetCombatTarget()
	If !t || t.IsDead() || Defending || !s.IsWeaponDrawn()
		Return
	EndIf
	If now - LastChidori < ChidoriCooldown || now - LastWindow < 1.0 || now - LastCombo < 1.0
		Return
	EndIf
	If s.GetDistance(t) > 450.0 || s.GetActorValue("Magicka") < 20.0 || Utility.RandomFloat() > 0.5
		Return
	EndIf
	LastChidori = now
	LastCombo = now
	Spell charge = Game.GetFormFromFile(0x00000816, "Serana Ninja Mode.esp") as Spell
	If charge
		charge.Cast(s, s)
	EndIf
	Debug.Trace("SNJ: gathering Chidori")
	Utility.Wait(0.8)
	If !t.IsDead() && s.GetDistance(t) <= 450.0
		LastCombo = Utility.GetCurrentRealTime()
		SendAttack(s, 1, "Chidori charged")
	EndIf
EndFunction

; Closing in: the AI runs at her target; every so often she throws lightning or frost on the way.
Function OpenerTick(Actor s, Float now)
	If !s.IsWeaponDrawn()
		Return
	EndIf
	Actor t = s.GetCombatTarget()
	If !t || t.IsDead()
		Return
	EndIf
	Float d = s.GetDistance(t)
	If Era() == 1
		KidOpener(s, t, d, now)
		Return
	EndIf
	Float minD = OpenerMinDistance
	If PlanFor(t) == PLAN_BRUTE
		minD = 350.0    ; hit and run: jutsu as soon as she has slipped out of reach
	EndIf
	If d < minD || d > OpenerMaxDistance
		Return
	EndIf
	If now - LastWindow > OpenerIdleSeconds && now - LastCombo > OpenerIdleSeconds
		LastCombo = now
		Int slot = PickJutsu(s, t, now, True)
		If slot > 0
			SendAttack(s, slot, "jutsu at " + (d as Int))
		EndIf
	EndIf
EndFunction

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If !NinjaOn
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
	If Mastery < 25
		KidCombo(s, asEventName, now)    ; first thing: the window is short (Era() inline)
		Return
	EndIf
	GuardClocks(now)
	If asEventName == "MCO_PowerWinOpen"
		Return    ; the Shinobi sword clips chain through MCO_WinOpen
	EndIf
	Bool opener = now - LastCombo > 1.5
	LastWindow = now
	If now - LastCombo < 0.25
		Return    ; MCO_WinOpen and SCAR_ComboStart arrive together
	EndIf
	Actor t = s.GetCombatTarget()
	If !t || t.IsDead() || s.GetDistance(t) > ComboReach || Math.Abs(s.GetHeadingAngle(t)) > 90.0
		Return
	EndIf
	LastCombo = now
	Int slot = 0
	If PendingCounter > 0
		slot = PendingCounter    ; the Sharingan read the attack she just dodged: punish it
		PendingCounter = 0
	Else
		slot = PickJutsu(s, t, now, False)
		If slot == 0 && opener && Utility.RandomFloat() < OpenerHeavyChance && s.GetActorValuePercentage("Stamina") >= 0.15
			slot = 1 + Utility.RandomInt(0, 1)    ; a heavy opener: lightning or frost
		EndIf
	EndIf
	SendAttack(s, slot, asEventName)
	If opener && Mastery >= 75 && IsMangekyo() && ClaimSusBlade(now)
		SusanooBladeStart(s)    ; after the attack is sent: the combo window is short
	EndIf
EndEvent

; ---------------- Sharingan read: analyse, then counter ----------------
; Like Sasuke against Deidara: she watches every enemy in the fight (the shared watcher in WOTW_QuestScript feeds
; Observe() with their swings, casts and draws; her own strikes feed ObserveStrike() with whether they were blocked),
; reads what kind of fighter each one is, and changes her plan to counter it. She keeps reading: if they change,
; she changes. The sharper her Sharingan, the fewer actions she needs to see (Genin: no reads at all).
; Plans: 1 brute (melee) -> hit and run, jutsu from mid range, parry and riposte
;        2 caster       -> stay on them, interrupt their casts (Chidori up close, Senbon/bolt further out)
;        3 archer       -> close the distance fast, sidestep the arrows
;        4 guard        -> blocks her cuts: current through the guard (Nagashi, Chidori), flank
; Element: lightning by default; frost (Hyoton) for fire users and for targets that shrug off lightning.

Int Property PLAN_NONE = 0 AutoReadOnly
Int Property PLAN_BRUTE = 1 AutoReadOnly
Int Property PLAN_CASTER = 2 AutoReadOnly
Int Property PLAN_ARCHER = 3 AutoReadOnly
Int Property PLAN_GUARD = 4 AutoReadOnly

Int Function ReadNeeded()
	If CurTier >= 5
		Return 1
	ElseIf CurTier == 4
		Return 2
	ElseIf CurTier == 3
		Return 4
	ElseIf CurTier == 2
		Return 6
	EndIf
	Return 99999    ; Genin: the eye is there, the insight is not yet
EndFunction

Int Function ReadSlot(Actor a, Bool create)
	If !RActor
		RActor = new Actor[6]
		RMelee = new Int[6]
		RCast = new Int[6]
		RArrow = new Int[6]
		RStrike = new Int[6]
		RBlock = new Int[6]
		RFire = new Int[6]
		RFrostUser = new Int[6]
		RPlan = new Int[6]
		RFrost = new Int[6]
		RSeen = new Int[6]
	EndIf
	Int free = -1
	Int i = 0
	While i < 6
		If RActor[i] == a
			Return i
		EndIf
		If free < 0 && (!RActor[i] || RActor[i].IsDead())
			free = i
		EndIf
		i += 1
	EndWhile
	If !create
		Return -1
	EndIf
	If free < 0
		free = Utility.RandomInt(0, 5)
	EndIf
	RActor[free] = a
	RMelee[free] = 0
	RCast[free] = 0
	RArrow[free] = 0
	RStrike[free] = 0
	RBlock[free] = 0
	RFire[free] = 0
	RFrostUser[free] = 0
	RPlan[free] = PLAN_NONE
	RFrost[free] = 0
	RSeen[free] = 0
	Return free
EndFunction

Int Function SpellElement(Actor a, String ev)
	{1 fire, 2 frost, 3 shock, 0 other}
	Int hand = 1
	If ev == "BeginCastLeft"
		hand = 0
	EndIf
	Spell sp = a.GetEquippedSpell(hand)
	If !sp
		Return 0
	EndIf
	Keyword fire = Game.GetFormFromFile(0x0001CEAD, "Skyrim.esm") as Keyword       ; MagicDamageFire
	Keyword frost = Game.GetFormFromFile(0x0001CEAE, "Skyrim.esm") as Keyword      ; MagicDamageFrost
	Keyword shock = Game.GetFormFromFile(0x0001CEAF, "Skyrim.esm") as Keyword      ; MagicDamageShock
	Int i = sp.GetNumEffects()
	While i > 0
		i -= 1
		MagicEffect e = sp.GetNthEffectMagicEffect(i)
		If e
			If e.HasKeyword(fire)
				Return 1
			ElseIf e.HasKeyword(frost)
				Return 2
			ElseIf e.HasKeyword(shock)
				Return 3
			EndIf
		EndIf
	EndWhile
	Return 0
EndFunction

; Every swing, cast or draw of any enemy in the fight (not only those aimed at her).
Function Observe(Actor a, String ev)
	If !NinjaOn || !a || a.IsDead() || CurTier < 2
		Return
	EndIf
	Int i = ReadSlot(a, True)
	If ev == "preHitFrame"
		RMelee[i] = RMelee[i] + 1
	ElseIf ev == "bowDraw"
		RArrow[i] = RArrow[i] + 1
	Else
		RCast[i] = RCast[i] + 1
		Int el = SpellElement(a, ev)
		If el == 1
			RFire[i] = RFire[i] + 1
		ElseIf el == 2
			RFrostUser[i] = RFrostUser[i] + 1
		EndIf
		Interrupt(a, i)
	EndIf
	Reassess(a, i)
EndFunction

; Her own strike landed (HitFrame in reach): was it blocked?
Function ObserveStrike(Actor t)
	If CurTier < 2 || !t
		Return
	EndIf
	Int i = ReadSlot(t, True)
	RStrike[i] = RStrike[i] + 1
	If t.GetAnimationVariableBool("IsBlocking")
		RBlock[i] = RBlock[i] + 1
	EndIf
	Reassess(t, i)
EndFunction

Function Reassess(Actor a, Int i)
	Int seen = RMelee[i] + RCast[i] + RArrow[i] + RStrike[i]
	If seen < ReadNeeded() || seen - RSeen[i] < ReadNeeded()
		Return
	EndIf
	RSeen[i] = seen
	Int acts = RMelee[i] + RCast[i] + RArrow[i]
	Int plan = PLAN_BRUTE
	If RStrike[i] >= 3 && RBlock[i] * 100 >= RStrike[i] * 35
		plan = PLAN_GUARD
	ElseIf acts > 0 && RCast[i] * 2 >= acts
		plan = PLAN_CASTER
	ElseIf acts > 0 && RArrow[i] * 2 >= acts
		plan = PLAN_ARCHER
	EndIf
	; element: frost answers fire (and fire users are her one real danger); frost users resist frost, so lightning;
	; from three tomoe she also reads their resistances
	Int frost = 0
	If RFire[i] > 0
		frost = 1
	EndIf
	If RFrostUser[i] > 0
		frost = 0
	EndIf
	If CurTier >= 4
		Float shockRes = a.GetActorValue("ElectricResist")
		Float frostRes = a.GetActorValue("FrostResist")
		If shockRes >= frostRes + 25.0
			frost = 1
		ElseIf frostRes >= shockRes + 25.0
			frost = 0
		EndIf
	EndIf
	If plan != RPlan[i] || frost != RFrost[i]
		Bool first = RPlan[i] == PLAN_NONE
		RPlan[i] = plan
		RFrost[i] = frost
		String what = PlanName(plan)
		If frost == 1
			what += ", answered with Hyoton"
		EndIf
		Debug.Trace("SNJ read: " + a.GetDisplayName() + " -> " + what + " (melee " + RMelee[i] + ", casts " + RCast[i] + ", fire " + RFire[i] + ", arrows " + RArrow[i] + ", blocked " + RBlock[i] + "/" + RStrike[i] + ")")
		If IsBoss(Serana(), a)
			If first
				Debug.Notification("Serana's Sharingan reads " + a.GetDisplayName() + ": " + what + ".")
			Else
				Debug.Notification("Serana changes her plan against " + a.GetDisplayName() + ": " + what + ".")
			EndIf
		EndIf
	EndIf
EndFunction

String Function PlanName(Int plan)
	If plan == PLAN_CASTER
		Return "a caster, so she stays on them and breaks their casts"
	ElseIf plan == PLAN_ARCHER
		Return "an archer, so she closes the distance"
	ElseIf plan == PLAN_GUARD
		Return "a guard, so she sends current through it and flanks"
	ElseIf plan == PLAN_BRUTE
		Return "a brute, so she strikes and slips away"
	EndIf
	Return "unread"
EndFunction

Int Function PlanFor(Actor t)
	If !t || !RActor
		Return PLAN_NONE
	EndIf
	Int i = ReadSlot(t, False)
	If i < 0
		Return PLAN_NONE
	EndIf
	Return RPlan[i]
EndFunction

Bool Function FrostFor(Actor t)
	If !t || !RActor
		Return False
	EndIf
	Int i = ReadSlot(t, False)
	Return i >= 0 && RFrost[i] == 1
EndFunction

; A read caster begins a spell: she breaks it. Chidori if she is close, Senbon (or a bolt) from further out.
Function Interrupt(Actor a, Int i)
	If RPlan[i] != PLAN_CASTER || Defending
		Return
	EndIf
	Actor s = Serana()
	If !s || s.GetCombatTarget() != a || s.GetActorValue("Magicka") < 20.0
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If LastInterrupt > now
		LastInterrupt = 0.0
	EndIf
	If now - LastInterrupt < 4.0 || now - LastCombo < 0.6
		Return
	EndIf
	LastInterrupt = now
	LastCombo = now
	Float d = s.GetDistance(a)
	If d <= 450.0
		SendAttack(s, 1, "interrupt " + a.GetDisplayName() + "'s cast")
	ElseIf CurTier >= 3
		SendAttack(s, 5, "interrupt " + a.GetDisplayName() + "'s cast")
	Else
		SendAttack(s, 4, "interrupt " + a.GetDisplayName() + "'s cast")
	EndIf
EndFunction

; Her movement for the plan against her current target (Combat Pathing Revolution).
Function PlanMovement(Actor s, Int plan)
	If Era() == 1
		Return    ; the kid doesn't hang back: she reads, but she fights up close
	EndIf
	Float backoff = 0.3
	Float cmin = 200.0
	Float cmax = 420.0
	If plan == PLAN_BRUTE
		backoff = 0.55
		cmin = 300.0
		cmax = 520.0
	ElseIf plan == PLAN_CASTER || plan == PLAN_ARCHER
		backoff = 0.0
		cmin = 90.0
		cmax = 220.0
	ElseIf plan == PLAN_GUARD
		backoff = 0.2
		cmin = 140.0
		cmax = 300.0
	EndIf
	s.SetAnimationVariableFloat("CPR_BackoffChance", backoff)
	s.SetAnimationVariableFloat("CPR_CirclingDistMin", cmin)
	s.SetAnimationVariableFloat("CPR_CirclingDistMax", cmax)
EndFunction

; Read-based adjustments to her jutsu choice (called by PickJutsu after its own pick).
Int Function PlanJutsu(Actor s, Actor t, Int slot, Bool opener, Float now)
	Int plan = PlanFor(t)
	Float m = s.GetActorValue("Magicka")
	Float d = s.GetDistance(t)
	If plan == PLAN_GUARD && !opener && slot == 0
		If CurTier >= 2 && m >= 25.0 && now - LastNagashi > NagashiCooldown
			LastNagashi = now
			Return 3            ; current runs through a raised guard
		ElseIf m >= 20.0 && Utility.RandomFloat() < 0.35
			Return 1            ; Chidori pierces it
		EndIf
	ElseIf plan == PLAN_ARCHER && opener && d < 1200.0
		Return 0                ; no standing around trading shots: she closes in
	EndIf
	If FrostFor(t) && (slot == 4 || slot == 5) && m >= 25.0 && Utility.RandomFloat() < 0.6
		Return 2                ; Hyoton instead of lightning
	EndIf
	Return slot
EndFunction

; Read-based defence bonuses (fair: capped well below certain).
Float Function PlanParryBonus(Actor a)
	If PlanFor(a) == PLAN_BRUTE
		Return 0.1              ; she has read the rhythm of their swings
	EndIf
	Return 0.0
EndFunction

Float Function PlanRangedBonus(Actor a, String ev)
	Float bonus = 0.0
	Int plan = PlanFor(a)
	If plan == PLAN_CASTER || plan == PLAN_ARCHER
		bonus = 0.15
	EndIf
	If CurTier >= 2 && ev != "bowDraw" && ev != "preHitFrame" && SpellElement(a, ev) == 1
		bonus += 0.15           ; fire: the one thing that can still burn her, and she knows it
	EndIf
	Return bonus
EndFunction

; ---------------- Eras (2026-10-18, the user's arc) ----------------
; Her mastery walks Sasuke's road:
;   0-24  KID: bare-handed taijutsu (the Juri Han kicks = his Shishi Rendan; the Juri OAR clips already apply to
;         Serana whenever she is unarmed), Chidori for the big hits, Hyoton: Gokakyu (breathed, now and then) at range (no Ice Spike), kunai only
;         when it gets serious (a boss, or she is below half health), parries at half the rate. Tomoe: one, two at
;         10, three at 17 (the end of Part 1).
;   25-49 HEBI: the Kusanagi (Shinobi moveset), cocky and aggressive, Chidori everywhere; three tomoe kept.
;   50+   TAKA: the Mangekyo; cold and patient. (80+ is held for the Rinnegan, later.)
; The Curse Mark is the Mark of Coldharbour, Molag Bal's brand on her blood. Kid: stage 1 flares when she is badly hurt
; or faces a boss. Hebi: stage 2, embraced (bat wings, Coldharbour's bats). Both end in exhaustion. The Mangekyo
; burns it out of her blood: she learns the power was never worth its price.

Int Function Era()
	If Mastery >= 50
		Return 3
	ElseIf Mastery >= 25
		Return 2
	EndIf
	Return 1
EndFunction

String Function EraName()
	Int e = Era()
	If e == 3
		Return "Taka"
	ElseIf e == 2
		Return "Hebi"
	EndIf
	Return "Genin"
EndFunction

Bool Function Unarmed(Actor s)
	Return s.GetEquippedItemType(1) == 0
EndFunction

Weapon Function Kunai()
	Return Game.GetFormFromFile(0x0002BB3D, "naruto overhaul.esp") as Weapon    ; Iron Kunai
EndFunction

; Her hands, for the era: kid = bare (or the kunai when serious), later = the Kusanagi.
Function EraGear(Actor s)
	Weapon k = Kunai()
	If Era() == 1
		If Blade && s.GetItemCount(Blade) > 0
			s.UnequipItem(Blade, False, True)
			s.RemoveItem(Blade, s.GetItemCount(Blade), True, Storage)
		EndIf
		If KunaiOut && k
			If s.GetItemCount(k) == 0
				s.AddItem(k, 1, True)
				AddedKunai = True
			EndIf
			s.EquipItem(k, True, True)
		ElseIf k && s.GetItemCount(k) > 0
			s.UnequipItem(k, False, True)
			If AddedKunai
				s.RemoveItem(k, s.GetItemCount(k), True)
				AddedKunai = False
			EndIf
		EndIf
	Else
		If k && s.GetItemCount(k) > 0 && AddedKunai
			s.UnequipItem(k, False, True)
			s.RemoveItem(k, s.GetItemCount(k), True)
			AddedKunai = False
		EndIf
		If Blade
			If s.GetItemCount(Blade) == 0 && Storage && Storage.GetItemCount(Blade) > 0
				Storage.RemoveItem(Blade, 1, True, s)
			ElseIf s.GetItemCount(Blade) == 0
				s.AddItem(Blade, 1, True)
			EndIf
			s.EquipItem(Blade, True, True)
		EndIf
	EndIf
	GearEra = Era()
EndFunction

; Kid Sasuke only draws a kunai when he fights seriously.
; RActor = None fails (None can't be cast to Actor[]), so the reads were never cleared between fights.
Function ClearReads()
	If RActor
		Int i = 0
		While i < RActor.Length
			RActor[i] = None
			i += 1
		EndWhile
	EndIf
EndFunction

; The kid is a taijutsu specialist: nothing in her hands but the kunai, and only when it gets serious.
; The AI picks up weapons from the ground (or equips one from her pack) when she is unarmed: take it out of her
; hands and lock it so the AI can't equip it again. It stays in her inventory, so nothing is lost.
Function BareHandsTick(Actor s)
	If Era() != 1
		Return
	EndIf
	Weapon k = Kunai()
	Int hand = 0
	While hand < 2
		Weapon w = s.GetEquippedWeapon(hand == 1)
		If w && !(KunaiOut && w == k)
			s.UnequipItem(w, True, True)    ; abPreventEquip: the AI may not equip it again
			Debug.Trace("SNJ: kid era, " + w.GetName() + " out of her hands: taijutsu only")
		EndIf
		hand += 1
	EndWhile
	If KunaiOut && k && s.GetEquippedWeapon() != k
		s.EquipItem(k, True, True)
	EndIf
EndFunction

Function KunaiTick(Actor s)
	BareHandsTick(s)
	If Era() != 1 || KunaiOut
		Return
	EndIf
	Actor t = s.GetCombatTarget()
	If (t && IsBoss(s, t)) || s.GetActorValuePercentage("Health") < 0.5
		KunaiOut = True
		EraGear(s)
		Debug.Trace("SNJ: kid era, this is serious: kunai out")
	EndIf
EndFunction

; Kid era jutsu, cast by script (the Juri and Tobirama clips carry no jutsu of their own).
; Chidori: the next strike that lands within 1.5 s carries it. Hyoton: an ice spike (three for her Hosenka).
Function KidJutsu(Actor s, Actor t, Int slot)
	If slot == 1 || slot == 3
		PendingChidoriHit = Utility.GetCurrentRealTime()
	EndIf
EndFunction

; Her one ranged jutsu as a kid: Hyoton: Gokakyu no Jutsu, Sasuke's Great Fireball in ice (SNJ_GokakyuSpell: the naruto
; overhaul fireball recoloured with frost palettes, tools/make_gokakyu_nif.py). She breathes it out like a shout.
; Only now and then, from mid range, on the way in; then she closes.
Float Property KidFireballCooldown = 20.0 AutoReadOnly
Function KidOpener(Actor s, Actor t, Float d, Float now)
	If LastKidFireball > now
		LastKidFireball = 0.0
	EndIf
	If d < 300.0 || d > 900.0 || now - LastKidFireball < KidFireballCooldown || s.GetActorValue("Magicka") < 35.0
		Return
	EndIf
	Spell gokakyu = Game.GetFormFromFile(0x0000082B, "Serana Ninja Mode.esp") as Spell
	If !gokakyu
		Return
	EndIf
	LastKidFireball = now
	LastCombo = now
	s.DamageActorValue("Magicka", 35.0)
	BreatheGokakyu(s, t, gokakyu)
	Debug.Trace("SNJ: kid Hyoton Gokakyu at " + (d as Int))
EndFunction

; The shout animation: she draws breath, then exhales the ball (shoutRelease). NPCs take NPCshoutStart (the player's
; shoutStart is ignored by their combat graphs: vanilla NPCVoiceStart idle); if she never got into the shout, she
; still exhales (CombatReady_BreathExhaleShort, the vanilla weapon-out voice release).
Function BreatheGokakyu(Actor s, Actor t, Spell gokakyu)
	Debug.SendAnimationEvent(s, "NPCshoutStart")
	Utility.Wait(0.6)
	Bool shouting = s.GetAnimationVariableBool("IsShouting")
	Debug.Trace("SNJ: Gokakyu breath, in the shout " + shouting)
	If shouting
		Debug.SendAnimationEvent(s, "shoutRelease")
	Else
		Debug.SendAnimationEvent(s, "CombatReady_BreathExhaleShort")
	EndIf
	Utility.Wait(0.15)
	If !t.IsDead()
		gokakyu.Cast(s, t)
	EndIf
	Utility.Wait(0.6)
	Debug.SendAnimationEvent(s, "shoutStop")
EndFunction

; The kid's combo driver: Taekwondo mode's fix for the "one attack and stop" problem (SCAR only ever reads one
; follow-up from the Juri clips). Every combo window sends the next light kick; the heavy string only as an opener;
; a power window alone (light attack 6, or the heavy string's next hit) gets the finisher. Chidori never breaks a
; string: it charges in her hand and rides on the next kick that lands (KidStrike).
Function KidLight(Actor s)
	If Unarmed(s)
		Debug.SendAnimationEvent(s, "AttackStartH2HRight")
	Else
		Debug.SendAnimationEvent(s, "attackStart")    ; the kunai
	EndIf
EndFunction

Function KidHeavy(Actor s)
	If Unarmed(s)
		Debug.SendAnimationEvent(s, "attackPowerStartForwardH2HRightHand")
	Else
		Debug.SendAnimationEvent(s, "attackPowerStartInPlace")
	EndIf
EndFunction

Function KidCombo(Actor s, String ev, Float now)
	; The combo window is a fraction of a second, and this script is busy (reads, ticks): send the next attack
	; FIRST, with only cheap checks, and decide anything else afterwards. (Deciding first with PickJutsu, which
	; counts enemies with dozens of engine calls, sent the kick after the window had closed: one kick, pause.)
	If LastKidWin > now
		LastKidWin = 0.0
	EndIf
	If LastCombo > now
		LastCombo = 0.0
	EndIf
	If ev == "MCO_WinOpen" || ev == "SCAR_ComboStart"
		LastKidWin = now
		LastWindow = now
		If now - LastCombo < 0.25
			Return    ; both events fire together: already sent for this window
		EndIf
		Actor t = s.GetCombatTarget()
		If !t || s.GetDistance(t) > ComboReach
			Return
		EndIf
		Bool opener = now - LastCombo > 1.5
		LastCombo = now
		Bool heavy = opener && Utility.RandomFloat() < OpenerHeavyChance
		If heavy
			KidHeavy(s)
		Else
			KidLight(s)
		EndIf
		; now the extras: Chidori charges in her hand and rides on the next kick that lands
		String what = "next kick"
		If heavy
			what = "heavy string"
		EndIf
		If LastKidChidori > now
			LastKidChidori = 0.0
		EndIf
		If PendingChidoriHit <= 0.0 && now - LastKidChidori > 4.0 && Utility.RandomFloat() < 0.3 && s.GetActorValue("Magicka") >= 20.0
			LastKidChidori = now
			Spell charge = Game.GetFormFromFile(0x00000816, "Serana Ninja Mode.esp") as Spell
			If charge
				charge.Cast(s, s)
			EndIf
			PendingChidoriHit = Utility.GetCurrentRealTime()
			what += ", Chidori in her hand"
		EndIf
		Debug.Trace("SNJ kid combo: " + ev + " -> " + what)
	ElseIf ev == "MCO_PowerWinOpen"
		Utility.Wait(0.1)
		If Utility.GetCurrentRealTime() - LastKidWin < 0.3 || now - LastCombo < 0.25
			Return    ; light attacks open both windows at once; the light handler covered it
		EndIf
		Actor t2 = s.GetCombatTarget()
		If t2 && s.GetDistance(t2) <= ComboReach
			LastCombo = Utility.GetCurrentRealTime()
			KidHeavy(s)
			Debug.Trace("SNJ kid combo: finisher")
		EndIf
	EndIf
EndFunction

Function KidStrike(Actor s, Actor t)
	If PendingChidoriHit <= 0.0 || Utility.GetCurrentRealTime() - PendingChidoriHit > 1.5
		Return
	EndIf
	PendingChidoriHit = 0.0
	Spell chidori = Game.GetFormFromFile(0x00000817, "Serana Ninja Mode.esp") as Spell
	If chidori && s.GetActorValue("Magicka") >= 20.0
		chidori.Cast(s, t)
		s.DamageActorValue("Magicka", 20.0)
		Debug.Trace("SNJ: kid Chidori lands on " + t.GetDisplayName())
	EndIf
EndFunction

; ---------------- the Curse Mark (Mark of Coldharbour) ----------------

Function CurseTick(Actor s, Float now)
	If LastCurse > now
		LastCurse = 0.0
	EndIf
	If CurseOn
		If now >= CurseUntil || Era() >= 3
			CurseEnd(s)
		EndIf
		Return
	EndIf
	Int e = Era()
	If e >= 3
		Return
	EndIf
	Float cd = 90.0
	Float hpLine = 0.35
	If e == 2
		cd = 70.0
		hpLine = 0.5
	EndIf
	If now - LastCurse < cd
		Return
	EndIf
	Actor t = s.GetCombatTarget()
	If s.GetActorValuePercentage("Health") < hpLine || (t && IsBoss(s, t))
		CurseStart(s, e, now)
	EndIf
EndFunction

Function CurseStart(Actor s, Int stage, Float now)
	CurseOn = True
	CurseStage = stage
	LastCurse = now
	Float dur = 20.0
	CurseSpeed = 15.0
	CurseDmg = 0.25
	CurseUnarmedBonus = 12.0
	If stage == 2
		dur = 25.0
		CurseSpeed = 25.0
		CurseDmg = 0.5
		CurseUnarmedBonus = 0.0
	EndIf
	CurseUntil = now + dur
	EffectShader marks = Game.GetFormFromFile(0x00081180, "Skyrim.esm") as EffectShader    ; DA02ArmorShadow: dark marks
	If marks
		marks.Play(s, dur)
	EndIf
	If stage == 2
		EffectShader change = Game.GetFormFromFile(0x000FD804, "Skyrim.esm") as EffectShader    ; VampireChangeFX
		If change
			change.Play(s, 2.0)
		EndIf
		Spell wings = Game.GetFormFromFile(0x00000809, "Daughter of Coldharbor.esp") as Spell    ; the bat swarm: her wings
		If wings
			wings.Cast(s, s)
		EndIf
	EndIf
	s.ModActorValue("SpeedMult", CurseSpeed)
	s.ModActorValue("CarryWeight", 0.1)
	s.ModActorValue("CarryWeight", -0.1)
	s.ModActorValue("AttackDamageMult", CurseDmg)
	s.ModActorValue("UnarmedDamage", CurseUnarmedBonus)
	If stage == 2
		Debug.Notification("The Mark of Coldharbour consumes Serana: stage two.")
	Else
		Debug.Notification("The Mark of Coldharbour spreads across Serana's skin.")
	EndIf
	Debug.Trace("SNJ: Curse Mark stage " + stage + " for " + (dur as Int) + " s")
EndFunction

Function CurseEnd(Actor s)
	If !CurseOn
		Return
	EndIf
	CurseOn = False
	s.ModActorValue("SpeedMult", -CurseSpeed)
	s.ModActorValue("CarryWeight", 0.1)
	s.ModActorValue("CarryWeight", -0.1)
	s.ModActorValue("AttackDamageMult", -CurseDmg)
	s.ModActorValue("UnarmedDamage", -CurseUnarmedBonus)
	CurseSpeed = 0.0
	CurseDmg = 0.0
	CurseUnarmedBonus = 0.0
	; the price: the mark burns through her reserves
	Float stam = 0.6
	Float mag = 0.4
	If CurseStage == 2
		stam = 0.8
		mag = 0.6
	EndIf
	s.DamageActorValue("Stamina", stam * s.GetActorValue("Stamina"))
	s.DamageActorValue("Magicka", mag * s.GetActorValue("Magicka"))
	Debug.Trace("SNJ: Curse Mark fades: exhaustion")
EndFunction

; ---------------- era personalities ----------------
; CPR base by era (her read plans adjust from here): the kid rushes in, Hebi presses, Taka waits for the opening.
Function EraMovement(Actor s)
	Int e = Era()
	Float backoff = 0.35
	Float cmin = 250.0
	Float cmax = 450.0
	If e == 1
		backoff = 0.0    ; as Taekwondo mode: no circling, no backing off, straight in
		cmin = 0.0
		cmax = 1.0
	ElseIf e == 2
		backoff = 0.2
		cmin = 150.0
		cmax = 320.0
	EndIf
	s.SetAnimationVariableFloat("CPR_BackoffChance", backoff)
	s.SetAnimationVariableFloat("CPR_CirclingDistMin", cmin)
	s.SetAnimationVariableFloat("CPR_CirclingDistMax", cmax)
EndFunction

; ---------------- Mangekyo Sharingan (tier 5, mastery 80) ----------------
; Her eye pattern: an eclipsed sun with three bat wings (textures\SNJ\eyes\mangekyo.dds, tools/make_mangekyo.py).
; Left eye, Black Frost (her Amaterasu): a gaze; frost seizes the blood (paralysis), burns from the inside and spreads.
; The eye bleeds: it costs her health. Right eye, Dimhollow: a seal in ice, out of time (shatter / stasis / protect).
; Her genjutsu becomes the Soul Cairn: a mind prison; a broken mind fights for her until the fight ends, then dies.
; No Mangekyo blindness (the user's call): cooldowns only.

Float Property BlackFrostCooldown = 40.0 AutoReadOnly
Float Property DimhollowCooldown = 35.0 AutoReadOnly
Float Property BlackFrostReach = 2500.0 AutoReadOnly
Float Property EyeBleedPct = 0.06 AutoReadOnly
{Each Black Frost costs her this much of her health: the eye bleeds.}
Int Property FrostHopsMax = 3 AutoReadOnly
Float Property ThrallChance = 0.25 AutoReadOnly

Bool Function IsMangekyo()
	Return NinjaOn && CurTier >= 5
EndFunction

Bool Function TakeFrostHop()
	If FrostHops >= FrostHopsMax
		Return False
	EndIf
	FrostHops += 1
	Return True
EndFunction

Bool Function IsAsheActor(Actor a)
	ActorBase b = a.GetLeveledActorBase()
	Return b && (b == Game.GetFormFromFile(0x00005900, "Ashe - Fire and Blood.esp") || b == Game.GetFormFromFile(0x0077052C, "Ashe - Fire and Blood.esp"))
EndFunction

; Who Dimhollow protects instead of sealing: Serana, Obito, Ashe and your other real followers.
Bool Function IsFriend(Actor a)
	If !a
		Return False
	EndIf
	If a == Serana() || a == PlayerRef || IsAsheActor(a)
		Return True
	EndIf
	Faction followers = Game.GetFormFromFile(0x0005C84E, "Skyrim.esm") as Faction    ; CurrentFollowerFaction
	Return a.IsPlayerTeammate() && followers && a.GetFactionRank(followers) >= 0
EndFunction

; Already broken: low health, or far weaker than her. Never a boss.
; A Soul Cairn thrall fights for her: her Mangekyo leaves it alone (she shattered her own thrall in the first Taka
; test: it was still her combat target).
Bool Function IsThrall(Actor a)
	If !a || !Thralls
		Return False
	EndIf
	Return Thralls.Find(a) >= 0
EndFunction

Bool Function Shatterable(Actor caster, Actor t)
	If !t || IsBoss(caster, t) || IsThrall(t)
		Return False
	EndIf
	Return t.GetActorValuePercentage("Health") <= 0.35 || t.GetLevel() <= caster.GetLevel() - 10
EndFunction

; Safety net: a stasis seal clears its own ghost flag, but if a save or load cut it short, the tick clears it.
Function NoteSealed(Actor a)
	If SealedActor && SealedActor != a
		SealedActor.SetGhost(False)
	EndIf
	SealedActor = a
	SealedSince = Utility.GetCurrentRealTime()
EndFunction

Function MangekyoGaze(Actor s, Actor t)
	Sound snd = Game.GetFormFromFile(0x00017C7C, "naruto overhaul.esp") as Sound    ; Mangekyou Sharingan
	If snd
		snd.Play(s)
	EndIf
EndFunction

; ---------------- flash Susanoo (mastery 55+) ----------------
; Sasuke never stands in a full Susanoo mech here: parts of it flash on for a moment and are gone. The ribcage
; (The Uchiha Clan's Sasuke ribcage in black ice, SNJ_Ribcage) snaps on to take a heavy blow, a fire spell or
; an arrow when she is hurt; she is out of reach for the hit, then it fades and she is moving again.
Float Property RibcageCooldown = 15.0 AutoReadOnly
Float Property RibcageSeconds = 2.0 AutoReadOnly
Float Property RibcageGuardSeconds = 0.8 AutoReadOnly

Bool Function RibcageReady(Float now)
	If !IsMangekyo() || Mastery < 55 || RibcageUp
		Return False
	EndIf
	; a value from an earlier session (the real-time clock restarts at 0) is far ahead; a Defend thread that began a moment
	; before another claimed the ribcage is only slightly behind, and must not wipe the cooldown (it flashed 5 s apart)
	If LastRibcage - now > RibcageCooldown
		LastRibcage = 0.0
	EndIf
	Return now - LastRibcage > RibcageCooldown
EndFunction

; Two attackers swinging at once run Defend on two threads; any engine call between the check and the flash lets the
; other thread in (it flashed twice, 2 s apart, in the first test). Claiming makes no engine calls: check and take.
Bool Function ClaimRibcage(Float now)
	If !RibcageReady(now)
		Return False
	EndIf
	RibcageUp = True
	LastRibcage = now
	RibcageSince = now
	Return True
EndFunction

Function FlashRibcage(Actor s, String why)
	Armor rib = Game.GetFormFromFile(0x0000082E, "Serana Ninja Mode.esp") as Armor
	If !rib
		RibcageUp = False
		Return
	EndIf
	Sound snd = Game.GetFormFromFile(0x0001AE79, "UchihaClan.esp") as Sound    ; aaaSusanooSummonMarker
	If snd
		snd.Play(s)
	EndIf
	If s.GetItemCount(rib) == 0
		s.AddItem(rib, 1, True)
	EndIf
	s.EquipItem(rib, True, True)
	s.SetGhost(True)    ; the blow lands on the ribcage, not on her
	Debug.Trace("SNJ: Susanoo ribcage takes " + why)
	Utility.Wait(RibcageGuardSeconds)
	s.SetGhost(False)
	Utility.Wait(RibcageSeconds - RibcageGuardSeconds)
	s.UnequipItem(rib, False, True)
	s.RemoveItem(rib, s.GetItemCount(rib), True)
	RibcageUp = False
EndFunction

; A save or load in the middle of a flash (or the mode turned off) must not leave her ghosted in a ribcage.
Function RibcageClear(Actor s)
	Armor rib = Game.GetFormFromFile(0x0000082E, "Serana Ninja Mode.esp") as Armor
	If rib && s.GetItemCount(rib) > 0
		s.UnequipItem(rib, False, True)
		s.RemoveItem(rib, s.GetItemCount(rib), True)
	EndIf
	s.SetGhost(False)
	RibcageUp = False
EndFunction

Function RibcageTick(Actor s, Float now)
	If RibcageUp && (RibcageSince - now > RibcageCooldown || now - RibcageSince > 5.0)
		RibcageClear(s)
	EndIf
	If RibcageReady(now) && s.GetActorValuePercentage("Health") < 0.3 && !Defending && ClaimRibcage(now)
		FlashRibcage(s, "the moment she faltered")
	EndIf
EndFunction

; The spectral bow (mastery 65): the ribcage forms with the bow, one black-ice arrow flies, and both are gone. Her
; answer at range (archers and casters most of all), between her Chidori Eiso and Senbon.
Float Property BowCooldown = 25.0 AutoReadOnly

Bool Function ClaimBow(Float now)
	If !IsMangekyo() || Mastery < 65 || RibcageUp
		Return False
	EndIf
	If LastBow - now > BowCooldown
		LastBow = 0.0    ; from an earlier session
	EndIf
	If now - LastBow <= BowCooldown
		Return False
	EndIf
	RibcageUp = True
	LastBow = now
	RibcageSince = now
	Return True
EndFunction

Function BowTick(Actor s, Float now)
	If Defending || Mastery < 65 || now - LastBow <= BowCooldown
		Return
	EndIf
	Actor t = s.GetCombatTarget()
	If !t || t.IsDead()
		Return
	EndIf
	Float d = s.GetDistance(t)
	If d < 450.0 || d > 3000.0
		Return
	EndIf
	Int plan = PlanFor(t)
	If (plan == PLAN_ARCHER || plan == PLAN_CASTER || d > 900.0 || Utility.RandomFloat() < 0.3) && s.HasLOS(t) && ClaimBow(now)
		SpectralBow(s, t)
	EndIf
EndFunction

Function SpectralBow(Actor s, Actor t)
	Armor rib = Game.GetFormFromFile(0x0000082E, "Serana Ninja Mode.esp") as Armor
	Spell arrow = Game.GetFormFromFile(0x00000835, "Serana Ninja Mode.esp") as Spell
	If !rib || !arrow
		RibcageUp = False
		Return
	EndIf
	Sound snd = Game.GetFormFromFile(0x0001AE79, "UchihaClan.esp") as Sound    ; aaaSusanooSummonMarker
	If snd
		snd.Play(s)
	EndIf
	If s.GetItemCount(rib) == 0
		s.AddItem(rib, 1, True)
	EndIf
	s.EquipItem(rib, True, True)
	Utility.Wait(0.5)    ; the bow forms
	If !t.IsDead()
		arrow.Cast(s, t)
		Debug.Trace("SNJ: Susanoo arrow at " + t.GetDisplayName() + " (" + (s.GetDistance(t) as Int) + ")")
	EndIf
	Utility.Wait(0.9)
	s.UnequipItem(rib, False, True)
	s.RemoveItem(rib, s.GetItemCount(rib), True)
	RibcageUp = False
EndFunction

; The Susanoo blade (mastery 75): for one combo string her Kusanagi is sheathed in Susanoo chakra. Black ice and
; lightning coat the blade (a frost + shock enchantment on the sword she holds: its glow is the coat), it reaches
; further and cuts harder; then it fades and the sword is as it was (its own enchantment, if any, put back).
Float Property SusBladeCooldown = 30.0 AutoReadOnly
Float Property SusBladeSeconds = 7.0 AutoReadOnly
Float Property SusBladeDamage = 0.4 AutoReadOnly
Float Property SusBladeReachMult = 1.3 AutoReadOnly

Bool Function ClaimSusBlade(Float now)
	If SusBladeOn
		Return False
	EndIf
	If LastSusBlade - now > SusBladeCooldown
		LastSusBlade = 0.0    ; from an earlier session
	EndIf
	If now - LastSusBlade <= SusBladeCooldown
		Return False
	EndIf
	SusBladeOn = True
	LastSusBlade = now
	SusBladeSince = now
	Return True
EndFunction

Function SusanooBladeStart(Actor s)
	If !Blade || s.GetEquippedWeapon() != Blade
		SusBladeOn = False
		Return
	EndIf
	SavedBladeEnch = WornObject.GetEnchantment(s, 1, 0)
	SavedBladeCharge = WornObject.GetItemMaxCharge(s, 1, 0)
	MagicEffect[] fx = new MagicEffect[2]
	Float[] mags = new Float[2]
	Int[] areas = new Int[2]
	Int[] durs = new Int[2]
	fx[0] = Game.GetFormFromFile(0x0004605B, "Skyrim.esm") as MagicEffect    ; EnchFrostDamageFFContact
	fx[1] = Game.GetFormFromFile(0x0004605C, "Skyrim.esm") as MagicEffect    ; EnchShockDamageFFContact
	mags[0] = 25.0 + 0.2 * Mastery
	mags[1] = 15.0 + 0.1 * Mastery
	WornObject.CreateEnchantment(s, 1, 0, 9999.0, fx, mags, areas, durs)
	If BaseBladeReach <= 0.0
		BaseBladeReach = Blade.GetReach()
	EndIf
	Blade.SetReach(BaseBladeReach * SusBladeReachMult)    ; in memory only: back to normal after a load anyway
	s.ModActorValue("AttackDamageMult", SusBladeDamage)
	Sound snd = Game.GetFormFromFile(0x0001AE79, "UchihaClan.esp") as Sound    ; aaaSusanooSummonMarker
	If snd
		snd.Play(s)
	EndIf
	Debug.Trace("SNJ: Susanoo blade (frost " + (mags[0] as Int) + ", shock " + (mags[1] as Int) + ")")
EndFunction

Function SusanooBladeEnd(Actor s)
	If !SusBladeOn
		Return
	EndIf
	SusBladeOn = False
	If Blade && s.GetEquippedWeapon() == Blade
		WornObject.SetEnchantment(s, 1, 0, SavedBladeEnch, SavedBladeCharge)
	EndIf
	If Blade && BaseBladeReach > 0.0
		Blade.SetReach(BaseBladeReach)
	EndIf
	s.ModActorValue("AttackDamageMult", -SusBladeDamage)
	SavedBladeEnch = None
	Debug.Trace("SNJ: Susanoo blade fades")
EndFunction

Function SusBladeTick(Actor s, Float now)
	If SusBladeOn && (now - SusBladeSince > SusBladeSeconds || SusBladeSince - now > SusBladeCooldown)
		SusanooBladeEnd(s)
	EndIf
EndFunction

; ---------------- Amenotejikara (Rinnegan, mastery 80) ----------------
; She trades places with anything she can see, in an instant. Blink: a pebble behind a far target (an archer, a caster,
; or anyone out of reach) and she is at their back, Chidori already in her hand. Swap: a blow is about to land and
; she is hurt; she trades places with another enemy, who takes it instead. The Uchiha Clan's Amenotejikara sound and
; visual effect mark both ends.
Float Property AmenoCooldown = 15.0 AutoReadOnly

Bool Function ClaimAmeno(Float now)
	If !IsMangekyo() || Mastery < 80
		Return False
	EndIf
	If LastAmeno - now > AmenoCooldown
		LastAmeno = 0.0    ; from an earlier session
	EndIf
	If now - LastAmeno <= AmenoCooldown
		Return False
	EndIf
	LastAmeno = now
	Return True
EndFunction

Function AmenoFX(Actor s, ObjectReference other)
	Sound a = Game.GetFormFromFile(0x002FBDCE, "UchihaClan.esp") as Sound    ; aaaRinneganAmenotejikaraSoundStart
	Sound b = Game.GetFormFromFile(0x002FBDCF, "UchihaClan.esp") as Sound    ; aaaRinneganAmenotejikaraSoundEnd
	VisualEffect vfx = Game.GetFormFromFile(0x002F962E, "UchihaClan.esp") as VisualEffect    ; aaaRinneganAmenotejikaraVFX
	If a
		a.Play(s)
	EndIf
	If vfx
		vfx.Play(s, 1.0)
		If other
			vfx.Play(other, 1.0)
		EndIf
	EndIf
	If b && other
		b.Play(other)
	EndIf
EndFunction

; Blink: behind the target, facing its back; then the Chidori.
Function AmenoTick(Actor s, Float now)
	If Defending || RibcageUp || Mastery < 80 || now - LastAmeno <= AmenoCooldown
		Return
	EndIf
	Actor t = s.GetCombatTarget()
	If !t || t.IsDead() || IsThrall(t)
		Return
	EndIf
	Float d = s.GetDistance(t)
	If d < 500.0 || d > 2500.0
		Return
	EndIf
	Int plan = PlanFor(t)
	If !(plan == PLAN_ARCHER || plan == PLAN_CASTER || d > 1000.0 || Utility.RandomFloat() < 0.35) || !s.HasLOS(t) || !ClaimAmeno(now)
		Return
	EndIf
	Float az = t.GetAngleZ()
	Float bx = t.GetPositionX() - 110.0 * Math.Sin(az)
	Float by = t.GetPositionY() - 110.0 * Math.Cos(az)
	AmenoFX(s, None)
	s.SetPosition(bx, by, t.GetPositionZ())
	s.SetAngle(0.0, 0.0, az)
	AmenoFX(s, None)
	Debug.Trace("SNJ: Amenotejikara: behind " + t.GetDisplayName() + " (" + (d as Int) + " away)")
	Utility.Wait(0.15)
	If !t.IsDead() && s.GetActorValue("Magicka") >= 20.0
		LastCombo = Utility.GetCurrentRealTime()
		SendAttack(s, 1, "Amenotejikara")    ; Chidori into the back
	EndIf
EndFunction

; Swap: she trades places with another enemy within sight; the blow meant for her lands on it. True if she swapped.
Bool Function AmenoSwap(Actor s, Actor attacker, Float now)
	If RibcageUp || now - LastAmeno <= AmenoCooldown
		Return False
	EndIf
	Actor other = None
	Int k = 0
	While k < 5 && !other
		Actor c = Game.FindRandomActorFromRef(s, 1500.0)
		If c && c != attacker && c != s && !c.IsDead() && !IsFriend(c) && !IsThrall(c) && !c.IsPlayerTeammate() && c.IsHostileToActor(PlayerRef) && s.GetDistance(c) > 250.0 && s.HasLOS(c)
			other = c
		EndIf
		k += 1
	EndWhile
	If !other || !ClaimAmeno(now)
		Return False
	EndIf
	Float sx = s.GetPositionX()
	Float sy = s.GetPositionY()
	Float sz = s.GetPositionZ()
	Float sa = s.GetAngleZ()
	AmenoFX(s, other)
	s.SetPosition(other.GetPositionX(), other.GetPositionY(), other.GetPositionZ())
	other.SetPosition(sx, sy, sz)
	other.SetAngle(0.0, 0.0, sa)
	Debug.Trace("SNJ: Amenotejikara: swapped with " + other.GetDisplayName() + "; " + attacker.GetDisplayName() + "'s blow lands on it")
	Return True
EndFunction

Function MSTick(Actor s, Float now)
	If !IsMangekyo() || Defending
		Return
	EndIf
	If LastBlackFrost > now
		LastBlackFrost = 0.0
	EndIf
	If LastDimhollow > now
		LastDimhollow = 0.0
	EndIf
	If SealedActor && now - SealedSince > 12.0
		SealedActor.SetGhost(False)
		SealedActor = None
	EndIf
	Spell dim = Game.GetFormFromFile(0x00000825, "Serana Ninja Mode.esp") as Spell
	; 1. Dimhollow protects: herself when badly hurt, or you
	If now - LastDimhollow > DimhollowCooldown
		If s.GetActorValuePercentage("Health") < 0.25
			LastDimhollow = now
			MangekyoGaze(s, s)
			dim.Cast(s, s)
			Return
		ElseIf PlayerRef.GetActorValuePercentage("Health") < 0.2 && s.GetDistance(PlayerRef) < 2000.0
			LastDimhollow = now
			MangekyoGaze(s, PlayerRef)
			dim.Cast(s, PlayerRef)
			Debug.Notification("Serana's Mangekyo seals you away from harm.")
			Return
		EndIf
	EndIf
	Actor t = s.GetCombatTarget()
	If !t || t.IsDead()
		Return
	EndIf
	If IsThrall(t)
		s.StopCombat()    ; it is hers now: find a real enemy
		Return
	EndIf
	Float d = s.GetDistance(t)
	; 2. Black Frost: her opening gaze on anything worth it
	MagicEffect frostMark = Game.GetFormFromFile(0x00000822, "Serana Ninja Mode.esp") as MagicEffect
	If now - LastBlackFrost > BlackFrostCooldown && d <= BlackFrostReach && !t.HasMagicEffect(frostMark) && (t.GetActorValuePercentage("Health") > 0.3 || IsBoss(s, t)) && s.GetActorValuePercentage("Health") > 0.3
		Spell frost = Game.GetFormFromFile(0x00000823, "Serana Ninja Mode.esp") as Spell
		LastBlackFrost = now
		FrostHops = 0
		MangekyoGaze(s, t)
		s.DamageActorValue("Health", EyeBleedPct * s.GetBaseActorValue("Health"))    ; the eye bleeds
		frost.Cast(s, t)
		Debug.Trace("SNJ: Black Frost on " + t.GetDisplayName())
		If IsBoss(s, t)
			Debug.Notification("Serana's left eye bleeds: Black Frost.")
		EndIf
		Return
	EndIf
	; 3. Dimhollow seals: shatter a broken foe, or take a second enemy out of the fight
	If now - LastDimhollow > DimhollowCooldown
		Actor victim = None
		If Shatterable(s, t) && d <= 1500.0
			victim = t
		ElseIf EnemiesNear(s, 1500.0) >= 2
			Int k = 0
			While k < 4 && !victim
				Actor a = Game.FindRandomActorFromRef(s, 1500.0)
				If a && a != t && a != s && !a.IsDead() && !IsFriend(a) && !IsThrall(a) && !a.IsPlayerTeammate() && a.IsHostileToActor(PlayerRef) && !IsBoss(s, a)
					victim = a
				EndIf
				k += 1
			EndWhile
		EndIf
		If victim
			LastDimhollow = now
			MangekyoGaze(s, victim)
			dim.Cast(s, victim)
		EndIf
	EndIf
	; 4. a Soul Cairn mind that broke: it fights for her now
	If PendingThrall && now - PendingThrallSince > 4.0
		Actor pt = PendingThrall
		PendingThrall = None
		MakeThrall(s, pt)
	EndIf
EndFunction

; The Soul Cairn: her Mangekyo genjutsu (replaces the three-tomoe one). Called from Dodge.
Function SoulCairn(Actor s, Actor a)
	Spell prison = Game.GetFormFromFile(0x00000827, "Serana Ninja Mode.esp") as Spell
	If prison
		prison.Cast(s, a)
	EndIf
	MangekyoGaze(s, a)
	Debug.Trace("SNJ: Soul Cairn genjutsu on " + a.GetDisplayName())
	If !PendingThrall && !IsBoss(s, a) && a.GetLevel() <= s.GetLevel() && a.HasKeyword(Game.GetFormFromFile(0x00013794, "Skyrim.esm") as Keyword) && Utility.RandomFloat() < ThrallChance
		PendingThrall = a
		PendingThrallSince = Utility.GetCurrentRealTime()
	EndIf
EndFunction

Function MakeThrall(Actor s, Actor a)
	If !a || a.IsDead()
		Return
	EndIf
	If !Thralls
		Thralls = new Actor[4]
	EndIf
	Int slot = -1
	Int i = 0
	While i < Thralls.Length && slot < 0
		If !Thralls[i] || Thralls[i].IsDead()
			slot = i
		EndIf
		i += 1
	EndWhile
	If slot < 0
		Return
	EndIf
	a.StopCombat()
	a.RemoveFromAllFactions()
	a.AddToFaction(Game.GetFormFromFile(0x00000DB1, "Skyrim.esm") as Faction)    ; PlayerFaction
	a.SetPlayerTeammate(True, False)
	Thralls[slot] = a
	CallOffFriendsOn(a)
	Actor foe = s.GetCombatTarget()
	If foe && foe != a && !foe.IsDead()
		a.StartCombat(foe)
	EndIf
	Debug.Notification(a.GetDisplayName() + "'s mind breaks in the Soul Cairn.")
	Debug.Trace("SNJ: Soul Cairn thrall " + a.GetDisplayName())
EndFunction

; Your companions were fighting it a moment ago and keep that target: tell them to stand down.
Function CallOffFriendsOn(Actor a)
	Cell c = a.GetParentCell()
	If !c
		Return
	EndIf
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor o = c.GetNthRef(i, 43) as Actor
		If o && o != a && !o.IsDead() && o.IsPlayerTeammate() && o.GetCombatTarget() == a
			o.StopCombat()
		EndIf
		i += 1
	EndWhile
EndFunction

; The fight is over: the broken minds go with it.
Function EndThralls()
	If !Thralls
		Return
	EndIf
	Int i = 0
	While i < Thralls.Length
		Actor a = Thralls[i]
		If a && !a.IsDead()
			a.Kill()
			Debug.Trace("SNJ: Soul Cairn thrall " + a.GetDisplayName() + " is gone")
		EndIf
		Thralls[i] = None
		i += 1
	EndWhile
	PendingThrall = None
EndFunction

; ---------------- Sharingan eyes ----------------

Function PlaySound(Actor s, Int id)
	Sound snd = Game.GetFormFromFile(id, "naruto overhaul.esp") as Sound
	If snd
		snd.Play(s)
	EndIf
EndFunction

; Female Sharingan eyes (Naruto Overhaul head parts, meshes from The Uchiha Clan): 1, 2, 3 tomoe.
; Genin and one tomoe both show one tomoe: the eye is there from the start, its power comes with mastery.
Int Function TomoeForTier()
	If CurTier >= 5 && Mastery >= 80
		Return 5    ; the Rinnegan (Sasuke's: six tomoe)
	ElseIf CurTier >= 5
		Return 4    ; the Mangekyo
	ElseIf CurTier >= 4
		Return 3
	ElseIf CurTier == 3
		Return 2
	EndIf
	Return 1
EndFunction

; Serana's face is a pre-built FaceGen head (Serana DF Edit's own NPC, SeranaDFE.esp 0x82C), so swapping head parts
; never shows (ChangeHeadPart and ReplaceHeadPart were both tried, 2026-10-17). Instead her own eye mesh keeps its
; shape and RaceMenu's NiOverride swaps its textures: diffuse (index 0) to the Naruto Overhaul Sharingan, glow (index 2)
; to the Uchiha Clan glow map, so the tomoe glow red. Persisted: RaceMenu reapplies it after a load by itself.
String Property EyeNode = "SDFEyes" AutoReadOnly
{Her eyeball's node in the FaceGen head (Serana DF Edit's SDFEyes head part; its extra parts are SDFLashes and GlowLens).}
String Property LensNode = "GlowLens" AutoReadOnly
{The glowing lens Serana DF Edit lays over her eyes (her blue glow). Hidden while the Sharingan shows.}
String Property OldNode = "SDFEyeFemaleShadow" AutoReadOnly
{The shadow shell: the first NiOverride build targeted it by mistake; its overrides are cleared.}
Bool Property ShowEyeDiagnostics = False AutoReadOnly
{Shows the eye node and whether RaceMenu holds the override, on activation (2026-10-18, while the eyes are being fixed).}

Function ShowEyes(Actor s, Bool force)
	Int want = TomoeForTier()
	If !force && want == EyesShown
		Return
	EndIf
	If !s.Is3DLoaded()
		Return
	EndIf
	ClearNode(s, OldNode)
	String tex = "textures\\SNJ\\eyes\\sharingan" + want + ".dds"
	If want >= 5
		tex = "textures\\SNJ\\eyes\\rinnegan.dds"    ; six tomoe on the ripples (make_rinnegan.py)
	ElseIf want >= 4
		tex = "textures\\SNJ\\eyes\\mangekyo.dds"    ; eclipsed sun, bat wings (make_mangekyo.py)
	EndIf
	NiOverride.AddNodeOverrideString(s, True, EyeNode, 9, 0, tex, True)    ; fitted to her iris (tools/make_eye_textures.py)
	If NiOverride.HasNodeOverride(s, True, EyeNode, 9, 2)    ; no glow map any more: the red glow hid the tomoe
		NiOverride.RemoveNodeOverride(s, True, EyeNode, 9, 2)
		If !s.IsOnMount()
			s.QueueNiNodeUpdate()    ; once: wash the old red glow off her loaded head (RaceMenu reapplies the rest)
		EndIf
	EndIf
	NiOverride.AddNodeOverrideFloat(s, True, LensNode, 8, -1, 0.0, True)    ; ShaderAlpha 0: no blue glow over the tomoe
	NiOverride.ApplyNodeOverrides(s)
	EyesShown = want
	Bool held = NiOverride.HasNodeOverride(s, True, EyeNode, 9, 0)
	Debug.Trace("SNJ: Sharingan eyes, " + want + " tomoe on node " + EyeNode + " (override held " + held + ")")
	If force && ShowEyeDiagnostics
		Debug.Notification("Sharingan eyes: node '" + EyeNode + "', override held " + held + ", tomoe " + want)
	EndIf
EndFunction

Function RestoreEyes(Actor s)
	ClearNode(s, EyeNode)
	ClearNode(s, OldNode)
	If NiOverride.HasNodeOverride(s, True, LensNode, 8, -1)
		NiOverride.RemoveNodeOverride(s, True, LensNode, 8, -1)
	EndIf
	EyesShown = 0
	; removing an override only stops RaceMenu reapplying it; rebuilding her loaded model brings back her own eyes
	If s.Is3DLoaded() && !s.IsOnMount()
		s.QueueNiNodeUpdate()
	EndIf
	Debug.Trace("SNJ: Sharingan off, her own eyes back")
EndFunction

Function ClearNode(Actor s, String node)
	If NiOverride.HasNodeOverride(s, True, node, 9, 0)
		NiOverride.RemoveNodeOverride(s, True, node, 9, 0)
	EndIf
	If NiOverride.HasNodeOverride(s, True, node, 9, 2)
		NiOverride.RemoveNodeOverride(s, True, node, 9, 2)
	EndIf
EndFunction

HeadPart Function BaseEyes(Actor s)
	ActorBase b = s.GetActorBase()
	Int i = b.GetNumHeadParts()
	While i > 0
		i -= 1
		HeadPart hp = b.GetNthHeadPart(i)
		If hp && hp.GetType() == 2    ; eyes
			Return hp
		EndIf
	EndWhile
	Return None
EndFunction

; The first build used ChangeHeadPart, which put the Sharingan into her base record (it never showed, but it could
; if her head were ever rebuilt from the base). Put her own eyes back there, once.
Function RepairBase(Actor s)
	If BaseRepaired || !OrigEyes
		Return
	EndIf
	BaseRepaired = True
	HeadPart cur = BaseEyes(s)
	If cur && cur != OrigEyes
		s.ChangeHeadPart(OrigEyes)
		Debug.Trace("SNJ: her base eyes put back to " + OrigEyes + " (were " + cur + ")")
	EndIf
EndFunction

; ---------------- defence: parry, dodge, riposte (offered by the shared watcher in WOTW_QuestScript) ----------------
; tiers: 1 Genin, 2 one tomoe, 3 two tomoe, 4 three tomoe, 5 awakened

Float Function ParryChance()
	Float c = 0.15 + 0.05 * CurTier             ; 20 .. 40 %
	If Era() == 1
		c = c * 0.5      ; the kid's inexperience
	ElseIf Era() == 3
		c += 0.05        ; Taka: patient, reads the strike
	EndIf
	Return c
EndFunction

Float Function DodgeChance()
	Return 0.25 + 0.05 * CurTier             ; 30 .. 50 % of what she does not parry
EndFunction

Float Function RangedDodgeChance()
	Return 0.25 + 0.1 * CurTier              ; 35 .. 75 %
EndFunction

Float Function RangedChanceVs(Actor a, String ev)
	Float c = RangedDodgeChance() + PlanRangedBonus(a, ev)
	If c > 0.85
		c = 0.85
	EndIf
	Return c
EndFunction

Float Function DefendCooldown()
	Return 2.2 - 0.2 * CurTier               ; 2.0 .. 1.2 s
EndFunction

; True if Ninja Mode handled the event (the shared watcher then does nothing else with it).
Bool Function Defend(Actor s, Actor a, String ev, Float d)
	If !NinjaOn
		Return False
	EndIf
	If Defending || !a || a.IsDead()
		Return True
	EndIf
	Float now = Utility.GetCurrentRealTime()
	GuardClocks(now)
	If now - LastDefend < DefendCooldown() || s.IsInKillMove() || s.GetSitState() != 0
		Return True
	EndIf
	If Era() == 1 && now - LastCombo < 1.0 && ev == "preHitFrame"
		Debug.Trace("SNJ defend: kid mid-string, she trades")
		Return True    ; the kid commits to her string (a dodge or parry here would break it)
	EndIf
	Float stamina = s.GetActorValue("Stamina")
	If ev == "preHitFrame"
		If d > 350.0
			Return True
		EndIf
		If Mastery >= 80 && IsMangekyo() && s.GetActorValuePercentage("Health") < 0.5 && Utility.RandomFloat() < 0.5 && AmenoSwap(s, a, now)
			LastDefend = now
			Return True
		EndIf
		If RibcageReady(now) && (IsBoss(s, a) || s.GetActorValuePercentage("Health") < 0.5 || Utility.RandomFloat() < 0.25) && ClaimRibcage(now)
			LastDefend = now
			FlashRibcage(s, a.GetDisplayName() + "'s blow")
			Return True
		EndIf
		Float r = Utility.RandomFloat()
		Float parry = ParryChance() + PlanParryBonus(a)
		If parry > 0.5
			parry = 0.5
		EndIf
		If r < parry && stamina >= 5.0
			LastDefend = now
			Parry(s, a)
		ElseIf r < parry + (1.0 - parry) * DodgeChance() && stamina >= DodgeStamina
			LastDefend = now
			Dodge(s, a, True)
		Else
			Debug.Trace("SNJ defend: " + a.GetDisplayName() + "'s strike gets through")
		EndIf
	ElseIf d <= 3000.0 && RibcageReady(now) && (s.GetActorValuePercentage("Health") < 0.5 || SpellElement(a, ev) == 1) && ClaimRibcage(now)
		LastDefend = now
		FlashRibcage(s, a.GetDisplayName() + "'s " + ev)    ; fire, or she is hurt: the ribcage takes it
	ElseIf d <= 3000.0 && Utility.RandomFloat() < RangedChanceVs(a, ev) && stamina >= DodgeStamina
		LastDefend = now
		Dodge(s, a, False)
	EndIf
	Return True
EndFunction

; A timed block: Elden Parry (NPC parry on, 0.3 s window) turns it into a parry that staggers the attacker.
Function Parry(Actor s, Actor a)
	Defending = True
	Debug.SendAnimationEvent(s, "blockStart")
	Utility.Wait(0.45)
	Debug.SendAnimationEvent(s, "blockStop")
	Debug.Trace("SNJ defend: parry vs " + a.GetDisplayName() + " (tier " + CurTier + ")")
	; riposte: a cut, or from two tomoe a jutsu half the time
	Int slot = 0
	If CurTier >= 3 && Utility.RandomFloat() < 0.5
		slot = 3 + Utility.RandomInt(0, 1)
	EndIf
	If !a.IsDead() && s.GetDistance(a) <= ComboReach
		LastCombo = Utility.GetCurrentRealTime()
		SendAttack(s, slot, "riposte")
	EndIf
	Defending = False
EndFunction

Function Dodge(Actor s, Actor a, Bool melee)
	Defending = True
	String dodge
	Float r = Utility.RandomFloat()
	If melee && r < 0.4
		dodge = "DodgeBack"
	ElseIf r < 0.7
		dodge = "DodgeLeft"
	Else
		dodge = "DodgeRight"
	EndIf
	s.DamageActorValue("Stamina", DodgeStamina)
	Debug.SendAnimationEvent(s, dodge)
	Debug.Trace("SNJ defend: " + dodge + " from " + a.GetDisplayName() + " (tier " + CurTier + ", melee " + melee + ")")
	If melee && CurTier >= 3
		; two tomoe: she saw it coming and answers it
		PendingCounter = 3 + Utility.RandomInt(0, 1)
		Float now = Utility.GetCurrentRealTime()
		; three tomoe: now and then the one who attacked her is caught in a genjutsu for a moment
		If CurTier >= 5 && now - LastGenjutsu > 8.0 && Utility.RandomFloat() < 0.6
			LastGenjutsu = now
			SoulCairn(s, a)
		ElseIf CurTier >= 4 && now - LastGenjutsu > 8.0 && Utility.RandomFloat() < 0.3 + 0.15 * (CurTier - 4)
			LastGenjutsu = now
			a.SetAnimationVariableFloat("staggerMagnitude", 1.0)
			Debug.SendAnimationEvent(a, "staggerStart")
			Spell para = Game.GetFormFromFile(0x000C1E99, "Skyrim.esm") as Spell    ; PerkGrandmaster1HParalyze
			If para
				para.Cast(s, a)
			EndIf
			Debug.Trace("SNJ: Sharingan genjutsu on " + a.GetDisplayName())
		EndIf
		Utility.Wait(0.5)
		If PendingCounter > 0 && !a.IsDead() && s.GetDistance(a) <= ComboReach && Utility.GetCurrentRealTime() - LastWindow > 0.6
			Int slot = PendingCounter
			PendingCounter = 0
			LastCombo = Utility.GetCurrentRealTime()
			SendAttack(s, slot, "Sharingan counter")
		EndIf
	EndIf
	Defending = False
EndFunction

; ---------------- Ninja Mastery ----------------

Float Function RankCost(Int rank)
	Return RankCostBase + RankCostStep * rank
EndFunction

Function OnStrike(Actor s)
	Actor t = s.GetCombatTarget()
	If !t || t.IsDead() || s.GetDistance(t) > HitReach || Math.Abs(s.GetHeadingAngle(t)) > 60.0
		Return
	EndIf
	GainMastery(s, 1.0)
	ObserveStrike(t)
	If Era() == 1
		KidStrike(s, t)
	EndIf
EndFunction

Function GainMastery(Actor s, Float pts)
	If Mastery >= 100
		Return
	EndIf
	MasteryPoints += pts
	While Mastery < 100 && MasteryPoints >= RankCost(Mastery)
		MasteryPoints -= RankCost(Mastery)
		Mastery += 1
		AnnounceRank(Mastery)
	EndWhile
	UpdateTier(s, True)
EndFunction

Function CheckSetMastery(Actor s)
	If !SetMasteryGlobal
		Return
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
	UpdateTier(s, False)
	ApplyBuffs(s)
	Debug.Notification("Serana: Ninja Mastery set to " + Mastery + " (" + TierName(CurTier) + ").")
EndFunction

Function AnnounceRank(Int r)
	String unlock = ""
	If r == 10
		unlock = " Two tomoe: she reads faster and answers what she reads."
	ElseIf r == 17
		unlock = " Three tomoe: she reads an opponent in a moment, and her genjutsu wakes."
	ElseIf r == 25
		unlock = " Hebi: she takes up the Kusanagi. The Mark of Coldharbour answers her more readily now."
	ElseIf r == 50
		unlock = " Her Mangekyo Sharingan awakens, and burns Molag Bal's mark out of her blood: Black Frost, Dimhollow, the Soul Cairn."
	ElseIf r == 55
		unlock = " Susanoo: for a moment, a ribcage of black ice takes the blow meant for her."
	ElseIf r == 65
		unlock = " Susanoo: a bow of black ice forms in her hands for a single arrow."
	ElseIf r == 75
		unlock = " Susanoo: for a string of cuts, black ice and lightning sheathe the Kusanagi."
	ElseIf r == 80
		unlock = " Her Rinnegan awakens, born of her bond with Obito: Amenotejikara, she trades places with anything she can see."
	EndIf
	If r % 5 == 0 || unlock != ""
		Debug.Notification("Serana: Ninja Mastery " + r + "." + unlock)
	EndIf
EndFunction

String Function TierName(Int t)
	If t == 5
		Return "Mangekyo Sharingan"
	ElseIf t == 4
		Return "Sharingan, three tomoe"
	ElseIf t == 3
		Return "Sharingan, two tomoe"
	ElseIf t == 2
		Return "Sharingan, one tomoe"
	EndIf
	Return "Genin"
EndFunction

; Only mastery opens her eyes (the user's call): no level shortcut here, unlike the Witch's grimoire.
; 2026-10-17: the mode leans on the Sharingan, so it comes sooner: one tomoe (with reads) from the start,
; two tomoe at 25, three at 50, awakened at 80. (Tier 1, Genin, is no longer used.)
Int Function WantedTier()
	If Mastery >= 50
		Return 5    ; Mangekyo (Taka)
	ElseIf Mastery >= 17
		Return 4    ; three tomoe (end of Part 1, kept through Hebi)
	ElseIf Mastery >= 10
		Return 3    ; two tomoe
	EndIf
	Return 2        ; one tomoe
EndFunction

Function UpdateTier(Actor s, Bool announce)
	If !NinjaOn
		Return
	EndIf
	Int t = WantedTier()
	If t != CurTier || !s.HasSpell(Game.GetFormFromFile(0x0000080A + t, "Serana Ninja Mode.esp") as Spell)
		SetTierAbility(s, t)
	EndIf
EndFunction

Function SetTierAbility(Actor s, Int t)
	Int i = 1
	While i <= 5
		Spell ab = Game.GetFormFromFile(0x0000080A + i, "Serana Ninja Mode.esp") as Spell
		If ab
			If i == t
				If !s.HasSpell(ab)
					s.AddSpell(ab, False)
				EndIf
			ElseIf s.HasSpell(ab)
				s.RemoveSpell(ab)
			EndIf
		EndIf
		i += 1
	EndWhile
	CurTier = t
EndFunction

; Leaf training: lighter on her feet out of heavy armour, and her blade cuts deeper as she grows.
Function ApplyBuffs(Actor s)
	Float speed = 0.0
	If !s.WornHasKeyword(Game.GetFormFromFile(0x0006BBD2, "Skyrim.esm") as Keyword)    ; no ArmorHeavy
		speed = 5.0 * CurTier
	EndIf
	Float dmg = 0.1 * (CurTier - 1) + 0.002 * s.GetLevel()
	If speed != AppliedSpeed
		s.ModActorValue("SpeedMult", speed - AppliedSpeed)
		AppliedSpeed = speed
		s.ModActorValue("CarryWeight", 0.1)     ; SpeedMult only takes effect when carry weight changes
		s.ModActorValue("CarryWeight", -0.1)
	EndIf
	If dmg != AppliedDamage
		s.ModActorValue("AttackDamageMult", dmg - AppliedDamage)
		AppliedDamage = dmg
	EndIf
	Float unarmed = 0.0
	If Era() == 1
		; the kid's kicks hit as hard as the Kusanagi would (as Taekwondo mode sizes her fists), and harder with mastery
		Float bladeDmg = 0.0
		If Blade
			bladeDmg = Blade.GetBaseDamage() * (1.0 + s.GetActorValue("OneHanded") * 0.005)
		EndIf
		unarmed = 12.0 + 1.5 * s.GetLevel()
		If bladeDmg > unarmed
			unarmed = bladeDmg
		EndIf
		unarmed = unarmed * (1.0 + 0.02 * Mastery)    ; up to +48% by mastery 24
	EndIf
	If unarmed != AppliedUnarmed
		s.ModActorValue("UnarmedDamage", unarmed - AppliedUnarmed)
		AppliedUnarmed = unarmed
	EndIf
	; chakra control: the Sharingan wastes nothing, so she recovers magicka and stamina faster while fighting
	Float magRate = 0.0
	Float stamRate = 0.0
	If s.IsInCombat()
		magRate = 25.0 * (CurTier - 1)
		stamRate = 20.0 * (CurTier - 1)
	EndIf
	If magRate != AppliedMagRate
		s.ModActorValue("MagickaRateMult", magRate - AppliedMagRate)
		AppliedMagRate = magRate
	EndIf
	If stamRate != AppliedStamRate
		s.ModActorValue("StaminaRateMult", stamRate - AppliedStamRate)
		AppliedStamRate = stamRate
	EndIf
EndFunction

Function ClearBuffs(Actor s)
	s.ModActorValue("SpeedMult", -AppliedSpeed)
	s.ModActorValue("AttackDamageMult", -AppliedDamage)
	s.ModActorValue("UnarmedDamage", -AppliedUnarmed)
	AppliedUnarmed = 0.0
	s.ModActorValue("MagickaRateMult", -AppliedMagRate)
	s.ModActorValue("StaminaRateMult", -AppliedStamRate)
	AppliedMagRate = 0.0
	AppliedStamRate = 0.0
	If AppliedSpeed != 0.0
		s.ModActorValue("CarryWeight", 0.1)
		s.ModActorValue("CarryWeight", -0.1)
	EndIf
	AppliedSpeed = 0.0
	AppliedDamage = 0.0
EndFunction

; ---------------- upkeep ----------------

Event OnUpdate()
	If !NinjaOn
		Return
	EndIf
	Actor s = Serana()
	If s && !s.IsDead()
		Float now = Utility.GetCurrentRealTime()
		GuardClocks(now)
		; eye changes are not saved and drop when her 3D reloads: put them back after a load or a cell change
		Bool loaded = s.Is3DLoaded()
		If loaded && (!WasLoaded || now < LastTickReal)
			ShowEyes(s, True)
		ElseIf loaded
			ShowEyes(s, False)    ; tier changed: more tomoe
		EndIf
		WasLoaded = loaded
		LastTickReal = now
		CheckSetMastery(s)
		If GearEra != Era()
			EraGear(s)    ; she grew into a new era
		EndIf
		Shinobi(s)
		UpdateTier(s, True)
		ApplyBuffs(s)
		If s.IsInCombat()
			If !WasFighting
				Debug.Trace("SNJ state: tier " + CurTier + ", mastery " + Mastery + ", right hand " + s.GetEquippedWeapon() + ", magicka " + (s.GetActorValue("Magicka") as Int))
			EndIf
			WasFighting = True
			OpenerTick(s, now)
			ChidoriTick(s, now)
			MSTick(s, now)
			RibcageTick(s, now)
			BowTick(s, now)
			SusBladeTick(s, now)
			AmenoTick(s, now)
			KunaiTick(s)
			CurseTick(s, now)
		ElseIf WasFighting
			WasFighting = False
			PendingCounter = 0
			WantKirin = False
			KirinQueued = False
			ClearReads()    ; a new fight, new reads
			SusanooBladeEnd(s)
			CurseEnd(s)
			If KunaiOut
				KunaiOut = False
				EraGear(s)    ; the kunai goes away when the fight is over
			EndIf
			EndThralls()
		EndIf
	EndIf
	RegisterForSingleUpdate(UpkeepSeconds)
EndEvent

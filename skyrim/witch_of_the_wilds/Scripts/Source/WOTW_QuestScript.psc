Scriptname WOTW_QuestScript extends Quest
{Serana: Witch of the Wilds. The ranged, spellcasting counterpart of the Taekwondo toggle (CTKD).
On: her weapons go into a hidden chest and she takes up a Stalhrim Bladestaff (BladeStaff.esp). The Dragon Age
Staff Moveset's Ice clips, copied per Grimoire tier into OAR folders that only she uses, cast her spells through
Payload Interpreter (SKSE/PayloadInterpreter/Config/WitchOfTheWilds.ini). Her AI keeps its distance, and this
script drives her casting: it chains her staff combos and opens from range, where the AI alone would walk in.
Flemeth's Grimoire (0-100) grows with every spell she casts and, with her level, opens higher spell tiers.
Blood Magic (Grimoire 20) turns her blood into magicka; when her reserves run dry she feeds on weakened enemies,
never on bystanders.
The dodge reflex works in both modes (here and in Taekwondo): she slips aside from strikes, spells and arrows
on a short cooldown, using the DMCO dodge; in this mode the dodge bursts into bats.
Needs SKSE (GetNthForm, GetWeaponType, Get/SetCombatStyle).}

Actor Property PlayerRef Auto
Spell Property TogglePower Auto
Container Property StorageBase Auto
{Empty, non-respawning container. One disabled copy is placed to hold Serana's weapons.}
CombatStyle Property WitchStyle Auto
{WOTW_WitchStyle: staff caster that keeps her distance. Swapped in while the mode is on.}
GlobalVariable Property SetGrimoireGlobal Auto
{WOTW_SetGrimoire: test hook. 'set WOTW_SetGrimoire to <0-100>' in the console sets her rank; -1 = idle.}

Float Property UpkeepSeconds = 1.0 AutoReadOnly
Float Property CastReach = 2500.0 AutoReadOnly
{The staff driver keeps casting while her target is this close.}
Float Property OpenerMinDistance = 400.0 AutoReadOnly
Float Property OpenerIdleSeconds = 2.0 AutoReadOnly
{At range the AI would walk in instead of casting: after this long without a cast, the script starts one.}
Float Property DodgeCooldown = 2.5 AutoReadOnly
Float Property DodgeMeleeReach = 350.0 AutoReadOnly
Float Property DodgeRangedReach = 3000.0 AutoReadOnly
Float Property DodgeRangedChance = 0.6 AutoReadOnly
Float Property FeedReach = 400.0 AutoReadOnly
Float Property FeedCooldown = 20.0 AutoReadOnly
Float Property FeedPreyHealthPct = 0.6 AutoReadOnly
{She only feeds on enemies at or below this much health. At or below FeedKillPct the feeding kills.}
Float Property FeedKillPct = 0.3 AutoReadOnly
Float Property BiteSeconds = 4.0 AutoReadOnly
{How long she drinks. Only silver or fire can break the bite.}
Float Property BloodCooldown = 6.0 AutoReadOnly
Float Property UltCooldown = 45.0 AutoReadOnly
Float Property SummonCooldown = 60.0 AutoReadOnly
Float Property BatsCooldown = 15.0 AutoReadOnly
Float Property RankCostBase = 15.0 AutoReadOnly
Float Property RankCostStep = 0.3 AutoReadOnly
{Casts needed for the next Grimoire rank = base + step x rank (about 3000 casts for rank 100).}

ObjectReference Storage
Bool WitchOn = False
Weapon PrevWeapon
Weapon Staff
CombatStyle SavedStyle
Float GrimoirePoints = 0.0
Int Grimoire = 0
Int CurTier = 0
Bool Feeding = False
Bool BiteBroken = False
Actor BiteVictim
Bool WasFighting = False
Actor[] Watched
Float AppliedMagicka = 0.0
Float AppliedSpeed = 0.0
Float AppliedMagRate = 0.0
; real-time stamps (GetCurrentRealTime restarts every launch; GuardClocks resets any from an earlier session)
Float LastWindow = 0.0
Float LastCombo = 0.0
Float LastDodge = 0.0
Float LastFeed = 0.0
Float LastBlood = 0.0
Float LastUlt = 0.0
Float LastSummon = 0.0
Float LastBats = 0.0

Event OnInit()
	PlayerRef.AddSpell(TogglePower)
	RegisterForSingleUpdate(5.0)    ; starts the loyalty guard
EndEvent

Actor Function Serana()
	Return Game.GetFormFromFile(0x00002B74, "Dawnguard.esm") as Actor
EndFunction

CTKD_QuestScript Function Juri()
	Return Game.GetFormFromFile(0x00000800, "Serana Taekwondo Toggle.esp") as CTKD_QuestScript
EndFunction

Bool Function JuriOn()
	CTKD_QuestScript q = Juri()
	Return q && q.IsOn()
EndFunction

Bool Function IsOn()
	Return WitchOn
EndFunction

; Serana Ninja Mode.esp (optional): the third mode. Its Sharingan tunes the dodge reflex below.
SNJ_QuestScript Function Ninja()
	Return Game.GetFormFromFile(0x00000800, "Serana Ninja Mode.esp") as SNJ_QuestScript
EndFunction

Bool Function NinjaOn()
	SNJ_QuestScript n = Ninja()
	Return n && n.IsOn()
EndFunction

; Called by the Taekwondo toggle after it changes, so the dodge reflex starts (or stops) with it.
Function Wake()
	RegisterForSingleUpdate(0.5)
EndFunction

Function Toggle()
	Actor s = Serana()
	If !s || s.IsDead() || s.IsDisabled()
		Debug.Notification("Serana isn't available.")
		Return
	EndIf
	If WitchOn
		StaffOff(s)
	Else
		If JuriOn()
			Juri().Toggle()    ; one mode at a time: Taekwondo gives her weapons back first
		EndIf
		If NinjaOn()
			Ninja().Toggle()   ; and Ninja Mode its Kusanagi
		EndIf
		StaffOn(s)
	EndIf
	RegisterForSingleUpdate(0.5)
EndFunction

Function StaffOn(Actor s)
	Staff = Game.GetFormFromFile(0x00000809, "BladeStaff.esp") as Weapon    ; Stalhrim Bladestaff
	If !Staff
		Debug.Notification("Witch of the Wilds needs Bladestaff of Skyrim (BladeStaff.esp).")
		Return
	EndIf
	If !Storage
		Storage = PlayerRef.PlaceAtMe(StorageBase, 1, True, True)
	EndIf
	PrevWeapon = s.GetEquippedWeapon()
	Int i = s.GetNumItems()
	While i > 0
		i -= 1
		Weapon w = s.GetNthForm(i) as Weapon
		If w && w != Staff
			s.RemoveItem(w, s.GetItemCount(w), True, Storage)
		EndIf
	EndWhile
	If s.GetItemCount(Staff) == 0
		s.AddItem(Staff, 1, True)
	EndIf
	s.EquipItem(Staff, True, True)    ; kept equipped: hand spells would drop the staff moveset
	WitchOn = True
	UpdateTier(s, False)
	Witchy(s)
	Debug.Notification("Serana: Witch of the Wilds. Grimoire " + Grimoire + " (" + TierName(CurTier) + ").")
EndFunction

Function StaffOff(Actor s)
	WitchOn = False
	If !Feeding
		s.SetGhost(False)    ; never leave her untouchable
	EndIf
	ClearBuffs(s)
	SetTierAbility(s, 0)
	If Staff
		s.UnequipItem(Staff, False, True)
		s.RemoveItem(Staff, s.GetItemCount(Staff), True)
	EndIf
	If Storage
		Storage.RemoveAllItems(s, False, True)
	EndIf
	If PrevWeapon && s.GetItemCount(PrevWeapon) > 0
		s.EquipItem(PrevWeapon, False, True)
	EndIf
	UnregisterForAnimationEvent(s, "MCO_WinOpen")
	UnregisterForAnimationEvent(s, "SCAR_ComboStart")
	UnregisterForAnimationEvent(s, "weaponSwing")
	If SavedStyle
		s.GetActorBase().SetCombatStyle(SavedStyle)
		SavedStyle = None
	EndIf
	s.EvaluatePackage()
	Debug.Notification("Serana sets the staff aside. Grimoire " + Grimoire + ".")
EndFunction

; Witch AI: her own combat style is a hand caster's, so swap in the staff style, and tell Combat Pathing
; Revolution to circle wide and fall back instead of closing in. Base-form combat style changes are not saved,
; so this is re-applied every tick while the mode is on.
Function Witchy(Actor s)
	ActorBase b = s.GetActorBase()
	CombatStyle cur = b.GetCombatStyle()
	If cur != WitchStyle
		If !SavedStyle
			SavedStyle = cur    ; Taekwondo has already put her own style back by now (one mode at a time)
		EndIf
		b.SetCombatStyle(WitchStyle)
	EndIf
	If !s.Is3DLoaded() || !s.IsWeaponDrawn()
		Return
	EndIf
	s.SetAnimationVariableBool("CPR_EnableBackoff", True)
	s.SetAnimationVariableFloat("CPR_BackoffChance", 0.6)
	s.SetAnimationVariableBool("CPR_EnableCircling", True)
	s.SetAnimationVariableFloat("CPR_CirclingDistMin", 500.0)
	s.SetAnimationVariableFloat("CPR_CirclingDistMax", 900.0)
	s.SetAnimationVariableBool("CPR_EnableFallback", True)
	s.SetAnimationVariableFloat("CPR_FallbackDistMin", 250.0)
	s.SetAnimationVariableFloat("CPR_FallbackDistMax", 600.0)
	s.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", 0.5)
	s.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", 1.5)
	RegisterForAnimationEvent(s, "MCO_WinOpen")
	RegisterForAnimationEvent(s, "SCAR_ComboStart")
	RegisterForAnimationEvent(s, "weaponSwing")
EndFunction

Function GuardClocks(Float now)
	If LastWindow > now
		LastWindow = 0.0
	EndIf
	If LastCombo > now
		LastCombo = 0.0
	EndIf
	If LastDodge > now
		LastDodge = 0.0
	EndIf
	If LastFeed > now
		LastFeed = 0.0
	EndIf
	If LastBlood > now
		LastBlood = 0.0
	EndIf
	If LastUlt > now
		LastUlt = 0.0
	EndIf
	If LastSummon > now
		LastSummon = 0.0
	EndIf
	If LastBats > now
		LastBats = 0.0
	EndIf
EndFunction

Bool Function ValidTarget(Actor s, Actor t, Float reach)
	Return t && !t.IsDead() && s.GetDistance(t) <= reach
EndFunction

; ---------------- staff driver ----------------

; Power attack slots of the Ice clips: 1-2 Winter's Grasp / Cone of Cold, 3 storm, 4 Drain Life,
; 5 the big finisher (cloak + Blizzard), 6 Bat Swarm, 7 Gargoyle. 0 = light attack (her bolt).
Int Function PickPower(Actor s, Actor t, Float now)
	Float m = s.GetActorValue("Magicka")
	Float hp = s.GetActorValuePercentage("Health")
	Float ultCd = UltCooldown
	If Grimoire >= 100
		ultCd = UltCooldown / 2.0
	EndIf
	If m >= 150.0 && now - LastUlt > ultCd && (CountEnemies(s) >= 3 || t.GetLevel() >= s.GetLevel() || hp < 0.5)
		LastUlt = now
		Return 5
	EndIf
	If m >= 50.0 && now - LastSummon > SummonCooldown
		LastSummon = now
		Return 7
	EndIf
	If m >= 35.0 && s.GetDistance(t) < 350.0 && now - LastBats > BatsCooldown
		LastBats = now
		Return 6
	EndIf
	Float roll = Utility.RandomFloat()
	If m >= 20.0 && hp < 0.6 && roll < 0.5
		Return 4
	ElseIf m >= 50.0 && roll < 0.25
		Return 3
	ElseIf m >= 35.0 && roll < 0.55
		Return 1
	EndIf
	Return 0
EndFunction

Function SendCast(Actor s, Actor t, Float now, String why)
	Int slot = PickPower(s, t, now)
	LastCombo = now
	If slot > 0
		s.SetAnimationVariableInt("MCO_nextpowerattack", slot)
		Debug.SendAnimationEvent(s, "attackPowerStartInPlace")
		Debug.Trace("WOTW: " + why + " -> power " + slot + " (magicka " + (s.GetActorValue("Magicka") as Int) + ", grimoire " + Grimoire + ")")
	Else
		Debug.SendAnimationEvent(s, "attackStart")
		Debug.Trace("WOTW: " + why + " -> bolt (magicka " + (s.GetActorValue("Magicka") as Int) + ", grimoire " + Grimoire + ")")
	EndIf
EndFunction

; Long range: the AI walks toward her target with the staff (it is a warhammer to the game); if she has not
; cast for a moment and the target is in reach, start a cast from where she stands.
Function OpenerTick(Actor s, Float now)
	If Feeding || !s.IsWeaponDrawn()
		Return
	EndIf
	Actor t = s.GetCombatTarget()
	If !ValidTarget(s, t, CastReach) || s.GetDistance(t) < OpenerMinDistance
		Return
	EndIf
	If now - LastWindow > OpenerIdleSeconds && now - LastCombo > OpenerIdleSeconds
		SendCast(s, t, now, "opener at " + (s.GetDistance(t) as Int))
	EndIf
EndFunction

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	Actor s = Serana()
	If !s || s.IsDead()
		Return
	EndIf
	If akSource != s
		OnEnemyEvent(s, akSource as Actor, asEventName)
		Return
	EndIf
	If !WitchOn || !s.IsInCombat()
		Return
	EndIf
	If asEventName == "weaponSwing"
		GainGrimoire(s, 1.0)    ; every staff swing casts a spell
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	GuardClocks(now)
	LastWindow = now
	If now - LastCombo < 0.25 || Feeding
		Return    ; MCO_WinOpen and SCAR_ComboStart arrive together
	EndIf
	Actor t = s.GetCombatTarget()
	If ValidTarget(s, t, CastReach)
		SendCast(s, t, now, asEventName)
	EndIf
EndEvent

; ---------------- dodge reflex (both modes) ----------------

Bool Function Hostile(Actor s, Actor a)
	If !a || a == s || a == PlayerRef || a.IsDead() || a.IsPlayerTeammate() || !a.IsInCombat()
		Return False
	EndIf
	Actor ct = a.GetCombatTarget()
	Return ct == s || ct == PlayerRef || a.IsHostileToActor(PlayerRef)
EndFunction

Int Function CountEnemies(Actor s)
	Int n = 0
	Int i = 0
	While Watched && i < Watched.Length
		If Watched[i] && Hostile(s, Watched[i])
			n += 1
		EndIf
		i += 1
	EndWhile
	Return n
EndFunction

Function Unwatch()
	Int i = 0
	While Watched && i < Watched.Length
		If Watched[i]
			UnregisterForAnimationEvent(Watched[i], "preHitFrame")
			UnregisterForAnimationEvent(Watched[i], "BeginCastLeft")
			UnregisterForAnimationEvent(Watched[i], "BeginCastRight")
			UnregisterForAnimationEvent(Watched[i], "bowDraw")
			Watched[i] = None
		EndIf
		i += 1
	EndWhile
EndFunction

Function AddWatch(Actor s, Actor a)
	If !Hostile(s, a)
		Return
	EndIf
	Int free = -1
	Int i = 0
	While i < Watched.Length
		If Watched[i] == a
			Return
		ElseIf !Watched[i] && free < 0
			free = i
		EndIf
		i += 1
	EndWhile
	If free < 0
		Return
	EndIf
	Watched[free] = a
	RegisterForAnimationEvent(a, "preHitFrame")
	RegisterForAnimationEvent(a, "BeginCastLeft")
	RegisterForAnimationEvent(a, "BeginCastRight")
	RegisterForAnimationEvent(a, "bowDraw")
EndFunction

; The enemies around her are re-picked every tick: her target, the player's target and a few nearby fighters.
Function WatchEnemies(Actor s)
	If !Watched
		Watched = new Actor[6]
	EndIf
	Unwatch()
	AddWatch(s, s.GetCombatTarget())
	AddWatch(s, PlayerRef.GetCombatTarget())
	Int n = 0
	While n < 4
		AddWatch(s, Game.FindRandomActorFromRef(s, DodgeRangedReach))
		n += 1
	EndWhile
EndFunction

Function OnEnemyEvent(Actor s, Actor a, String ev)
	If a && BiteVictim
		CheckBiteBreak(s, a, ev)
		Return
	EndIf
	Bool ninjaOn = NinjaOn()
	If !a || Feeding || !s.IsInCombat() || !(WitchOn || JuriOn() || ninjaOn)
		Return
	EndIf
	If ninjaOn
		Ninja().Observe(a, ev)    ; her Sharingan reads every fighter, whoever they are aiming at
	EndIf
	If a.GetCombatTarget() != s
		Return    ; only what is aimed at her
	EndIf
	If ninjaOn && Ninja().Defend(s, a, ev, s.GetDistance(a))
		Return    ; Ninja Mode has its own Sharingan defence: parry, dodge, riposte
	EndIf
	Float now = Utility.GetCurrentRealTime()
	GuardClocks(now)
	If now - LastDodge < DodgeCooldown || s.IsInKillMove() || s.GetSitState() != 0
		Return
	EndIf
	Float d = s.GetDistance(a)
	String dodge
	If ev == "preHitFrame"
		If d > DodgeMeleeReach
			Return
		EndIf
		Float r = Utility.RandomFloat()
		If r < 0.5
			dodge = "DodgeBack"
		ElseIf r < 0.75
			dodge = "DodgeLeft"
		Else
			dodge = "DodgeRight"
		EndIf
	Else
		If d > DodgeRangedReach || Utility.RandomFloat() > DodgeRangedChance
			Return
		EndIf
		If Utility.RandomInt(0, 1) == 0
			dodge = "DodgeLeft"
		Else
			dodge = "DodgeRight"
		EndIf
	EndIf
	LastDodge = now
	Debug.SendAnimationEvent(s, dodge)
	Debug.Trace("WOTW dodge: " + dodge + " from " + a.GetDisplayName() + " (" + ev + ", " + (d as Int) + ")")
	If WitchOn
		Spell bats = Game.GetFormFromFile(0x00000813, "Daughter of Coldharbor.esp") as Spell    ; Vampiric Dodge
		If bats
			bats.Cast(s, s)
		EndIf
		s.SetGhost(True)
		Utility.Wait(0.6)
		s.SetGhost(False)
	EndIf
EndFunction

; ---------------- Flemeth's Grimoire ----------------

Float Function RankCost(Int rank)
	Return RankCostBase + RankCostStep * rank
EndFunction

Function GainGrimoire(Actor s, Float pts)
	If Grimoire >= 100
		Return
	EndIf
	GrimoirePoints += pts
	While Grimoire < 100 && GrimoirePoints >= RankCost(Grimoire)
		GrimoirePoints -= RankCost(Grimoire)
		Grimoire += 1
		AnnounceRank(Grimoire)
	EndWhile
	UpdateTier(s, True)
EndFunction

Function CheckSetGrimoire(Actor s)
	If !SetGrimoireGlobal
		Return
	EndIf
	Int want = SetGrimoireGlobal.GetValue() as Int
	If want < 0
		Return
	EndIf
	SetGrimoireGlobal.SetValue(-1.0)
	If want > 100
		want = 100
	EndIf
	Grimoire = want
	GrimoirePoints = 0.0
	UpdateTier(s, False)
	ApplyBuffs(s)
	Debug.Notification("Serana: Grimoire set to " + Grimoire + " (" + TierName(CurTier) + " spells).")
EndFunction

Function AnnounceRank(Int r)
	String unlock = ""
	If r == 10
		unlock = " Witch's Reserve (more magicka)."
	ElseIf r == 15
		unlock = " Rogue Mage (lighter on her feet, out of heavy armour)."
	ElseIf r == 20
		unlock = " Blood Magic."
	ElseIf r == 25 || r == 50 || r == 75
		unlock = " New spells."
	ElseIf r == 100
		unlock = " The full grimoire: Blizzard returns twice as fast."
	EndIf
	If r % 5 == 0 || unlock != ""
		Debug.Notification("Serana: Grimoire " + r + "." + unlock)
	EndIf
EndFunction

String Function TierName(Int t)
	If t == 5
		Return "Master"
	ElseIf t == 4
		Return "Expert"
	ElseIf t == 3
		Return "Adept"
	ElseIf t == 2
		Return "Apprentice"
	EndIf
	Return "Novice"
EndFunction

; Her spells come from her level or her Grimoire, whichever has gone further.
Int Function WantedTier(Actor s)
	Int lvl = s.GetLevel()
	Int byLevel = 1
	If lvl >= 50
		byLevel = 5
	ElseIf lvl >= 40
		byLevel = 4
	ElseIf lvl >= 30
		byLevel = 3
	ElseIf lvl >= 20
		byLevel = 2
	EndIf
	Int byRank = 1 + Grimoire / 25
	If byRank > 5
		byRank = 5
	EndIf
	If byRank > byLevel
		Return byRank
	EndIf
	Return byLevel
EndFunction

Function UpdateTier(Actor s, Bool announce)
	If !WitchOn
		Return
	EndIf
	Int t = WantedTier(s)
	If t != CurTier || !s.HasSpell(Game.GetFormFromFile(0x0000080A + t, "Witch of the Wilds.esp") as Spell)
		Bool up = t > CurTier && CurTier > 0
		SetTierAbility(s, t)
		If announce && up
			Debug.Notification("Serana's grimoire opens: " + TierName(t) + " spells.")
		EndIf
	EndIf
EndFunction

; Exactly one tier ability (0x80B-0x80F) while the mode is on; its hidden effect picks her OAR spell folder.
Function SetTierAbility(Actor s, Int t)
	Int i = 1
	While i <= 5
		Spell ab = Game.GetFormFromFile(0x0000080A + i, "Witch of the Wilds.esp") as Spell
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

Int Function Step3(Int a, Int b, Int c)
	If Grimoire >= c
		Return 3
	ElseIf Grimoire >= b
		Return 2
	ElseIf Grimoire >= a
		Return 1
	EndIf
	Return 0
EndFunction

; Passive Grimoire buffs, applied as deltas so nothing stacks; ClearBuffs takes them back off.
Function ApplyBuffs(Actor s)
	Float magicka = 40.0 * Step3(10, 40, 70)        ; Witch's Reserve
	Float speed = 0.0
	If !s.WornHasKeyword(Game.GetFormFromFile(0x0006BBD2, "Skyrim.esm") as Keyword)    ; no ArmorHeavy
		speed = 5.0 * Step3(15, 45, 75)               ; Rogue Mage
	EndIf
	Float magRate = 0.0
	If s.IsInCombat()
		magRate = 30.0 * Step3(20, 50, 80)            ; Hungry Blood
	EndIf
	If magicka != AppliedMagicka
		s.ModActorValue("Magicka", magicka - AppliedMagicka)
		AppliedMagicka = magicka
	EndIf
	If speed != AppliedSpeed
		s.ModActorValue("SpeedMult", speed - AppliedSpeed)
		AppliedSpeed = speed
		s.ModActorValue("CarryWeight", 0.1)     ; SpeedMult only takes effect when carry weight changes
		s.ModActorValue("CarryWeight", -0.1)
	EndIf
	If magRate != AppliedMagRate
		s.ModActorValue("MagickaRateMult", magRate - AppliedMagRate)
		AppliedMagRate = magRate
	EndIf
EndFunction

Function ClearBuffs(Actor s)
	s.ModActorValue("Magicka", -AppliedMagicka)
	s.ModActorValue("SpeedMult", -AppliedSpeed)
	s.ModActorValue("MagickaRateMult", -AppliedMagRate)
	If AppliedSpeed != 0.0
		s.ModActorValue("CarryWeight", 0.1)
		s.ModActorValue("CarryWeight", -0.1)
	EndIf
	AppliedMagicka = 0.0
	AppliedSpeed = 0.0
	AppliedMagRate = 0.0
EndFunction

; ---------------- blood: Blood Magic and feeding ----------------

; Blood Magic (Grimoire 20): when her magicka runs low and she still has blood to spare, she spends it.
Function BloodMagic(Actor s, Float now)
	If Grimoire < 20 || now - LastBlood < BloodCooldown
		Return
	EndIf
	If s.GetActorValuePercentage("Magicka") >= 0.25 || s.GetActorValuePercentage("Health") <= 0.5
		Return
	EndIf
	LastBlood = now
	Float cost = 0.15 * s.GetBaseActorValue("Health")
	s.DamageActorValue("Health", cost)
	s.RestoreActorValue("Magicka", cost * 2.0)
	Spell fx = Game.GetFormFromFile(0x00010E18, "Dawnguard.esm") as Spell    ; DLC1FXCastVampireBleedSpell
	If fx
		fx.Cast(s, s)
	EndIf
	Debug.Trace("WOTW: Blood Magic, " + (cost as Int) + " health -> " + ((cost * 2.0) as Int) + " magicka")
EndFunction

; Prey: a living enemy in this fight, weakened. Never a bystander, a follower or the undead.
Bool Function Prey(Actor s, Actor t)
	If !Hostile(s, t) || s.GetDistance(t) > FeedReach || t.GetActorValuePercentage("Health") > FeedPreyHealthPct
		Return False
	EndIf
	If t.HasKeyword(Game.GetFormFromFile(0x00013796, "Skyrim.esm") as Keyword)       ; ActorTypeUndead
		Return False
	ElseIf t.HasKeyword(Game.GetFormFromFile(0x0001397A, "Skyrim.esm") as Keyword)   ; ActorTypeDwarven
		Return False
	ElseIf t.HasKeyword(Game.GetFormFromFile(0x00013797, "Skyrim.esm") as Keyword)   ; ActorTypeDaedra
		Return False
	EndIf
	Return True
EndFunction

; Feeding. On a humanoid she bites: the Dawnguard standing feed (the bite Harkon and Serana give in the main
; quest), a paired animation that pulls the prey in. While she drinks nothing can touch her (ghost), except what a
; vampire truly fears: an enemy striking at her with a SILVER weapon, or casting a FIRE spell at her, breaks the
; bite (see OnEnemyEvent); she reels, the hit lands, and she only gets a third of the blood.
; Other prey (beasts, monsters) gets the blood siphon instead of a bite, and that can be interrupted normally.
Function Feed(Actor s, Float now)
	If Feeding || now - LastFeed < FeedCooldown
		Return
	EndIf
	If s.GetActorValuePercentage("Magicka") >= 0.35 && s.GetActorValuePercentage("Health") >= 0.45
		Return
	EndIf
	Actor t = s.GetCombatTarget()
	If !Prey(s, t)
		t = None
		Int i = 0
		While !t && Watched && i < Watched.Length
			If Watched[i] && Prey(s, Watched[i])
				t = Watched[i]
			EndIf
			i += 1
		EndWhile
	EndIf
	If !t
		Return
	EndIf
	Feeding = True
	BiteBroken = False
	LastFeed = now
	Bool lethal = t.GetActorValuePercentage("Health") <= FeedKillPct
	Bool bit = False
	If t.HasKeyword(Game.GetFormFromFile(0x00013794, "Skyrim.esm") as Keyword)    ; ActorTypeNPC: a real bite
		If Math.Abs(t.GetHeadingAngle(s)) > 110.0    ; she is behind her prey
			bit = s.PlayIdleWithTarget(Game.GetFormFromFile(0x0000BDE3, "Dawnguard.esm") as Idle, t)    ; IdleVampireStandingBack
		EndIf
		If !bit
			bit = s.PlayIdleWithTarget(Game.GetFormFromFile(0x0000E6A8, "Dawnguard.esm") as Idle, t)    ; IdleVampireStandingFeedFront_Loose
		EndIf
	EndIf
	If bit
		BiteVictim = t
		s.SetGhost(True)
		Int ticks = 0
		While ticks < (BiteSeconds * 4.0) as Int && !BiteBroken && !s.IsDead()
			Utility.Wait(0.25)
			ticks += 1
			If ticks % 4 == 0
				WatchEnemies(s)    ; once a second: enemies who join mid-bite are watched too
			EndIf
		EndWhile
		s.SetGhost(False)
		BiteVictim = None
	Else
		Spell drain = Game.GetFormFromFile(0x0000080D, "Daughter of Coldharbor.esp") as Spell    ; the blood siphon
		If drain
			drain.Cast(s, t)
		EndIf
		Utility.Wait(1.5)
	EndIf
	Float share = 1.0
	If BiteBroken
		share = 1.0 / 3.0
		lethal = False
	EndIf
	If lethal
		t.Kill(s)
	ElseIf !t.IsDead()
		t.DamageActorValue("Health", 0.35 * share * t.GetBaseActorValue("Health"))
		If !BiteBroken
			t.SetAnimationVariableFloat("staggerMagnitude", 0.8)
			Debug.SendAnimationEvent(t, "staggerStart")
		EndIf
	EndIf
	s.RestoreActorValue("Magicka", 0.6 * share * s.GetBaseActorValue("Magicka"))
	s.RestoreActorValue("Health", 0.35 * share * s.GetBaseActorValue("Health"))
	GainGrimoire(s, 5.0 * share)
	Debug.Trace("WOTW: fed on " + t.GetDisplayName() + " (bite " + bit + ", broken " + BiteBroken + ", lethal " + lethal + ")")
	Feeding = False
	BiteBroken = False
EndFunction

Bool Function SilverStrike(Actor a)
	Weapon w = a.GetEquippedWeapon()
	If !w
		w = a.GetEquippedWeapon(True)
	EndIf
	Return w && w.HasKeyword(Game.GetFormFromFile(0x0010AA1A, "Skyrim.esm") as Keyword)    ; WeapMaterialSilver
EndFunction

Bool Function FireCast(Actor a, String ev)
	Int hand = 1
	If ev == "BeginCastLeft"
		hand = 0
	EndIf
	Spell sp = a.GetEquippedSpell(hand)
	If !sp
		Return False
	EndIf
	Keyword fire = Game.GetFormFromFile(0x0001CEAD, "Skyrim.esm") as Keyword    ; MagicDamageFire
	Int i = sp.GetNumEffects()
	While i > 0
		i -= 1
		MagicEffect e = sp.GetNthEffectMagicEffect(i)
		If e && e.HasKeyword(fire)
			Return True
		EndIf
	EndWhile
	Return False
EndFunction

; Called while she is biting, for each watched enemy's attack or cast.
Function CheckBiteBreak(Actor s, Actor a, String ev)
	If BiteBroken || !BiteVictim || a == BiteVictim
		Return
	EndIf
	String why = ""
	If ev == "preHitFrame" && s.GetDistance(a) <= DodgeMeleeReach && SilverStrike(a)
		why = "silver"
	ElseIf (ev == "BeginCastLeft" || ev == "BeginCastRight") && (a.GetCombatTarget() == s || s.GetDistance(a) <= 600.0) && FireCast(a, ev)
		why = "fire"
	EndIf
	If why == ""
		Return
	EndIf
	BiteBroken = True
	s.SetGhost(False)    ; the strike or spell lands
	Debug.SendAnimationEvent(s, "IdleForceDefaultState")
	Debug.SendAnimationEvent(BiteVictim, "IdleForceDefaultState")
	s.SetAnimationVariableFloat("staggerMagnitude", 0.5)
	Debug.SendAnimationEvent(s, "staggerStart")
	Debug.Notification("Serana recoils from the " + why + "!")
	Debug.Trace("WOTW: bite broken by " + why + " from " + a.GetDisplayName())
EndFunction

; Diagnostic, once per fight: is the tier marker her OAR spell folders check for really active on her?
Function ReportState(Actor s)
	MagicEffect marker = Game.GetFormFromFile(0x00000805 + CurTier, "Witch of the Wilds.esp") as MagicEffect
	Weapon w = s.GetEquippedWeapon()
	String held = "nothing"
	If w
		held = w.GetName()
	EndIf
	Debug.Trace("WOTW state: tier " + CurTier + ", marker active " + (marker && s.HasMagicEffect(marker)) + ", right hand " + held + ", magicka " + (s.GetActorValue("Magicka") as Int) + "/" + (s.GetBaseActorValue("Magicka") as Int) + ", grimoire " + Grimoire)
EndFunction

; ---------------- loyalty ----------------
; Serana defends Obito and Ashe, nobody else. A vampire she charmed (Shinobi Enemies' turncoat) becomes a
; teammate, so when Ashe attacks one, Serana would turn on Ashe to protect it. If she ever targets Obito, Ashe or
; another real follower, both of them stand down; a thrall gets no loyalty (she neither defends nor attacks it),
; any other foe of her friend she takes on.
; Runs every second in any mode (also with no mode on), once the loop has been started by either toggle.

Bool Function IsAshe(Actor a)
	ActorBase b = a.GetLeveledActorBase()
	Return b && (b == Game.GetFormFromFile(0x00005900, "Ashe - Fire and Blood.esp") || b == Game.GetFormFromFile(0x0077052C, "Ashe - Fire and Blood.esp"))
EndFunction

Bool Function Protected(Actor a)
	If !a || a.IsDead()
		Return False
	EndIf
	If a == PlayerRef || IsAshe(a)
		Return True
	EndIf
	Faction followers = Game.GetFormFromFile(0x0005C84E, "Skyrim.esm") as Faction    ; CurrentFollowerFaction
	Return a.IsPlayerTeammate() && followers && a.GetFactionRank(followers) >= 0
EndFunction

Function GuardLoyalty(Actor s)
	If !s.IsInCombat()
		Return
	EndIf
	Actor friend = s.GetCombatTarget()
	If !Protected(friend)
		Return
	EndIf
	Actor theirFoe = friend.GetCombatTarget()
	s.StopCombat()
	If theirFoe == s
		friend.StopCombat()
		theirFoe = None
	EndIf
	s.StopCombatAlarm()
	Debug.Trace("WOTW loyalty: Serana stood down from " + friend.GetDisplayName())
	; A thrall she charmed (Shinobi Enemies turncoat: a teammate, but not a real follower) gets no loyalty either way:
	; she won't defend it, and she won't attack it. Any other foe of her friend, she takes on.
	If theirFoe && theirFoe != PlayerRef && !Protected(theirFoe) && !theirFoe.IsDead() && !theirFoe.IsPlayerTeammate()
		s.StartCombat(theirFoe)    ; she sides with her friend instead
		Debug.Trace("WOTW loyalty: Serana turns on " + theirFoe.GetDisplayName())
	EndIf
EndFunction

; ---------------- upkeep ----------------

Event OnUpdate()
	Bool juriOn = JuriOn()
	Actor s = Serana()
	If s && !s.IsDead() && s.Is3DLoaded()
		GuardLoyalty(s)
	EndIf
	If !s || s.IsDead() || (!WitchOn && !juriOn && !NinjaOn())
		Unwatch()
		RegisterForSingleUpdate(UpkeepSeconds)    ; the loyalty guard keeps running in every mode
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	GuardClocks(now)
	If WitchOn
		CheckSetGrimoire(s)
		Witchy(s)
		UpdateTier(s, True)
		ApplyBuffs(s)
	EndIf
	If s.IsInCombat()
		If !WasFighting && WitchOn
			ReportState(s)
		EndIf
		WasFighting = True
		WatchEnemies(s)
		If WitchOn
			OpenerTick(s, now)
			BloodMagic(s, now)
			Feed(s, now)
		EndIf
	ElseIf WasFighting
		WasFighting = False
		Unwatch()
	EndIf
	RegisterForSingleUpdate(UpkeepSeconds)
EndEvent

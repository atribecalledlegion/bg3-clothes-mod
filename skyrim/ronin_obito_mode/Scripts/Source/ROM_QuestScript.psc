Scriptname ROM_QuestScript extends Quest
{Ronin Obito Mode: Obito Uchiha [Ronin], "the Wandering Ronin" (Naruto Mobile, 2025), for the player.
Phase 1 skeleton (2026-10-18), built before the movesets are chosen; they will hang off the stance abilities (OAR).
 - Toggle: the "Ronin" lesser power. One stance at a time: Sheathed (default) or Drawn, each an ability whose effect
   is the OAR condition for its moveset and shows in Active Effects.
 - Ki is Magicka (the user's pick): the skills spend it; every hit that lands gives some back.
 - With the Yamato (Vergil Yamato 5.7, ChaosYamato.esp: its effect 0x861 is on him), the stances FOLLOW Vergil's:
   Iai (scabbard in hand, effect 0x876) = Sheathed, Open (blade out, effect 0x877) = Drawn. Ichishun is Vergil's
   Trick (direction + heavy). With any other sword: the first swing draws, DrawnSeconds idle or the fight's end
   sheathes. (2026-10-18: the old Ichishun teleport T-posed the player every time and was retired.)
 - Counter-slash: a real block (ECB_Guard sends ROM_CounterKept; with the Yamato it keeps Vergil's heavy instead of
   Elden Counter's guard counter) arms the next hit within CutWindow s: it leaves a Kamui distortion on the enemy
   that tears a moment later, the Dimension Cut.
 - Drawn: cuts bite deeper (+DrawnDamage); a Kamui dodge (Sharingan Copy's Reflex Phase, Mangekyo open) restores Ki.
 Skills (2026-10-19): Uchiha Flame Formation (every 6th hit of a string: a flare of Uchiha fire, a burn and a stagger);
 the skill key (SkillKeyCode, B; Shift+B since 2026-10-19, either stance) - B: Issen (a scabbard-slam shockwave staggers everyone close, the nearest
 takes the Kamui tear), Shift+B: Wood Spear (Sashiki spikes, then the Tree Bind wood skin holds the target 4 s, still hittable);
 Bakufu Ranbu on a wood-bound enemy ignites the wood (the fan concept's Wood + Fire combo; Obito's Hashirama cells).
 Phase 2 (2026-10-18): Resolve, his ultimate gauge (0-100): +ResolvePerHit a hit, +ResolvePerCut a Dimension Cut,
 +ResolvePerParry a parry, +ResolvePerKamui a Kamui dodge. Full, it is spent by whichever ultimate comes first:
 - Heaven Slash (a parry): Dimension Blades rake the attacker, then a great Kamui tear.
 - Focused Slash (a Kamui dodge): his target is wrapped in Kamui; below half health (and no boss) it is swallowed
   whole, else it takes a great cut.
 - Annihilation of Heaven and Earth (the taunt, hotkey ROM_TauntKey, with full resolve): Judgement Cut End (ap05) is
   unsealed for JceWindow s and he presses its power key (needs AnnihilationMagicka % Magicka and JCE off cooldown;
   resolve kept if not). In Ronin mode JCE is sealed otherwise (its JCEReqMP global is held at 101%); setting Ronin down puts it back.
Trace lines start with "ROM:".}

Actor Property PlayerRef Auto
Spell Property TogglePower Auto
Spell Property SheathedAbility Auto
Spell Property DrawnAbility Auto
Spell Property DimensionCut Auto
GlobalVariable Property TauntKey Auto
{ROM_TauntKey: the taunt hotkey (DirectInput scan code, default 34 = G).}
GlobalVariable Property FillResolve Auto
{ROM_FillResolve: test hook. 'set ROM_FillResolve to 1' fills his resolve (read every half second).}
Spell Property TauntSpell Auto
{ROM_TauntSpell: while its effect is on him, the 'Ronin Obito/Taunt' OAR folder plays Vergil's EX Taunt as his combat idle.}

Float Property KiPerHit = 4.0 AutoReadOnly
Float Property KamuiDodgeKi = 25.0 AutoReadOnly
Float Property CutCost = 15.0 AutoReadOnly
Float Property CutWindow = 2.5 AutoReadOnly
Float Property CutDelay = 0.6 AutoReadOnly
Float Property DrawnDamage = 0.15 AutoReadOnly
Float Property DrawnSeconds = 20.0 AutoReadOnly
Float Property ResolvePerHit = 4.0 AutoReadOnly
Float Property ResolvePerCut = 10.0 AutoReadOnly
Float Property ResolvePerParry = 20.0 AutoReadOnly
Float Property ResolvePerKamui = 15.0 AutoReadOnly
Float Property ResolvePerTaunt = 10.0 AutoReadOnly
Float Property JceWindow = 6.0 AutoReadOnly
Int Property SkillKeyCode = 48 AutoReadOnly
{The skill key: B (free in the user's setup, checked 2026-10-19).}
Int Property FlameEvery = 5 AutoReadOnly
Float Property StringGap = 2.5 AutoReadOnly
Float Property IssenCost = 20.0 AutoReadOnly
Float Property IssenCooldown = 6.0 AutoReadOnly
Float Property IssenReach = 450.0 AutoReadOnly
Float Property KamuiVanishSeconds = 0.35 AutoReadOnly
Float Property KamuiArriveSeconds = 0.25 AutoReadOnly
Float Property KamuiArriveWindow = 1.5 AutoReadOnly
{A blade-draw (bowReset) this soon after a vanish is where he comes out of Kamui.}
Float Property IssenDrawDelay = 0.12 AutoReadOnly
{The Issen draw: seconds from its start to the blade leaving the scabbard (the cuts land then).}
Float Property IssenDrawSeconds = 1.35 AutoReadOnly
{The draw is 1.5 s; its mark goes just before it would loop.}
Float Property WoodCost = 25.0 AutoReadOnly
Float Property WoodCooldown = 10.0 AutoReadOnly
Float Property WoodBindSeconds = 10.0 AutoReadOnly
{How long a wood-bound enemy can be ignited.}
Float Property WoodHoldSeconds = 4.0 AutoReadOnly
{How long the wood holds him still (AI off, still hittable).}
Float Property AnnihilationMagicka = 50.0 AutoReadOnly
{Magicka % Annihilation needs (JCE's own 80% was too hard to hold with Ki = Magicka; the user's pick, 2026-10-19).}
Float Property TauntResolveCooldown = 15.0 AutoReadOnly
{The taunt's own resolve comes once per this many seconds, in combat only (test 1: spamming it filled the gauge).}
Bool Property Verbose = False AutoReadOnly
{Test traces: every hit and its Ki, Vergil's stance hooks, an armed cut running out. Off once the kit is settled.}

Bool RoninOn = False
Bool Drawn = False
Float AppliedDamage = 0.0
Int VergilStance = 0    ; 0 none, 1 Iai, 2 Open (for the trace)
Float LastAttack = -100.0
Float CounterArmed = -100.0
Bool WasFighting = False
Float Resolve = 0.0
Bool JceOpen = False
Float JceUntil = -100.0
Int BoundKey = -1
Float LastTauntResolve = -100.0
Int StringHits = 0
Float LastStringHit = -100.0
Float LastIssen = -100.0
Float LastWood = -100.0
Actor WoodBound
Float WoodBoundUntil = -100.0
Bool SkillKeyBound = False
Actor WoodHeld
Float WoodHeldUntil = -100.0
Bool GaveOutfit = False
Float LastVanish = -100.0
Bool ArrivePending = False
Bool SkillBusy = False    ; claimed before any engine call: five quick B presses once stacked five Wood Prisons

Event OnInit()
	PlayerRef.AddSpell(TogglePower, False)
EndEvent

Bool Function IsOn()
	Return RoninOn
EndFunction

; ChaosYamato.esp: 0x861 Yamato equipped (zzYamatoMainMGEF), 0x876 Iai, 0x877 Open (cast by Dynamic Animation Casting
; on ShdEquip / bowReset, StanceToggle.toml)
MagicEffect Function VergilEffect(Int id)
	Return Game.GetFormFromFile(id, "ChaosYamato.esp") as MagicEffect
EndFunction

Bool Function HasYamato()
	MagicEffect e = VergilEffect(0x861)
	Return e && PlayerRef.HasMagicEffect(e)
EndFunction

; Follow Vergil's stance while the Yamato is out. True if the Yamato is out (then nothing else decides the stance).
Bool Function FollowVergil()
	If !HasYamato()
		If VergilStance != 0
			VergilStance = 0
			Debug.Trace("ROM: Yamato put away")
		EndIf
		Return False
	EndIf
	Int now = 0
	If PlayerRef.HasMagicEffect(VergilEffect(0x877))
		now = 2
	ElseIf PlayerRef.HasMagicEffect(VergilEffect(0x876))
		now = 1
	EndIf
	If now != VergilStance
		VergilStance = now
		Debug.Trace("ROM: Vergil stance " + now + " (0 none, 1 Iai, 2 Open)")
	EndIf
	If now == 2
		SetStance(True, False)
	ElseIf now == 1
		SetStance(False, False)
	EndIf
	Return True
EndFunction

CSHC_KamuiQuestScript Function Kamui()
	Return Game.GetFormFromFile(0x00000800, "Sharingan Copy.esp") as CSHC_KamuiQuestScript
EndFunction

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

; Real time restarts at 0 every launch, but these are saved: a value far ahead is from an earlier session.
Function FixClocks(Float t)
	If LastAttack - t > 60.0
		LastAttack = -100.0
	EndIf
	If CounterArmed - t > 60.0
		CounterArmed = -100.0
	EndIf
	If JceUntil - t > 60.0
		JceUntil = -100.0
	EndIf
	If LastTauntResolve - t > 60.0
		LastTauntResolve = -100.0
	EndIf
	If LastVanish - t > 60.0
		LastVanish = -100.0
	EndIf
	If LastStringHit - t > 60.0
		LastStringHit = -100.0
	EndIf
	If LastIssen - t > 60.0
		LastIssen = -100.0
	EndIf
	If LastWood - t > 60.0
		LastWood = -100.0
	EndIf
	If WoodBoundUntil - t > 60.0
		WoodBoundUntil = -100.0
	EndIf
EndFunction

; ---------------- the mode ----------------

Function Toggle()
	If RoninOn
		RoninOn = False
		WoodRelease()
		SetStance(False, False)
		PlayerRef.RemoveSpell(SheathedAbility)
		UnregisterForUpdate()
		UnregisterForModEvent("ROM_CounterKept")
		UnregisterForAnimationEvent(PlayerRef, "MCO_DodgeOpen")
		UnregisterForAnimationEvent(PlayerRef, "weaponSwing")
		UnregisterForAnimationEvent(PlayerRef, "HitFrame")
		UnregisterForAnimationEvent(PlayerRef, "ShdEquip")
		UnregisterForAnimationEvent(PlayerRef, "bowReset")
		UnregisterForAllKeys()
		BoundKey = -1
		SkillKeyBound = False
		JceOpen = False
		SetJceReq(80.0)    ; Judgement Cut End as it was before Ronin
		If TauntSpell
			PlayerRef.DispelSpell(TauntSpell)
		EndIf
		Debug.Notification("Obito sets down the ronin's way.")
		Debug.Trace("ROM: off")
		Return
	EndIf
	RoninOn = True
	SetStance(False, True)
	Listen()
	RegisterForModEvent("ROM_CounterKept", "OnCounterKept")
	SetJceReq(101.0)    ; sealed until the taunt
	RegisterForSingleUpdate(0.5)
	Debug.Notification("Obito walks the ronin's way. His blade rests in its scabbard.")
	Debug.Trace("ROM: on (sheathed)")
	; GiveOutfit()    ; ON HOLD (user, 2026-10-19): the outfit will be rebuilt on another base mod later
EndFunction

; The Ronin outfit, handed over the first time he takes up the way (2026-10-19): the Ronin Kimono (Blades Samurai
; Shihanke kimono in Kamui purple, Uchiha crest on the back) and the Blades black tabi and sandals.
Function GiveOutfit()
	If GaveOutfit
		Return
	EndIf
	GaveOutfit = True
	Armor kimono = Game.GetFormFromFile(0x00000815, "Ronin Obito Mode.esp") as Armor    ; ROM_Kimono
	Armor sandals = Game.GetFormFromFile(0x00000D66, "SamuraiBlades.esp") as Armor        ; Tabi and Sandles (black)
	If kimono && PlayerRef.GetItemCount(kimono) == 0
		PlayerRef.AddItem(kimono, 1, True)
	EndIf
	If sandals && PlayerRef.GetItemCount(sandals) == 0
		PlayerRef.AddItem(sandals, 1, True)
	EndIf
	Debug.Notification("The ronin's garb is in your pack: Ronin Kimono" + StringIf(sandals != None, ", tabi and sandals.", "."))
	Debug.Trace("ROM: outfit given (kimono " + (kimono != None) + ", sandals " + (sandals != None) + ")")
EndFunction

Function Listen()
	; the player alias (ROM_PlayerAlias: Kamui teleports) - a quest already running in a save never fills a new
	; alias by itself, so it is forced here
	ReferenceAlias me = GetAlias(0) as ReferenceAlias
	If me && me.GetReference() != PlayerRef
		me.ForceRefTo(PlayerRef)
		Debug.Trace("ROM: player alias filled (Kamui teleports)")
	EndIf
	RegisterForAnimationEvent(PlayerRef, "MCO_DodgeOpen")
	RegisterForAnimationEvent(PlayerRef, "weaponSwing")
	RegisterForAnimationEvent(PlayerRef, "HitFrame")
	RegisterForAnimationEvent(PlayerRef, "ShdEquip")    ; Vergil's Iai hook (StanceToggle.toml)
	RegisterForAnimationEvent(PlayerRef, "bowReset")    ; Vergil's Open hook
	Int k = 34
	If TauntKey
		k = TauntKey.GetValueInt()
	EndIf
	If k != BoundKey
		If BoundKey >= 0
			UnregisterForKey(BoundKey)
		EndIf
		RegisterForKey(k)
		BoundKey = k
	EndIf
	If !SkillKeyBound
		RegisterForKey(SkillKeyCode)
		SkillKeyBound = True
	EndIf
EndFunction

; Sheathed <-> Drawn. force: apply even if already in that stance.
Function SetStance(Bool drawIt, Bool force)
	If drawIt == Drawn && !force
		Return
	EndIf
	Drawn = drawIt
	If drawIt
		PlayerRef.RemoveSpell(SheathedAbility)
		PlayerRef.AddSpell(DrawnAbility, False)
	Else
		PlayerRef.RemoveSpell(DrawnAbility)
		If RoninOn
			PlayerRef.AddSpell(SheathedAbility, False)
		EndIf
	EndIf
	Float want = 0.0
	If drawIt
		want = DrawnDamage
	EndIf
	If want != AppliedDamage
		PlayerRef.ModActorValue("AttackDamageMult", want - AppliedDamage)
		AppliedDamage = want
	EndIf
	Debug.Trace("ROM: stance " + StanceName())
EndFunction

String Function StanceName()
	If Drawn
		Return "drawn"
	EndIf
	Return "sheathed"
EndFunction

Event OnUpdate()
	If !RoninOn
		Return
	EndIf
	Float t = Now()
	FixClocks(t)
	Listen()    ; registrations drop when the 3D reloads
	Bool fighting = PlayerRef.IsInCombat()
	If FollowVergil()
		; the Yamato's own stances decide
	ElseIf Drawn && ((!fighting && WasFighting) || t - LastAttack > DrawnSeconds)
		SetStance(False, False)    ; back in the scabbard
	EndIf
	WasFighting = fighting
	If FillResolve && FillResolve.GetValue() > 0.0
		FillResolve.SetValue(0.0)
		AddResolve(100.0, "console test hook")
	EndIf
	If WoodHeld && (t > WoodHeldUntil || WoodHeldUntil - t > 60.0 || WoodHeld.IsDead())
		WoodRelease()
	EndIf
	If WoodBound && t < WoodBoundUntil && !WoodBound.IsDead()
		MagicEffect bakufu = Game.GetFormFromFile(0x0000083D, "Obito Tobi Path Additions.esp") as MagicEffect    ; CTOB_BakufuBurn
		If bakufu && WoodBound.HasMagicEffect(bakufu)
			Actor burn = WoodBound
			WoodBound = None
			Ignite(burn)
		EndIf
	ElseIf WoodBound
		WoodBound = None
	EndIf
	If JceOpen && t > JceUntil
		JceOpen = False
		SetJceReq(101.0)
		Debug.Trace("ROM: Judgement Cut End sealed again")
	EndIf
	RegisterForSingleUpdate(0.5)
EndEvent

; ---------------- Ichishun, Ki, the draw, Kamui ----------------

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If !RoninOn || akSource != PlayerRef
		Return
	EndIf
	Float t = Now()
	FixClocks(t)
	If (asEventName == "MCO_DodgeOpen" || asEventName == "weaponSwing") && TauntSpell
		PlayerRef.DispelSpell(TauntSpell)    ; acting ends the taunt
		Spell issenAnim = Game.GetFormFromFile(0x00000813, "Ronin Obito Mode.esp") as Spell
		If issenAnim
			PlayerRef.DispelSpell(issenAnim)    ; and the Issen draw
		EndIf
	EndIf
	If asEventName == "MCO_DodgeOpen"
		Dodged(t)
	ElseIf asEventName == "weaponSwing"
		LastAttack = t
		If !Drawn && !HasYamato()
			SetStance(True, False)    ; any other sword: the first swing draws it
		EndIf
	ElseIf asEventName == "HitFrame"
		Struck(t)
	ElseIf asEventName == "ShdEquip" || asEventName == "bowReset"
		If asEventName == "bowReset" && ArrivePending && t - LastVanish < KamuiArriveWindow
			ArrivePending = False
			KamuiArrive()    ; the blade comes out where he reappears (Trick's lunge)
		EndIf
		If Verbose
			Debug.Trace("ROM: anim " + asEventName + " (Yamato " + HasYamato() + ")")
		EndIf
	EndIf
EndEvent

; ---------------- Kamui teleports (2026-10-19) ----------------
; The Vergil moveset's own teleports (Trick, Ultimate Slay Tempest, the Beowulf teleport combo, the step dodges) all
; start with its vanish spell ($Shinobi4); ROM_PlayerAlias hears it land and the vanish becomes Kamui's: the space
; around him twists and swallows him, and twists again where he comes out. No movement of our own: the moveset
; moves him (moving the player mid-dodge T-posed him, the old Ichishun).
Function Vanished()
	If !RoninOn
		Return
	EndIf
	Float t = Now()
	If t - LastVanish < 0.3 && t >= LastVanish
		Return    ; the vanish spell has two effects: one Kamui
	EndIf
	LastVanish = t
	ArrivePending = True
	If Verbose
		Debug.Trace("ROM: Kamui vanish")
	EndIf
	KamuiOn(PlayerRef, True)
	Utility.Wait(KamuiVanishSeconds)
	KamuiOn(PlayerRef, False)
EndFunction

Function KamuiArrive()
	If Verbose
		Debug.Trace("ROM: Kamui arrival (" + ((Now() - LastVanish) * 100.0) as Int + " cs after the vanish)")
	EndIf
	KamuiOn(PlayerRef, True)
	Utility.Wait(KamuiArriveSeconds)
	KamuiOn(PlayerRef, False)
EndFunction

Function Dodged(Float t)
	CSHC_KamuiQuestScript k = Kamui()
	If !k || !k.MangekyoActive()
		Return    ; no Kamui without the Mangekyo: a plain dodge
	EndIf
	If Drawn
		PlayerRef.RestoreActorValue("Magicka", KamuiDodgeKi)    ; his Kamui dodge: the chakra comes back
	EndIf
	Actor target = PlayerRef.GetCombatTarget()
	If Resolve >= 100.0 && target && !target.IsDead() && PlayerRef.GetDistance(target) < 800.0
		Resolve = 0.0
		FocusedSlash(target)
	Else
		AddResolve(ResolvePerKamui, "Kamui dodge")
	EndIf
EndFunction

; A hit that lands: Ki back; an armed counter becomes the Dimension Cut.
Function Struck(Float t)
	Actor target = PlayerRef.GetCombatTarget()
	If !target || target.IsDead() || PlayerRef.GetDistance(target) > 260.0 || target.IsPlayerTeammate()
		Return
	EndIf
	PlayerRef.RestoreActorValue("Magicka", KiPerHit)
	AddResolve(ResolvePerHit, "")
	If t - LastStringHit > StringGap
		StringHits = 0
	EndIf
	LastStringHit = t
	StringHits += 1
	If StringHits % FlameEvery == 0
		FlameFormation(target)
	EndIf
	If Verbose
		Debug.Trace("ROM: hit " + target.GetDisplayName() + " (string " + StringHits + ", " + StanceName() + ", +" + (KiPerHit as Int) + " Ki, magicka " + (PlayerRef.GetActorValue("Magicka") as Int) + ")")
	EndIf
	If Verbose && CounterArmed > 0.0 && t - CounterArmed >= CutWindow
		Debug.Trace("ROM: armed cut ran out (" + ((t - CounterArmed) as Int) + " s after the block)")
		CounterArmed = -100.0
	EndIf
	If t - CounterArmed < CutWindow
		CounterArmed = -100.0
		If PlayerRef.GetActorValue("Magicka") >= CutCost
			PlayerRef.DamageActorValue("Magicka", CutCost)
			DelayedCut(target)
		EndIf
	EndIf
EndFunction

; ---------------- the counter-slash ----------------

Event OnCounterKept(String eventName, String strArg, Float numArg, Form sender)
	If !RoninOn
		Return
	EndIf
	Actor target = PlayerRef.GetCombatTarget()
	If Resolve >= 100.0 && (!target || target.IsDead() || PlayerRef.GetDistance(target) >= 500.0)
		target = NearestFoe(500.0)    ; the one he parried is close even if the game's target is someone else
	EndIf
	If Resolve >= 100.0 && target && !target.IsDead() && PlayerRef.GetDistance(target) < 500.0
		Resolve = 0.0
		HeavenSlash(target)
		Return
	EndIf
	CounterArmed = Now()
	Debug.Trace("ROM: counter armed")
	AddResolve(ResolvePerParry, "parry")
EndEvent

Function DelayedCut(Actor target)
	VisualEffect distort = Game.GetFormFromFile(0x000266AB, "UchihaClan.esp") as VisualEffect    ; aaaTimeTeleportTargetVFX
	VisualEffect void = Game.GetFormFromFile(0x00000842, "Sharingan Copy.esp") as VisualEffect    ; CSHC_KamuiDistortVFX
	If distort
		distort.Play(target)
	EndIf
	If void
		void.Play(target)
	EndIf
	Debug.Trace("ROM: Dimension Cut on " + target.GetDisplayName())
	Utility.Wait(CutDelay)
	If distort
		distort.Stop(target)
	EndIf
	If void
		void.Stop(target)
	EndIf
	If !target.IsDead()
		DimensionCut.Cast(PlayerRef, target)
		target.DamageActorValue("Health", 1.5 * PlayerRef.GetLevel())    ; it grows with him
		AddResolve(ResolvePerCut, "Dimension Cut")
	EndIf
EndFunction

; ---------------- Resolve and the ultimates (phase 2) ----------------

Function AddResolve(Float pts, String why)
	If Resolve >= 100.0
		Return
	EndIf
	Resolve += pts
	If Resolve >= 100.0
		Resolve = 100.0
		Debug.Notification("Obito's resolve is full: parry, Kamui dodge or taunt to unleash it.")
		Debug.Trace("ROM: resolve FULL (" + why + ")")
	ElseIf Verbose && why != ""
		Debug.Trace("ROM: resolve " + (Resolve as Int) + " (+" + (pts as Int) + " " + why + ")")
	EndIf
EndFunction

GlobalVariable Function JceReq()
	Return Game.GetFormFromFile(0x000008DA, "Judgement Cut End - ap05's Remake.esp") as GlobalVariable    ; JCEReqMP
EndFunction

Function SetJceReq(Float v)
	GlobalVariable g = JceReq()
	If g
		g.SetValue(v)
	EndIf
EndFunction

Event OnKeyDown(Int keyCode)
	If !RoninOn || Utility.IsInMenuMode() || !PlayerRef.IsWeaponDrawn()
		Return
	EndIf
	If keyCode == BoundKey
		Taunt()
	ElseIf keyCode == SkillKeyCode
		If SkillBusy
			Return
		EndIf
		SkillBusy = True
		; 2026-10-19: Shift+B = Wood Spear, B = Issen, in either stance. The Yamato's "Open" stance is only the blade
		; being out mid-move (its DAC casts Open on bowReset, Iai on ShdEquip), about a second at a time.
		Bool wood = Input.IsKeyPressed(42) || Input.IsKeyPressed(54)    ; left / right Shift
		Debug.Trace("ROM: skill key (" + StringIf(wood, "Shift+B: Wood Spear", "B: Issen") + ")")
		If wood
			WoodSpear()
		Else
			Issen()
		EndIf
		SkillBusy = False
	EndIf
EndEvent

; The taunt: he plants himself and dares them. With full resolve: Annihilation of Heaven and Earth (JCE) opens.
Function Taunt()
	If Resolve >= 100.0
		; JCE starts by restarting the combat idle; if the taunt's combat idle is already playing, that restart does
		; nothing and JCE stalls after its intro (2026-10-19). With full resolve, JCE's own intro is the taunt.
		Sound mangekyo = Game.GetFormFromFile(0x00017C7C, "naruto overhaul.esp") as Sound
		If mangekyo
			mangekyo.Play(PlayerRef)
		EndIf
		Annihilation()
		Return
	EndIf
	; Vanilla has no human taunt (its 1HM taunts are draugr idles: tests 1-2 played nothing). Judgement Cut End's
	; trick instead: an effect switches an OAR folder that replaces the combat idle, then the combat idle restarts.
	If TauntSpell
		TauntSpell.Cast(PlayerRef, PlayerRef)
	EndIf
	Sound eye = Game.GetFormFromFile(0x00017C7C, "naruto overhaul.esp") as Sound    ; "Mangekyou Sharingan"
	If eye
		eye.Play(PlayerRef)
	EndIf
	Utility.Wait(0.1)
	Idle restart = Game.GetFormFromFile(0x000B8C73, "Skyrim.esm") as Idle    ; CombatIdleABC (IdleCombatStart)
	Bool played = restart && PlayerRef.PlayIdle(restart)
	If !played
		Debug.SendAnimationEvent(PlayerRef, "IdleCombatStart")
	EndIf
	If Verbose
		Debug.Trace("ROM: taunt animation via " + StringIf(played, "PlayIdle CombatIdleABC", "IdleCombatStart event"))
	EndIf
	Float t = Now()
	If PlayerRef.IsInCombat() && t - LastTauntResolve > TauntResolveCooldown
		LastTauntResolve = t
		AddResolve(ResolvePerTaunt, "taunt")
	EndIf
	Debug.Trace("ROM: taunt (resolve " + (Resolve as Int) + ")")
EndFunction

String Function StringIf(Bool c, String a, String b)
	If c
		Return a
	EndIf
	Return b
EndFunction

; Annihilation of Heaven and Earth: the taunt with full resolve UNSEALS Judgement Cut End for JceWindow s and he presses
; the power key (Z) himself - the one way JCE has worked for him. (2026-10-19: casting JCE from the script failed three
; builds running: its cut stalls after the intro without the key's own animation, and a second taunt on top of that
; locked his controls.) Refused with a message, resolve kept, below 80% Magicka or while JCE recovers.
String Property JceFile = "Judgement Cut End - ap05's Remake.esp" AutoReadOnly
Function Annihilation()
	MagicEffect recovering = Game.GetFormFromFile(0x000008D6, JceFile) as MagicEffect    ; JCECooldown_spell's effect
	If !JceReq()
		Debug.Trace("ROM: Judgement Cut End not loaded")
		Return
	EndIf
	If recovering && PlayerRef.HasMagicEffect(recovering)
		Debug.Notification("Judgement Cut End is still recovering. Your resolve holds.")
		Debug.Trace("ROM: Annihilation refused: JCE cooldown running")
		Return
	EndIf
	Float mp = PlayerRef.GetActorValuePercentage("Magicka")
	If mp * 100.0 < AnnihilationMagicka
		Debug.Notification("Not enough chakra for Annihilation (" + ((mp * 100.0) as Int) + "% of " + (AnnihilationMagicka as Int) + "%). Your resolve holds.")
		Debug.Trace("ROM: Annihilation refused: magicka " + ((mp * 100.0) as Int) + "%")
		Return
	EndIf
	Resolve = 0.0
	JceOpen = True
	JceUntil = Now() + JceWindow
	SetJceReq(AnnihilationMagicka)
	Debug.Notification("The Mangekyo opens. Annihilation of Heaven and Earth: press your power key!")
	Debug.Trace("ROM: Annihilation: JCE unsealed for " + (JceWindow as Int) + " s (magicka " + ((mp * 100.0) as Int) + "%)")
EndFunction

; ---------------- skills (2026-10-19) ----------------

Function FlameFormation(Actor t)
	If t == WoodBound && Now() < WoodBoundUntil
		WoodBound = None
		Ignite(t)
		Return
	EndIf
	Explosion flare = Game.GetFormFromFile(0x0000080E, "Ronin Obito Mode.esp") as Explosion    ; ROM_FlameBurst
	Spell fire = Game.GetFormFromFile(0x00000810, "Ronin Obito Mode.esp") as Spell              ; ROM_FlameFormation
	If flare
		t.PlaceAtMe(flare)
	EndIf
	If fire
		fire.Cast(PlayerRef, t)
	EndIf
	Debug.Trace("ROM: Uchiha Flame Formation on " + t.GetDisplayName() + " (hit " + StringHits + ")")
EndFunction

Bool Function SkillReady(Float last, Float cooldown, Float cost, String name)
	Float t = Now()
	If t - last < cooldown
		Debug.Notification(name + " ready in " + (Math.Ceiling(cooldown - (t - last)) as Int) + " s.")
		Return False
	EndIf
	If PlayerRef.GetActorValue("Magicka") < cost
		Debug.Notification("Not enough chakra for " + name + ".")
		Return False
	EndIf
	Return True
EndFunction

; Issen: one flash of the blade from the scabbard (the Judgement Cut quick-draw animation, 2026-10-19); every enemy close is cut by a Dimension Blade and staggered,
; the nearest also takes the Kamui tear. No animation event: an attack event comes out as MCO's power attack.
Function Issen()
	If !SkillReady(LastIssen, IssenCooldown, IssenCost, "Issen")
		Return
	EndIf
	Actor[] near = MiscUtil.ScanCellNPCs(PlayerRef, IssenReach)    ; one call: 15 random-actor asks made B take 2-3 s
	Actor[] hit = new Actor[6]
	Int n = 0
	Actor nearest = PlayerRef.GetCombatTarget()
	Int k = 0
	While k < near.Length && n < 6
		Actor a = near[k]
		If a && a != PlayerRef && a.IsHostileToActor(PlayerRef)
			hit[n] = a
			n += 1
		EndIf
		k += 1
	EndWhile
	If n > 0 && (!nearest || hit.Find(nearest) < 0)
		nearest = hit[0]
	EndIf
	If n == 0
		Debug.Notification("No enemy in reach of Issen.")
		Debug.Trace("ROM: Issen - nobody within " + (IssenReach as Int))
		Return
	EndIf
	LastIssen = Now()
	PlayerRef.DamageActorValue("Magicka", IssenCost)
	; the draw: the Yamato's Judgement Cut quick-draw as his combat idle ('Ronin Obito/Issen', on ROM_IssenMark), the
	; taunt's trick; the blade is out at 0.1 s, so the cuts land then. No attack event: MCO would take it.
	Float drawStart = Now()
	Spell anim = Game.GetFormFromFile(0x00000813, "Ronin Obito Mode.esp") as Spell    ; ROM_IssenAnim
	Bool played = False
	If anim && !PlayerRef.IsInKillMove()
		anim.Cast(PlayerRef, PlayerRef)
		Idle restart = Game.GetFormFromFile(0x000B8C73, "Skyrim.esm") as Idle    ; CombatIdleABC (IdleCombatStart)
		played = restart && PlayerRef.PlayIdle(restart)
		Utility.Wait(IssenDrawDelay)
	EndIf
	Spell slam = Game.GetFormFromFile(0x00000811, "Ronin Obito Mode.esp") as Spell    ; ROM_IssenSpell
	Int i = 0
	While i < n
		Spell blade = Game.GetFormFromFile(0x00000810 + (i % 4), "JCEfxPIE.esp") as Spell    ; zzSlashDimensionBlade01-04
		If blade
			blade.Cast(PlayerRef, hit[i])
		EndIf
		If slam
			slam.Cast(PlayerRef, hit[i])
		EndIf
		i += 1
	EndWhile
	Debug.Notification("Issen")
	Debug.Trace("ROM: Issen - " + n + " cut, nearest " + nearest.GetDisplayName() + " (draw animation " + played + ")")
	DelayedCut(nearest)
	If anim
		Float left = IssenDrawSeconds - (Now() - drawStart)
		If left > 0.0
			Utility.Wait(left)
		EndIf
		PlayerRef.DispelSpell(anim)    ; back to his own combat idle before the draw loops
	EndIf
EndFunction

; Wood Spear: Sashiki's wood spikes at the target, then the wood closes over it (WoodHold).
Function WoodSpear()
	If !SkillReady(LastWood, WoodCooldown, WoodCost, "Wood Spear")
		Return
	EndIf
	Actor t = PlayerRef.GetCombatTarget()
	If !t || t.IsDead() || t.IsPlayerTeammate() || PlayerRef.GetDistance(t) > 1500.0
		t = NearestFoe(1200.0)
	EndIf
	If !t
		Debug.Notification("No enemy in reach of Wood Spear.")
		Debug.Trace("ROM: Wood Spear - no target within 1200")
		Return
	EndIf
	LastWood = Now()
	PlayerRef.DamageActorValue("Magicka", WoodCost)
	Spell sashiki = Game.GetFormFromFile(0x00000802, "Obito Tobi Path Additions.esp") as Spell    ; Mokuton: Sashiki
	If sashiki
		sashiki.Cast(PlayerRef, t)
	EndIf
	Utility.Wait(0.3)
	If !t.IsDead()
		WoodHold(t)
		WoodBound = t
		WoodBoundUntil = Now() + WoodBindSeconds
		Debug.Notification("Wood-bound! Set it alight: Bakufu Ranbu or a flame string.")
	EndIf
	Debug.Trace("ROM: Wood Spear on " + t.GetDisplayName() + " (sashiki " + (sashiki != None) + ")")
EndFunction

; The wood closes over him (the Uchiha Clan's Tree Bind Burial: its wood skin and its freeze, AI off, still hittable).
; Replaces the Wood Prison, whose tree pillars blocked sword hits (2026-10-19).
Function WoodHold(Actor t)
	WoodRelease()
	EffectShader wood = Game.GetFormFromFile(0x002E318C, "UchihaClan.esp") as EffectShader    ; aaaMokutonTreeBindBurialEffectShader
	If wood
		wood.Play(t, WoodHoldSeconds)
	EndIf
	t.InterruptCast()
	t.EnableAI(False)
	WoodHeld = t
	WoodHeldUntil = Now() + WoodHoldSeconds
	Debug.Trace("ROM: wood holds " + t.GetDisplayName() + " for " + (WoodHoldSeconds as Int) + " s (shader " + (wood != None) + ")")
EndFunction

Function WoodRelease()
	If WoodHeld
		WoodHeld.EnableAI(True)
		EffectShader wood = Game.GetFormFromFile(0x002E318C, "UchihaClan.esp") as EffectShader
		If wood
			wood.Stop(WoodHeld)
		EndIf
		WoodHeld = None
	EndIf
EndFunction

; Bakufu Ranbu on a wood-bound enemy: the wood catches fire.
Function Ignite(Actor t)
	EffectShader burning = Game.GetFormFromFile(0x0001B212, "Skyrim.esm") as EffectShader    ; FireFXShader
	If burning
		burning.Play(t, 3.0)
	EndIf
	FlameFormation(t)
	t.DamageActorValue("Health", 5.0 * PlayerRef.GetLevel())
	Debug.Notification("The wood catches fire.")
	Debug.Trace("ROM: IGNITE - Bakufu Ranbu set " + t.GetDisplayName() + "'s wood alight")
EndFunction

Function KamuiOn(Actor t, Bool on)
	VisualEffect distort = Game.GetFormFromFile(0x000266AB, "UchihaClan.esp") as VisualEffect
	VisualEffect void = Game.GetFormFromFile(0x00000842, "Sharingan Copy.esp") as VisualEffect
	If on
		If distort
			distort.Play(t)
		EndIf
		If void
			void.Play(t)
		EndIf
	Else
		If distort
			distort.Stop(t)
		EndIf
		If void
			void.Stop(t)
		EndIf
	EndIf
EndFunction

Actor Function NearestFoe(Float reach)
	Actor[] near = MiscUtil.ScanCellNPCs(PlayerRef, reach)    ; one call (8 random-actor asks were slow and missed people)
	Actor best = None
	Float bestD = reach + 1.0
	Int k = 0
	While k < near.Length
		Actor a = near[k]
		If a && a != PlayerRef && !a.IsPlayerTeammate() && a.IsHostileToActor(PlayerRef)
			Float dd = PlayerRef.GetDistance(a)
			If dd < bestD
				best = a
				bestD = dd
			EndIf
		EndIf
		k += 1
	EndWhile
	Return best
EndFunction

Bool Function TooBigToSwallow(Actor t)
	Return t.IsEssential() || t.GetLevel() > PlayerRef.GetLevel() + 5 || t.GetBaseActorValue("Health") > 2.0 * PlayerRef.GetBaseActorValue("Health")
EndFunction

; Heaven Slash: after a parry. Four Dimension Blades rake the attacker, then a great Kamui tear.
Function HeavenSlash(Actor t)
	Debug.Notification("Heaven Slash")
	Debug.Trace("ROM: HEAVEN SLASH on " + t.GetDisplayName())
	Int i = 0
	While i < 4 && !t.IsDead()
		Spell blade = Game.GetFormFromFile(0x00000810 + i, "JCEfxPIE.esp") as Spell    ; zzSlashDimensionBlade01-04
		If blade
			blade.Cast(PlayerRef, t)
		EndIf
		DimensionCut.Cast(PlayerRef, t)
		Utility.Wait(0.15)
		i += 1
	EndWhile
	KamuiOn(t, True)
	Utility.Wait(0.5)
	KamuiOn(t, False)
	If !t.IsDead()
		Spell jc = Game.GetFormFromFile(0x00000846, "Anchor spell for MCO.esp") as Spell    ; MCO_YAMATO_JudgeCut
		If jc
			jc.Cast(PlayerRef, t)
		EndIf
		DimensionCut.Cast(PlayerRef, t)
		t.DamageActorValue("Health", 4.0 * PlayerRef.GetLevel() + 0.10 * t.GetBaseActorValue("Health"))
	EndIf
EndFunction

; Focused Slash: after a Kamui dodge. The target is wrapped in Kamui; the weak are swallowed whole.
Function FocusedSlash(Actor t)
	Debug.Notification("Focused Slash")
	Debug.Trace("ROM: FOCUSED SLASH on " + t.GetDisplayName())
	KamuiOn(t, True)
	Spell cut3d = Game.GetFormFromFile(0x00000801, "JCEfxPIE.esp") as Spell    ; zzJCE030_Cut3D_spell
	If cut3d
		cut3d.Cast(PlayerRef, t)
	EndIf
	Utility.Wait(1.0)
	KamuiOn(t, False)
	If t.IsDead()
		Return
	EndIf
	Float hp = t.GetActorValuePercentage("Health")
	Debug.Trace("ROM: Focused Slash check: " + t.GetDisplayName() + " health " + ((hp * 100.0) as Int) + "%, level " + t.GetLevel() + " (you " + PlayerRef.GetLevel() + "), essential " + t.IsEssential() + ", base health " + (t.GetBaseActorValue("Health") as Int) + " (you " + (PlayerRef.GetBaseActorValue("Health") as Int) + ")")
	If hp < 0.5 && !TooBigToSwallow(t)
		t.Kill(PlayerRef)
		t.SetCriticalStage(t.CritStage_DisintegrateStart)
		Utility.Wait(1.0)
		t.SetAlpha(0.0, True)
		t.SetCriticalStage(t.CritStage_DisintegrateEnd)
		Debug.Trace("ROM: " + t.GetDisplayName() + " swallowed by Kamui")
	Else
		DimensionCut.Cast(PlayerRef, t)
		t.DamageActorValue("Health", 3.0 * PlayerRef.GetLevel() + 0.25 * t.GetBaseActorValue("Health"))
	EndIf
EndFunction

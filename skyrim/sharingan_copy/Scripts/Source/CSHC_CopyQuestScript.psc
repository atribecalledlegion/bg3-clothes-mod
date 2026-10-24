Scriptname CSHC_CopyQuestScript extends Quest
{Sharingan Copy. While the Uchiha Clan Sharingan is open (NightEyeTransitionGlobal == 2), spells cast by
NPCs in sight are copied, following the canon rules:
 - no kekkei genkai / hiden / senjutsu / sign-less jutsu (Blocked form list)
 - eye maturity: 1 tomoe copies up to Apprentice, 2 tomoe up to Adept, 3 tomoe and beyond anything
 - the body must be able to perform it: skill in the spell's school >= the spell's level
 - copying costs chakra (Magicka) and has a short cooldown
Copied spells are forgotten after CopyDays in-game days; seeing the spell again refreshes the timer.
Needs SKSE (GetCostliestEffectIndex, GetSkillLevel, GetAssociatedSkill, GetCastingType).
SHARINGAN FORESIGHT (2026-10-16): a parry while the Sharingan is open - seen as the attacker's recoil
(recoilLargeStart / recoilStart, which Elden Parry plays on a parried enemy) within ParryWindow s of its swing at
you - (A) opens a counter window on that enemy at ANY Read tier (perfect window during Quick Reflexes or against a
tier 3 read), (C) adds ParryReadPts to its Read, (D) with the Mangekyo, a short Kamui slip (CSHC_KamuiQuestScript
.ParrySlip: small magicka cost, cooldown) so the follow-up swing passes through you.}

Actor Property PlayerRef Auto
Spell Property EyeAbility Auto
{Hidden ability holding the watching cloak. Only active while the Sharingan is open AND copying is switched on.}
Spell Property TogglePower Auto
{"Sharingan: Copy" lesser power. Given while the Sharingan is open, taken away when it closes.}
GlobalVariable Property CopyOn Auto
GlobalVariable Property SharinganState Auto
{Vanilla NightEyeTransitionGlobal: the Uchiha Clan Sharingan sets it to 2 while the eye is open.}
Float Property StatePollSeconds = 1.0 AutoReadOnly
FormList Property Blocked Auto
Perk Property Stage1 Auto
{Uchiha Clan: 1 tomoe}
Perk Property Stage2 Auto
{Uchiha Clan: 2 tomoe}
GlobalVariable Property GameDaysPassed Auto
Float Property CopyDays = 2.0 AutoReadOnly
Float Property CooldownSeconds = 10.0 AutoReadOnly
Float Property MagickaCostFraction = 0.10 AutoReadOnly
Float Property ExpiryPollSeconds = 10.0 AutoReadOnly

; --- Sharingan Read + smoother Quick Reflexes ---
FormList Property SlowSpells Auto
{Slow-time spells, one per magnitude in SlowMag() order.}
Spell Property ReadAbility Auto
Perk Property ReadPerk Auto
Spell Property MarkSpell1 Auto
Spell Property MarkSpell2 Auto
Spell Property MarkSpell3 Auto
Spell Property OpeningSpell Auto
Spell Property OpeningPerfectSpell Auto
Float Property QRCooldown = 2.5 AutoReadOnly
{No stutter: at most one Quick Reflexes slowdown per this many seconds.}
Float Property QRRange = 450.0 AutoReadOnly
{No stutter: only enemies this close (and targeting you) trigger Quick Reflexes.}
Float Property WatchRange = 3000.0 AutoReadOnly
{Enemies this close are watched: their attacks on anyone build Read.}
Float Property SwingAtYouPts = 0.5 AutoReadOnly
{An attack swung at you (hit, blocked or dodged; a hit adds its own point on top).}
Float Property ShotAtYouPts = 0.5 AutoReadOnly
{A spell or arrow loosed at you. (1.0 let an apprentice mage reach tier 3 in 6 s: test 2026-10-15.)}
Float Property ActionGap = 1.0 AutoReadOnly
{Seconds between two seen actions of the same enemy that count (fast casters fire many spells a second).}
Float Property WatchPts = 0.34 AutoReadOnly
{An attack on someone else that you can see.}
Float Property DodgeWindow = 1.0 AutoReadOnly
{A dodge this soon after an attack swung at you is a counter.}
Float Property MasteryReadBonus = 0.3 AutoReadOnly
{Eye Adaptation rank 100 (Obito Tobi Path Additions) lowers the stacks Read needs by this share.}
Float Property ParryReadPts = 1.5 AutoReadOnly
{Read points a parry adds on that enemy (a swing at you is 0.5, a hit taken 1-2).}
Float Property ParryWindow = 1.5 AutoReadOnly
{A recoil counts as your parry when that enemy swung at you within this many seconds.}

Actor[] ReadActors
Int[] ReadStacks          ; v1 (whole stacks); v2 uses ReadPts
Float[] ReadPts
Float[] ReadLastAction
Int[] ReadTier
Int CachedStage = 1
Float CachedQRMag = 0.2
Float CachedMastery = 0.0
Float QREndAt = 0.0
Int ReadCount = 0
Float LastQR = 0.0
Bool QRActive = False
Spell CurrentSlow
Actor LastSwinger
Float LastSwingTime = 0.0
Float LastCounterMsg = 0.0
Actor LastParried
Float LastParryTime = 0.0
Float LastParryMsg = 0.0

Spell[] Copied
Float[] ExpiresAt
Float NextCopyTime = 0.0
Spell LastMessageSpell
Float LastMessageTime = 0.0
Float NextExpiryCheck = 0.0

Event OnInit()
	Copied = new Spell[128]
	ExpiresAt = new Float[128]
	PlayerRef.AddSpell(EyeAbility, False)
	SetupRead()
	RegisterForSingleUpdate(StatePollSeconds)
EndEvent

; Also run from the poll, so saves made before Sharingan Read get it without a new game.
Function SetupRead()
	If !ReadAbility || !ReadPerk || !SlowSpells || !OpeningSpell
		; properties added after the save was made: look the forms up directly
		SlowSpells = Game.GetFormFromFile(0x80A, "Sharingan Copy.esp") as FormList
		ReadAbility = Game.GetFormFromFile(0x81C, "Sharingan Copy.esp") as Spell
		MarkSpell1 = Game.GetFormFromFile(0x820, "Sharingan Copy.esp") as Spell
		MarkSpell2 = Game.GetFormFromFile(0x821, "Sharingan Copy.esp") as Spell
		MarkSpell3 = Game.GetFormFromFile(0x822, "Sharingan Copy.esp") as Spell
		OpeningSpell = Game.GetFormFromFile(0x825, "Sharingan Copy.esp") as Spell
		OpeningPerfectSpell = Game.GetFormFromFile(0x826, "Sharingan Copy.esp") as Spell
		ReadPerk = Game.GetFormFromFile(0x827, "Sharingan Copy.esp") as Perk
	EndIf
	If !ReadActors || !ReadPts
		ReadActors = new Actor[16]
		ReadPts = new Float[16]
		ReadTier = new Int[16]
		ReadCount = 0
	EndIf
	If !ReadLastAction
		ReadLastAction = new Float[16]
	EndIf
	If ReadAbility && !PlayerRef.HasSpell(ReadAbility)
		PlayerRef.AddSpell(ReadAbility, False)
	EndIf
	If ReadPerk && !PlayerRef.HasPerk(ReadPerk)
		PlayerRef.AddPerk(ReadPerk)
	EndIf
	RegisterForAnimationEvent(PlayerRef, "MCO_DodgeOpen")    ; renewed every poll (dropped on reload)
	RegisterForActorAction(0)                                ; weapon swings (every actor; filtered in OnActorAction)
	RegisterForActorAction(2)                                ; spells fired
	RegisterForActorAction(6)                                ; arrows loosed
	; cached once per poll so a swing can start Quick Reflexes without a dozen lookups first
	CachedStage = EyeStage()
	CachedQRMag = StageMagnitude()
	GlobalVariable mastery = Game.GetFormFromFile(0x830, "Obito Tobi Path Additions.esp") as GlobalVariable
	If mastery
		CachedMastery = mastery.GetValue()
	EndIf
	((Self as Quest) as CSHC_KamuiQuestScript).Ensure()
EndFunction

Event OnUpdate()
	If !PlayerRef.HasSpell(EyeAbility)
		PlayerRef.AddSpell(EyeAbility, False)
	EndIf
	; the power only exists while the Sharingan is open; closing the eye also stops copying
	Bool eyeOpen = SharinganState.GetValue() == 2
	If eyeOpen && !PlayerRef.HasSpell(TogglePower)
		PlayerRef.AddSpell(TogglePower, False)
		Debug.Notification("Sharingan: Copy is ready (Powers).")
	ElseIf !eyeOpen && PlayerRef.HasSpell(TogglePower)
		PlayerRef.RemoveSpell(TogglePower)
		CopyOn.SetValue(0)
	EndIf
	SetupRead()
	If ReadCount > 0 && !PlayerRef.IsInCombat()
		ResetRead()    ; Read is per fight
	EndIf
	Float rt = Utility.GetCurrentRealTime()
	If NextExpiryCheck > rt + ExpiryPollSeconds
		NextExpiryCheck = 0.0    ; real time restarts every launch; a saved value from a longer session would stall this
	EndIf
	If rt >= NextExpiryCheck
		NextExpiryCheck = rt + ExpiryPollSeconds
		ForgetExpired()
	EndIf
	RegisterForSingleUpdate(StatePollSeconds)
EndEvent

Function ForgetExpired()
	Float now = GameDaysPassed.GetValue()
	Int i = 0
	While i < Copied.Length
		If Copied[i] && now >= ExpiresAt[i]
			PlayerRef.RemoveSpell(Copied[i])
			Debug.Notification("The copied " + Copied[i].GetName() + " fades from your memory.")
			Copied[i] = None
		EndIf
		i += 1
	EndWhile
EndFunction

Int Function FindCopied(Spell s)
	Int i = 0
	While i < Copied.Length
		If Copied[i] == s
			Return i
		EndIf
		i += 1
	EndWhile
	Return -1
EndFunction

Function Explain(Spell s, String msg)
	; one message per spell per 20 seconds, so a caster spamming a spell does not flood the screen
	Float t = Utility.GetCurrentRealTime()
	If LastMessageTime > t
		LastMessageTime = 0.0    ; saved from a longer session (real time restarts every launch)
	EndIf
	If s != LastMessageSpell || t - LastMessageTime > 20.0
		Debug.Notification(msg)
		LastMessageSpell = s
		LastMessageTime = t
	EndIf
EndFunction

Function Observe(Spell s, Actor caster)
	If !s || !caster || caster == PlayerRef || !PlayerRef.HasLOS(caster)
		Return
	EndIf
	Int idx = FindCopied(s)
	If idx >= 0
		ExpiresAt[idx] = GameDaysPassed.GetValue() + CopyDays    ; seen again: memory refreshed
		Return
	EndIf
	If PlayerRef.HasSpell(s)
		Return
	EndIf
	String name = s.GetName()
	If Blocked.HasForm(s)
		Explain(s, "Sharingan: " + name + " is a kekkei genkai or secret technique. It cannot be copied.")
		Return
	EndIf
	MagicEffect me = s.GetNthEffectMagicEffect(s.GetCostliestEffectIndex())
	If !me || me.GetCastingType() == 0
		Return    ; constant effects (abilities) are part of the body, not a technique
	EndIf
	Int level = me.GetSkillLevel()
	Int cap = 100
	If PlayerRef.HasPerk(Stage1)
		cap = 25
	ElseIf PlayerRef.HasPerk(Stage2)
		cap = 50
	EndIf
	If level > cap
		Explain(s, "Sharingan: your eye is not mature enough to read " + name + ".")
		Return
	EndIf
	String school = me.GetAssociatedSkill()
	If school != "" && PlayerRef.GetActorValue(school) < level
		Explain(s, "Sharingan: you saw " + name + ", but lack the chakra control (" + school + " " + level + ").")
		Return
	EndIf
	Float t = Utility.GetCurrentRealTime()
	If NextCopyTime > t + CooldownSeconds
		NextCopyTime = 0.0    ; saved from a longer session (real time restarts every launch)
	EndIf
	If t < NextCopyTime
		Return
	EndIf
	Float pct = PlayerRef.GetActorValuePercentage("Magicka")
	Float cur = PlayerRef.GetActorValue("Magicka")
	Float cost = 0.0
	If pct > 0.0
		cost = (cur / pct) * MagickaCostFraction
	EndIf
	If pct <= 0.0 || cur < cost
		Explain(s, "Sharingan: your chakra is exhausted. You cannot copy " + name + ".")
		Return
	EndIf
	Int slot = FindCopied(None)
	If slot < 0
		Explain(s, "Sharingan: your mind cannot hold more copied jutsu.")
		Return
	EndIf
	PlayerRef.DamageActorValue("Magicka", cost)
	PlayerRef.AddSpell(s, False)
	Copied[slot] = s
	ExpiresAt[slot] = GameDaysPassed.GetValue() + CopyDays
	NextCopyTime = t + CooldownSeconds
	Debug.Notification("Sharingan: copied " + name + "!")
EndFunction

; =====================================================================================================
; Sharingan Read. While the Sharingan is open, every attack an enemy makes builds Read stacks on that enemy:
; a melee hit on you +1 (power +2), any swing at you +0.5 (so dodged and missed attacks teach too), a power-attack
; swing +2, a spell or arrow at you +1, an attack on someone else you can see +0.34. Tiers:
;   1 Adaptation      you take 15% less damage from them (25% at tier 2, 35% at tier 3) - CSHC_ReadPerk
;   2 Counter-Read    blocking, parrying or dodging their attack opens them up: your next hit within 2 s does
;                     +50% damage and may stagger; read during Quick Reflexes slow time it is +100% and always staggers
;   3 Seeing through  Quick Reflexes against them is slower and longer, and EVERY swing at you triggers it
; Quick Reflexes (the Uchiha Clan's perk, swing spell replaced) keeps its slowdown and screen effect, scales
; with how well you read the attacker, and only fires for close enemies targeting you, at most every 2.5 s.
; Everything resets when the fight ends. A more mature eye reads faster, and Eye Adaptation (Obito Tobi Path
; Additions) speeds it up further.
; =====================================================================================================

Bool Function EyeOpen()
	Return SharinganState.GetValue() == 2
EndFunction

Perk Function UchihaPerk(Int id)
	Return Game.GetFormFromFile(id, "UchihaClan.esp") as Perk
EndFunction

; Highest Sharingan stage: 1 = 1 tomoe (aaaStage1), 2 = 2 tomoe, 3 = 3 tomoe (aaaStage3), 4 = Mangekyo (aaaStage4-6).
; Awakening the Mangekyo removes the stage perks, so the Uchiha Clan's aaaMangekyouAwakened flag is checked first
; (without it a Mangekyo user read as a 1-tomoe beginner).
Int Function EyeStage()
	GlobalVariable awakened = Game.GetFormFromFile(0x160CAE, "UchihaClan.esp") as GlobalVariable
	If awakened && awakened.GetValue() >= 1
		Return 4
	EndIf
	Int i = 0x48D4
	While i >= 0x48D1
		Perk p = UchihaPerk(i)
		If p && PlayerRef.HasPerk(p)
			If i >= 0x48D2
				Return 4
			EndIf
			Return 3
		EndIf
		i -= 1
	EndWhile
	If PlayerRef.HasPerk(Stage2)
		Return 2
	EndIf
	Return 1
EndFunction

; The Uchiha Clan's own Quick Reflexes strength (remaining world speed) by path and stage.
Float Function StageMagnitude()
	Int st = CachedStage
	If st > 3
		st = 3
	EndIf
	Float[] m = new Float[3]
	If PlayerRef.HasPerk(UchihaPerk(0x2256D))          ; Shisui
		m[0] = 0.15
		m[1] = 0.1
		m[2] = 0.01
	ElseIf PlayerRef.HasPerk(UchihaPerk(0x22568))      ; Itachi
		m[0] = 0.25
		m[1] = 0.2
		m[2] = 0.1
	ElseIf PlayerRef.HasPerk(UchihaPerk(0x22569))      ; Madara
		m[0] = 0.2
		m[1] = 0.15
		m[2] = 0.05
	ElseIf PlayerRef.HasPerk(UchihaPerk(0x2256C)) || PlayerRef.HasPerk(UchihaPerk(0x2256B))   ; Tobi, Sasuke
		m[0] = 0.3
		m[1] = 0.2
		m[2] = 0.15
	Else
		Return 0.2
	EndIf
	Return m[st - 1]
EndFunction

; Stacks needed for tier 1/2/3; a more mature eye reads faster.
Int Function TierNeed(Int tier)
	Float base = 3.0
	If tier == 2
		base = 6.0
	ElseIf tier == 3
		base = 10.0
	EndIf
	Int st = CachedStage
	If st == 1
		base *= 1.5
	ElseIf st == 2
		base *= 1.2
	ElseIf st >= 4
		base *= 0.7
	EndIf
	base *= 1.0 - MasteryReadBonus * CachedMastery / 100.0
	Return Math.Ceiling(base)
EndFunction

Int Function ReadIndex(Actor a, Bool create)
	Int i = 0
	While i < ReadCount
		If ReadActors[i] == a
			Return i
		EndIf
		i += 1
	EndWhile
	If !create
		Return -1
	EndIf
	If ReadCount < 16
		i = ReadCount
		ReadCount += 1
	Else
		; full: take over the slot of an enemy that is dead or gone
		i = 0
		While i < 16 && ReadActors[i] && !ReadActors[i].IsDead() && ReadActors[i].Is3DLoaded()
			i += 1
		EndWhile
		If i >= 16
			Return -1
		EndIf
		Actor old = ReadActors[i]
		If old
			old.DispelSpell(MarkSpell1)
			old.DispelSpell(MarkSpell2)
			old.DispelSpell(MarkSpell3)
		EndIf
	EndIf
	ReadActors[i] = a
	ReadPts[i] = 0.0
	ReadTier[i] = 0
	ReadLastAction[i] = 0.0
	Return i
EndFunction

Int Function TierOf(Actor a)
	If !a || !ReadActors
		Return 0
	EndIf
	Int i = ReadIndex(a, False)
	If i < 0
		Return 0
	EndIf
	Return ReadTier[i]
EndFunction

; Points from a seen action (OnActorAction): at most one per ActionGap per enemy.
Function AddSeen(Actor a, Float pts)
	Int i = ReadIndex(a, True)
	If i < 0
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If ReadLastAction[i] > now
		ReadLastAction[i] = 0.0       ; real time restarts every launch
	EndIf
	If now - ReadLastAction[i] < ActionGap
		Return
	EndIf
	ReadLastAction[i] = now
	AddRead(a, pts)
EndFunction

Function AddRead(Actor a, Float pts)
	If !a || a == PlayerRef || a.IsDead() || !EyeOpen() || !ReadActors
		Return
	EndIf
	Int i = ReadIndex(a, True)
	If i < 0
		Return
	EndIf
	ReadPts[i] = ReadPts[i] + pts
	Int tier = ReadTier[i]
	While tier < 3 && ReadPts[i] >= TierNeed(tier + 1)
		tier += 1
	EndWhile
	If tier == ReadTier[i]
		Return
	EndIf
	ReadTier[i] = tier
	a.DispelSpell(MarkSpell1)
	a.DispelSpell(MarkSpell2)
	a.DispelSpell(MarkSpell3)
	String who = a.GetDisplayName()
	If tier == 1
		MarkSpell1.Cast(PlayerRef, a)
		Debug.Notification("Sharingan: you are adapting to " + who + "'s movements.")
	ElseIf tier == 2
		MarkSpell2.Cast(PlayerRef, a)
		Debug.Notification("Sharingan: you can read " + who + "'s attacks. Counter them!")
	Else
		MarkSpell3.Cast(PlayerRef, a)
		Debug.Notification("Sharingan: you see through " + who + " completely.")
	EndIf
	Debug.Trace("CSHC read: " + who + " tier " + tier + " (" + ReadPts[i] + " stacks)")
EndFunction

Function ResetRead()
	Int i = 0
	While i < ReadCount
		Actor a = ReadActors[i]
		If a
			a.DispelSpell(MarkSpell1)
			a.DispelSpell(MarkSpell2)
			a.DispelSpell(MarkSpell3)
			a.DispelSpell(OpeningSpell)
			a.DispelSpell(OpeningPerfectSpell)
		EndIf
		ReadActors[i] = None
		ReadPts[i] = 0.0
		ReadTier[i] = 0
		ReadLastAction[i] = 0.0
		i += 1
	EndWhile
	ReadCount = 0
	LastSwinger = None
EndFunction

; From CSHC_ReadEffect: a melee hit on the player (blocked or not).
Function HitBy(Actor a, Bool power, Bool blocked)
	Float pts = 1.0
	If power
		pts = 2.0
	EndIf
	AddRead(a, pts)
	((Self as Quest) as CSHC_KamuiQuestScript).NoteAttacker(a, False)
	If blocked
		Counter(a)    ; blocks and Elden Parry parries both arrive as blocked hits
	EndIf
EndFunction

; From the Quick Reflexes perk: an enemy power attack swung at the player. One of the two actors is the player.
Function PowerSwing(Actor akTarget, Actor akCaster)
	Actor a = akCaster
	If !a || a == PlayerRef
		a = akTarget
	EndIf
	If a == PlayerRef
		a = None
	EndIf
	Bool slowed = StartQR(a)          ; first: the slowdown is all about timing
	If a
		LastSwinger = a
		LastSwingTime = Utility.GetCurrentRealTime()
		AddRead(a, 2.0)
		((Self as Quest) as CSHC_KamuiQuestScript).PhaseThrough(a)    ; it passed through you: an opening
		((Self as Quest) as CSHC_KamuiQuestScript).NoteAttacker(a, True)
	EndIf
	Debug.Trace("CSHC read: power swing by " + a + ", slowed=" + slowed)
	If slowed
		FinishQR()
	EndIf
EndFunction

; 2-4: every enemy attack nearby, seen through SKSE actor actions (0 swing, 2 spell fired, 6 arrow loosed)
Event OnActorAction(Int actionType, Actor akActor, Form source, Int slot)
	If !akActor || akActor == PlayerRef || !EyeOpen() || akActor.IsDead() || !akActor.IsHostileToActor(PlayerRef)
		Return
	EndIf
	If PlayerRef.GetDistance(akActor) > WatchRange
		Return
	EndIf
	If akActor.GetCombatTarget() == PlayerRef
		If actionType == 0
			LastSwinger = akActor                                  ; any attack you dodge now counts as a counter
			LastSwingTime = Utility.GetCurrentRealTime()
			RegisterForAnimationEvent(akActor, "recoilLargeStart")  ; Sharingan foresight: a parry makes it recoil
			RegisterForAnimationEvent(akActor, "recoilStart")
			If TierOf(akActor) == 3 && StartQR(akActor)            ; you see through them: every swing is slowed
				AddSeen(akActor, SwingAtYouPts)
				FinishQR()
				Return
			EndIf
			AddSeen(akActor, SwingAtYouPts)
		Else
			AddSeen(akActor, ShotAtYouPts)
		EndIf
	ElseIf PlayerRef.HasLOS(akActor)
		AddSeen(akActor, WatchPts)
	EndIf
EndEvent

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If asEventName == "recoilLargeStart" || asEventName == "recoilStart"
		Parried(akSource as Actor)
		Return
	EndIf
	If asEventName != "MCO_DodgeOpen" || !LastSwinger
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If LastSwingTime > now
		LastSwingTime = 0.0
	EndIf
	If now - LastSwingTime <= DodgeWindow
		Counter(LastSwinger)    ; dodged an attack that was just swung at you
		LastSwinger = None
	EndIf
EndEvent

Function Counter(Actor a)
	If !a || a.IsDead() || TierOf(a) < 2
		Return
	EndIf
	a.DispelSpell(OpeningSpell)
	a.DispelSpell(OpeningPerfectSpell)
	Float now = Utility.GetCurrentRealTime()
	Bool say = now - LastCounterMsg > 6.0 || LastCounterMsg > now
	If QRActive
		OpeningPerfectSpell.Cast(PlayerRef, a)
		If say
			Debug.Notification("Sharingan: perfect read - strike now!")
		EndIf
	Else
		OpeningSpell.Cast(PlayerRef, a)
		If say
			Debug.Notification("Sharingan: you read the attack - counter!")
		EndIf
	EndIf
	If say
		LastCounterMsg = now
	EndIf
	Debug.Trace("CSHC read: counter opening on " + a.GetDisplayName() + " perfect=" + QRActive)
EndFunction

; ---- Sharingan foresight: parries ----

Function Parried(Actor a)
	If !a || a == PlayerRef || a.IsDead() || !EyeOpen() || a.GetCombatTarget() != PlayerRef || PlayerRef.GetDistance(a) > 500.0
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If LastSwingTime > now
		LastSwingTime = 0.0
	EndIf
	If LastParryTime > now
		LastParryTime = 0.0
	EndIf
	If a != LastSwinger || now - LastSwingTime > ParryWindow
		Return                      ; it recoiled, but not from a swing at you just now
	EndIf
	If a == LastParried && now - LastParryTime < 0.8
		Return                      ; recoilLargeStart and recoilStart can both arrive for one parry
	EndIf
	LastParried = a
	LastParryTime = now
	; (C) the parry teaches the eye
	AddRead(a, ParryReadPts)
	; (A) an opening at any tier; perfect during Quick Reflexes or against an enemy you see through
	a.DispelSpell(OpeningSpell)
	a.DispelSpell(OpeningPerfectSpell)
	Bool perfect = QRActive || TierOf(a) == 3
	If perfect
		OpeningPerfectSpell.Cast(PlayerRef, a)
	Else
		OpeningSpell.Cast(PlayerRef, a)
	EndIf
	If now - LastParryMsg > 6.0 || LastParryMsg > now
		LastParryMsg = now
		If perfect
			Debug.Notification("Sharingan: parried and seen through - strike!")
		Else
			Debug.Notification("Sharingan: parry read - counter!")
		EndIf
	EndIf
	Debug.Trace("CSHC read: PARRY of " + a.GetDisplayName() + " (tier " + TierOf(a) + ", perfect " + perfect + ")")
	; (D) Mangekyo: the follow-up passes through you
	((Self as Quest) as CSHC_KamuiQuestScript).ParrySlip(a)
EndFunction

; ---- Quick Reflexes ----

Float Function SlowMag(Int i)
	Float[] m = new Float[14]
	m[0] = 0.01
	m[1] = 0.03
	m[2] = 0.05
	m[3] = 0.08
	m[4] = 0.1
	m[5] = 0.12
	m[6] = 0.15
	m[7] = 0.2
	m[8] = 0.25
	m[9] = 0.3
	m[10] = 0.4
	m[11] = 0.5
	m[12] = 0.65
	m[13] = 0.8
	Return m[i]
EndFunction

Function SetSlow(Float mag)
	Int best = 0
	Float bestDiff = 9.0
	Int i = 0
	While i < 14
		Float d = Math.Abs(SlowMag(i) - mag)
		If d < bestDiff
			bestDiff = d
			best = i
		EndIf
		i += 1
	EndWhile
	Spell sp = SlowSpells.GetAt(best) as Spell
	If sp == CurrentSlow
		Return
	EndIf
	CurrentSlow = sp
	sp.Cast(PlayerRef, PlayerRef)
EndFunction

; Waits real seconds (slow time stretches game-time waits).
Function WaitReal(Float secs)
	Float endAt = Utility.GetCurrentRealTime() + secs
	While Utility.GetCurrentRealTime() < endAt
		Utility.Wait(0.02)
	EndWhile
EndFunction

; Starts the slowdown at once (values cached by the poll). Returns False when it does not fire.
Bool Function StartQR(Actor attacker)
	Float now = Utility.GetCurrentRealTime()
	If LastQR > now
		LastQR = 0.0
	EndIf
	If QRActive || now - LastQR < QRCooldown
		Return False
	EndIf
	If attacker && (PlayerRef.GetDistance(attacker) > QRRange || attacker.GetCombatTarget() != PlayerRef)
		Return False
	EndIf
	LastQR = now
	QRActive = True
	; Read-aware: lighter against an enemy you have not read yet, deeper and longer once you see through them
	Float target = CachedQRMag
	Float hold = 1.0                  ; (the Uchiha original: stage strength for 1 s)
	Int tier = TierOf(attacker)
	If tier == 0
		target = target * 1.3
		If target > 0.4
			target = 0.4
		EndIf
		hold = 0.8
	ElseIf tier == 3
		target = target * 0.6
		hold = 1.4
	EndIf
	; one clean slowdown: stepping between several slow-time effects cancelled it (an ending slow-time effect
	; resets time to normal); the smooth part is the Quick Reflexes screen effect, which fades in and out
	SetSlow(target)
	QREndAt = now + hold
	Debug.Trace("CSHC read: Quick Reflexes to " + target + " for " + hold + " s (tier " + tier + ")")
	Return True
EndFunction

Function FinishQR()
	WaitReal(QREndAt - Utility.GetCurrentRealTime())
	If CurrentSlow
		PlayerRef.DispelSpell(CurrentSlow)
		CurrentSlow = None
	EndIf
	QRActive = False
EndFunction

Scriptname CSHC_KamuiQuestScript extends Quest
{Kamui upgrades for the Uchiha Clan's "Kamui: Ethereal" (second script on CSHC_Quest).
 1 Kamui mode: cast the power to phase, cast again to solidify; up to 5 minutes (canon), then forced solid with a
   short strain. The power keeps its own eye swap, sounds and blindness; CSHC_PhaseSpell does the phasing.
 2 Phase Strike: attacking in Kamui mode solidifies you only while you attack, then you phase back.
 3 Reflex Phase: every dodge phases you for half a second while the Mangekyo Sharingan is open.
 4 Kamui travel (teleport / warp spells) needs a solid body: it ends Kamui mode first.
 5 Visuals: translucent while phased, Kamui swirl on phasing in and out and when an attack passes through.
 6 Only the manual power adds Mangekyo blindness (Phase Strike and Reflex Phase use CSHC_PhaseSpell).
 7 An enemy power attack passing through you counts as a read for Counter-Read (CSHC_CopyQuestScript).
 8 Kamui Instinct (on/off power): with the Mangekyo open, two enemies power attacking you within 1.5 s, or falling
   below 25% health with two enemies on you, phases you for 2.5 s (45 s cooldown). Attacking ends it early.
 9 Kamui: Shuriken Barrage (lesser power): a Kamui opens at your eye and fires a stream of Fuma shuriken from the
   Kamui dimension at your target; the last one staggers. Needs the Mangekyo open and a solid body (canon: Kamui
   cannot eject things while intangible).
10 Kamui: Severance (lesser power, left eye): fix the Mangekyo on an enemy in sight; a Kamui distortion forms on
   them for a moment, then tears away part of their body: heavy damage that ignores armor (flat + level + a share of
   their health, so it matters against giants and dragons too), a large stagger, and their weapon (or shield) is
   warped into the Kamui chest. Bosses immune to Kamui keep their weapon. Needs a solid body like the barrage.
   Left eye only: needs the Mangekyo awakened, not the Sharingan open.}

Actor Property PlayerRef Auto
Spell Property PhaseSpell Auto
Spell Property SwirlSpell Auto
Spell Property KamuiEthereal Auto
{The Uchiha Clan's "Kamui: Ethereal" power (overridden: 5 minutes + CSHC_KamuiModeEffect).}
FormList Property Teleports Auto
GlobalVariable Property MangekyoAwakened Auto
{Uchiha Clan aaaMangekyouAwakened: 1 once the Mangekyo Sharingan is awakened.}
GlobalVariable Property SharinganState Auto
{Vanilla NightEyeTransitionGlobal: 2 while the Sharingan is open.}
Sound Property SlipSound Auto
{"Obito no Kamui" line, played when an attack passes through you (at most every SlipSoundCooldown seconds).}
Float Property SlipSoundCooldown = 3.0 AutoReadOnly
Int Property DodgesPerSound = 5 AutoReadOnly
{Reflex Phase plays the line on every this-many-th phase dodge.}
GlobalVariable Property InstinctOn Auto
{CSHC_InstinctOn: 1 = Kamui Instinct on.}
Spell Property InstinctPower Auto
{"Kamui: Instinct" on/off lesser power, given once the Mangekyo is awakened.}
Float Property InstinctSeconds = 2.5 AutoReadOnly
Float Property InstinctCooldown = 45.0 AutoReadOnly
Float Property PowerPairWindow = 1.5 AutoReadOnly
{Trigger A: power attacks from two different enemies within this many seconds.}
Float Property NearDeathHealth = 0.25 AutoReadOnly
{Trigger C: health fraction.}
Float Property EngagedWindow = 6.0 AutoReadOnly
{Trigger C: an enemy counts as "on you" if it attacked you in the last this many seconds.}
Spell Property ShurikenSpell Auto
Spell Property ShurikenFinal Auto
{Last shuriken: damage + stagger.}
Spell Property BarragePower Auto
Activator Property CasterBase Auto
{Vanilla FXEmptyActivator: invisible launch point placed at Obito's eye.}
Sound Property SwirlSound Auto
{Naruto Overhaul's Kamui warp sound: the barrage's swirl. ("Obito no Kamui" is only for attacks slipping through.)}
Int Property BarrageCount = 14 AutoReadOnly
Float Property BarrageInterval = 0.08 AutoReadOnly
Float Property BarrageCooldown = 20.0 AutoReadOnly
Float Property BarrageMagicka = 40.0 AutoReadOnly
Float Property BarrageRange = 3000.0 AutoReadOnly
Float Property BarrageWindup = 0.45 AutoReadOnly
{The eye-cast animation (OAR "Kamui Barrage - Eye Cast") raises the hand to the eye first; the swirl opens then.}
Spell Property SeveranceFocus Auto
{The distortion forming on the target (swirl art).}
Spell Property SeveranceStrike Auto
{Large stagger as the distortion tears; cast by the player so it counts as an attack.}
Spell Property SeverancePower Auto
Float Property SeveranceRange = 6000.0 AutoReadOnly
Float Property SeveranceAimCone = 8.0 AutoReadOnly
Float Property SeveranceFocusSeconds = 1.0 AutoReadOnly
Float Property SeveranceCooldown = 30.0 AutoReadOnly
Float Property SeveranceMagicka = 60.0 AutoReadOnly
Float Property SeveranceHealthShare = 0.12 AutoReadOnly
{Share of the target's full health added to the damage.}
Float Property ModeSeconds = 300.0 AutoReadOnly
Float Property StrainSeconds = 30.0 AutoReadOnly
Float Property RephaseDelay = 0.9 AutoReadOnly
{Phase Strike: phase back this long after your last attack input.}
Float Property ReflexSeconds = 0.5 AutoReadOnly
Float Property ReflexCooldown = 2.0 AutoReadOnly
Float Property ParrySlipSeconds = 0.8 AutoReadOnly
{Sharingan foresight (D): after a parry with the Mangekyo open, you phase this long so the follow-up passes through.}
Float Property ParrySlipCooldown = 6.0 AutoReadOnly
Float Property ParrySlipMagicka = 10.0 AutoReadOnly
{Small on purpose (user, 2026-10-16): no potions, light armour - this is part of Obito's defence.}
Float Property PhasedAlpha = 0.45 AutoReadOnly
Int Property Mouse5 = 260 AutoReadOnly
{The SkyFX power-attack key (DKAF), so power attacks solidify you too.}

Bool ModeOn = False
Bool Phased = False
Bool Rephasing = False
Float ModeStart = 0.0
Float LastModeEnd = -100.0
Float StrainUntil = 0.0
Float LastAttackInput = 0.0
Float LastReflex = -100.0
Float LastParrySlip = -100.0
Float NotifiedAt = -1.0
Float LastTick = -100.0
Float LastSlipSound = -100.0
Int ReflexCount = 0
Bool InstinctActive = False
Float InstinctEndAt = 0.0
Float LastBarrage = -100.0
Float LastSeverance = -100.0
Bool Severing = False
Bool Barraging = False
Float LastInstinct = -100.0
Actor LastPowerAttacker
Float LastPowerTime = -100.0
Actor[] RecentAttackers
Float[] RecentTimes

Event OnInit()
	RegisterForSingleUpdate(1.0)
EndEvent

; ---------------- state ----------------

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

; Real time restarts every launch; times saved from a longer session are cleared before use.
Function FixClocks()
	Float t = Now()
	If ModeStart > t
		ModeStart = t
	EndIf
	If LastModeEnd > t
		LastModeEnd = -100.0
	EndIf
	If StrainUntil > t + StrainSeconds
		StrainUntil = 0.0
	EndIf
	If LastAttackInput > t
		LastAttackInput = 0.0
	EndIf
	If LastReflex > t
		LastReflex = -100.0
	EndIf
EndFunction

Bool Function IsPhased()
	Return Phased
EndFunction

Bool Function MangekyoActive()
	Return SharinganState.GetValue() == 2 && MangekyoAwakened && MangekyoAwakened.GetValue() >= 1
EndFunction

Function Phase()
	If Phased
		Return
	EndIf
	Phased = True
	PhaseSpell.Cast(PlayerRef, PlayerRef)
	Debug.Trace("CSHC kamui: phase (mode=" + ModeOn + ")")
	PlayerRef.SetAlpha(PhasedAlpha, True)
EndFunction

Function Solid()
	If !Phased
		Return
	EndIf
	Phased = False
	PlayerRef.DispelSpell(PhaseSpell)
	Debug.Trace("CSHC kamui: solid (mode=" + ModeOn + ")")
	PlayerRef.SetAlpha(1.0, True)
EndFunction

Function Swirl()
	SwirlSpell.Cast(PlayerRef, PlayerRef)
EndFunction

; "Obito no Kamui" line, at most every SlipSoundCooldown seconds.
Function PlaySlipSound()
	Float t = Now()
	If LastSlipSound > t
		LastSlipSound = -100.0
	EndIf
	If SlipSound && t - LastSlipSound >= SlipSoundCooldown
		LastSlipSound = t
		SlipSound.Play(PlayerRef)
	EndIf
EndFunction

; ---------------- 1: Kamui mode ----------------

Function ModeEffectStart()
	FixClocks()
	Float t = Now()
	If t < StrainUntil
		Debug.Notification("Kamui: your body has not recovered from the strain (" + ((StrainUntil - t) as Int) + "s).")
		PlayerRef.DispelSpell(KamuiEthereal)
		Return
	EndIf
	If ModeOn || t - LastModeEnd < 0.5
		; the power was cast again while active: solidify (casting it restarts the effect first)
		EndMode()
		PlayerRef.DispelSpell(KamuiEthereal)
		Debug.Notification("Kamui: you solidify.")
		Return
	EndIf
	ModeOn = True
	ModeStart = t
	Debug.Trace("CSHC kamui: mode on")
	Swirl()
	Phase()
	RegisterForControl("Right Attack/Block")
	RegisterForControl("Left Attack/Block")
	RegisterForKey(Mouse5)
	Debug.Notification("Kamui: intangible (up to 5 minutes). Attack to strike, cast again to solidify.")
EndFunction

Function ModeEffectFinish()
	FixClocks()
	Float t = Now()
	LastModeEnd = t
	If !ModeOn
		Return
	EndIf
	Bool timedOut = t - ModeStart >= ModeSeconds - 5.0
	EndMode()
	If timedOut
		StrainUntil = t + StrainSeconds
		Debug.Notification("Kamui: five minutes reached. You are forced solid.")
	EndIf
EndFunction

Function EndMode()
	Debug.Trace("CSHC kamui: mode off")
	ModeOn = False
	UnregisterForControl("Right Attack/Block")
	UnregisterForControl("Left Attack/Block")
	UnregisterForKey(Mouse5)
	If Phased
		Solid()
		Swirl()
	EndIf
EndFunction

; ---------------- 2: Phase Strike ----------------

Event OnControlDown(String control)
	If Utility.IsInMenuMode()
		Return
	EndIf
	If ModeOn
		StrikeInput()
	ElseIf InstinctActive
		EndInstinct()
	EndIf
EndEvent

Event OnKeyDown(Int keyCode)
	If keyCode != Mouse5 || Utility.IsInMenuMode()
		Return
	EndIf
	If ModeOn
		StrikeInput()
	ElseIf InstinctActive
		EndInstinct()
	EndIf
EndEvent

Function StrikeInput()
	LastAttackInput = Now()
	Debug.Trace("CSHC kamui: strike input")
	Solid()
	If Rephasing
		Return
	EndIf
	Rephasing = True
	While ModeOn && Now() - LastAttackInput < RephaseDelay
		Utility.Wait(0.1)
	EndWhile
	If ModeOn
		Phase()
	EndIf
	Rephasing = False
EndFunction

; ---------------- 3: Reflex Phase ----------------

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If asEventName != "MCO_DodgeOpen" || ModeOn || !MangekyoActive()
		Return
	EndIf
	FixClocks()
	Float t = Now()
	If t - LastReflex < ReflexCooldown
		Return
	EndIf
	LastReflex = t
	Debug.Trace("CSHC kamui: reflex phase on dodge")
	Phase()
	Swirl()
	ReflexCount += 1
	If ReflexCount >= DodgesPerSound
		ReflexCount = 0
		PlaySlipSound()
	EndIf
	Float endAt = Now() + ReflexSeconds
	While Now() < endAt
		Utility.Wait(0.05)
	EndWhile
	If !ModeOn && !InstinctActive
		Solid()
	EndIf
EndEvent

; ---------------- 3b: Kamui slip after a parry (Sharingan foresight) ----------------

; From CSHC_CopyQuestScript.Parried.
Function ParrySlip(Actor attacker)
	If ModeOn || InstinctActive || !MangekyoActive()
		Return
	EndIf
	FixClocks()
	Float t = Now()
	If LastParrySlip > t
		LastParrySlip = -100.0
	EndIf
	If t - LastParrySlip < ParrySlipCooldown * Focus()
		Return
	EndIf
	Float cost = ParrySlipMagicka * Focus()
	If PlayerRef.GetActorValue("Magicka") < cost
		Return
	EndIf
	LastParrySlip = t
	PlayerRef.DamageActorValue("Magicka", cost)
	Debug.Trace("CSHC kamui: parry slip after parrying " + attacker)
	Phase()
	Swirl()
	PlaySlipSound()
	Float endAt = Now() + ParrySlipSeconds
	While Now() < endAt
		Utility.Wait(0.05)
	EndWhile
	If !ModeOn && !InstinctActive
		Solid()
	EndIf
EndFunction

; ---------------- 4: Kamui travel needs a solid body ----------------

Function KamuiTravelCast(Form akSpell)
	If !Teleports || !Teleports.HasForm(akSpell)
		Return
	EndIf
	Debug.Trace("CSHC kamui: travel spell " + akSpell.GetName())
	If ModeOn
		EndMode()
		PlayerRef.DispelSpell(KamuiEthereal)
		Debug.Notification("Kamui: you solidify to warp.")
	ElseIf Phased
		Solid()
	EndIf
EndFunction

; ---------------- 5 + 7: attacks passing through ----------------

; From CSHC_CopyQuestScript.PowerSwing: an enemy power attack swung at you.
Function PhaseThrough(Actor attacker)
	If !Phased || !attacker
		Return
	EndIf
	Swirl()
	Debug.Trace("CSHC kamui: attack passed through from " + attacker.GetDisplayName())
	PlaySlipSound()
	((Self as Quest) as CSHC_CopyQuestScript).Counter(attacker)
EndFunction

; ---------------- upkeep ----------------

Event OnUpdate()
	LastTick = Now()
	FixClocks()
	If InstinctActive && (Now() >= InstinctEndAt - 0.05 || InstinctEndAt > Now() + InstinctSeconds)
		EndInstinct()
	EndIf
	RegisterForAnimationEvent(PlayerRef, "MCO_DodgeOpen")    ; renewed every tick (dropped on reload)
	If InstinctPower && MangekyoAwakened && MangekyoAwakened.GetValue() >= 1 && !PlayerRef.HasSpell(InstinctPower)
		PlayerRef.AddSpell(InstinctPower, False)
		Debug.Notification("Kamui: Instinct is ready (Powers). It is on; use the power to switch it off.")
	EndIf
	If BarragePower && MangekyoAwakened && MangekyoAwakened.GetValue() >= 1 && !PlayerRef.HasSpell(BarragePower)
		PlayerRef.AddSpell(BarragePower, False)
		Debug.Notification("Kamui: Shuriken Barrage is ready (Powers).")
	EndIf
	If SeverancePower && MangekyoAwakened && MangekyoAwakened.GetValue() >= 1 && !PlayerRef.HasSpell(SeverancePower)
		PlayerRef.AddSpell(SeverancePower, False)
		Debug.Notification("Kamui: Severance is ready (Powers).")
	EndIf
	If MangekyoActive()
		Float t = Now()
		If NotifiedAt < 0.0 || NotifiedAt > t
			NotifiedAt = t
			Debug.Trace("CSHC kamui: Mangekyou detected, path " + PathName())
			Debug.Notification("Sharingan: Mangekyou detected (" + PathName() + " path). Kamui reflexes active.")
		EndIf
	EndIf
	If Phased && !ModeOn && !InstinctActive && Now() - LastReflex > ReflexSeconds + 2.0 && !Rephasing
		Solid()    ; safety: never stay phased outside Kamui mode
	EndIf
	RegisterForSingleUpdate(1.0)
EndEvent

String Function PathName()
	If PlayerRef.HasPerk(Game.GetFormFromFile(0x2256C, "UchihaClan.esp") as Perk)
		Return "Tobi"
	ElseIf PlayerRef.HasPerk(Game.GetFormFromFile(0x22569, "UchihaClan.esp") as Perk)
		Return "Madara"
	ElseIf PlayerRef.HasPerk(Game.GetFormFromFile(0x22568, "UchihaClan.esp") as Perk)
		Return "Itachi"
	ElseIf PlayerRef.HasPerk(Game.GetFormFromFile(0x2256B, "UchihaClan.esp") as Perk)
		Return "Sasuke"
	ElseIf PlayerRef.HasPerk(Game.GetFormFromFile(0x2256D, "UchihaClan.esp") as Perk)
		Return "Shisui"
	EndIf
	Return "no"
EndFunction

; Called from CSHC_CopyQuestScript's poll, so saves made before the Kamui upgrade start this script's loop too.
Function Ensure()
	If !PhaseSpell
		PhaseSpell = Game.GetFormFromFile(0x829, "Sharingan Copy.esp") as Spell
		SwirlSpell = Game.GetFormFromFile(0x82B, "Sharingan Copy.esp") as Spell
		Teleports = Game.GetFormFromFile(0x82D, "Sharingan Copy.esp") as FormList
		KamuiEthereal = Game.GetFormFromFile(0x26C14, "UchihaClan.esp") as Spell
		MangekyoAwakened = Game.GetFormFromFile(0x160CAE, "UchihaClan.esp") as GlobalVariable
		SharinganState = Game.GetFormFromFile(0x0EFC75, "Skyrim.esm") as GlobalVariable
		PlayerRef = Game.GetPlayer()
	EndIf
	If !SlipSound
		SlipSound = Game.GetFormFromFile(0x82F, "Sharingan Copy.esp") as Sound
	EndIf
	If !BarragePower
		ShurikenSpell = Game.GetFormFromFile(0x835, "Sharingan Copy.esp") as Spell
		ShurikenFinal = Game.GetFormFromFile(0x837, "Sharingan Copy.esp") as Spell
		BarragePower = Game.GetFormFromFile(0x839, "Sharingan Copy.esp") as Spell
		CasterBase = Game.GetFormFromFile(0x0B79FF, "Skyrim.esm") as Activator
	EndIf
	If !SwirlSound
		SwirlSound = Game.GetFormFromFile(0x83A, "Sharingan Copy.esp") as Sound
	EndIf
	If !SeverancePower
		SeveranceFocus = Game.GetFormFromFile(0x83C, "Sharingan Copy.esp") as Spell
		SeveranceStrike = Game.GetFormFromFile(0x83E, "Sharingan Copy.esp") as Spell
		SeverancePower = Game.GetFormFromFile(0x840, "Sharingan Copy.esp") as Spell
	EndIf
	If !InstinctOn
		InstinctOn = Game.GetFormFromFile(0x830, "Sharingan Copy.esp") as GlobalVariable
		InstinctPower = Game.GetFormFromFile(0x832, "Sharingan Copy.esp") as Spell
	EndIf
	Float t = Now()
	If LastTick > t || t - LastTick > 3.0
		LastTick = t
		RegisterForSingleUpdate(0.5)    ; loop not running (script added to an existing save, or a fresh launch)
	EndIf
EndFunction

; ---------------- 8: Kamui Instinct ----------------

; From CSHC_CopyQuestScript: any melee hit (or blocked hit) and every power swing at you.
Function NoteAttacker(Actor a, Bool powerSwing)
	If !a || a.IsDead()
		Return
	EndIf
	If !RecentAttackers
		RecentAttackers = new Actor[8]
		RecentTimes = new Float[8]
	EndIf
	Float t = Now()
	If LastPowerTime > t
		LastPowerTime = -100.0
	EndIf
	Int i = 0
	Int oldest = 0
	Bool stored = False
	While i < 8 && !stored
		If RecentAttackers[i] == a || !RecentAttackers[i]
			RecentAttackers[i] = a
			RecentTimes[i] = t
			stored = True
		ElseIf RecentTimes[i] < RecentTimes[oldest]
			oldest = i
		EndIf
		i += 1
	EndWhile
	If !stored
		RecentAttackers[oldest] = a
		RecentTimes[oldest] = t
	EndIf
	If powerSwing
		If LastPowerAttacker && LastPowerAttacker != a && t - LastPowerTime <= PowerPairWindow
			TryInstinct("two power attacks at once")
		EndIf
		LastPowerAttacker = a
		LastPowerTime = t
	EndIf
	CheckNearDeath()
EndFunction

Int Function EngagedCount()
	If !RecentAttackers
		Return 0
	EndIf
	Float t = Now()
	Int n = 0
	Int i = 0
	While i < 8
		Actor a = RecentAttackers[i]
		If a && RecentTimes[i] <= t && t - RecentTimes[i] <= EngagedWindow && !a.IsDead()
			n += 1
		EndIf
		i += 1
	EndWhile
	Return n
EndFunction

Function CheckNearDeath()
	If PlayerRef.GetActorValuePercentage("Health") < NearDeathHealth && EngagedCount() >= 2
		TryInstinct("near death")
	EndIf
EndFunction

Function TryInstinct(String reason)
	If !InstinctOn || InstinctOn.GetValue() < 1 || ModeOn || InstinctActive || !MangekyoActive()
		Return
	EndIf
	FixClocks()
	Float t = Now()
	If LastInstinct > t
		LastInstinct = -100.0
	EndIf
	If t - LastInstinct < InstinctCooldown * Focus()
		Return
	EndIf
	LastInstinct = t
	InstinctActive = True
	Debug.Trace("CSHC kamui: instinct (" + reason + ")")
	Debug.Notification("Kamui: instinct.")
	Phase()
	Swirl()
	PlaySlipSound()
	RegisterForControl("Right Attack/Block")
	RegisterForControl("Left Attack/Block")
	RegisterForKey(Mouse5)
	; ended by the upkeep tick (scheduled for exactly then) instead of waiting here: callers (hit tracking in
	; CSHC_CopyQuestScript) must not be held up
	InstinctEndAt = Now() + InstinctSeconds
	RegisterForSingleUpdate(InstinctSeconds)
EndFunction

Function EndInstinct()
	If !InstinctActive
		Return
	EndIf
	InstinctActive = False
	If !ModeOn
		UnregisterForControl("Right Attack/Block")
		UnregisterForControl("Left Attack/Block")
		UnregisterForKey(Mouse5)
		Solid()
	EndIf
EndFunction

; ---------------- 9: Kamui: Shuriken Barrage ----------------

; Who to shoot: the actor under the crosshair, else the nearest recent attacker in front of you (Read / Instinct
; tracking), else nothing (fire straight ahead).
Actor Function BarrageTarget()
	Actor c = Game.GetCurrentCrosshairRef() as Actor
	If c && !c.IsDead() && c != PlayerRef && PlayerRef.GetDistance(c) <= BarrageRange
		Return c
	EndIf
	Actor best = None
	Float bestDist = BarrageRange
	If RecentAttackers
		Int i = 0
		While i < 8
			Actor a = RecentAttackers[i]
			If a && !a.IsDead() && Math.Abs(PlayerRef.GetHeadingAngle(a)) < 70.0
				Float dist = PlayerRef.GetDistance(a)
				If dist < bestDist
					best = a
					bestDist = dist
				EndIf
			EndIf
			i += 1
		EndWhile
	EndIf
	Return best
EndFunction

Function Barrage()
	If Barraging
		Return
	EndIf
	If !MangekyoActive()
		Debug.Notification("Kamui: Shuriken Barrage needs the Mangekyou Sharingan open.")
		Return
	EndIf
	FixClocks()
	Float t = Now()
	If LastBarrage > t
		LastBarrage = -100.0
	EndIf
	If t - LastBarrage < BarrageCooldown * Focus()
		Debug.Notification("Kamui: the barrage is not ready (" + ((BarrageCooldown * Focus() - (t - LastBarrage)) as Int) + "s).")
		Return
	EndIf
	If PlayerRef.GetActorValue("Magicka") < BarrageMagicka * Focus()
		Debug.Notification("Kamui: not enough chakra for the barrage.")
		Return
	EndIf
	Barraging = True
	LastBarrage = t
	PlayerRef.DamageActorValue("Magicka", BarrageMagicka * Focus())
	; canon: Kamui cannot eject things while you are intangible
	If ModeOn
		EndMode()
		PlayerRef.DispelSpell(KamuiEthereal)
	ElseIf Phased
		Solid()
	EndIf
	Float dmg = 6.0 + 0.5 * PlayerRef.GetLevel()
	ShurikenSpell.SetNthEffectMagnitude(0, dmg)
	ShurikenFinal.SetNthEffectMagnitude(0, dmg * 2.0)

	Actor target = BarrageTarget()
	Float a = PlayerRef.GetAngleZ()
	Float eyeZ = PlayerRef.GetHeight() * 0.93
	ObjectReference caster = PlayerRef.PlaceAtMe(CasterBase, 1, False, False)
	ObjectReference aim = None
	If !target
		aim = PlayerRef.PlaceAtMe(CasterBase, 1, False, False)
		aim.MoveTo(PlayerRef, Math.Sin(a) * BarrageRange, Math.Cos(a) * BarrageRange, eyeZ)
	EndIf
	Debug.Trace("CSHC kamui: barrage at " + target + " (" + dmg + " per shuriken)")
	Utility.Wait(BarrageWindup)
	Swirl()
	If SwirlSound
		SwirlSound.Play(PlayerRef)
	EndIf
	Int i = 0
	While i < BarrageCount
		; the stream leaves a Kamui swirl just in front of the eye, a little scattered like the anime
		Float side = Utility.RandomFloat(-18.0, 18.0)
		Float up = Utility.RandomFloat(-12.0, 12.0)
		caster.MoveTo(PlayerRef, Math.Sin(a) * 45.0 + Math.Cos(a) * side, Math.Cos(a) * 45.0 - Math.Sin(a) * side, eyeZ + up)
		Spell sp = ShurikenSpell
		If i == BarrageCount - 1
			sp = ShurikenFinal
		EndIf
		If target
			sp.Cast(caster, target)
		Else
			sp.Cast(caster, aim)
		EndIf
		Utility.Wait(BarrageInterval)
		i += 1
	EndWhile
	Utility.Wait(1.0)
	caster.Disable()
	caster.Delete()
	If aim
		aim.Disable()
		aim.Delete()
	EndIf
	Barraging = False
EndFunction

; ---------------- 10: Kamui: Severance (left eye) ----------------

; The enemy under the crosshair, else the nearest recent attacker in front of you; it must be in sight.
Actor Function SeveranceTarget()
	Actor c = Game.GetCurrentCrosshairRef() as Actor
	If c && !c.IsDead() && c != PlayerRef && PlayerRef.GetDistance(c) <= SeveranceRange && PlayerRef.HasLOS(c)
		Return c
	EndIf
	; the crosshair only sees actors within activation distance: scan everyone loaded around you instead and take
	; the one closest to where you are aiming (within SeveranceAimCone degrees), preferring enemies
	Actor[] around = MiscUtil.ScanCellNPCs(PlayerRef, SeveranceRange, None, True)
	Actor aimed = None
	Float bestScore = 1000.0
	Int k = 0
	While around && k < around.Length
		Actor x = around[k]
		If x && x != PlayerRef && !x.IsPlayerTeammate() && !x.IsDead()
			Float ang = Math.Abs(PlayerRef.GetHeadingAngle(x))
			If ang < SeveranceAimCone && PlayerRef.HasLOS(x)
				Float score = ang
				If !x.IsHostileToActor(PlayerRef)
					score += SeveranceAimCone                 ; enemies first
				EndIf
				If score < bestScore
					aimed = x
					bestScore = score
				EndIf
			EndIf
		EndIf
		k += 1
	EndWhile
	If aimed
		Return aimed
	EndIf
	Actor best = None
	Float bestDist = SeveranceRange
	If RecentAttackers
		Int i = 0
		While i < 8
			Actor a = RecentAttackers[i]
			If a && !a.IsDead() && Math.Abs(PlayerRef.GetHeadingAngle(a)) < 45.0 && PlayerRef.HasLOS(a)
				Float dist = PlayerRef.GetDistance(a)
				If dist < bestDist
					best = a
					bestDist = dist
				EndIf
			EndIf
			i += 1
		EndWhile
	EndIf
	Return best
EndFunction

Function Severance()
	If Severing
		Return
	EndIf
	; a left-eye technique: needs the Mangekyou awakened, not the Sharingan switched on (that is both eyes)
	If !MangekyoAwakened || MangekyoAwakened.GetValue() < 1
		Debug.Notification("Kamui: Severance needs the Mangekyou Sharingan awakened.")
		Return
	EndIf
	FixClocks()
	Float t = Now()
	If LastSeverance > t
		LastSeverance = -100.0
	EndIf
	If t - LastSeverance < SeveranceCooldown * Focus()
		Debug.Notification("Kamui: Severance is not ready (" + ((SeveranceCooldown * Focus() - (t - LastSeverance)) as Int) + "s).")
		Return
	EndIf
	Actor target = SeveranceTarget()
	If !target
		Debug.Notification("Kamui: no target in sight.")
		Return
	EndIf
	If PlayerRef.GetActorValue("Magicka") < SeveranceMagicka * Focus()
		Debug.Notification("Kamui: not enough chakra for Severance.")
		Return
	EndIf
	Severing = True
	LastSeverance = t
	PlayerRef.DamageActorValue("Magicka", SeveranceMagicka * Focus())
	; the left eye warps what it looks at: it needs a solid body, like the barrage
	If ModeOn
		EndMode()
		PlayerRef.DispelSpell(KamuiEthereal)
	ElseIf Phased
		Solid()
	EndIf
	Debug.Trace("CSHC kamui: severance on " + target)
	; the distortion forms on the target: vanilla distortion + a colourless Kamui ripple
	VisualEffect distort = Game.GetFormFromFile(0x0266AB, "UchihaClan.esp") as VisualEffect	; aaaTimeTeleportTargetVFX
	; the Uchiha void effect without its purple layers: only the refraction ripple (canon: Kamui has no colour)
	VisualEffect void = Game.GetFormFromFile(0x842, "Sharingan Copy.esp") as VisualEffect		; CSHC_KamuiDistortVFX
	If distort
		distort.Play(target)
	EndIf
	If void
		void.Play(target)
	EndIf
	If SwirlSound
		SwirlSound.Play(target)
	EndIf
	Utility.Wait(SeveranceFocusSeconds)
	If target.IsDead() || !target.Is3DLoaded() || PlayerRef.GetDistance(target) > SeveranceRange * 1.2
		Debug.Notification("Kamui: the target slipped out of your sight.")
		StopDistortion(target, distort, void)
		Severing = False
		Return
	EndIf
	; it tears: heavy damage that ignores armor + a large stagger
	Float hp = target.GetActorValue("Health")
	Float pct = target.GetActorValuePercentage("Health")
	Float full = hp
	If pct > 0.01
		full = hp / pct
	EndIf
	Float dmg = 20.0 + 2.0 * PlayerRef.GetLevel() + SeveranceHealthShare * full
	SeveranceStrike.Cast(PlayerRef, target)
	If dmg >= hp && !target.IsEssential()
		target.Kill(PlayerRef)
	Else
		target.DamageActorValue("Health", dmg)
	EndIf
	; the weapon arm's weapon (else the shield) is warped into the Kamui chest
	String taken = ""
	Keyword uchihaBoss = Game.GetFormFromFile(0x02E8C9, "UchihaClan.esp") as Keyword
	ObjectReference chest = Game.GetFormFromFile(0x030EE3, "UchihaClan.esp") as ObjectReference
	If chest && !(uchihaBoss && target.HasKeyword(uchihaBoss))
		Weapon w = target.GetEquippedWeapon(False)
		If !w
			w = target.GetEquippedWeapon(True)
		EndIf
		If w
			taken = w.GetName()
			target.RemoveItem(w, 1, True, chest)
		Else
			Armor sh = target.GetEquippedShield()
			If sh
				taken = sh.GetName()
				target.RemoveItem(sh, 1, True, chest)
			EndIf
		EndIf
	EndIf
	Utility.Wait(0.3)
	StopDistortion(target, distort, void)
	Debug.Trace("CSHC kamui: severance " + dmg + " damage on " + target + ", took '" + taken + "'")
	If taken != ""
		Debug.Notification("Kamui: " + taken + " warped into the Kamui dimension.")
	EndIf
	Severing = False
EndFunction

Function StopDistortion(Actor target, VisualEffect distort, VisualEffect void)
	If distort
		distort.Stop(target)
	EndIf
	If void
		void.Stop(target)
	EndIf
EndFunction

; ---------------- Kamui Focus (Tobi war gear, unmasked) ----------------

; Unmasked in the Tobi war outfit, boots and gloves (Obito Tobi Path Additions' "Unmasked" ability, whose marker
; effect is only active then), Kamui techniques cost less and recover faster.
Float Property FocusMultiplier = 0.7 AutoReadOnly
Float Function Focus()
	MagicEffect m = Game.GetFormFromFile(0x823, "Obito Tobi Path Additions.esp") as MagicEffect
	If m && PlayerRef.HasMagicEffect(m)
		Return FocusMultiplier
	EndIf
	Return 1.0
EndFunction

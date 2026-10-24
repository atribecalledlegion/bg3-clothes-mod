Scriptname CTOB_NinjaTravelEffect extends ActiveMagicEffect
{Ninja Travel (on CTOB_NinjaTravelAbility, given on the Tobi path). Always on, out of combat only.
- Chakra Sprint: sprinting builds momentum over RampSeconds; speed rises to TopSpeed% at full momentum. Breaks
  shorter than GraceSeconds (a jump, a turn) keep it. Costs MagickaPerSecond at full momentum (scaled below).
- Chakra Leap: at full momentum jumps are LeapMult x higher, and falls do no damage until LandingSeconds after.
  fJumpHeightMin is a global setting, so NPCs jumping meanwhile get it too; the fall setting is player-only.
- Water Running: at full momentum you run across water. Lose the momentum and you sink.
- Momentum Strike: a swing within StrikeWindow s of a full-speed sprint staggers the enemy in front of you.}

Float Property TickSeconds = 0.25 AutoReadOnly
Float Property RampSeconds = 4.0 AutoReadOnly
Float Property GraceSeconds = 1.5 AutoReadOnly
Float Property TopSpeed = 60.0 AutoReadOnly
Float Property SpeedStep = 10.0 AutoReadOnly          ; speed changes in steps (each change nudges carry weight)
Float Property MagickaPerSecond = 3.0 AutoReadOnly
Float Property MinMagicka = 5.0 AutoReadOnly
Float Property LeapMult = 2.5 AutoReadOnly
Float Property SafeFall = 100000.0 AutoReadOnly
Float Property LandingSeconds = 3.0 AutoReadOnly
Float Property StrikeWindow = 1.0 AutoReadOnly
Float Property StrikeReach = 230.0 AutoReadOnly
Float Property StrikeStagger = 0.75 AutoReadOnly

Actor Me
Float Momentum = 0.0      ; 0..1
Float Grace = 0.0         ; seconds of not sprinting tolerated
Float SpeedApplied = 0.0  ; our SpeedMult mod, kept with the save
Bool WaterOn = False      ; our WaterWalking mod, kept with the save
Float Landing = 0.0       ; seconds of safe falls left
Float StrikeLeft = 0.0    ; seconds left in the Momentum Strike window
Float JumpBase = 0.0
Float JumpSet = -1.0
Float FallBase = 0.0
Float FallSet = -1.0

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	RegisterForActorAction(0)          ; weapon swing
	RegisterForSingleUpdate(TickSeconds)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Momentum = 0.0
	Landing = 0.0
	Apply()
EndEvent

Event OnUpdate()
	If !Me
		Return
	EndIf
	Tick()
	RegisterForSingleUpdate(TickSeconds)
EndEvent

Function Tick()
	Bool canRun = !Me.IsInCombat() && !Me.IsOnMount() && !Me.IsSwimming() && !Me.IsSneaking() && !Me.IsDead()
	Bool full = Momentum >= 1.0
	If canRun && Me.IsSprinting() && Me.GetActorValue("Magicka") >= MinMagicka
		Momentum += TickSeconds / RampSeconds
		If Momentum > 1.0
			Momentum = 1.0
		EndIf
		Grace = GraceSeconds
		Me.DamageActorValue("Magicka", MagickaPerSecond * Momentum * TickSeconds)
	ElseIf !canRun
		Momentum = 0.0
	ElseIf Grace > 0.0
		Grace -= TickSeconds
	Else
		Momentum = 0.0
	EndIf
	If full
		StrikeLeft = StrikeWindow          ; refreshed while at full speed, runs out once you stop
		Landing = LandingSeconds
	Else
		If StrikeLeft > 0.0
			StrikeLeft -= TickSeconds
		EndIf
		If Landing > 0.0
			Landing -= TickSeconds
		EndIf
	EndIf
	If Me.IsDead()
		StrikeLeft = 0.0
	EndIf
	Apply()
EndFunction

; Brings speed, water walking and the jump/fall settings in line with the current momentum.
Function Apply()
	Float want = Math.Floor(TopSpeed * Momentum / SpeedStep) * SpeedStep
	If want != SpeedApplied
		Me.ModActorValue("SpeedMult", want - SpeedApplied)
		SpeedApplied = want
		Me.ModActorValue("CarryWeight", 0.1)            ; a SpeedMult change only applies after a carry weight change
		Me.ModActorValue("CarryWeight", -0.1)
	EndIf
	Bool full = Momentum >= 1.0
	If full != WaterOn
		If full
			Me.ModActorValue("WaterWalking", 1.0)
		Else
			Me.ModActorValue("WaterWalking", -1.0)
		EndIf
		WaterOn = full
	EndIf
	; settings reset on every game load, so the base is re-read whenever the value isn't the one we set
	Float jump = Game.GetGameSettingFloat("fJumpHeightMin")
	If jump != JumpSet
		JumpBase = jump
	EndIf
	If full
		JumpSet = JumpBase * LeapMult
	Else
		JumpSet = JumpBase
	EndIf
	If jump != JumpSet
		Game.SetGameSettingFloat("fJumpHeightMin", JumpSet)
	EndIf
	Float fall = Game.GetGameSettingFloat("fJumpFallHeightMin")
	If fall != FallSet
		FallBase = fall
	EndIf
	If Landing > 0.0
		FallSet = SafeFall
	Else
		FallSet = FallBase
	EndIf
	If fall != FallSet
		Game.SetGameSettingFloat("fJumpFallHeightMin", FallSet)
	EndIf
EndFunction

Event OnActorAction(Int actionType, Actor akActor, Form source, Int slot)
	If akActor != Me || StrikeLeft <= 0.0
		Return
	EndIf
	StrikeLeft = 0.0
	Utility.Wait(0.25)                 ; let the swing land
	Actor t = Me.GetCombatTarget()
	If !t || t.IsDead() || Me.GetDistance(t) > StrikeReach || Math.Abs(Me.GetHeadingAngle(t)) > 60.0
		t = Game.GetCurrentCrosshairRef() as Actor
	EndIf
	If t && !t.IsDead() && Me.GetDistance(t) <= StrikeReach && Math.Abs(Me.GetHeadingAngle(t)) <= 60.0
		t.SetAnimationVariableFloat("staggerMagnitude", StrikeStagger)
		Debug.SendAnimationEvent(t, "staggerStart")
		Debug.Trace("CTOB ninja travel: momentum strike on " + t)
	EndIf
EndEvent

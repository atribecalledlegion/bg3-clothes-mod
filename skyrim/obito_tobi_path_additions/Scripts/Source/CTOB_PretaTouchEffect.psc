Scriptname CTOB_PretaTouchEffect extends ActiveMagicEffect
{"Preta Path: Chakra Grasp" (hold-to-cast, self). Canon: the Preta body drains whoever it lays hands on.
While you keep casting, the enemy within touch range in front of you is being absorbed (absorb shader on them).
Keep the same target in reach for HoldSeconds: they lose up to DrainAmount Magicka, you gain what they lost, and
they are Drained (DrainedSpell: much slower Magicka regen). Keep holding to drain again. Losing the target, or
stopping the cast, resets the timer.}

Spell Property DrainedSpell Auto
EffectShader Property AbsorbShader Auto

Float Property Reach = 160.0 AutoReadOnly
Float Property Facing = 60.0 AutoReadOnly
Float Property HoldSeconds = 2.5 AutoReadOnly
Float Property TickSeconds = 0.25 AutoReadOnly
Float Property DrainAmount = 100.0 AutoReadOnly

Actor Me
Actor Target
Float Held = 0.0
Bool Done = False

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akCaster
	RegisterForSingleUpdate(TickSeconds)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Done = True
	SetTarget(None)
EndEvent

Bool Function InReach(Actor x)
	Return x && x != Me && !x.IsDead() && Me.GetDistance(x) <= Reach && Math.Abs(Me.GetHeadingAngle(x)) < Facing
EndFunction

; Keep the current target while it stays in reach; else the crosshair actor, else the nearest hostile in reach.
Actor Function FindTouch()
	If InReach(Target)
		Return Target
	EndIf
	Actor x = Game.GetCurrentCrosshairRef() as Actor
	If InReach(x)
		Return x
	EndIf
	Cell c = Me.GetParentCell()
	If !c
		Return None
	EndIf
	Actor best = None
	Float bestDist = Reach
	Int n = c.GetNumRefs(62)
	Int i = 0
	While i < n
		x = c.GetNthRef(i, 62) as Actor
		If InReach(x) && x.IsHostileToActor(Me)
			Float d = Me.GetDistance(x)
			If d < bestDist
				best = x
				bestDist = d
			EndIf
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction

Function SetTarget(Actor t)
	If Target && AbsorbShader
		AbsorbShader.Stop(Target)
	EndIf
	Target = t
	Held = 0.0
	If t && AbsorbShader && !Done
		AbsorbShader.Play(t)
	EndIf
EndFunction

Event OnUpdate()
	If Done || !Me
		Return
	EndIf
	Actor t = FindTouch()
	If t != Target
		SetTarget(t)
	ElseIf t
		Held += TickSeconds
		If Held >= HoldSeconds
			Drain(t)
			Held = 0.0
		EndIf
	EndIf
	If !Done
		RegisterForSingleUpdate(TickSeconds)
	EndIf
EndEvent

Function Drain(Actor t)
	Float take = t.GetActorValue("Magicka")
	If take > DrainAmount
		take = DrainAmount
	EndIf
	If take > 0.0
		t.DamageActorValue("Magicka", take)
		Me.RestoreActorValue("Magicka", take)
	EndIf
	DrainedSpell.Cast(Me, t)
	Debug.Trace("CTOB preta grasp: drained " + t + " of " + take)
	If Me == Game.GetPlayer()
		Debug.Notification("Preta Path: absorbed " + (take as Int) + " chakra from " + t.GetDisplayName() + ".")
	EndIf
EndFunction

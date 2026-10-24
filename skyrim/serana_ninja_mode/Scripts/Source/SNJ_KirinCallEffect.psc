Scriptname SNJ_KirinCallEffect extends ActiveMagicEffect
{Kirin. Cast on Serana by her big jutsu (power attack 6, Payload Interpreter) from three tomoe on. Sasuke heats the
sky with fire to build thunderclouds; Serana seeds them with her Hyoton storm instead (or uses a storm already
there: rain or snow). Outdoors and with clouds above, lightning in the shape of a dragon comes down on her target:
the Kirin beam is cast from a marker high above the target. Without clouds (or indoors) she throws Chidori Eiso.}

SNJ_QuestScript Property Master Auto
Spell Property KirinSpell Auto
Spell Property EisoSpell Auto
Static Property XMarker Auto
Float Property Height = 1800.0 AutoReadOnly

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Actor s = akCaster
	If !s
		s = akTarget
	EndIf
	Actor t = s.GetCombatTarget()
	If !t || t.IsDead()
		Return
	EndIf
	Int verdict = Master.TakeKirin(s)
	If verdict == 2
		Return    ; the dragon already came down for this jutsu (the animation calls twice)
	ElseIf verdict == 0
		EisoSpell.Cast(s, t)
		Return
	EndIf
	ObjectReference sky = t.PlaceAtMe(XMarker, 1, False, False)
	sky.MoveTo(t, 0.0, 0.0, Height)
	Utility.Wait(0.1)
	KirinSpell.RemoteCast(sky, s, t)
	Debug.Trace("SNJ: Kirin strikes " + t.GetDisplayName())
	Utility.Wait(3.0)
	sky.Delete()
EndEvent

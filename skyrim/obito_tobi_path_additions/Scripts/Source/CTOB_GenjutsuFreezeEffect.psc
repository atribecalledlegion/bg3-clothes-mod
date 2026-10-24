Scriptname CTOB_GenjutsuFreezeEffect extends ActiveMagicEffect
{UNUSED since 2026-10-14: the freeze is now a Paralysis effect (AI off left the body animating).}

Actor Target

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Target = akTarget
	Target.EnableAI(False)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	If Target
		Target.EnableAI(True)
	EndIf
EndEvent

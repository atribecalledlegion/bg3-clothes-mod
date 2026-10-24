Scriptname CTOB_ReceiverRodEffect extends ActiveMagicEffect
{Outer Path: Chakra Receivers. One black rod has struck the target; CTOB_RinneganQuestScript.RodHit does the rest.}

Quest Property Master Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If akTarget && !akTarget.IsDead()
		(Master as CTOB_RinneganQuestScript).RodHit(akTarget, akCaster)
	EndIf
EndEvent

Scriptname HKO_SealEffect extends ActiveMagicEffect
{The Hiraishin seal a Hokage kunai leaves on an enemy (30 s): tells the quest where he can warp.}

HKO_QuestScript Property Master Auto
Actor Sealed

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If akCaster == Game.GetPlayer()
		Sealed = akTarget
		Master.AddSeal(akTarget)
	EndIf
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	If Sealed
		Master.SealGone(Sealed)
	EndIf
EndEvent

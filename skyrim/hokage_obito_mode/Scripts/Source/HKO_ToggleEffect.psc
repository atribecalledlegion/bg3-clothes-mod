Scriptname HKO_ToggleEffect extends ActiveMagicEffect
{Lesser power "Hokage": hands the work to the quest script.}

HKO_QuestScript Property Master Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Master.Toggle()
EndEvent

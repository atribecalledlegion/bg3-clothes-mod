Scriptname SNJ_ToggleEffect extends ActiveMagicEffect
{Lesser power "Serana: Way of the Shinobi": hands the work to the quest script.}

SNJ_QuestScript Property Master Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Master.Toggle()
EndEvent

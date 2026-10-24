Scriptname ROM_ToggleEffect extends ActiveMagicEffect
{Lesser power "Ronin": hands the work to the quest script.}

ROM_QuestScript Property Master Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Master.Toggle()
EndEvent

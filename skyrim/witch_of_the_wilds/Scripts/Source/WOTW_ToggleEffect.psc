Scriptname WOTW_ToggleEffect extends ActiveMagicEffect
{Lesser power "Serana: Witch of the Wilds": hands the work to the quest script.}

WOTW_QuestScript Property Master Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Master.Toggle()
EndEvent

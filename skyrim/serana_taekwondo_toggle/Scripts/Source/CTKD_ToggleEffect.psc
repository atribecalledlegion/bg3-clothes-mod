Scriptname CTKD_ToggleEffect extends ActiveMagicEffect
{On the toggle power's magic effect. Hands the work to the quest.}

Quest Property Master Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	(Master as CTKD_QuestScript).Toggle()
EndEvent

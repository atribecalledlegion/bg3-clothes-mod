Scriptname CSHC_KamuiSeveranceEffect extends ActiveMagicEffect
{"Kamui: Severance" lesser power: runs the left-eye Kamui (CSHC_KamuiQuestScript.Severance).}

Quest Property Master Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	(Master as CSHC_KamuiQuestScript).Severance()
EndEvent

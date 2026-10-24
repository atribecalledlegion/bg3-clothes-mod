Scriptname CSHC_KamuiBarrageEffect extends ActiveMagicEffect
{"Kamui: Shuriken Barrage" lesser power: runs the barrage (CSHC_KamuiQuestScript.Barrage).}

Quest Property Master Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	(Master as CSHC_KamuiQuestScript).Barrage()
EndEvent

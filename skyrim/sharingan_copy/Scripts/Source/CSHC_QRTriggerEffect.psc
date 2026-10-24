Scriptname CSHC_QRTriggerEffect extends ActiveMagicEffect
{Cast by the Uchiha Clan's Quick Reflexes perk (weapon-swing entry, enemy power attack) in place of its instant
slow-time spell. Hands the swing to the quest, which runs the eased, Read-aware slowdown.}

CSHC_CopyQuestScript Property Master Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Master.PowerSwing(akTarget, akCaster)
EndEvent

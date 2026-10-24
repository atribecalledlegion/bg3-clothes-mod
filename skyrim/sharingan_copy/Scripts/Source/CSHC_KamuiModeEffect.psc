Scriptname CSHC_KamuiModeEffect extends ActiveMagicEffect
{Added to the Uchiha Clan's "Kamui: Ethereal" power. Starts and ends Kamui mode (CSHC_KamuiQuestScript); casting
the power again while it runs solidifies you.}

Quest Property Master Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	(Master as CSHC_KamuiQuestScript).ModeEffectStart()
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	(Master as CSHC_KamuiQuestScript).ModeEffectFinish()
EndEvent

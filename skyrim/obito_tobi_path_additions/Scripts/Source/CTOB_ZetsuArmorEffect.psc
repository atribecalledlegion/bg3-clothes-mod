Scriptname CTOB_ZetsuArmorEffect extends ActiveMagicEffect
{Hidden part of the Hashirama Cell Healing Factor, active at levels 1-15 (the effect's condition).
White Zetsu armor: below 20% health, a 5 second +300% health regen burst, once per in-game day.}

Spell Property BurstSpell Auto
GlobalVariable Property NextAllowedDay Auto
GlobalVariable Property GameDaysPassed Auto
Float Property HealthThreshold = 0.2 Auto
Float Property PollSeconds = 1.0 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnUpdate()
	Actor a = GetTargetActor()
	If !a || a.IsDead()
		Return
	EndIf
	If a.GetActorValuePercentage("Health") < HealthThreshold && GameDaysPassed.GetValue() >= NextAllowedDay.GetValue()
		BurstSpell.Cast(a, a)
		NextAllowedDay.SetValue(GameDaysPassed.GetValue() + 1.0)
		If a == Game.GetPlayer()
			Debug.Notification("The White Zetsu armor knits your wounds closed.")
		EndIf
	EndIf
	RegisterForSingleUpdate(PollSeconds)
EndEvent

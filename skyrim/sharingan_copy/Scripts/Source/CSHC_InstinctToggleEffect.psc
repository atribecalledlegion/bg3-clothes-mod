Scriptname CSHC_InstinctToggleEffect extends ActiveMagicEffect
{"Kamui: Instinct" lesser power: switches Kamui Instinct on or off.}

GlobalVariable Property InstinctOn Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If InstinctOn.GetValue() >= 1
		InstinctOn.SetValue(0)
		Debug.Notification("Kamui: Instinct off.")
	Else
		InstinctOn.SetValue(1)
		Debug.Notification("Kamui: Instinct on.")
	EndIf
EndEvent

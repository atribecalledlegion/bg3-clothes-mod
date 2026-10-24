Scriptname CSHC_CopyToggleEffect extends ActiveMagicEffect
{On the "Sharingan: Copy" lesser power. Switches copying on and off (the watching cloak's condition reads CopyOn).}

GlobalVariable Property CopyOn Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If CopyOn.GetValue() == 0
		CopyOn.SetValue(1)
		Debug.Notification("Sharingan Copy: on. Watching every jutsu around you.")
	Else
		CopyOn.SetValue(0)
		Debug.Notification("Sharingan Copy: off.")
	EndIf
EndEvent

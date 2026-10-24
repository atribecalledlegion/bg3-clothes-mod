Scriptname CTOB_ChakraSurgeEffect extends ActiveMagicEffect
{Unmasked: Will of the Uchiha (Tobi war outfit + boots + gloves, no mask). Only active under those conditions.
Chakra Surge: in combat, when chakra (Magicka) falls below SurgeBelow, half of it comes rushing back, twice per
fight; the charges return when combat ends. Its presence also tells Sharingan Copy's Kamui to use Kamui Focus.}

Float Property SurgeBelow = 0.15 AutoReadOnly
Float Property SurgeRestore = 0.5 AutoReadOnly
Int Property SurgesPerFight = 2 AutoReadOnly
Float Property TickSeconds = 0.5 AutoReadOnly

Actor Me
Int Used = 0

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	RegisterForSingleUpdate(TickSeconds)
EndEvent

Event OnUpdate()
	If !Me
		Return
	EndIf
	If !Me.IsInCombat()
		Used = 0
	ElseIf Used < SurgesPerFight
		Float pct = Me.GetActorValuePercentage("Magicka")
		If pct < SurgeBelow
			Float full = Me.GetBaseActorValue("Magicka")
			If pct > 0.01
				full = Me.GetActorValue("Magicka") / pct
			EndIf
			Me.RestoreActorValue("Magicka", full * SurgeRestore)
			Used += 1
			Debug.Trace("CTOB unmasked: chakra surge " + Used + "/" + SurgesPerFight)
			Debug.Notification("Chakra Surge (" + (SurgesPerFight - Used) + " left this fight).")
		EndIf
	EndIf
	RegisterForSingleUpdate(TickSeconds)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	UnregisterForUpdate()
EndEvent

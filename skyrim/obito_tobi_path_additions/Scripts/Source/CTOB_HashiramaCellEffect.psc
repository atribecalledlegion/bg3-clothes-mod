Scriptname CTOB_HashiramaCellEffect extends ActiveMagicEffect
{On the Hashirama Cell item's effect. Grants the permanent Hashirama Cell Healing Factor ability.}

Spell Property HealingFactor Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If akTarget.HasSpell(HealingFactor)
		If akTarget == Game.GetPlayer()
			Debug.Notification("Hashirama's cells are already part of you.")
		EndIf
		Return
	EndIf
	akTarget.AddSpell(HealingFactor, False)
	If akTarget == Game.GetPlayer()
		Debug.Notification("Hashirama Cell Healing Factor: Hashirama's cells take hold.")
	EndIf
EndEvent

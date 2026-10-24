Scriptname CSHC_ObserveEffect extends ActiveMagicEffect
{Put on NPCs near the player by the Sharingan's watching cloak (only while the Sharingan is open).
Reports every spell the NPC casts to the copy quest.}

Quest Property Master Auto

Event OnSpellCast(Form akSpell)
	Spell s = akSpell as Spell
	If s
		(Master as CSHC_CopyQuestScript).Observe(s, GetTargetActor())
	EndIf
EndEvent

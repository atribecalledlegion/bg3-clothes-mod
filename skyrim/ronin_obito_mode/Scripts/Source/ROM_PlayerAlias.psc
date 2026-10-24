Scriptname ROM_PlayerAlias extends ReferenceAlias
{Ronin Obito Mode (2026-10-19): the player alias. Hears the Vergil moveset's vanish spell land on him (its $Shinobi4
payload: Trick, Ultimate Slay Tempest, the Beowulf teleport combo and the step dodges) and tells the quest, which
turns the teleport into a Kamui one. PIE's $Shinobi4 is defined twice: InvisibleEffect.esp "Dodge1" (the Yamato's)
and ShinobiEffects.esp "Shinobi4" (Mist Form); both are caught.}

MagicEffect VanishA
MagicEffect VanishB
MagicEffect VanishC
Bool Cached

Event OnMagicEffectApply(ObjectReference akCaster, MagicEffect akEffect)
	If !Cached
		Cached = True
		VanishA = Game.GetFormFromFile(0x00000808, "InvisibleEffect.esp") as MagicEffect    ; SDT Dodge1
		VanishB = Game.GetFormFromFile(0x0000AA21, "InvisibleEffect.esp") as MagicEffect    ; Dodge1
		VanishC = Game.GetFormFromFile(0x00000808, "ShinobiEffects.esp") as MagicEffect     ; MistForm4
	EndIf
	If akEffect && (akEffect == VanishA || akEffect == VanishB || akEffect == VanishC)
		(GetOwningQuest() as ROM_QuestScript).Vanished()
	EndIf
EndEvent

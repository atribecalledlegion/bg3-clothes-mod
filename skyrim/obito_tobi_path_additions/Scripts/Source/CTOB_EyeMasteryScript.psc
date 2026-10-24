Scriptname CTOB_EyeMasteryScript extends Quest
{Eye Adaptation (fourth script on CTOB_Quest). Uchiha who live with the Sharingan stop feeling it: Obito kept his open
even close to death. The Uchiha Clan's upkeep (aaaSlowTimeUpkeepspell: max Magicka -25 and 1 Magicka/s, the Detect
Chakra version 2/s; at 0 Magicka it eats Health) shrinks as the eye adapts, by setting those spells' magnitudes at
runtime (no Uchiha Clan file changes; runtime values are not saved, so every poll sets them again):
 - Hashirama cells (CTOB_HashiramaAbility): half the upkeep gone at once.
 - Eye Mastery rank 0-100 (GLOB CTOB_EyeMastery): grows while the eye is open in combat (about 3 hours to 100), a
   little more for every swing and cast. It removes the rest; at 100 the eye costs nothing and gives +10% Magicka
   regeneration while open (CTOB_EyeAdaptAbility, conditioned in the plugin).
Console: "set CTOB_SetEyeMastery to N" sets the rank (applied at the next poll, within 3 s).}

Float Property SecondsPerRank = 108.0 AutoReadOnly
{Seconds of combat with the eye open per rank: 108 = about 3 hours to rank 100.}
Float Property ActionBonus = 0.01 AutoReadOnly
{Rank per weapon swing or spell cast in combat with the eye open.}
Float Property CellsShare = 0.5 AutoReadOnly
Float Property BaseMaxMagicka = 25.0 AutoReadOnly
Float Property BaseDrain = 1.0 AutoReadOnly
Float Property DetectDrain = 2.0 AutoReadOnly

Float LastTick = -1.0
Bool Attuned = False

Form Function Own(Int id)
	Return Game.GetFormFromFile(id, "Obito Tobi Path Additions.esp")
EndFunction

Bool Function SharinganOpen()
	Return (Game.GetFormFromFile(0x0EFC75, "Skyrim.esm") as GlobalVariable).GetValue() == 2
EndFunction

Float Function Clamp(Float v)
	If v < 0.0
		Return 0.0
	ElseIf v > 100.0
		Return 100.0
	EndIf
	Return v
EndFunction

; Called by CTOB_TobiPathQuestScript's poll while on the Tobi path.
Function Tick(Actor p)
	RegisterForActorAction(0)                                ; weapon swing
	RegisterForActorAction(2)                                ; spell fire
	Spell ability = Own(0x832) as Spell
	If ability && !p.HasSpell(ability)
		p.AddSpell(ability, False)
	EndIf
	GlobalVariable rankG = Own(0x830) as GlobalVariable
	GlobalVariable setG = Own(0x831) as GlobalVariable
	If !rankG
		Return
	EndIf
	Float rank = rankG.GetValue()
	If setG && setG.GetValue() >= 0.0
		rank = Clamp(setG.GetValue())
		setG.SetValue(-1.0)
		Attuned = rank >= 100.0
		Debug.Notification("Eye Adaptation set to rank " + (rank as Int) + ".")
	EndIf
	; real time restarts every launch: skip a tick after a load or a long pause
	Float t = Utility.GetCurrentRealTime()
	Float dt = t - LastTick
	If LastTick < 0.0 || dt < 0.0 || dt > 10.0
		dt = 0.0
	EndIf
	LastTick = t
	If dt > 0.0 && SharinganOpen() && p.IsInCombat()
		rank += dt / SecondsPerRank
	EndIf
	rank = Clamp(rank)
	rankG.SetValue(rank)
	Apply(p, rank)
	If rank >= 100.0 && !Attuned
		Attuned = True
		Debug.Notification("The Sharingan no longer strains you.")
	EndIf
EndFunction

Function Apply(Actor p, Float rank)
	Float share = rank / 100.0
	Spell cells = Own(0x808) as Spell                         ; Hashirama Cell Healing Factor
	If cells && p.HasSpell(cells)
		share = CellsShare + (1.0 - CellsShare) * share
	EndIf
	If share > 1.0
		share = 1.0
	EndIf
	Float left = 1.0 - share
	Spell upkeep = Game.GetFormFromFile(0x01FA2E, "UchihaClan.esp") as Spell        ; aaaSlowTimeUpkeepspell
	Spell detect = Game.GetFormFromFile(0x033A41, "UchihaClan.esp") as Spell        ; aaaDetectChakraUpkeepspell
	If upkeep && Math.Abs(upkeep.GetNthEffectMagnitude(0) - BaseMaxMagicka * left) > 0.01
		upkeep.SetNthEffectMagnitude(0, BaseMaxMagicka * left)
		upkeep.SetNthEffectMagnitude(1, BaseDrain * left)
		If detect
			detect.SetNthEffectMagnitude(0, BaseMaxMagicka * left)
			detect.SetNthEffectMagnitude(1, DetectDrain * left)
		EndIf
		Debug.Trace("CTOB eye: rank " + rank + ", upkeep left " + left)
	EndIf
	MagicEffect shown = Own(0x82F) as MagicEffect
	String title = "Eye Adaptation (rank " + (rank as Int) + ")"
	If shown && shown.GetName() != title
		shown.SetName(title)
	EndIf
EndFunction

Event OnActorAction(Int actionType, Actor akActor, Form source, Int slot)
	If akActor != Game.GetPlayer() || !SharinganOpen() || !akActor.IsInCombat()
		Return
	EndIf
	GlobalVariable rankG = Own(0x830) as GlobalVariable
	If rankG && rankG.GetValue() < 100.0
		rankG.SetValue(Clamp(rankG.GetValue() + ActionBonus))
	EndIf
EndEvent

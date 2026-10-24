Scriptname CTOB_TobiPathQuestScript extends Quest
{Obito Tobi Path Additions. Gives the Uchiha Clan "Tobi path" the canon abilities that path is missing:
Wood Style (Hashirama's cells) plus Mokuton: Sashiki no Jutsu and Katon: Bakufu Ranbu from the start,
Izanagi once Kamui (the Tobi Mangekyou) is unlocked, and Rinne Rebirth while the Rinnegan is active.
Polls every few seconds; the update registration is saved with the game.}

Perk Property aaaPathTobi Auto
Spell[] Property PathSpells Auto
{Granted as soon as the player is on the Tobi path: the seven Mokuton spells, Sashiki and Bakufu Ranbu.}
Spell Property KamuiEthereal Auto
{Unlocked by the Tobi path's Mangekyou. Used to tell that the Mangekyou is awakened.}
Spell Property IzanagiSpell Auto
Perk Property IzanagiPower Auto
Spell Property RinneganAbility Auto
Spell Property RinneRebirthSpell Auto
Float Property PollSeconds = 3.0 Auto
Potion Property HashiramaCell Auto
{The Hashirama Cell test item. No longer handed out; the cells come from the Kannabi event.}
Spell Property HealingFactor Auto
Spell Property KannabiWatch Auto
{Hidden watcher ability: on while on the Tobi path without the cells.}
GlobalVariable Property KannabiDone Auto

Bool PathGranted = False
Bool CellGiven = False
Bool IzanagiGranted = False
Bool RebirthAdded = False

Event OnInit()
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnUpdate()
	Actor p = Game.GetPlayer()
	Bool wantWatch = p.HasPerk(aaaPathTobi) && !p.HasSpell(HealingFactor) && KannabiDone.GetValue() == 0
	If wantWatch && !p.HasSpell(KannabiWatch)
		p.AddSpell(KannabiWatch, False)
	ElseIf !wantWatch && p.HasSpell(KannabiWatch)
		p.RemoveSpell(KannabiWatch)
	EndIf
	GrantCellCombat(p)
	If p.HasPerk(aaaPathTobi)
		If !PathGranted
			Int i = 0
			While i < PathSpells.Length
				p.AddSpell(PathSpells[i], False)
				i += 1
			EndWhile
			PathGranted = True
			Debug.Notification("Hashirama's cells: Wood Style, Sashiki and Bakufu Ranbu unlocked.")
		EndIf
		GrantGenjutsu(p)
		GrantUnmasked(p)
		CTOB_RinneganQuestScript r = (Self as Quest) as CTOB_RinneganQuestScript
		If r
			r.Tick(p)
		EndIf
		CTOB_EyeMasteryScript e = (Self as Quest) as CTOB_EyeMasteryScript
		If e
			e.Tick(p)
		EndIf
		If !IzanagiGranted && p.HasSpell(KamuiEthereal)
			p.AddPerk(IzanagiPower)
			p.AddSpell(IzanagiSpell, False)
			IzanagiGranted = True
			Debug.Notification("Izanagi unlocked.")
		EndIf
		If p.HasSpell(RinneganAbility)
			If !p.HasSpell(RinneRebirthSpell)
				p.AddSpell(RinneRebirthSpell, False)
				RebirthAdded = True
			EndIf
		ElseIf RebirthAdded
			p.RemoveSpell(RinneRebirthSpell)
			RebirthAdded = False
		EndIf
		; Preta Path powers follow the Rinnegan like Rinne Rebirth
		Spell seal = Game.GetFormFromFile(0x81F, "Obito Tobi Path Additions.esp") as Spell
		Spell drain = Game.GetFormFromFile(0x821, "Obito Tobi Path Additions.esp") as Spell
		If seal
			If p.HasSpell(RinneganAbility)
				If !p.HasSpell(seal)
					p.AddSpell(seal, False)
					p.AddSpell(drain, False)
					Debug.Notification("Rinnegan: Preta Path unlocked (Powers).")
				EndIf
			ElseIf p.HasSpell(seal)
				p.RemoveSpell(seal)
				p.RemoveSpell(drain)
			EndIf
		EndIf
		Spell grasp = Game.GetFormFromFile(0x83A, "Obito Tobi Path Additions.esp") as Spell
		If grasp
			If p.HasSpell(RinneganAbility)
				If !p.HasSpell(grasp)
					p.AddSpell(grasp, False)
					Debug.Notification("Rinnegan: Preta Path: Chakra Grasp unlocked (Spell).")
				EndIf
			ElseIf p.HasSpell(grasp)
				p.RemoveSpell(grasp)
			EndIf
		EndIf
	EndIf
	RegisterForSingleUpdate(PollSeconds)
EndEvent

; Obito's Sharingan genjutsu powers (CTOB_GenjutsuQuestScript): given to the Tobi path, also on existing saves.
Function GrantGenjutsu(Actor p)
	Spell gaze = Game.GetFormFromFile(0x816, "Obito Tobi Path Additions.esp") as Spell
	Spell puppet = Game.GetFormFromFile(0x818, "Obito Tobi Path Additions.esp") as Spell
	If gaze && !p.HasSpell(gaze)
		p.AddSpell(gaze, False)
		p.AddSpell(puppet, False)
		Debug.Notification("Sharingan genjutsu unlocked: Genjutsu: Sharingan and Sharingan Puppet (Powers).")
	EndIf
EndFunction

; Unmasked: Will of the Uchiha. Always held on the Tobi path; its own conditions switch it on only in the war outfit,
; boots and gloves without the war mask.
Function GrantUnmasked(Actor p)
	Spell ab = Game.GetFormFromFile(0x822, "Obito Tobi Path Additions.esp") as Spell
	If ab && !p.HasSpell(ab)
		p.AddSpell(ab, False)
	EndIf
EndFunction

; Hashirama Cells: Combat Regeneration (CTOB_CellCombatEffect): follows the Hashirama Cell Healing Factor,
; also on existing saves.
Function GrantCellCombat(Actor p)
	Spell ab = Game.GetFormFromFile(0x836, "Obito Tobi Path Additions.esp") as Spell
	If ab && p.HasSpell(HealingFactor) && !p.HasSpell(ab)
		p.AddSpell(ab, False)
		Debug.Notification("Hashirama's cells now heal you in battle.")
	EndIf
EndFunction

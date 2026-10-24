Scriptname SNE_LeafNinja extends ActiveMagicEffect
{Shinobi Enemies, Leaf ninja of the Imperial Legion (2026-10-16). SNE_LegionBrain picks some Legion soldiers (once,
from the form ID: about 8% Leaf Jonin, 5% Leaf Medical Ninja, rare female level 20+ Leaf Medical Captains) and gives
them this ability (men are mostly jonin, women mostly medics - see LeafRank). They are the Legion's elite and its "rogue class": light armour, so they live by being quick.
- Everyone: Leaf headband (Naruto Overhaul) and an outfit (male Jonin: Naruto Wardrobe's Leaf shinobi outfit, Anbu
  shoes and Konoha headband; female Jonin: Penitus Oculatus armour; medics: women
  AE Essential Nurse in one of three colours with its cap, men the white Sasuke clothes from Naruto Wardrobe, grey robes
  if neither is installed; captains: the Sakura outfit). +20% speed. DMCO DODGE with a short cooldown (jonin 3 s, medics 2.5 s and
  more likely): when an enemy is on top of them, and after a hit. Between dodges they are fragile.
- Jonin (canon basics, the clan specialists come later): an upgraded kunai (Naruto Overhaul's Iron Kunai, daggers x2
  via SNE_LegionPerk) in the Tobirama MCO moveset (DAR folder keyed to SNE_JoninMark); off hand free. At 450-1800
  they use jutsu every 3.5 s, one nature each: lightning (Chain Lightning at 30+), water (ice spike) or wind (force
  blast + cut); up close they fight - not afraid of a straight fight, speed and dodges against tankier enemies.
  SUBSTITUTION JUTSU: a heavy hit (power attack or 20%+ of its health) is replaced by a log - the damage is undone
  and it reappears behind the attacker (12 s cooldown). FOUR-MAN CELL: the highest-level jonin near is the captain;
  the others take its target. SENSOR: a hostile player sneaking within 1200 is sensed and the area alerted.
  EXPLOSIVE TAGS: the first time it is badly hurt it falls back and leaves a tag that blows up on whoever follows.
  Level 35+: RASENGAN (dash in, knockback blast) or CHIDORI (dash in, shock strike), 20 s cooldown.
- Medical ninja (Tsunade's rules: never die first, stay out of melee): MYSTIC PALM - runs to a hurt ally and
  channels a big heal (15% a second for 3 s; a hit stops it), answers line-rotation calls first; CHAKRA SCALPEL when
  cornered (stamina drain and severed muscles: slower, weaker swings for 8 s).
- Medical Captain (Sakura/Tsunade tier, rare): Mystic Palm 25% a second, MASS HEALING (every ally near: 30% health,
  half stamina, Ironflesh), STRENGTH OF A HUNDRED SEAL once below 35% (full heal, +100 armour, faster for 20 s),
  CHERRY BLOSSOM IMPACT when cornered (heavy hit, everything near is thrown back).
Off: console "set SNE_LegionTactics to 0".}

GlobalVariable Property TacticsOn Auto
Actor Property PlayerRef Auto
Faction Property LegionFaction Auto
Faction Property OculatusFaction Auto
Outfit Property JoninOutfit Auto
Outfit Property MedicOutfit Auto
Outfit Property EmptyOutfit Auto
CombatStyle Property StyleJonin Auto
CombatStyle Property StyleMedic Auto
Spell Property SpellIronflesh Auto
Spell Property Exhaustion Auto        ; reused as the Chakra Scalpel's severed muscles
Spell Property StrengthOfHundred Auto
EffectShader Property HealFX Auto
EffectShader Property ShockFX Auto
EffectShader Property ChakraFX Auto
Explosion Property TagBlast Auto
MiscObject Property LogItem Auto
Static Property XMarkerBase Auto
Spell Property JoninMark Auto          ; Tobirama moveset (DAR) + kunai damage x2 (SNE_LegionPerk)
Spell Property SpellLightning Auto
Spell Property SpellChainLightning Auto
Spell Property SpellIceSpike Auto
Spell Property SpellFus Auto

Int Property RANK_JONIN = 1 AutoReadOnly
Int Property RANK_MEDIC = 2 AutoReadOnly
Int Property RANK_CAPTAIN = 3 AutoReadOnly

Actor Me
Int Rank
Bool Done
Bool Busy
Bool Dressed
Bool Agile
Bool BusyHit
Float NextDodge
Float NextSub
Float NextBig
Float NextPalm
Float NextScalpel
Float NextMass
Float NextSense
Float NextJutsu
Bool TagUsed
Bool HundredUsed
ObjectReference Tag
Float TagUntil
Float LastHp

; the same pick SNE_LegionBrain makes (0 none, 1 jonin, 2 medic, 3 captain). Most jonin are men and most
; medics are women (user, 2026-10-16): men 8% jonin / 2% medics; women 3% jonin / 8% medics / 2% captains (level 20+)
Int Function LeafRank(Actor a) global
	Int id = a.GetFormID()
	If id < 0
		id = -(id + 1)
	EndIf
	Int r = ((id % 9973) * 37 + 11) % 100
	If a.GetLeveledActorBase().GetSex() == 1
		If r < 3
			Return 1
		ElseIf r < 11
			Return 2
		ElseIf r < 13 && a.GetLevel() >= 20
			Return 3
		EndIf
		Return 0
	EndIf
	If r < 8
		Return 1
	ElseIf r < 10
		Return 2
	EndIf
	Return 0
EndFunction

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	Rank = LeafRank(Me)
	If Rank == 0
		Rank = RANK_JONIN
	EndIf
	Prepare()
	Debug.Trace("SNE leaf: start " + Me + " " + Me.GetDisplayName() + " rank " + RankName() + " (level " + Me.GetLevel() + ")")
	If Me.IsInCombat()
		RegisterForSingleUpdate(0.5)
	EndIf
EndEvent

String Function RankName()
	If Rank == RANK_MEDIC
		Return "Leaf Medical Ninja"
	ElseIf Rank == RANK_CAPTAIN
		Return "Leaf Medical Captain"
	EndIf
	Return "Leaf Jonin"
EndFunction

Function Prepare()
	Me.SetDisplayName(RankName(), True)
	If !Agile
		Agile = True
		Me.ModActorValue("SpeedMult", 20.0)
		Me.ModActorValue("CarryWeight", 0.1)
		Me.ModActorValue("CarryWeight", -0.1)
	EndIf
	Dress()
	If Rank == RANK_JONIN
		Arm()
	EndIf
	ApplyStyle()
EndFunction

; jonin fight with an upgraded kunai (Naruto Overhaul's Iron Kunai; jonin daggers hit x2) in the Tobirama moveset,
; and keep the off hand free for jutsu
Function Arm()
	If !Me.HasSpell(JoninMark)
		Me.AddSpell(JoninMark, False)
	EndIf
	Weapon kunai = Game.GetFormFromFile(0x02BB3D, "naruto overhaul.esp") as Weapon
	If !kunai
		Return
	EndIf
	If Me.GetItemCount(kunai) == 0
		Me.AddItem(kunai, 1, True)
	EndIf
	Armor shield = Me.GetEquippedShield()
	If shield
		Me.UnequipItem(shield, False, True)
	EndIf
	Me.EquipItemEx(kunai, 1, True, False)
EndFunction

Function Dress()
	Bool wardrobeBand = False
	If Rank == RANK_JONIN
		; men: Naruto Wardrobe's standard Leaf shinobi outfit (flak vest; male mesh only) + Anbu shoes + its Konoha
		; headband. Women, or no Naruto Wardrobe: the Penitus Oculatus placeholder.
		Armor vest = Game.GetFormFromFile(0x004E18, "NarutoWardrobe.esp") as Armor
		If vest && Me.GetLeveledActorBase().GetSex() == 0
			Me.SetOutfit(EmptyOutfit)
			EquipPiece(vest)
			Armor feet = Game.GetFormFromFile(0x003881, "NarutoWardrobe.esp") as Armor
			If feet
				EquipPiece(feet)
			EndIf
			Armor konoha = Game.GetFormFromFile(0x004349, "NarutoWardrobe.esp") as Armor
			If konoha
				EquipPiece(konoha)
				wardrobeBand = True
			EndIf
		Else
			Me.SetOutfit(JoninOutfit)
		EndIf
	ElseIf Rank == RANK_MEDIC && Me.GetLeveledActorBase().GetSex() == 1 && NurseOutfit()
		wardrobeBand = True    ; the nurse cap instead of a headband
	ElseIf Rank == RANK_MEDIC
		; men: Naruto Wardrobe's white Sasuke clothes and shoes
		Armor top = Game.GetFormFromFile(0x0012C7, "NarutoWardrobe.esp") as Armor
		Armor shoes = Game.GetFormFromFile(0x003DE5, "NarutoWardrobe.esp") as Armor
		If top
			Me.SetOutfit(EmptyOutfit)
			EquipPiece(top)
			If shoes
				EquipPiece(shoes)
			EndIf
		Else
			Me.SetOutfit(MedicOutfit)
		EndIf
	Else
		Me.SetOutfit(EmptyOutfit)
		Int[] ids = new Int[7]
		ids[0] = 0x000D69    ; [Odd] Sakura: dress, shoes, gloves, sleeves, headband, leg pouch, shorts
		ids[1] = 0x000D6A
		ids[2] = 0x000D6B
		ids[3] = 0x000D6C
		ids[4] = 0x000D6F
		ids[5] = 0x000D70
		ids[6] = 0x000D72
		Int i = 0
		Bool any = False
		While i < ids.Length
			Armor piece = Game.GetFormFromFile(ids[i], "[Odd] Sakura.esp") as Armor
			If piece
				any = True
				If Me.GetItemCount(piece) == 0
					Me.AddItem(piece, 1, True)
				EndIf
				Me.EquipItem(piece, True, True)
			EndIf
			i += 1
		EndWhile
		If !any
			Me.SetOutfit(MedicOutfit)    ; Sakura outfit not installed
		EndIf
	EndIf
	If Rank != RANK_CAPTAIN && !wardrobeBand
		Armor band = Game.GetFormFromFile(0x0E41D3, "naruto overhaul.esp") as Armor    ; Hidden Leaf Village's Headband
		If band
			If Me.GetItemCount(band) == 0
				Me.AddItem(band, 1, True)
			EndIf
			Me.EquipItem(band, True, True)
		EndIf
	EndIf
	Dressed = True
EndFunction

; women medics: AE Essential Nurse (3BA, BodySlide-built) in one of its three colours, picked from the form ID
Bool Function NurseOutfit()
	Int id = Me.GetFormID()
	If id < 0
		id = -(id + 1)
	EndIf
	Int c = (id / 7) % 3
	Int[] ids = new Int[5]
	If c == 0
		ids[0] = 0x000D67    ; colour A: top, feet, gloves, cap, stockings
		ids[1] = 0x000D66
		ids[2] = 0x000D68
		ids[3] = 0x000D69
		ids[4] = 0x000002
	ElseIf c == 1
		ids[0] = 0x00000C    ; colour B
		ids[1] = 0x000008
		ids[2] = 0x000009
		ids[3] = 0x00000A
		ids[4] = 0x00000B
	Else
		ids[0] = 0x000016    ; colour C
		ids[1] = 0x000012
		ids[2] = 0x000013
		ids[3] = 0x000014
		ids[4] = 0x000015
	EndIf
	Armor top = Game.GetFormFromFile(ids[0], "AE_Essential_Nurse.esp") as Armor
	If !top
		Return False
	EndIf
	Me.SetOutfit(EmptyOutfit)
	Int i = 0
	While i < 5
		Armor piece = Game.GetFormFromFile(ids[i], "AE_Essential_Nurse.esp") as Armor
		If piece
			EquipPiece(piece)
		EndIf
		i += 1
	EndWhile
	Return True
EndFunction

Function EquipPiece(Armor piece)
	If Me.GetItemCount(piece) == 0
		Me.AddItem(piece, 1, True)
	EndIf
	Me.EquipItem(piece, True, True)
EndFunction

Bool Function Active()
	Return TacticsOn.GetValue() >= 0.5 && !Me.IsPlayerTeammate()
EndFunction

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Done = True
EndEvent

Event OnDying(Actor akKiller)
	Done = True
	If Tag
		Tag.Delete()
	EndIf
EndEvent

Event OnLoad()
	If !Done
		Prepare()
	EndIf
EndEvent

Event OnCombatStateChanged(Actor akTarget, Int aeCombatState)
	If Done
		Return
	EndIf
	If !Me
		Me = GetTargetActor()
	EndIf
	If aeCombatState == 1
		RegisterForModEvent("SNE_LegionHealMe", "OnHealMe")
		LastHp = Me.GetActorValuePercentage("Health")
		ApplyStyle()
		PushCPR()
		RegisterForSingleUpdate(0.5)
	ElseIf aeCombatState == 0
		RegisterForSingleUpdate(2.0)    ; keep sensing
	EndIf
EndEvent

Event OnUpdate()
	If Done || !Me || Me.IsDead()
		Return
	EndIf
	Float t = Now()
	If !Me.IsInCombat()
		Sense(t)
		RegisterForSingleUpdate(2.0)
		Return
	EndIf
	Actor foe = Me.GetCombatTarget()
	If Active() && !Busy && foe && !foe.IsDead()
		Float d = Me.GetDistance(foe)
		; dodge when it is on top of us
		If d < 220.0 && Utility.RandomFloat() < DodgeChance()
			TryDodge("too close")
		EndIf
		TagTick()
		If Rank == RANK_JONIN
			JoninTick(t, foe, d)
		Else
			MedicTick(t, foe, d)
		EndIf
	EndIf
	LastHp = Me.GetActorValuePercentage("Health")
	ApplyStyle()
	PushCPR()
	If !Done && !Me.IsDead()
		RegisterForSingleUpdate(0.5)
	EndIf
EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If Busy
		BusyHit = True
	EndIf
	If Done || !Me || Me.IsDead() || !Active()
		Return
	EndIf
	Actor att = akAggressor as Actor
	If !att || att.IsInFaction(LegionFaction)
		Return
	EndIf
	Float hp = Me.GetActorValuePercentage("Health")
	Float lost = LastHp - hp
	If Rank == RANK_JONIN && (abPowerAttack || lost >= 0.2) && Now() >= NextSub && !Busy
		Substitution(att, lost)
		Return
	EndIf
	LastHp = hp
	If Utility.RandomFloat() < DodgeChance() + 0.2
		TryDodge("after a hit")
	EndIf
	If Rank == RANK_CAPTAIN && !HundredUsed && hp < 0.35 && hp > 0.0
		StrengthOfAHundred()
	EndIf
EndEvent

; ---------- dodging ----------
Float Function DodgeChance()
	If Rank == RANK_JONIN
		Return 0.45
	EndIf
	Return 0.6    ; medics are meant to be hard to hit
EndFunction

Function TryDodge(String why)
	Float t = Now()
	If NextDodge > t + 30.0
		NextDodge = 0.0
	EndIf
	If t < NextDodge || Busy
		Return
	EndIf
	If Rank == RANK_JONIN
		NextDodge = t + 3.0
	Else
		NextDodge = t + 2.5
	EndIf
	Float angle = 180.0
	Float r = Utility.RandomFloat()
	If r < 0.35
		angle = 90.0
	ElseIf r < 0.7
		angle = 270.0
	EndIf
	Me.SetAnimationVariableFloat("Dodge_Angle", angle)
	Debug.SendAnimationEvent(Me, "Dodge")
	Debug.Trace("SNE leaf: " + RankName() + " " + Me + " DODGES (" + why + ")")
EndFunction

; ---------- jonin ----------
Function JoninTick(Float t, Actor foe, Float d)
	; four-man cell: follow the captain's target
	Actor cap = CellCaptain()
	If cap && cap != Me
		Actor ct = cap.GetCombatTarget()
		If ct && ct != foe && !ct.IsDead() && Me.GetDistance(ct) < 1500.0 && Utility.RandomFloat() < 0.3
			Me.StartCombat(ct)
		EndIf
	EndIf
	; explosive tag on the first bad wound
	If !TagUsed && Me.GetActorValuePercentage("Health") < 0.4
		TagUsed = True
		Tag = Me.PlaceAtMe(XMarkerBase)
		TagUntil = t + 20.0
		Debug.Trace("SNE leaf: Leaf Jonin " + Me + " leaves an EXPLOSIVE TAG and falls back")
		ObjectReference away = Me.PlaceAtMe(XMarkerBase)
		Float dx = Me.GetPositionX() - foe.GetPositionX()
		Float dy = Me.GetPositionY() - foe.GetPositionY()
		Float len = Math.sqrt(dx * dx + dy * dy)
		If len > 1.0
			away.SetPosition(Me.GetPositionX() + dx / len * 500.0, Me.GetPositionY() + dy / len * 500.0, Me.GetPositionZ())
			Busy = True
			Me.StopCombat()
			Me.PathToReference(away, 1.0)
			Busy = False
			If !Me.IsDead() && !foe.IsDead()
				Me.StartCombat(foe)
			EndIf
		EndIf
		away.Delete()
		Return
	EndIf
	; medium to long range: jutsu; up close they fight (the kunai, the dodges)
	If NextJutsu > t + 30.0
		NextJutsu = 0.0
	EndIf
	If d >= 450.0 && d <= 1800.0 && t >= NextJutsu && Me.HasLOS(foe)
		NextJutsu = t + 3.5
		RangedJutsu(foe)
		Return
	EndIf
	; Rasengan / Chidori
	If NextBig > t + 40.0
		NextBig = 0.0
	EndIf
	If Me.GetLevel() >= 35 && t >= NextBig && d > 250.0 && d < 900.0 && Me.HasLOS(foe)
		NextBig = t + 20.0
		BigJutsu(foe)
	EndIf
EndFunction

; each jonin has one nature (from the form ID): lightning, water or wind - no fire (Uchiha)
Function RangedJutsu(Actor foe)
	Int id = Me.GetFormID()
	If id < 0
		id = -(id + 1)
	EndIf
	Int nature = (id / 3) % 3
	If nature == 0
		If Me.GetLevel() >= 30
			SpellChainLightning.Cast(Me, foe)
		Else
			SpellLightning.Cast(Me, foe)
		EndIf
		Debug.Trace("SNE leaf: Leaf Jonin " + Me + " LIGHTNING RELEASE at " + foe)
	ElseIf nature == 1
		SpellIceSpike.Cast(Me, foe)
		Debug.Trace("SNE leaf: Leaf Jonin " + Me + " WATER RELEASE (ice spike) at " + foe)
	Else
		SpellFus.Cast(Me, foe)
		foe.DamageActorValue("Health", 10.0 + Me.GetLevel() * 0.5)
		Debug.Trace("SNE leaf: Leaf Jonin " + Me + " WIND RELEASE at " + foe)
	EndIf
EndFunction

Actor Function CellCaptain()
	Actor best = Me
	Cell c = Me.GetParentCell()
	If !c
		Return best
	EndIf
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a != Me && !a.IsDead() && a.IsInCombat() && a.IsInFaction(LegionFaction) && LeafRank(a) == RANK_JONIN && Me.GetDistance(a) < 2500.0 && a.GetLevel() > best.GetLevel()
			best = a
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction

Function Substitution(Actor att, Float lost)
	NextSub = Now() + 12.0
	Busy = True
	If lost > 0.0
		If !Me.IsInKillMove() && !Me.IsBleedingOut() && Me.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
			Me.RestoreActorValue("Health", Me.GetBaseActorValue("Health") * lost)    ; it was only a log
		EndIf
	EndIf
	ObjectReference log = Me.PlaceAtMe(LogItem)
	Float a = att.GetAngleZ()
	Me.MoveTo(att, -Math.sin(a) * 150.0, -Math.cos(a) * 150.0, 0.0)
	Debug.Trace("SNE leaf: Leaf Jonin " + Me + " SUBSTITUTION JUTSU - behind " + att)
	Utility.Wait(0.3)
	Me.StartCombat(att)
	Busy = False
	LastHp = Me.GetActorValuePercentage("Health")
	Utility.Wait(5.0)
	If log
		log.Delete()
	EndIf
EndFunction

Function TagTick()
	If !Tag
		Return
	EndIf
	If Now() > TagUntil || TagUntil > Now() + 30.0
		Tag.Delete()
		Tag = None
		Return
	EndIf
	Cell c = Tag.GetParentCell()
	If !c
		Return
	EndIf
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && !a.IsDead() && a.IsHostileToActor(Me) && Tag.GetDistance(a) < 160.0
			Tag.PlaceAtMe(TagBlast)
			Debug.Trace("SNE leaf: explosive tag goes off on " + a)
			Tag.Delete()
			Tag = None
			Return
		EndIf
		i += 1
	EndWhile
EndFunction

Function BigJutsu(Actor foe)
	Busy = True
	Bool rasengan = Utility.RandomFloat() < 0.5
	ChakraFX.Play(Me, 1.0)
	Utility.Wait(0.4)
	Me.MoveTo(foe, Math.sin(foe.GetAngleZ()) * 90.0, Math.cos(foe.GetAngleZ()) * 90.0, 0.0)
	If rasengan
		foe.DamageActorValue("Health", 30.0 + Me.GetLevel())
		Me.PushActorAway(foe, 6.0)
		Debug.Trace("SNE leaf: Leaf Jonin " + Me + " RASENGAN on " + foe)
	Else
		ShockFX.Play(foe, 1.0)
		foe.DamageActorValue("Health", 25.0 + Me.GetLevel())
		foe.DamageActorValue("Magicka", 40.0)
		foe.SetAnimationVariableFloat("staggerMagnitude", 1.0)
		Debug.SendAnimationEvent(foe, "staggerStart")
		Debug.Trace("SNE leaf: Leaf Jonin " + Me + " CHIDORI on " + foe)
	EndIf
	If foe == PlayerRef
		Game.ShakeCamera(None, 0.5, 0.5)
	EndIf
	Busy = False
EndFunction

; a hostile player sneaking near a jonin is sensed
Function Sense(Float t)
	If Rank != RANK_JONIN || !Active() || t < NextSense
		Return
	EndIf
	NextSense = t + 2.0
	If PlayerRef.IsSneaking() && Me.IsHostileToActor(PlayerRef) && Me.GetDistance(PlayerRef) < 1200.0
		PlayerRef.CreateDetectionEvent(PlayerRef, 100)
		Debug.Trace("SNE leaf: Leaf Jonin " + Me + " SENSES you sneaking")
	EndIf
EndFunction

; ---------- medics ----------
Event OnHealMe(String eventName, String strArg, Float numArg, Form sender)
	Actor s = sender as Actor
	If Done || !Me || Me.IsDead() || Rank == RANK_JONIN || Busy || !s || s.IsDead() || Me.GetDistance(s) > 1500.0
		Return
	EndIf
	MysticPalm(s)
EndEvent

Function MedicTick(Float t, Actor foe, Float d)
	If NextScalpel > t + 30.0
		NextScalpel = 0.0
	EndIf
	If d < 200.0 && t >= NextScalpel
		NextScalpel = t + 8.0
		If Rank == RANK_CAPTAIN
			CherryBlossomImpact(foe)
		Else
			ChakraScalpel(foe)
		EndIf
		Return
	EndIf
	If NextMass > t + 30.0
		NextMass = 0.0
	EndIf
	Actor hurt = None
	Float hurtPct = 0.6
	Int hurtCount = 0
	Cell c = Me.GetParentCell()
	If c
		Int n = c.GetNumRefs(43)
		If n > 80
			n = 80
		EndIf
		Int i = 0
		While i < n
			Actor a = c.GetNthRef(i, 43) as Actor
			If a && a != Me && !a.IsDead() && (a.IsInFaction(LegionFaction) || a.IsInFaction(OculatusFaction) || a.IsPlayerTeammate() || a == PlayerRef) && !a.IsHostileToActor(Me) && Me.GetDistance(a) < 1500.0
				Float p = a.GetActorValuePercentage("Health")
				If p < 0.7
					hurtCount += 1
				EndIf
				If p < hurtPct
					hurtPct = p
					hurt = a
				EndIf
			EndIf
			i += 1
		EndWhile
	EndIf
	If Rank == RANK_CAPTAIN && hurtCount >= 2 && t >= NextMass
		NextMass = t + 8.0
		MassHealing()
		Return
	EndIf
	If hurt && t >= NextPalm
		MysticPalm(hurt)
	EndIf
EndFunction

Function MysticPalm(Actor ally)
	NextPalm = Now() + 6.0
	Busy = True
	BusyHit = False
	Actor foe = Me.GetCombatTarget()
	If Me.GetDistance(ally) > 250.0
		Me.StopCombat()
		Me.PathToReference(ally, 1.0)
	EndIf
	Float per = 0.15
	If Rank == RANK_CAPTAIN
		per = 0.25
	EndIf
	Int ticks = 0
	Float maxHp = ally.GetBaseActorValue("Health")
	While ticks < 3 && !BusyHit && !Me.IsDead() && !ally.IsDead() && Me.GetDistance(ally) < 350.0
		HealFX.Play(ally, 1.0)
		If !ally.IsInKillMove() && !ally.IsBleedingOut() && ally.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
			ally.RestoreActorValue("Health", maxHp * per)
		EndIf
		Utility.Wait(1.0)
		ticks += 1
	EndWhile
	Debug.Trace("SNE leaf: " + RankName() + " " + Me + " MYSTIC PALM on " + ally + " for " + ticks + " s (interrupted " + BusyHit + ")")
	If foe && !foe.IsDead() && !Me.IsDead() && !Me.IsInCombat()
		Me.StartCombat(foe)
	EndIf
	Busy = False
EndFunction

Function ChakraScalpel(Actor foe)
	foe.DamageActorValue("Stamina", 60.0 + Me.GetLevel())
	foe.DamageActorValue("Health", 15.0 + Me.GetLevel() * 0.5)
	Exhaustion.Cast(foe, foe)
	ChakraFX.Play(foe, 1.0)
	Debug.Trace("SNE leaf: medical ninja " + Me + " CHAKRA SCALPEL on " + foe)
EndFunction

Function MassHealing()
	Cell c = Me.GetParentCell()
	If !c
		Return
	EndIf
	Int healed = 0
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && !a.IsDead() && (a == Me || a.IsInFaction(LegionFaction) || a.IsInFaction(OculatusFaction) || a.IsPlayerTeammate() || a == PlayerRef) && !a.IsHostileToActor(Me) && Me.GetDistance(a) < 900.0
			If !a.IsInKillMove() && !a.IsBleedingOut() && a.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
				a.RestoreActorValue("Health", a.GetBaseActorValue("Health") * 0.3)
			EndIf
			a.RestoreActorValue("Stamina", a.GetBaseActorValue("Stamina") * 0.5)
			SpellIronflesh.Cast(a, a)
			HealFX.Play(a, 1.5)
			healed += 1
		EndIf
		i += 1
	EndWhile
	Debug.Trace("SNE leaf: Medical Captain " + Me + " MASS HEALING on " + healed)
EndFunction

Function StrengthOfAHundred()
	HundredUsed = True
	If !Me.IsInKillMove() && !Me.IsBleedingOut() && Me.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
		Me.RestoreActorValue("Health", Me.GetBaseActorValue("Health"))
	EndIf
	StrengthOfHundred.Cast(Me, Me)
	ChakraFX.Play(Me, 20.0)
	Debug.Trace("SNE leaf: Medical Captain " + Me + " STRENGTH OF A HUNDRED SEAL released")
EndFunction

Function CherryBlossomImpact(Actor foe)
	foe.DamageActorValue("Health", 50.0 + Me.GetLevel())
	Cell c = Me.GetParentCell()
	If c
		Int n = c.GetNumRefs(43)
		If n > 80
			n = 80
		EndIf
		Int i = 0
		While i < n
			Actor a = c.GetNthRef(i, 43) as Actor
			If a && !a.IsDead() && a.IsHostileToActor(Me) && Me.GetDistance(a) < 300.0
				Me.PushActorAway(a, 8.0)
			EndIf
			i += 1
		EndWhile
	EndIf
	If Me.GetDistance(PlayerRef) < 1500.0
		Game.ShakeCamera(None, 0.8, 0.8)
	EndIf
	Debug.Trace("SNE leaf: Medical Captain " + Me + " CHERRY BLOSSOM IMPACT on " + foe)
EndFunction

; ---------- style and CPR ----------
Function ApplyStyle()
	If !Me || Me.IsPlayerTeammate()
		Return
	EndIf
	ActorBase b = Me.GetLeveledActorBase()
	If !b || TacticsOn.GetValue() < 0.5
		Return
	EndIf
	CombatStyle want = StyleJonin
	If Rank != RANK_JONIN
		want = StyleMedic
	EndIf
	If b.GetCombatStyle() != want
		b.SetCombatStyle(want)
	EndIf
EndFunction

Function PushCPR()
	If !Active() || Busy
		Return
	EndIf
	If Rank == RANK_JONIN
		SetCPR(True, 0.2, True, 100.0, 300.0, 60.0, 160.0, False)    ; not afraid of a straight fight: in close, round the flanks
	Else
		SetCPR(True, 0.9, True, 400.0, 900.0, 30.0, 60.0, True)       ; medics stay out of reach
	EndIf
EndFunction

Function SetCPR(Bool backoff, Float backoffChance, Bool circle, Float circleMin, Float circleMax, Float angleMin, Float angleMax, Bool fallback)
	Me.SetAnimationVariableBool("CPR_EnableBackoff", backoff)
	Me.SetAnimationVariableFloat("CPR_BackoffChance", backoffChance)
	Me.SetAnimationVariableBool("CPR_EnableCircling", circle)
	Me.SetAnimationVariableFloat("CPR_CirclingDistMin", circleMin)
	Me.SetAnimationVariableFloat("CPR_CirclingDistMax", circleMax)
	Me.SetAnimationVariableFloat("CPR_CirclingAngleMin", angleMin)
	Me.SetAnimationVariableFloat("CPR_CirclingAngleMax", angleMax)
	Me.SetAnimationVariableBool("CPR_EnableFallback", fallback)
	If fallback
		Me.SetAnimationVariableFloat("CPR_FallbackDistMin", 400.0)
		Me.SetAnimationVariableFloat("CPR_FallbackDistMax", 900.0)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMin", 0.3)
		Me.SetAnimationVariableFloat("CPR_FallbackWaitTimeMax", 0.6)
	EndIf
EndFunction

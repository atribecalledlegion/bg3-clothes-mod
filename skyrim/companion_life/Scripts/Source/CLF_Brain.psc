Scriptname CLF_Brain extends Quest
{Companion Life v6 (2026-10-17): BAREFOOT AT HOME ONLY.
When Serana or Ashe is inside a player home (her own location has LocTypePlayerHouse) she takes off whatever covers
her feet - the feet slot (37) and calf pieces (38: socks, greaves, tall boots; never trousers, never an item that is
part of the body piece, slot 32) - and puts exactly those back on once she is out of the home. If her outfit script
puts something back on while she is home, it comes off again. Their own AI is untouched (v1-v5's downtime packages
are gone; that build is kept in old_v5/). Off switch: set CLF_Enabled to 0. Trace lines start with "CLF:".}

Bool AliasesCleared = False
Actor Property PlayerRef Auto
GlobalVariable Property Enabled Auto
Keyword Property LocTypePlayerHouse Auto

Float Property Tick = 2.0 AutoReadOnly

Actor AsheRef
Bool[] Barefoot
Form[] Shoes        ; 3 per companion: index i * 3 + k

Event OnInit()
	RegisterForSingleUpdate(5.0)
EndEvent

Event OnUpdate()
	If !Barefoot || Barefoot.Length != 2
		Barefoot = new Bool[2]
	EndIf
	If !Shoes || Shoes.Length != 6
		Shoes = new Form[6]
	EndIf
	If !AsheRef
		AsheRef = Game.GetFormFromFile(0x2D4A35, "Ashe - Fire and Blood.esp") as Actor
	EndIf
	; v7 (2026-10-19): Serana straight from Dawnguard, like Ashe; the aliases are emptied so nothing of ours holds her
	; (user: her own sandboxing back, barefoot kept as the sign the mod is on)
	If !AliasesCleared
		AliasesCleared = True
		Int i = 0
		While i < 4
			ReferenceAlias ra = GetAlias(i) as ReferenceAlias
			If ra && ra.GetReference()
				ra.Clear()
			EndIf
			i += 1
		EndWhile
		Debug.Trace("CLF: v7 - aliases cleared, Serana and Ashe run only their own AI (barefoot at home kept)")
	EndIf
	Actor serana = Game.GetFormFromFile(0x002B74, "Dawnguard.esm") as Actor
	If Enabled.GetValue() > 0.0
		Check(0, serana)
		If AsheRef != serana
			Check(1, AsheRef)
		EndIf
	Else
		If serana && Barefoot[0]
			ShoesOn(0, serana)
		EndIf
		If AsheRef && Barefoot[1]
			ShoesOn(1, AsheRef)
		EndIf
	EndIf
	RegisterForSingleUpdate(Tick)
EndEvent

Function Check(Int i, Actor a)
	If !a || !a.Is3DLoaded() || a.IsDead()
		Return
	EndIf
	If AtHome(a)
		If Barefoot[i]
			StripFeet(i, a, False)          ; her outfit script put something back on: off again
		ElseIf StripFeet(i, a, True)
			Barefoot[i] = True
		EndIf
	ElseIf Barefoot[i]
		ShoesOn(i, a)
	EndIf
EndFunction

Bool Function AtHome(Actor a)
	Location loc = a.GetCurrentLocation()
	Return loc && loc.HasKeyword(LocTypePlayerHouse) && a.IsInInterior()
EndFunction

Bool Function StripFeet(Int i, Actor a, Bool remember)
	Int n = 0
	Int k = 0
	While k < 2
		Int mask = 0x80
		If k == 1
			mask = 0x100
		EndIf
		Armor w = a.GetWornForm(mask) as Armor
		If w && Math.LogicalAnd(w.GetSlotMask(), 0x4) == 0
			Int m = w.GetSlotMask()
			If mask == 0x80 || Math.LogicalAnd(m, 0x80) != 0 || m == 0x100
				If remember
					Remember(i, w)
					Debug.Trace("CLF: " + a.GetDisplayName() + " takes off " + w.GetName() + " (barefoot at home)")
				EndIf
				a.UnequipItem(w, False, True)
				n += 1
			EndIf
		ElseIf w && remember && mask == 0x80
			Debug.Trace("CLF: " + a.GetDisplayName() + "'s " + w.GetName() + " covers her feet but is part of her body piece - left on")
		EndIf
		k += 1
	EndWhile
	Return n > 0
EndFunction

Function Remember(Int i, Form f)
	Int k = 0
	While k < 3
		If Shoes[i * 3 + k] == f
			Return
		EndIf
		k += 1
	EndWhile
	k = 0
	While k < 3
		If !Shoes[i * 3 + k]
			Shoes[i * 3 + k] = f
			Return
		EndIf
		k += 1
	EndWhile
EndFunction

Function ShoesOn(Int i, Actor a)
	Barefoot[i] = False
	Int k = 0
	While k < 3
		Form f = Shoes[i * 3 + k]
		Shoes[i * 3 + k] = None
		If f && a.GetItemCount(f) > 0
			a.EquipItem(f, False, True)
			Debug.Trace("CLF: " + a.GetDisplayName() + " puts " + f.GetName() + " back on (left home)")
		EndIf
		k += 1
	EndWhile
EndFunction

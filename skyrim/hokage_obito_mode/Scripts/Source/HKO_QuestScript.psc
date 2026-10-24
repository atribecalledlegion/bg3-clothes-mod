Scriptname HKO_QuestScript extends Quest
{Hokage Obito Mode (2026-10-20): the what-if Obito who saved Rin, kept both eyes and became Hokage. Minato's space-time
warps + Kakashi's copy-ninja style. Kit design: skyrim/hokage_obito_mode/KIT_DESIGN.md.

Stage 1 (this build):
- the "Hokage" lesser power toggles the mode. The mode ability (HKO_ModeMark) is the OAR condition that moves
  Jetstream Sam's moveset onto any two-handed sword while the mode is on (one-handed until 2026-10-20). Ronin Obito and Hokage Obito never run
  together (they share hotkeys).
- X tap: throw a kunai. An enemy it hits carries the Hiraishin seal for 30 s (red outline, seen through walls; up to 3).
- X held: plant a seal kunai where he stands (one at a time).
- Shift+X: warp to the newest seal. Behind a sealed enemy (facing its back, it staggers), or onto the planted kunai.
  WARP TEST: 'set HKO_WarpMethod to N' picks how he is moved (Ronin's script teleports T-posed him):
  0 = Uchiha Clan's way (controls off, MoveTo, controls on), 1 = a plain MoveTo, 2 = 0 + IdleForceDefaultState first.
Stage 3: the Copy Wheel. H cycles Leaf (Sam) -> Fire Release (Kagutsuchi's EvilFire set) -> Copied (Mitsunari's sets,
Sam underneath). Each style is an ability whose effect the OAR/DAR folders check. Shift+H is kept for the ultimate.}

Actor Property PlayerRef Auto
Spell Property TogglePower Auto
Spell Property ModeAbility Auto
Spell Property KunaiSpell Auto
Spell Property WarpStrike Auto
GlobalVariable Property WarpMethod Auto
Spell Property FireStyle Auto
Spell Property CopiedStyle Auto
Weapon Property CopiedBlade Auto

Int Property KunaiKeyCode = 45 AutoReadOnly       ; X
Int Property WheelKeyCode = 35 AutoReadOnly       ; H
Float Property PlantHoldSeconds = 0.35 AutoReadOnly
Float Property WarpCost = 10.0 AutoReadOnly       ; magicka (chakra)
Float Property WarpBehind = 110.0 AutoReadOnly
Float Property WarpReach = 4000.0 AutoReadOnly
Float Property KunaiCooldown = 0.4 AutoReadOnly
Float Property WarpCooldown = 0.8 AutoReadOnly
Bool Property Verbose = True AutoReadOnly

Bool HokageOn = False
Bool KeyBound = False
Bool GaveBlade = False
Bool GaveDaiKatana = False
Actor[] Seals
Float[] SealTimes
ObjectReference Planted
Float LastKunai = -100.0
Float LastWarp = -100.0
Bool WarpBusy = False
Int Style = 0    ; 0 Leaf, 1 Fire Release, 2 Copied
Weapon PrevBlade    ; the sword he held before taking up the Copied style

Event OnInit()
	PlayerRef.AddSpell(TogglePower, False)
	Seals = new Actor[3]
	SealTimes = new Float[3]
EndEvent

Bool Function IsOn()
	Return HokageOn
EndFunction

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

Function Note(String s)
	If Verbose
		Debug.Trace("HKO: " + s)
	EndIf
EndFunction

ROM_QuestScript Function Ronin()
	Return Game.GetFormFromFile(0x00000800, "Ronin Obito Mode.esp") as ROM_QuestScript
EndFunction

; ---------------- the mode ----------------

Function Toggle()
	If HokageOn
		TurnOff("Obito sets the Hokage's mantle aside.")
		Return
	EndIf
	ROM_QuestScript r = Ronin()
	If r && r.IsOn()
		r.Toggle()    ; the two modes share hotkeys
	EndIf
	If !Seals
		Seals = new Actor[3]
		SealTimes = new Float[3]
	EndIf
	HokageOn = True
	PlayerRef.AddSpell(ModeAbility, False)
	BindKeys()
	ApplyStyle(False)
	GiveBlade()
	RegisterForSingleUpdate(1.0)
	Debug.Notification("The Hokage takes the field (" + StyleName() + "). X kunai, hold X seal, Shift+X warp, H Copy Wheel.")
	Note("on (warp method " + Method() + ")")
EndFunction

Function TurnOff(String msg)
	HokageOn = False
	PlayerRef.RemoveSpell(ModeAbility)
	PlayerRef.RemoveSpell(FireStyle)
	PlayerRef.RemoveSpell(CopiedStyle)
	SwapBack()
	UnregisterForAllKeys()
	KeyBound = False
	UnregisterForUpdate()
	ClearSeals()
	Debug.Notification(msg)
	Note("off")
EndFunction

; The Hokage's blade, handed over the first time. 2026-10-20: all three movesets (Sam, Kagutsuchi, Mitsunari) are
; two-handed sets, so any TWO-HANDED sword carries them; the gift is Katana Crafting's Akaviri Dai-Katana (the
; Black Dragon Ninjato from stage 1 no longer carries the moveset).
Function GiveBlade()
	If GaveDaiKatana
		Return
	EndIf
	GaveDaiKatana = True
	Weapon w = Game.GetFormFromFile(0x0000018F, "KatanaCrafting.esp") as Weapon
	If w && PlayerRef.GetItemCount(w) == 0
		PlayerRef.AddItem(w, 1, True)
		Debug.Notification("An Akaviri Dai-Katana is in your pack: the Hokage's blade (any two-handed sword works).")
	EndIf
EndFunction

Event OnUpdate()
	If !HokageOn
		Return
	EndIf
	ROM_QuestScript r = Ronin()
	If r && r.IsOn()
		TurnOff("Obito walks the ronin's way instead.")
		Return
	EndIf
	BindKeys()    ; keys are not kept across a load
	ExpireSeals()
	RegisterForSingleUpdate(1.0)
EndEvent

; ---------------- kunai, seals, warp ----------------

Int Function Method()
	If WarpMethod
		Return WarpMethod.GetValueInt()
	EndIf
	Return 0
EndFunction

Function BindKeys()
	; always (re)register: a save from stage 1 has KeyBound set with only X registered
	RegisterForKey(KunaiKeyCode)
	RegisterForKey(WheelKeyCode)
	KeyBound = True
EndFunction

Event OnKeyDown(Int keyCode)
	If !HokageOn || Utility.IsInMenuMode()
		Return
	EndIf
	Bool shift = Input.IsKeyPressed(42) || Input.IsKeyPressed(54)    ; left / right Shift
	If keyCode == KunaiKeyCode && shift
		Warp()
	ElseIf keyCode == WheelKeyCode && !shift
		Style = (Style + 1) % 3
		ApplyStyle(True)
	EndIf
EndEvent

; ---------------- the Copy Wheel ----------------

; 2026-10-20: the Copied style is Mitsunari's whole art, blade included. His katana is a rig (sheathed in the left
; hand at rest, drawn by his own moves) that needs his scabbard props; the plain Katana Crafting blades can't carry
; both. So Copied swaps to the Copied blade (Mitsunari's Akaviri Dai-Katana with his props) and leaving it swaps back.
Function SwapToCopied()
	If !CopiedBlade
		Return
	EndIf
	Weapon w = PlayerRef.GetEquippedWeapon()
	If w == CopiedBlade
		Return
	EndIf
	If w
		PrevBlade = w
	EndIf
	Bool drawn = PlayerRef.IsWeaponDrawn()
	If PlayerRef.GetItemCount(CopiedBlade) == 0
		PlayerRef.AddItem(CopiedBlade, 1, True)
	EndIf
	PlayerRef.EquipItem(CopiedBlade, False, True)
	If drawn
		PlayerRef.DrawWeapon()
	EndIf
	Note("copied blade on (was " + w + ")")
EndFunction

Function SwapBack()
	If !CopiedBlade || PlayerRef.GetEquippedWeapon() != CopiedBlade
		Return
	EndIf
	Bool drawn = PlayerRef.IsWeaponDrawn()
	If PrevBlade && PlayerRef.GetItemCount(PrevBlade) > 0
		PlayerRef.EquipItem(PrevBlade, False, True)
	Else
		PlayerRef.UnequipItem(CopiedBlade, False, True)
	EndIf
	If drawn && PrevBlade
		PlayerRef.DrawWeapon()
	EndIf
	Note("copied blade off, back to " + PrevBlade)
EndFunction

String Function StyleName()
	If Style == 1
		Return "Fire Release"
	ElseIf Style == 2
		Return "Copied"
	EndIf
	Return "Leaf"
EndFunction

Function ApplyStyle(Bool announce)
	If Style == 1
		PlayerRef.RemoveSpell(CopiedStyle)
		PlayerRef.AddSpell(FireStyle, False)
	ElseIf Style == 2
		PlayerRef.RemoveSpell(FireStyle)
		PlayerRef.AddSpell(CopiedStyle, False)
	Else
		PlayerRef.RemoveSpell(FireStyle)
		PlayerRef.RemoveSpell(CopiedStyle)
	EndIf
	If Style == 2
		SwapToCopied()
	Else
		SwapBack()
	EndIf
	If announce
		Sound eye = Game.GetFormFromFile(0x00003E10, "naruto overhaul.esp") as Sound    ; A0SharinganMarker
		If eye
			eye.Play(PlayerRef)
		EndIf
		Debug.Notification("Copy Wheel: " + StyleName())
		Note("style " + StyleName())
	EndIf
EndFunction

Event OnKeyUp(Int keyCode, Float holdTime)
	If !HokageOn || keyCode != KunaiKeyCode || Utility.IsInMenuMode()
		Return
	EndIf
	If Input.IsKeyPressed(42) || Input.IsKeyPressed(54)
		Return    ; that was the warp
	EndIf
	If holdTime >= PlantHoldSeconds
		Plant()
	Else
		ThrowKunai()
	EndIf
EndEvent

Function ThrowKunai()
	Float t = Now()
	If t - LastKunai < KunaiCooldown && t >= LastKunai
		Return
	EndIf
	LastKunai = t
	Actor aim = Game.GetCurrentCrosshairRef() as Actor
	If !aim || aim.IsDead()
		aim = PlayerRef.GetCombatTarget()
	EndIf
	If aim && (aim.IsDead() || aim == PlayerRef)
		aim = None
	EndIf
	KunaiSpell.Cast(PlayerRef, aim)
	Note("kunai thrown at " + aim)
EndFunction

Function Plant()
	If Planted
		Planted.Disable()
		Planted.Delete()
	EndIf
	Form xmarker = Game.GetFormFromFile(0x0000003B, "Skyrim.esm")
	Planted = PlayerRef.PlaceAtMe(xmarker, 1, True, False)
	Debug.Notification("Seal planted.")
	Note("seal planted")
EndFunction

; called by HKO_SealEffect on the enemy a kunai hit
Function AddSeal(Actor a)
	If !HokageOn || !a
		Return
	EndIf
	Int i = Seals.Find(a)
	If i < 0
		i = OldestSlot()
	EndIf
	Seals[i] = a
	SealTimes[i] = Now()
	Note("seal on " + a.GetDisplayName() + " (slot " + i + ")")
EndFunction

Function SealGone(Actor a)
	Int i = Seals.Find(a)
	If i >= 0
		Seals[i] = None
	EndIf
EndFunction

Int Function OldestSlot()
	Int best = 0
	Int k = 0
	While k < Seals.Length
		If !Seals[k]
			Return k
		EndIf
		If SealTimes[k] < SealTimes[best]
			best = k
		EndIf
		k += 1
	EndWhile
	Return best
EndFunction

Function ExpireSeals()
	Float t = Now()
	Int k = 0
	While k < Seals.Length
		If Seals[k] && (Seals[k].IsDead() || t - SealTimes[k] > 31.0 || t < SealTimes[k])
			Seals[k] = None
		EndIf
		k += 1
	EndWhile
EndFunction

Function ClearSeals()
	Int k = 0
	While Seals && k < Seals.Length
		Seals[k] = None
		k += 1
	EndWhile
	If Planted
		Planted.Disable()
		Planted.Delete()
		Planted = None
	EndIf
EndFunction

; newest living sealed enemy in reach, else None
Actor Function NewestSeal()
	Actor best = None
	Float bestT = -1000000.0
	Int k = 0
	While k < Seals.Length
		Actor a = Seals[k]
		If a && !a.IsDead() && a.Is3DLoaded() && PlayerRef.GetDistance(a) <= WarpReach && SealTimes[k] > bestT
			best = a
			bestT = SealTimes[k]
		EndIf
		k += 1
	EndWhile
	Return best
EndFunction

Function Warp()
	If WarpBusy
		Return
	EndIf
	WarpBusy = True    ; claimed before any engine call (Ronin lesson: fast presses stack)
	Float t = Now()
	If t - LastWarp < WarpCooldown && t >= LastWarp
		WarpBusy = False
		Return
	EndIf
	Actor target = NewestSeal()
	ObjectReference spot = None
	If !target && Planted && Planted.GetParentCell() == PlayerRef.GetParentCell()
		spot = Planted
	EndIf
	If !target && !spot
		Debug.Notification("No seal in reach.")
		WarpBusy = False
		Return
	EndIf
	If PlayerRef.GetActorValue("Magicka") < WarpCost
		Debug.Notification("Not enough chakra to warp.")
		WarpBusy = False
		Return
	EndIf
	LastWarp = t
	PlayerRef.DamageActorValue("Magicka", WarpCost)
	Int m = Method()
	Bool wasDrawn = PlayerRef.IsWeaponDrawn()
	If target
		Note("warp (method " + m + ") behind " + target.GetDisplayName() + ", " + PlayerRef.GetDistance(target) as Int + " away")
	Else
		Note("warp (method " + m + ") to the planted seal, " + PlayerRef.GetDistance(spot) as Int + " away")
	EndIf
	KamuiOn(PlayerRef, True)
	If m != 1
		; movement only: turning fighting controls off makes the game sheathe his weapon (stage 1 test, 2026-10-20)
		Game.DisablePlayerControls(True, False, False, False, False, False, True, False, 0)
	EndIf
	If m == 2
		Debug.SendAnimationEvent(PlayerRef, "IdleForceDefaultState")
	EndIf
	Utility.Wait(0.1)
	If target
		Float a = target.GetAngleZ()
		PlayerRef.MoveTo(target, -Math.Sin(a) * WarpBehind, -Math.Cos(a) * WarpBehind, 0.0, True)    ; his back, facing it
	Else
		PlayerRef.MoveTo(spot, 0.0, 0.0, 0.0, False)
	EndIf
	Utility.Wait(0.05)
	If m != 1
		Game.EnablePlayerControls()
	EndIf
	If wasDrawn && !PlayerRef.IsWeaponDrawn()
		PlayerRef.DrawWeapon()    ; he lands ready to strike
		Note("blade re-drawn after the warp")
	EndIf
	If target
		WarpStrike.Cast(PlayerRef, target)
	EndIf
	Debug.Notification("Hiraishin (method " + m + ")")
	Utility.Wait(0.25)
	KamuiOn(PlayerRef, False)
	WarpBusy = False
EndFunction

; the colourless Kamui distortion (Uchiha Clan RFCT + Sharingan Copy's void), as Ronin's
Function KamuiOn(Actor t, Bool on)
	VisualEffect distort = Game.GetFormFromFile(0x000266AB, "UchihaClan.esp") as VisualEffect
	VisualEffect void = Game.GetFormFromFile(0x00000842, "Sharingan Copy.esp") as VisualEffect
	If on
		If distort
			distort.Play(t)
		EndIf
		If void
			void.Play(t)
		EndIf
	Else
		If distort
			distort.Stop(t)
		EndIf
		If void
			void.Stop(t)
		EndIf
	EndIf
EndFunction

Scriptname ECB_Guard extends Quest
{Elden Counter - Block Only (2026-10-17). Elden Counter swaps the player's next first power attack (mco_powerattack1)
for its guard counter while its trigger ability (EldenCounter.esp 0x801, effect 0x800) is on, and the user's MCO
combos (SkyFX unarmed, Olivier battleaxe/gunbai) were getting it mid-combo: white flash, then the counter instead of
the 2nd power attack. This watches the moment the window opens: if the player was blocking within BlockGrace s
(holding block, or a bash parry, which is done from block), the window stays; otherwise it is removed at once, so the
combo goes on. Never touches NPCs. Polls every 0.1 s with a weapon out or in combat, else every 1 s.
v2 (2026-10-17): v1 watched only the trigger ability and never fired - with Elden Counter's Nemesis "Vanilla Behavior
Patch" (ecvpc) the switch is the behaviour int Val_GuardCounter (power attacks go through Guard_CounterDecider when it
is not 0), set by the DLL. v2 watches both and resets Val_GuardCounter to 0 when the window opens without a block.
v4 (2026-10-19, lean): Val_GuardCounter is in the Nemesis output but every read failed ("cannot fetch variable",
hundreds of stack dumps a fight, slowing all Papyrus) and the trigger ability caught every window anyway, so it is gone.
A tick is now one engine call (HasMagicEffect) instead of ~7: blocking comes from block animation events (plus one
IsBlocking check when a window opens, for alternate block keys), the weapon-drawn check runs once a second.
Trace lines start with "ECB:".}

Actor Property PlayerRef Auto
Float Property BlockGrace = 0.6 AutoReadOnly

Spell CounterSpell
MagicEffect CounterEffect
Bool HadTrigger
Float LastBlock = -100.0
Bool Blocking
Bool Announced
Bool Fast
Int Tick

MagicEffect YamatoEffect

; Vergil Yamato 5.7's "Yamato equipped" effect (ChaosYamato.esp 0x861), when that mod is loaded
Bool Function YamatoOut()
	If !YamatoEffect
		YamatoEffect = Game.GetFormFromFile(0x861, "ChaosYamato.esp") as MagicEffect
		If !YamatoEffect
			Return False
		EndIf
	EndIf
	Return PlayerRef.HasMagicEffect(YamatoEffect)
EndFunction

Event OnInit()
	RegisterForSingleUpdate(2.0)
EndEvent

; registrations are lost on load: renewed once a second from the tick
Function ListenBlock()
	RegisterForAnimationEvent(PlayerRef, "blockStartOut")
	RegisterForAnimationEvent(PlayerRef, "blockStop")
EndFunction

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If asEventName == "blockStartOut"
		Blocking = True
	Else
		Blocking = False
		LastBlock = Utility.GetCurrentRealTime()
	EndIf
EndEvent

Event OnUpdate()
	If !CounterSpell
		CounterSpell = Game.GetFormFromFile(0x801, "EldenCounter.esp") as Spell
		CounterEffect = Game.GetFormFromFile(0x800, "EldenCounter.esp") as MagicEffect
		If !CounterSpell || !CounterEffect
			RegisterForSingleUpdate(30.0)       ; Elden Counter not loaded
			Return
		EndIf
	EndIf
	If !Announced
		Announced = True
		Debug.Trace("ECB: watching Elden Counter (v4 lean: trigger ability + block events)")
	EndIf
	Tick += 1
	If Tick >= 10 || !Fast
		Tick = 0
		ListenBlock()
		Fast = PlayerRef.IsWeaponDrawn()
	EndIf
	Bool has = PlayerRef.HasMagicEffect(CounterEffect)
	If has && !HadTrigger
		Float now = Utility.GetCurrentRealTime()
		If LastBlock > now
			LastBlock = -100.0                       ; real-time clock restarts on load
		EndIf
		If Blocking || PlayerRef.GetAnimationVariableBool("IsBlocking")
			LastBlock = now
		EndIf
		; v3 (2026-10-18): with the Vergil Yamato out, its heavy (mco_powerattack1) is a Vergil move, so the counter
		; window goes even after a real block; Ronin Obito Mode is still told about the block (its delayed cut)
		Bool yamato = YamatoOut()
		If now - LastBlock > BlockGrace || yamato
			PlayerRef.RemoveSpell(CounterSpell)
			PlayerRef.DispelSpell(CounterSpell)
			has = False
			If yamato && now - LastBlock <= BlockGrace
				SendModEvent("ROM_CounterKept")
				Debug.Trace("ECB: real block with the Yamato - Elden Counter's counter removed so Vergil's heavy plays; Ronin's cut armed")
			Else
				Debug.Trace("ECB: counter window opened without a block (" + (now - LastBlock) + " s since block) - removed, combo continues")
			EndIf
		Else
			Debug.Trace("ECB: counter window from a real block - kept")
			SendModEvent("ROM_CounterKept")    ; Ronin Obito Mode: the counter becomes his delayed Dimension Cut
		EndIf
	EndIf
	HadTrigger = has
	If Fast
		RegisterForSingleUpdate(0.1)
	Else
		RegisterForSingleUpdate(1.0)
	EndIf
EndEvent

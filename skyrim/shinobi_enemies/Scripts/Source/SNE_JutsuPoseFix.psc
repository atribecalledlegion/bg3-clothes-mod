Scriptname SNE_JutsuPoseFix extends Quest
{Shinobi Enemies. The Ryuka pose watcher is DISABLED (2026-10-16): it misread the casting button, interrupted casts
and forced the idle state (weapon sheathed, then a crash). The script stays because saves hold it on SNE_CQ.
What is left is a read-only DIAGNOSTIC (temporary): out of combat and not casting, it logs every change of the
player's magicka or max magicka ("SNE magicka:", at most 60 lines a session), to find the magicka bar flicker.
It changes nothing in the game.}

Actor Property PlayerRef Auto

Float LastTick = -100.0
Float LastMag = -1.0
Float LastMax = -1.0
Int MagLines
Float NextBeat

Event OnInit()
	RegisterForSingleUpdate(2.0)
EndEvent

Bool Property TraceOn = False AutoReadOnly    ; 2026-10-16: done - magicka stayed 370/370 through a flicker

Event OnUpdate()
	LastTick = Utility.GetCurrentRealTime()
	If !TraceOn
		Return    ; diagnostic finished; Kick() no longer restarts the loop
	EndIf
	TraceMagicka()
	RegisterForSingleUpdate(0.5)
EndEvent

; SNE_CompanionBrain calls this every tick: restarts the trace loop if it is not running (a save can lose it)
Function Kick()
	If !TraceOn
		Return
	EndIf
	Float t = Utility.GetCurrentRealTime()
	If t - LastTick > 3.0 || LastTick > t + 1.0
		LastTick = t
		RegisterForSingleUpdate(0.5)
	EndIf
EndFunction

Function TraceMagicka()
	Float now = Utility.GetCurrentRealTime()
	If now >= NextBeat || NextBeat > now + 60.0
		NextBeat = now + 20.0
		Debug.Trace("SNE magicka: tracer alive - " + (PlayerRef.GetActorValue("Magicka") as Int) + "/" + (PlayerRef.GetActorValueMax("Magicka") as Int) + " combat " + PlayerRef.IsInCombat() + " weapon out " + PlayerRef.IsWeaponDrawn())
	EndIf
	If MagLines >= 120 || PlayerRef.IsInCombat() || PlayerRef.GetAnimationVariableBool("IsCastingRight") || PlayerRef.GetAnimationVariableBool("IsCastingLeft")
		LastMag = -1.0
		Return
	EndIf
	Float mag = PlayerRef.GetActorValue("Magicka")
	Float mx = PlayerRef.GetActorValueMax("Magicka")
	If LastMag >= 0.0 && (Math.Abs(mag - LastMag) > 0.5 || Math.Abs(mx - LastMax) > 0.5)
		MagLines += 1
		GlobalVariable eye = Game.GetFormFromFile(0x0EFC75, "Skyrim.esm") as GlobalVariable
		Float eyeState = -1.0
		If eye
			eyeState = eye.GetValue()
		EndIf
		Debug.Trace("SNE magicka: " + (LastMag as Int) + "/" + (LastMax as Int) + " -> " + (mag as Int) + "/" + (mx as Int) + " (sprinting " + PlayerRef.IsSprinting() + ", weapon out " + PlayerRef.IsWeaponDrawn() + ", sharingan global " + eyeState + ")")
	EndIf
	LastMag = mag
	LastMax = mx
EndFunction

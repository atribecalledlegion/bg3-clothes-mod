"""Patch the Uchiha Clan Kamui realm scripts (originals extracted from UchihaClan.bsa into Scripts/Source).

aaaTobiKamuiSelf: leaving the realm no longer activates the cage/gas/fire levers with the player (they are
furniture, LeverPushAnimatingNoPlayer, so the player walked over and pulled one); the door is closed and the traps
switched off directly, the way the levers' activate links would. Arriving puts any captive found outside the cage
back inside it (twice: on arrival and again once the cell has settled).
aaaTobiKamuiTarget: warped actors land on one of nine spots spread around the cage instead of all on one marker
(stacked actors get pushed apart along the navmesh, which runs out through the cage door)."""
import os, sys
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Scripts', 'Source')

def patch(name, reps, tail=''):
    p = os.path.join(SRC, name); s = open(p, encoding='latin1').read()
    if 'Kamui Realm Fix' in s:
        print(name, 'already patched'); return
    for a, b in reps:
        assert s.count(a) == 1, (name, a[:80], s.count(a)); s = s.replace(a, b)
    s = s.rstrip() + '\n' + tail
    open(p, 'w', encoding='latin1', newline='\r\n').write(s.replace('\r\n', '\n')); print('patched', name)

SELF_LEVERS = """		INT openState = JailDoor01.GetOpenState()
		If (openState == 1 || openState == 2) 										; Check if door is open or opening
			Lever.Activate(Game.GetPlayer(), false)									; Close the jail door
		EndIf
		If (Gas01.GetState() == "On") 												; Check if the gas is being released
			Lever02.Activate(Game.GetPlayer(), false)								; Turn off the gas
		EndIf
		If (Fire01.GetState() != "Idle") 												; Check if the fire is being released
			Lever03.Activate(Game.GetPlayer(), false)								; Turn off the fire
		EndIf
"""
SELF_TAIL = r"""
; ********** Kamui Realm Fix **********
; The three levers are furniture: activating them with the player made the player walk over and pull one. Do what
; their activate links do instead: close the door, and activate each trap with its lever as the trigger.
Function ResetCage()
	INT openState = JailDoor01.GetOpenState()
	If (openState == 1 || openState == 2)
		JailDoor01.SetOpen(False)
	EndIf
	If (Gas01.GetState() == "On")
		Int i = 0
		While i < 4																	; the four gas vents, 0x0319B3-B6
			ObjectReference gas = Game.GetFormFromFile(0x0319B3 + i, "UchihaClan.esp") as ObjectReference
			If gas
				gas.Activate(Lever02)
			EndIf
			i += 1
		EndWhile
	EndIf
	If (Fire01.GetState() != "Idle")
		Fire01.Activate(Lever03)
		Int j = 0
		While j < 15																; FlameTrap002-008 and FlameTrapRight001-008, 0x2EF7A9-B7
			ObjectReference fire = Game.GetFormFromFile(0x2EF7A9 + j, "UchihaClan.esp") as ObjectReference
			If fire
				fire.Activate(Lever03)
			EndIf
			j += 1
		EndWhile
	EndIf
EndFunction

; Inside the cage bars, on its floor (not its roof, which has navmesh too).
Bool Function InCage(Actor a)
	Float px = a.GetPositionX()
	Float py = a.GetPositionY()
	Return px > 345.0 && px < 795.0 && py > -55.0 && py < 415.0 && a.GetPositionZ() < 120.0
EndFunction

; Captives found outside the cage: enemies die there and fade away (Kamui's dimension is no place to survive, and
; the realm stays uncluttered); essential/protected enemies, which cannot die, and non-hostile NPCs you stored are
; put back in the cage. Skips the player's teammates (Serana, followers, summons), the follower alias, disabled
; actors, the dead (corpses kept on the altars) and the mannequin.
Function CageCaptives()
	Actor player = Game.GetPlayer()
	Actor follow = Follower.GetActorRef()
	ActorBase mannequin = Game.GetFormFromFile(0x089A85, "Skyrim.esm") as ActorBase
	ObjectReference cage = Game.GetFormFromFile(0x0303C8, "UchihaClan.esp") as ObjectReference	; aaaTargetHomeMarkerREF (HomeMarker here is the player's spot)
	Actor[] dying = new Actor[32]
	Int killed = 0
	Int moved = 0
	Int n = HomeCell.GetNumRefs(62)													; 62 = actor references
	Int i = 0
	While i < n
		Actor a = HomeCell.GetNthRef(i, 62) as Actor
		If a && a != player && a != follow && !a.IsDead() && !a.IsDisabled() && !a.IsPlayerTeammate() && !a.IsCommandedActor() && a.GetActorBase() != mannequin && !InCage(a)
			ActorBase ab = a.GetActorBase()
			If a.IsHostileToActor(player) && !a.IsEssential() && !ab.IsProtected() && killed < 32
				a.Kill()																; no killer: no bounty, no crime
				dying[killed] = a
				killed += 1
			Else
				a.MoveTo(cage, (moved % 3 - 1) * 140.0, ((moved / 3) % 3 - 1) * 150.0, 0.0)
				moved += 1
			EndIf
		EndIf
		i += 1
	EndWhile
	If killed > 0
		Utility.Wait(2.0)														; let them fall, then fade them out of existence
		i = 0
		While i < killed
			dying[i].Disable(True)
			dying[i].Delete()
			i += 1
		EndWhile
	EndIf
	If killed + moved > 0
		Debug.Trace("Kamui Realm Fix: " + killed + " escaped enemy(ies) died in the void, " + moved + " captive(s) put back in the cage")
	EndIf
EndFunction
"""
patch('aaatobikamuiself.psc', [
    (SELF_LEVERS, "\t\tResetCage()\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t; Kamui Realm Fix: no lever pulling\n"),
    # follower lines: guard against no follower (GetActorRef() is None)
    ("""			Follower.GetActorRef().moveto(DefaultMarker,""", """			If Follower.GetActorRef()
			Follower.GetActorRef().moveto(DefaultMarker,"""),
    ("""Math.Cos(DefaultMarker.GetAngleZ()) * -120, 0) ; Let the follower go with you
""", """Math.Cos(DefaultMarker.GetAngleZ()) * -120, 0) ; Let the follower go with you
			EndIf
"""),
    ("""			Follower.GetActorRef().moveto(CurrentMarker,""", """			If Follower.GetActorRef()
			Follower.GetActorRef().moveto(CurrentMarker,"""),
    ("""Math.Cos(CurrentMarker.GetAngleZ()) * -120, 0) ; Let the follower go with you
""", """Math.Cos(CurrentMarker.GetAngleZ()) * -120, 0) ; Let the follower go with you
			EndIf
"""),
    ("""		Follower.GetActorRef().moveto(HomeMarker,""", """		If Follower.GetActorRef()
		Follower.GetActorRef().moveto(HomeMarker,"""),
    ("""Math.Cos(HomeMarker.GetAngleZ()) * -120, 0) ; Let the follower go with you
""", """Math.Cos(HomeMarker.GetAngleZ()) * -120, 0) ; Let the follower go with you
		EndIf
"""),
    # arriving in the realm: settle the cage
    ("""		Game.EnablePlayerControls(1, 1, 0, 0, 0, 1, 1)
		If(aaaTobiKamuiAutoSave.GetValue() == 1)
			Game.RequestAutoSave()											; Request autosave
		EndIf
		If(!Game.GetPlayer().HasPerk(EternalMangekyouPerk))""", """		Game.EnablePlayerControls(1, 1, 0, 0, 0, 1, 1)
		ResetCage()																; Kamui Realm Fix: cage shut, captives inside
		CageCaptives()
		If(aaaTobiKamuiAutoSave.GetValue() == 1)
			Game.RequestAutoSave()											; Request autosave
		EndIf
		If(!Game.GetPlayer().HasPerk(EternalMangekyouPerk))"""),
], SELF_TAIL)

# second pass after the blindness block at the very end of the arrival branch
p = os.path.join(SRC, 'aaatobikamuiself.psc'); s = open(p, encoding='latin1').read()
if 'again once the cell' in s: sys.exit()
a = """				BlindImod.Apply(1)
			EndIf
		EndIf
	EndIf
EndEvent"""
assert s.count(a) == 1
s = s.replace(a, """				BlindImod.Apply(1)
			EndIf
		EndIf
		Utility.Wait(3.0)														; Kamui Realm Fix: again once the cell has settled
		If Game.GetPlayer().GetParentCell() == HomeCell
			CageCaptives()
		EndIf
	EndIf
EndEvent""")
open(p, 'w', encoding='latin1', newline='\r\n').write(s.replace('\r\n', '\n'))

TARGET_MOVE = """				target.MoveTo(HomeMarker, abMatchRotation = True) 					; If they aren't inside, move target to the void
"""
patch('aaatobikamuitarget.psc', [
    (TARGET_MOVE, """				; Kamui Realm Fix: one of nine spots around the cage, not all on the same marker
				Int spot = Utility.RandomInt(0, 8)
				target.MoveTo(HomeMarker, (spot % 3 - 1) * 140.0, (spot / 3 - 1) * 150.0, 0.0)	; move target to the void
"""),
], '')

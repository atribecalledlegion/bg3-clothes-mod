Scriptname SPP_SixPathsQuestScript extends Quest
{Master control for Obito's Six Paths of Pain. Owns the six path aliases and every group command.
Attach to quest SPP_SixPathsQuest (Start Game Enabled).}

; ---------------------------------------------------------------------------
; Properties (fill in the Creation Kit)
; ---------------------------------------------------------------------------

ReferenceAlias[] Property Paths Auto
{The six path aliases, in this order: Yugito, Yagura, Roushi, Han, Utakata, Fuu.}

Actor Property PlayerRef Auto
{The player (Obito).}

GlobalVariable Property SPP_PathsState Auto
{0 = at home, not recruited. 1 = following. 2 = waiting. Alias packages read this.}

Faction Property SPP_SixPathsFaction Auto
{All six are in it (through their aliases). Used to tell a path from an enemy.}

ObjectReference Property SPP_HomeMarker Auto
{XMarkerHeading in the home cell. Dismissed paths are sent back here.}

Message Property SPP_MsgRecruited Auto
{Optional. "The Six Paths answer your will."}

Spell[] Property CommandPowers Auto
{Obito's lesser powers (Command, Summon, Release). Given to the player when the quest starts.}

Float Property FormationRadius = 220.0 Auto
{How far behind the player the paths appear when summoned.}

Float Property ShareTargetCooldown = 2.0 Auto
{Seconds between shared-vision target calls, so OnHit spam cannot flood the VM.}

Int Property STATE_HOME = 0 AutoReadOnly
Int Property STATE_FOLLOW = 1 AutoReadOnly
Int Property STATE_WAIT = 2 AutoReadOnly

Actor LastSharedTarget
Float LastShareTime

Event OnInit()
	GivePowers()
EndEvent

; ---------------------------------------------------------------------------
; Queries
; ---------------------------------------------------------------------------

Bool Function IsRecruited()
	Return SPP_PathsState.GetValueInt() != STATE_HOME
EndFunction

Bool Function IsPath(Actor akActor)
	Return akActor && akActor.IsInFaction(SPP_SixPathsFaction)
EndFunction

; ---------------------------------------------------------------------------
; Group commands
; ---------------------------------------------------------------------------

; Recruit all six at once. Called from the recruit dialogue (any path) or the Obito command power.
Function RecruitAll()
	If IsRecruited()
		Return
	EndIf
	Int i = 0
	While i < Paths.Length
		Actor path = Paths[i].GetActorReference()
		If path
			path.SetPlayerTeammate(true, true)
			path.SetRelationshipRank(PlayerRef, 3)
			path.IgnoreFriendlyHits(true)
		EndIf
		i += 1
	EndWhile
	SetGroupState(STATE_FOLLOW)
	If SPP_MsgRecruited
		SPP_MsgRecruited.Show()
	EndIf
EndFunction

; Release all six. They return to the home cell and stop being teammates.
Function DismissAll()
	If !IsRecruited()
		Return
	EndIf
	Int i = 0
	While i < Paths.Length
		Actor path = Paths[i].GetActorReference()
		If path
			path.SetPlayerTeammate(false)
			path.StopCombat()
		EndIf
		i += 1
	EndWhile
	SetGroupState(STATE_HOME)
	If SPP_HomeMarker
		MoveAllToFormation(SPP_HomeMarker)
	EndIf
EndFunction

Function FollowAll()
	If IsRecruited()
		SetGroupState(STATE_FOLLOW)
	EndIf
EndFunction

Function WaitAll()
	If IsRecruited()
		SetGroupState(STATE_WAIT)
	EndIf
EndFunction

; Follow <-> wait toggle for the command power.
Function ToggleFollowWait()
	If SPP_PathsState.GetValueInt() == STATE_FOLLOW
		WaitAll()
	Else
		FollowAll()
	EndIf
EndFunction

; Pull every path to the player in a fan behind them, then resume following.
Function SummonAll()
	If !IsRecruited()
		Return
	EndIf
	MoveAllToFormation(PlayerRef)
	SetGroupState(STATE_FOLLOW)
EndFunction

; ---------------------------------------------------------------------------
; Shared vision: when one path is attacked, the idle ones turn on the attacker.
; Called by SPP_PathAliasScript.
; ---------------------------------------------------------------------------

Function OnPathAttacked(Actor akPath, Actor akAggressor)
	If !akAggressor || akAggressor == PlayerRef || IsPath(akAggressor) || akAggressor.IsPlayerTeammate()
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If akAggressor == LastSharedTarget && now - LastShareTime < ShareTargetCooldown
		Return
	EndIf
	LastSharedTarget = akAggressor
	LastShareTime = now

	Int i = 0
	While i < Paths.Length
		Actor path = Paths[i].GetActorReference()
		If path && path != akPath && path.Is3DLoaded() && !path.IsDead() && !path.IsInCombat()
			path.StartCombat(akAggressor)
		EndIf
		i += 1
	EndWhile
EndFunction

; ---------------------------------------------------------------------------
; Upkeep. Called by SPP_PlayerAliasScript.
; ---------------------------------------------------------------------------

; After a load: re-apply teammate status in case another mod cleared it.
Function Maintenance()
	GivePowers()
	FillNewPaths()
	If IsRecruited()
		Int i = 0
		While i < Paths.Length
			Actor path = Paths[i].GetActorReference()
			If path && !path.IsPlayerTeammate()
				path.SetPlayerTeammate(true, true)
			EndIf
			i += 1
		EndWhile
	EndIf
	EvaluateAll()
EndFunction

; After the player changes location: bring along any following path left in another cell.
Function CatchUp()
	If SPP_PathsState.GetValueInt() != STATE_FOLLOW
		Return
	EndIf
	Cell playerCell = PlayerRef.GetParentCell()
	Int i = 0
	While i < Paths.Length
		Actor path = Paths[i].GetActorReference()
		If path && !path.IsDead() && path.GetParentCell() != playerCell
			PlaceInFormation(path, i, PlayerRef)
		EndIf
		i += 1
	EndWhile
EndFunction

; ---------------------------------------------------------------------------
; Internals
; ---------------------------------------------------------------------------

Function GivePowers()
	Int i = 0
	While i < CommandPowers.Length
		If CommandPowers[i] && !PlayerRef.HasSpell(CommandPowers[i])
			PlayerRef.AddSpell(CommandPowers[i], false)
		EndIf
		i += 1
	EndWhile
	; "Edo Tensei: <path>" summon spells, from form list SPP_SummonSpells (0x81E). Looked up by ID
	; rather than a property, because property values are already baked into older saves.
	FormList summons = Game.GetFormFromFile(0x81E, "SixPathsOfPain.esp") as FormList
	If summons
		i = 0
		While i < summons.GetSize()
			Spell summon = summons.GetAt(i) as Spell
			If summon && !PlayerRef.HasSpell(summon)
				PlayerRef.AddSpell(summon)
			EndIf
			i += 1
		EndWhile
	EndIf
EndFunction

; A running quest never re-fills its aliases, so paths added in a later version of the plugin
; would stay empty in existing saves. SPP_PathRefs (0x82A) lists each path's placed actor in
; alias order (a non-actor placeholder where that path doesn't exist yet).
Function FillNewPaths()
	FormList pathRefs = Game.GetFormFromFile(0x82A, "SixPathsOfPain.esp") as FormList
	If !pathRefs
		Return
	EndIf
	Int i = 0
	While i < Paths.Length && i < pathRefs.GetSize()
		Actor path = pathRefs.GetAt(i) as Actor
		If path && !Paths[i].GetReference()
			Paths[i].ForceRefTo(path)
			If IsRecruited()
				path.SetPlayerTeammate(true, true)
			EndIf
		EndIf
		i += 1
	EndWhile
EndFunction

Function SetGroupState(Int aiState)
	SPP_PathsState.SetValueInt(aiState)
	EvaluateAll()
EndFunction

Function EvaluateAll()
	Int i = 0
	While i < Paths.Length
		Actor path = Paths[i].GetActorReference()
		If path
			path.EvaluatePackage()
		EndIf
		i += 1
	EndWhile
EndFunction

Function MoveAllToFormation(ObjectReference akAnchor)
	Int i = 0
	While i < Paths.Length
		Actor path = Paths[i].GetActorReference()
		If path && !path.IsDead()
			PlaceInFormation(path, i, akAnchor)
		EndIf
		i += 1
	EndWhile
EndFunction

; Six slots on an arc behind the anchor, 30 degrees apart.
Function PlaceInFormation(Actor akPath, Int aiSlot, ObjectReference akAnchor)
	Float angle = akAnchor.GetAngleZ() + 180.0 + (aiSlot - 2.5) * 30.0
	Float offsetX = FormationRadius * Math.Sin(angle)
	Float offsetY = FormationRadius * Math.Cos(angle)
	akPath.MoveTo(akAnchor, offsetX, offsetY, 0.0)
EndFunction

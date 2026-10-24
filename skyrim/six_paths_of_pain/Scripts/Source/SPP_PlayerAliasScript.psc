Scriptname SPP_PlayerAliasScript extends ReferenceAlias
{On the quest's Player alias. Load-game upkeep and catch-up after the player changes location.}

Float Property CatchUpDelay = 2.0 Auto
{Give the engine's own follower travel a moment before teleporting stragglers.}

SPP_SixPathsQuestScript Function Master()
	Return GetOwningQuest() as SPP_SixPathsQuestScript
EndFunction

Event OnPlayerLoadGame()
	Master().Maintenance()
EndEvent

Event OnLocationChange(Location akOldLoc, Location akNewLoc)
	RegisterForSingleUpdate(CatchUpDelay)
EndEvent

Event OnUpdate()
	Master().CatchUp()
EndEvent

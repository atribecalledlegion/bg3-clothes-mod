Scriptname SNE_WarlockQuest extends Quest
{Shinobi Enemies, warlocks: the necromancer's phylactery (lore: a lich's soul in a vessel; Naruto: Orochimaru's
immortality). A strong necromancer's black soul gem lies in its lair; if it is still lying there when the
necromancer dies, the necromancer rises from it 4 s later (once, SNE_WarlockRevivedFaction) and the gem is used up.
Pick the gem up (or it is gone) and the necromancer stays dead.}

Actor Property PlayerRef Auto
Faction Property RevivedFaction Auto
EffectShader Property ReanimateFX Auto
GlobalVariable Property TacticsOn Auto

Float Property ReviveDelay = 4.0 AutoReadOnly

Actor PendingActor
ObjectReference PendingGem
Float PendingAt
Bool Explained

Function NecromancerFell(Actor a, ObjectReference gem)
	If !a || TacticsOn.GetValue() < 0.5 || a.IsInFaction(RevivedFaction)
		Return
	EndIf
	If !gem || !gem.GetParentCell() || gem.IsDisabled()
		Debug.Trace("SNE warlock: necromancer " + a + " dies for good: its phylactery is gone")
		Return
	EndIf
	If PendingActor
		Return    ; one at a time
	EndIf
	PendingActor = a
	PendingGem = gem
	PendingAt = Utility.GetCurrentRealTime() + ReviveDelay
	ReanimateFX.Play(gem, ReviveDelay + 1.0)
	Debug.Trace("SNE warlock: necromancer " + a + " fell; its phylactery " + gem + " pulls the soul back (" + ReviveDelay + " s)")
	RegisterForSingleUpdate(0.5)
EndFunction

Event OnUpdate()
	If !PendingActor
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If PendingAt > now + 30.0 || !PendingActor.Is3DLoaded()
		PendingActor = None    ; stale (a reload) or unloaded
		Return
	EndIf
	If now < PendingAt
		RegisterForSingleUpdate(0.5)
		Return
	EndIf
	Actor a = PendingActor
	ObjectReference gem = PendingGem
	PendingActor = None
	PendingGem = None
	If !gem.GetParentCell() || gem.IsDisabled()
		Debug.Trace("SNE warlock: phylactery taken in time, " + a + " stays dead")
		Return
	EndIf
	a.AddToFaction(RevivedFaction)
	a.MoveTo(gem)
	a.Resurrect()
	gem.Delete()
	ReanimateFX.Play(a, 6.0)
	a.DamageActorValue("Health", a.GetBaseActorValue("Health") * 0.4)
	a.StartCombat(PlayerRef)
	If !Explained
		Explained = True
		Debug.Notification("The necromancer rises again from a soul gem hidden in its lair.")
	EndIf
	Debug.Trace("SNE warlock: PHYLACTERY - necromancer " + a + " rises again at " + ((a.GetActorValuePercentage("Health") * 100.0) as Int) + "%")
EndEvent

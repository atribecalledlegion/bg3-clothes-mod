Scriptname SNJ_BlackFrostEffect extends ActiveMagicEffect
{Black Frost, Serana's left Mangekyo eye (her answer to Amaterasu). The frost starts in the victim's blood (the spell's
paralysis), burns them from the inside (the spell's damage over time, no resistance: it never thaws) and spreads to
enemies standing beside them, a few hops per gaze (SNJ_QuestScript.TakeFrostHop).}

SNJ_QuestScript Property Master Auto
Spell Property BlackFrostSpell Auto
EffectShader Property FrostShader Auto
Float Property SpreadReach = 260.0 AutoReadOnly

Actor Victim
Actor Caster

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Victim = akTarget
	Caster = akCaster
	FrostShader.Play(Victim, 12.0)
	RegisterForSingleUpdate(2.0)
EndEvent

Event OnUpdate()
	If !Victim || Victim.IsDead() || !Caster
		Return
	EndIf
	Actor next = Game.FindRandomActorFromRef(Victim, SpreadReach)
	If next && next != Victim && next != Caster && !next.IsDead() && !next.IsPlayerTeammate() && next != Game.GetPlayer() && next.IsHostileToActor(Game.GetPlayer()) && !next.HasMagicEffect(GetBaseObject())
		If Master.TakeFrostHop()
			BlackFrostSpell.Cast(Caster, next)
			Debug.Trace("SNJ: Black Frost spreads from " + Victim.GetDisplayName() + " to " + next.GetDisplayName())
		EndIf
	EndIf
	RegisterForSingleUpdate(2.0)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	FrostShader.Stop(akTarget)
EndEvent

Scriptname SPP_PathAliasScript extends ReferenceAlias
{On each of the six path aliases. Reports hits to the master (shared vision)
and reforms the body after bleedout (Edo Tensei). Mark the alias Essential.}

Float Property ReformDelay = 6.0 Auto
{Seconds in bleedout before the Edo Tensei body reforms.}

EffectShader Property SPP_EdoReformFX Auto
{Optional. Played while the body reforms (e.g. a grey ash/paper shader).}

SPP_SixPathsQuestScript Function Master()
	Return GetOwningQuest() as SPP_SixPathsQuestScript
EndFunction

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	Master().OnPathAttacked(GetActorReference(), akAggressor as Actor)
EndEvent

Event OnEnterBleedout()
	Actor path = GetActorReference()
	If SPP_EdoReformFX
		SPP_EdoReformFX.Play(path, ReformDelay)
	EndIf
	RegisterForSingleUpdate(ReformDelay)
EndEvent

Event OnUpdate()
	Actor path = GetActorReference()
	If path && !path.IsDead() && path.IsBleedingOut()
		path.RestoreActorValue("Health", path.GetBaseActorValue("Health"))
	EndIf
EndEvent

Scriptname CSHC_OpeningEffect extends ActiveMagicEffect
{Counter-Read opening on an enemy whose attack the player just blocked, parried or dodged. While it lasts, the
player's hits on this enemy deal bonus damage (CSHC_ReadPerk); the first one may stagger and ends the opening.
Perfect = the attack was read during Quick Reflexes slow time: bigger bonus, guaranteed stagger.}

Actor Property PlayerRef Auto
Bool Property Perfect Auto

Actor Target
Bool Finished = False

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Target = akTarget
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Finished = True    ; hit events can still arrive after the 2 s opening ends
EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If Finished || !Target || akAggressor != PlayerRef || abHitBlocked
		Return
	EndIf
	Finished = True
	If !Target.IsDead() && (Perfect || Utility.RandomInt(1, 100) <= 50)
		If Perfect
			Target.SetAnimationVariableFloat("staggerMagnitude", 1.0)
		Else
			Target.SetAnimationVariableFloat("staggerMagnitude", 0.6)
		EndIf
		Debug.SendAnimationEvent(Target, "staggerStart")
	EndIf
	Dispel()
EndEvent

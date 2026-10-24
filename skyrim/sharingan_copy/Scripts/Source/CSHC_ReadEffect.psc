Scriptname CSHC_ReadEffect extends ActiveMagicEffect
{Sharingan Read, on the player (hidden ability). Every melee hit the player takes or blocks is reported to the
quest, which builds Read stacks on that enemy.}

CSHC_CopyQuestScript Property Master Auto

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	Actor a = akAggressor as Actor
	If !a || akProjectile || !(akSource as Weapon)
		Return    ; melee only: spells, arrows and traps are not taijutsu
	EndIf
	Master.HitBy(a, abPowerAttack, abHitBlocked)
EndEvent

; Kamui travel needs a solid body (CSHC_KamuiQuestScript ends Kamui mode first).
Event OnSpellCast(Form akSpell)
	((Master as Quest) as CSHC_KamuiQuestScript).KamuiTravelCast(akSpell)
EndEvent

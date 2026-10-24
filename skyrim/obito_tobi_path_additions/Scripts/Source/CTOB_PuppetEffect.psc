Scriptname CTOB_PuppetEffect extends ActiveMagicEffect
{Genjutsu: Sharingan Puppet on the target: hands it to CTOB_GenjutsuQuestScript, which turns it and later releases it.}

Quest Property Master Auto
Actor Target

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Target = akTarget
	(Master as CTOB_GenjutsuQuestScript).BeginPuppet(akTarget)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	(Master as CTOB_GenjutsuQuestScript).EndPuppet(Target)
EndEvent

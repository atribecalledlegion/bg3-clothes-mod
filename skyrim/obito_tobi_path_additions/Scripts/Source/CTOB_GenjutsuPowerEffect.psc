Scriptname CTOB_GenjutsuPowerEffect extends ActiveMagicEffect
{Lesser powers: Mode 1 = Genjutsu: Sharingan (gaze), 2 = Genjutsu: Sharingan Puppet,
 3 = Preta Path: Absorption Seal, 4 = Preta Path: Chakra Absorption.}

Quest Property Master Auto
Int Property Mode Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	CTOB_GenjutsuQuestScript g = Master as CTOB_GenjutsuQuestScript
	If Mode == 1
		g.Gaze()
	ElseIf Mode == 2
		g.PuppetPower()
	ElseIf Mode == 3
		g.PretaSeal()
	Else
		g.PretaDrain()
	EndIf
EndEvent

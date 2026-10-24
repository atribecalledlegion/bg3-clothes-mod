Scriptname SPP_ObitoCommandEffect extends ActiveMagicEffect
{Obito's command powers. One magic effect per command, each with its own Command value:
  0 = "Six Paths: Command"  - recruit all six if not yet recruited, otherwise toggle follow/wait
  1 = "Six Paths: Summon"   - pull all six to the player in formation
  2 = "Six Paths: Release"  - dismiss all six back to the home cell}

SPP_SixPathsQuestScript Property Master Auto
Int Property Command = 0 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If akCaster != Master.PlayerRef
		Return
	EndIf
	If Command == 0
		If Master.IsRecruited()
			Master.ToggleFollowWait()
		Else
			Master.RecruitAll()
		EndIf
	ElseIf Command == 1
		Master.SummonAll()
	ElseIf Command == 2
		Master.DismissAll()
	EndIf
EndEvent

Scriptname SNJ_DimhollowEffect extends ActiveMagicEffect
{Dimhollow, Serana's right Mangekyo eye: what was done to her becomes her power. A seal in ice, out of time.
- An enemy that is already broken (low health or far weaker than her, never a boss) shatters into ice.
- Any other enemy is sealed in stasis: frozen (paralysed) and untouchable for a few seconds, out of the fight.
- Cast on herself or a friend, it is the protection her mother gave her: a brief untouchable seal, with some healing.}

SNJ_QuestScript Property Master Auto
Spell Property StasisParalysis Auto
EffectShader Property IceShader Auto
EffectShader Property BreakShader Auto
Activator Property IcePile Auto
Float Property StasisSeconds = 6.0 AutoReadOnly
Float Property ProtectSeconds = 3.0 AutoReadOnly

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If !akTarget || akTarget.IsDead()
		Return
	EndIf
	If Master.IsFriend(akTarget)
		Protect(akTarget)
	ElseIf Master.Shatterable(akCaster, akTarget)
		Shatter(akCaster, akTarget)
	Else
		Stasis(akCaster, akTarget)
	EndIf
EndEvent

Function Protect(Actor a)
	IceShader.Play(a, ProtectSeconds)
	a.SetGhost(True)
	a.RestoreActorValue("Health", 0.2 * a.GetBaseActorValue("Health"))
	Debug.Trace("SNJ: Dimhollow protects " + a.GetDisplayName())
	Utility.Wait(ProtectSeconds)
	a.SetGhost(False)
	BreakShader.Play(a, 1.0)
EndFunction

Function Shatter(Actor caster, Actor a)
	IceShader.Play(a, 2.0)
	StasisParalysis.Cast(caster, a)
	Debug.Trace("SNJ: Dimhollow shatters " + a.GetDisplayName())
	Utility.Wait(1.2)
	If a.IsDead()
		Return
	EndIf
	a.Kill(caster)
	BreakShader.Play(a, 1.5)
	a.SetCriticalStage(a.CritStage_DisintegrateStart)
	a.AttachAshPile(IcePile)
	Utility.Wait(1.2)
	a.SetAlpha(0.0, True)
	a.SetCriticalStage(a.CritStage_DisintegrateEnd)
EndFunction

Function Stasis(Actor caster, Actor a)
	IceShader.Play(a, StasisSeconds)
	StasisParalysis.Cast(caster, a)
	a.SetGhost(True)
	Master.NoteSealed(a)
	Debug.Trace("SNJ: Dimhollow seals " + a.GetDisplayName() + " for " + (StasisSeconds as Int) + " s")
	Utility.Wait(StasisSeconds)
	a.SetGhost(False)
	Master.NoteSealed(None)
	BreakShader.Play(a, 1.0)
EndFunction

Scriptname SNE_AsheShutdown extends ActiveMagicEffect
{Shinobi Enemies: Ashe is a soul-gem-powered automaton (canon: a bolt of pure lightning once forced her into a
complete shutdown). On top of the -25 shock resistance in the same ability, a strong shock hit can glitch her:
1.5 s frozen and staggered, with one of her own "system failure" lines. 35% per shock hit, at most every 20 s.
Off: SNE_CompanionTactics 0. Needs SKSE (Spell effects, MagicEffect.GetResistance).}

Actor Property PlayerRef Auto
GlobalVariable Property TacticsOn Auto
Topic[] Property ShutdownLines Auto

Float Property GlitchChance = 0.35 AutoReadOnly
Float Property GlitchCooldown = 20.0 AutoReadOnly
Float Property GlitchSeconds = 1.5 AutoReadOnly

Actor Me
Float NextGlitch
Bool Glitching

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If Glitching || !Me || Me.IsDead() || TacticsOn.GetValue() < 0.5 || !IsShock(akSource)
		Return
	EndIf
	Float n = Utility.GetCurrentRealTime()
	If NextGlitch > n + GlitchCooldown + 1.0
		NextGlitch = 0.0
	EndIf
	If n < NextGlitch || Utility.RandomFloat() >= GlitchChance
		Return
	EndIf
	NextGlitch = n + GlitchCooldown
	Glitching = True
	If ShutdownLines && ShutdownLines.Length > 0
		Me.Say(ShutdownLines[Utility.RandomInt(0, ShutdownLines.Length - 1)])
	EndIf
	Me.SetAnimationVariableFloat("staggerMagnitude", 1.0)
	Debug.SendAnimationEvent(Me, "staggerStart")
	Me.SetRestrained(True)
	Debug.Trace("SNE companion: Ashe SHUTDOWN glitch from " + akSource + " (by " + akAggressor + ")")
	Utility.Wait(GlitchSeconds)
	Me.SetRestrained(False)
	Glitching = False
EndEvent

Bool Function IsShock(Form src)
	Spell s = src as Spell
	If !s
		Return False
	EndIf
	Int i = 0
	Int n = s.GetNumEffects()
	While i < n
		MagicEffect m = s.GetNthEffectMagicEffect(i)
		If m && m.GetResistance() == "ElectricResist"
			Return True
		EndIf
		i += 1
	EndWhile
	Return False
EndFunction

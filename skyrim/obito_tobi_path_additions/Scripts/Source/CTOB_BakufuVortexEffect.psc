Scriptname CTOB_BakufuVortexEffect extends ActiveMagicEffect
{Katon: Bakufu Ranbu, on every actor the vortex catches. Canon: fire breathed out and spun into a whirlwind by Kamui.
The heat leaves them Exposed (ExposedSpell, as the Rinnegan uses it). With the Mangekyou awakened (Kamui known),
the Kamui whirlwind also drags everyone caught towards the middle of the group: each is pushed away from a marker
placed just beyond them, on the far side from the centre.}

Spell Property ExposedSpell Auto
Spell Property KamuiEthereal Auto
{aaaTobiBecomeEthereal: known once the Tobi path's Mangekyou is awakened.}

Float Property GatherRadius = 450.0 AutoReadOnly     ; others caught within this of me count towards the centre
Float Property MinPull = 60.0 AutoReadOnly          ; closer than this to the centre: no pull
Float Property ForcePerUnit = 0.0125 AutoReadOnly   ; push force per unit of distance to the centre
Float Property MaxForce = 5.0 AutoReadOnly
Float Property MinForce = 1.5 AutoReadOnly

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If !akTarget || !akCaster || akTarget == akCaster || akTarget.IsDead() || akTarget.IsPlayerTeammate()
		Return
	EndIf
	ExposedSpell.Cast(akCaster, akTarget)
	If !KamuiEthereal || !akCaster.HasSpell(KamuiEthereal)
		Return
	EndIf
	Utility.Wait(0.1)                  ; let the rest of the group receive the effect
	MagicEffect me = GetBaseObject()
	Float cx = 0.0
	Float cy = 0.0
	Int count = 0
	Cell c = akTarget.GetParentCell()
	If !c
		Return
	EndIf
	Int n = c.GetNumRefs(62)
	Int i = 0
	While i < n
		Actor x = c.GetNthRef(i, 62) as Actor
		If x && !x.IsDead() && x.HasMagicEffect(me) && x.GetDistance(akTarget) <= GatherRadius
			cx += x.GetPositionX()
			cy += x.GetPositionY()
			count += 1
		EndIf
		i += 1
	EndWhile
	If count < 2
		Return
	EndIf
	cx /= count
	cy /= count
	Float dx = akTarget.GetPositionX() - cx
	Float dy = akTarget.GetPositionY() - cy
	Float d = Math.Sqrt(dx * dx + dy * dy)
	If d < MinPull || akTarget.IsDead()
		Return
	EndIf
	ObjectReference m = akTarget.PlaceAtMe(Game.GetForm(0x0000003B))     ; XMarker
	If !m
		Return
	EndIf
	m.SetPosition(akTarget.GetPositionX() + dx / d * 100.0, akTarget.GetPositionY() + dy / d * 100.0, akTarget.GetPositionZ())
	Float force = d * ForcePerUnit
	If force > MaxForce
		force = MaxForce
	ElseIf force < MinForce
		force = MinForce
	EndIf
	m.PushActorAway(akTarget, force)
	Debug.Trace("CTOB bakufu: pulled " + akTarget + " " + d + " units, force " + force)
	m.Delete()
EndEvent

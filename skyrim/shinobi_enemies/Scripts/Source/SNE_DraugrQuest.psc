Scriptname SNE_DraugrQuest extends Quest
{Shinobi Enemies, draugr: things that must outlive a draugr's death (its SNE_DraugrBrain effect ends when it dies).
- Life force: a fallen draugr's soul leaves the body (Soul Trap shader) and heals the nearest living lord or Dragon
  Priest within 2500 by 10% of its health.
- Edo Tensei: a fallen lord may rise again after 3.5 s (15%, names with "Death" 20%), once (SNE_DraugrRevivedFaction),
  at half health, with the reanimation glow. Not when the body was cleansed (fire or Restoration killing blow).}

Actor Property PlayerRef Auto
Faction Property RevivedFaction Auto
Faction Property DraugrFaction Auto
Race Property DragonPriestRace Auto
EffectShader Property ReanimateFX Auto
EffectShader Property SoulLeaveFX Auto
EffectShader Property SoulTakeFX Auto
GlobalVariable Property TacticsOn Auto

Float Property ReviveChance = 0.15 AutoReadOnly
Float Property ReviveChanceDeath = 0.2 AutoReadOnly
Float Property ReviveDelay = 3.5 AutoReadOnly

Actor[] Pending
Float[] PendingAt

Function DraugrFell(Actor a, Bool isLord, Bool cleansed)
	If !a || TacticsOn.GetValue() < 0.5
		Return
	EndIf
	LifeForce(a)
	If !isLord
		Return
	EndIf
	If a.IsInFaction(RevivedFaction)
		Debug.Trace("SNE draugr: lord " + a + " " + a.GetDisplayName() + " fell for good (already rose once)")
		Return
	EndIf
	If cleansed
		Debug.Trace("SNE draugr: lord " + a + " " + a.GetDisplayName() + " CLEANSED (fire or Restoration killing blow): no revival")
		Return
	EndIf
	Float chance = ReviveChance
	If StringUtil.Find(a.GetDisplayName(), "Death") >= 0
		chance = ReviveChanceDeath
	EndIf
	If Utility.RandomFloat() >= chance
		Debug.Trace("SNE draugr: lord " + a + " " + a.GetDisplayName() + " stays down (" + ((chance * 100.0) as Int) + "% revival roll failed)")
		Return
	EndIf
	QueueRevive(a)
EndFunction

Function LifeForce(Actor dead)
	Cell c = dead.GetParentCell()
	If !c
		Return
	EndIf
	Actor master = None
	Float best = 2500.0
	Int n = c.GetNumRefs(43)
	If n > 80
		n = 80
	EndIf
	Int i = 0
	While i < n
		Actor a = c.GetNthRef(i, 43) as Actor
		If a && a != dead && !a.IsDead() && !a.IsDisabled() && (a.GetRace() == DragonPriestRace || (a.IsInFaction(DraugrFaction) && StringUtil.Find(a.GetDisplayName(), "Lord") >= 0))
			Float d = a.GetDistance(dead)
			If d < best
				best = d
				master = a
			EndIf
		EndIf
		i += 1
	EndWhile
	If !master
		Return
	EndIf
	SoulLeaveFX.Play(dead, 2.0)
	SoulTakeFX.Play(master, 1.5)
	If !master.IsInKillMove() && !master.IsBleedingOut() && master.GetActorValuePercentage("Health") > 0.05    ; never heal the dying (killmove bug, 2026-10-17)
		master.RestoreActorValue("Health", master.GetBaseActorValue("Health") * 0.1)
	EndIf
	Debug.Trace("SNE draugr: " + dead + "'s life force flows to " + master + " " + master.GetDisplayName() + ", now " + ((master.GetActorValuePercentage("Health") * 100.0) as Int) + "%")
EndFunction

Function QueueRevive(Actor a)
	If !Pending
		Pending = new Actor[8]
		PendingAt = new Float[8]
	EndIf
	Int i = 0
	While i < 8
		If !Pending[i]
			Pending[i] = a
			PendingAt[i] = Utility.GetCurrentRealTime() + ReviveDelay
			ReanimateFX.Play(a, ReviveDelay + 1.0)
			Debug.Trace("SNE draugr: lord " + a + " " + a.GetDisplayName() + " is stirring (Edo Tensei in " + ReviveDelay + " s)")
			RegisterForSingleUpdate(0.5)
			Return
		EndIf
		i += 1
	EndWhile
EndFunction

Event OnUpdate()
	If !Pending
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	Bool waiting = False
	Int i = 0
	While i < 8
		Actor a = Pending[i]
		If a
			If PendingAt[i] > now + 30.0 || !a.Is3DLoaded() || a.IsDisabled()
				Pending[i] = None    ; stale (a reload) or gone
			ElseIf now >= PendingAt[i]
				Pending[i] = None
				Rise(a)
			Else
				waiting = True
			EndIf
		EndIf
		i += 1
	EndWhile
	If waiting
		RegisterForSingleUpdate(0.5)
	EndIf
EndEvent

Function Rise(Actor a)
	If !a.IsDead()
		Return
	EndIf
	a.AddToFaction(RevivedFaction)
	a.Resurrect()
	ReanimateFX.Play(a, 6.0)
	a.DamageActorValue("Health", a.GetBaseActorValue("Health") * 0.5)
	a.StartCombat(PlayerRef)
	Debug.Trace("SNE draugr: EDO TENSEI - " + a + " " + a.GetDisplayName() + " rises again at " + ((a.GetActorValuePercentage("Health") * 100.0) as Int) + "%")
EndFunction

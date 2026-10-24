Scriptname CTOB_KannabiWatchEffect extends ActiveMagicEffect
{Hidden "Kannabi Bridge" watcher, on the player while on the Tobi path without Hashirama's cells.
The first time a hit leaves the player below the health threshold: fade to black, the boulder scene,
wake fully healed by the Naka Shrine exit with the Hashirama Cell Healing Factor. Happens once.}

Spell Property HealingFactor Auto
Spell Property WatchAbility Auto
{This effect's own ability, removed when the event is over.}
ObjectReference Property WakeSpot Auto
{Naka Shrine's inner door. The player is placed a little inside it, where the door normally drops you.}
GlobalVariable Property KannabiDone Auto
Float Property HealthThreshold = 0.2 Auto
Float Property WakeOffsetX = -44.0 Auto
Float Property WakeOffsetY = 241.0 Auto

Bool Busy = False

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	Actor p = GetTargetActor()
	If Busy || KannabiDone.GetValue() != 0 || p.IsDead() || p.GetActorValuePercentage("Health") >= HealthThreshold
		Return
	EndIf
	Busy = True
	KannabiDone.SetValue(1)
	p.RestoreActorValue("Health", 100000)
	Game.DisablePlayerControls()
	Game.FadeOutGame(True, True, 0.0, 1.0)
	Utility.Wait(1.0)
	Debug.MessageBox("The ground gives way. A boulder crushes the right side of your body...\nEverything goes dark.")
	p.StopCombat()
	p.MoveTo(WakeSpot, WakeOffsetX, WakeOffsetY, 0.0)
	p.AddSpell(HealingFactor, False)
	p.RestoreActorValue("Health", 100000)
	Utility.Wait(1.0)
	Game.FadeOutGame(False, True, 0.5, 2.0)
	Game.EnablePlayerControls()
	Debug.MessageBox("You wake deep beneath the Naka Shrine. White, living flesh holds your shattered body together.\n\nMadara: \"Welcome to the world of the living, Obito. Hashirama's cells... you belong to me now.\"")
	Debug.Notification("Hashirama Cell Healing Factor gained.")
	p.RemoveSpell(WatchAbility)
EndEvent

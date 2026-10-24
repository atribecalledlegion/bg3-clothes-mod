Scriptname CTOB_CellCombatEffect extends ActiveMagicEffect
{Hashirama Cells: Combat Regeneration (on CTOB_CellCombatAbility, given with the Hashirama Cell Healing Factor).
The cells heal directly, so hits do not pause the healing and the combat regen penalty does not apply.
- Chakra regeneration: in combat, heals every second, faster the lower your health, scaled by level tier.
- Cell Activation: a hit that leaves you below 30% health heals 40% at once plus 20% over 4 s. 60 s cooldown.
- Wound regrowth: a single hit worth over 15% of max health has half of it healed back over 4 s.
All healing costs Magicka (MagickaPerHP); without chakra the cells cannot heal.
Cell overgrowth (Danzo, Yamato): healing builds strain, which drains away over time. Heal more than StrainLimit
times your max health in a short time and the cells run wild: slowed, and no cell healing for OvergrowthSeconds.}

Spell Property OvergrowthSpell Auto

Float Property TickSeconds = 1.0 AutoReadOnly
; fraction of max health per second at the top tier: RegenBase + RegenLow * (fraction missing)
Float Property RegenBase = 0.025 AutoReadOnly
Float Property RegenLow = 0.03 AutoReadOnly
Float Property TierLow = 0.5 AutoReadOnly        ; levels 1-15
Float Property TierMid = 0.75 AutoReadOnly       ; levels 16-40, 41+ is 1.0
Float Property MagickaPerHP = 0.4 AutoReadOnly
Float Property ActivateBelow = 0.30 AutoReadOnly
Float Property ActivateHeal = 0.40 AutoReadOnly
Float Property ActivateRegen = 0.20 AutoReadOnly
Float Property ActivateMinHeal = 0.10 AutoReadOnly   ; not enough chakra for this much: no activation, no cooldown
Int Property ActivateCooldown = 60 AutoReadOnly
Float Property BigHit = 0.15 AutoReadOnly
Float Property RegrowShare = 0.5 AutoReadOnly
Float Property SpreadTicks = 4.0 AutoReadOnly         ; regrowth and the activation regen are spread over this many ticks
Float Property StrainLimit = 1.5 AutoReadOnly
Float Property StrainDecay = 0.05 AutoReadOnly        ; per second: StrainLimit over 30 s
Float Property StrainWarn = 0.75 AutoReadOnly         ; of StrainLimit
Int Property OvergrowthSeconds = 12 AutoReadOnly

Actor Me
Float LastHealth = 0.0
Float Pool = 0.0          ; health still to heal from regrowth / activation
Float PoolRate = 0.0      ; per tick
Float Strain = 0.0        ; in max-health units
Bool Warned = False
Int Cooldown = 0
Int Overgrown = 0

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Me = akTarget
	LastHealth = Me.GetActorValue("Health")
	RegisterForSingleUpdate(TickSeconds)
EndEvent

Float Function MaxHealth()
	Float pct = Me.GetActorValuePercentage("Health")
	If pct > 0.01
		Return Me.GetActorValue("Health") / pct
	EndIf
	Return Me.GetBaseActorValue("Health")
EndFunction

Float Function TierMult()
	Int lv = Me.GetLevel()
	If lv <= 15
		Return TierLow
	ElseIf lv <= 40
		Return TierMid
	EndIf
	Return 1.0
EndFunction

; Heals up to hp, paid with Magicka. Returns what was healed.
Float Function Heal(Float hp, Float maxHP)
	Float missing = maxHP - Me.GetActorValue("Health")
	If hp > missing
		hp = missing
	EndIf
	Float affordable = Me.GetActorValue("Magicka") / MagickaPerHP
	If hp > affordable
		hp = affordable
	EndIf
	If hp < 0.5
		Return 0.0
	EndIf
	Me.DamageActorValue("Magicka", hp * MagickaPerHP)
	Me.RestoreActorValue("Health", hp)
	Strain += hp / maxHP
	If Strain >= StrainLimit
		Overgrow()
	ElseIf !Warned && Strain >= StrainLimit * StrainWarn
		Warned = True
		Notify("Bark creeps over your skin. Hashirama's cells are straining.")
	EndIf
	Return hp
EndFunction

Function Overgrow()
	Overgrown = OvergrowthSeconds
	Strain = 0.0
	Warned = False
	Pool = 0.0
	OvergrowthSpell.Cast(Me, Me)
	Debug.Trace("CTOB cells: overgrowth")
	Notify("Hashirama's cells run wild! Your body stiffens and the healing stops.")
EndFunction

Function AddPool(Float hp)
	Pool += hp
	PoolRate = Pool / SpreadTicks
EndFunction

Function Notify(String msg)
	If Me == Game.GetPlayer()
		Debug.Notification(msg)
	EndIf
EndFunction

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If !Me || Me.IsDead()
		Return
	EndIf
	Float maxHP = MaxHealth()
	Float now = Me.GetActorValue("Health")
	Float dmg = LastHealth - now
	LastHealth = now
	If Overgrown > 0
		Return
	EndIf
	If dmg >= maxHP * BigHit
		AddPool(dmg * RegrowShare)
		Debug.Trace("CTOB cells: regrowth " + dmg * RegrowShare)
	EndIf
	If Cooldown == 0 && now < maxHP * ActivateBelow && Me.GetActorValue("Magicka") / MagickaPerHP >= maxHP * ActivateMinHeal
		Cooldown = ActivateCooldown
		Float healed = Heal(maxHP * ActivateHeal, maxHP)
		If Overgrown == 0
			AddPool(maxHP * ActivateRegen)
		EndIf
		LastHealth = Me.GetActorValue("Health")
		Debug.Trace("CTOB cells: activation " + healed)
		Notify("Cell Activation! Hashirama's cells surge through your wounds.")
	EndIf
EndEvent

Event OnUpdate()
	If !Me
		Return
	EndIf
	If !Me.IsDead()
		Tick()
	EndIf
	RegisterForSingleUpdate(TickSeconds)
EndEvent

Function Tick()
	Float maxHP = MaxHealth()
	Strain -= StrainDecay * TickSeconds
	If Strain < 0.0
		Strain = 0.0
	EndIf
	If Warned && Strain < StrainLimit * StrainWarn * 0.5
		Warned = False
	EndIf
	If Cooldown > 0
		Cooldown -= 1
		If Cooldown == 0
			Notify("Cell Activation is ready.")
		EndIf
	EndIf
	If Overgrown > 0
		Overgrown -= 1
		If Overgrown == 0
			Notify("The cells settle. Healing resumes.")
		EndIf
	Else
		Float hp = 0.0
		If Me.IsInCombat()
			Float missing = 1.0 - Me.GetActorValuePercentage("Health")
			If missing > 0.0
				hp = maxHP * (RegenBase + RegenLow * missing) * TierMult() * TickSeconds
			EndIf
		EndIf
		If Pool > 0.0
			Float part = PoolRate
			If part > Pool
				part = Pool
			EndIf
			Pool -= part
			hp += part
		EndIf
		If hp > 0.0
			Heal(hp, maxHP)
		EndIf
	EndIf
	LastHealth = Me.GetActorValue("Health")
EndFunction

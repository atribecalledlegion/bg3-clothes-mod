Scriptname CTOB_GenjutsuQuestScript extends Quest
{Obito's Sharingan genjutsu (second script on CTOB_Quest). Canon: Obito's genjutsu comes from the ordinary Sharingan
and is about control: he held the Nine-Tails and the Fourth Mizukage Yagura (a perfect jinchuriki) under his will,
and Yagura died from the after-effects. Both powers need the Sharingan open and target the actor you aim at.
 A "Genjutsu: Sharingan" (lesser power): eye contact. An enemy that is looking at you freezes where it stands.
 B "Genjutsu: Sharingan Puppet" (lesser power): one humanoid becomes your puppet and fights for you. Casting it at
   your puppet releases it. On release the after-effect hits: half its full health as damage, which kills a
   weakened puppet (not essential actors).
 C Beast domination (B's Mangekyou tier): with the Mangekyou awakened, B also takes creatures (trolls, giants,
   dragons...), for a shorter time and more chakra. Dwarven machines have no mind to seize; Uchiha bosses resist.
Rinnegan: Preta Path (Gakido), the Path of Pain the Uchiha Clan's Rinnegan lacks (canon: the Preta body absorbs any
chakra technique fired at it, and drains chakra from whoever it grabs):
 D "Preta Path: Absorption Seal" (lesser power): 8 s of full spell absorption; absorbed spells refill your Magicka.
 E "Preta Path: Chakra Absorption" (lesser power): drain the enemy in front of you; drained dry, it collapses.}

Float Property GazeRange = 2500.0 AutoReadOnly
Float Property GazeFacing = 60.0 AutoReadOnly
{The target must be looking at you: its heading to you within this many degrees.}
Int Property GazeSeconds = 4 AutoReadOnly
Int Property GazeSecondsMangekyo = 7 AutoReadOnly
Float Property GazeMagicka = 30.0 AutoReadOnly
Float Property GazeCooldown = 8.0 AutoReadOnly
Float Property PuppetRange = 2500.0 AutoReadOnly
Int Property PuppetSeconds = 60 AutoReadOnly
Int Property PuppetSecondsMangekyo = 90 AutoReadOnly
Int Property BeastSeconds = 30 AutoReadOnly
Float Property PuppetMagicka = 80.0 AutoReadOnly
Float Property BeastMagicka = 150.0 AutoReadOnly
Float Property PuppetCooldown = 45.0 AutoReadOnly
Float Property BeastCooldown = 120.0 AutoReadOnly
Float Property AfterEffectShare = 0.5 AutoReadOnly
{Share of the puppet's full health lost when the genjutsu is released.}

Actor Puppet = None
Faction[] SavedFactions
Int[] SavedRanks
Int SavedCount = 0
Bool WasTeammate = False
Float LastGaze = -100.0
Float LastPuppet = -100.0
Float PuppetCooldownUsed = 45.0

Float Function Now()
	Return Utility.GetCurrentRealTime()
EndFunction

Form Function Own(Int id)
	Return Game.GetFormFromFile(id, "Obito Tobi Path Additions.esp")
EndFunction

Bool Function SharinganOpen()
	Return (Game.GetFormFromFile(0x0EFC75, "Skyrim.esm") as GlobalVariable).GetValue() == 2
EndFunction

Bool Function MangekyoAwakened()
	GlobalVariable g = Game.GetFormFromFile(0x160CAE, "UchihaClan.esp") as GlobalVariable
	Return g && g.GetValue() >= 1
EndFunction

Bool Function UchihaBoss(Actor a)
	Keyword k = Game.GetFormFromFile(0x02E8C9, "UchihaClan.esp") as Keyword
	Return k && a.HasKeyword(k)
EndFunction

; Cooldowns are kept in real time, which restarts every launch: clear stale values.
Float Function Ready(Float last, Float cooldown)
	Float t = Now()
	If last > t
		Return 0.0
	EndIf
	Float left = cooldown - (t - last)
	If left < 0.0
		Return 0.0
	EndIf
	Return left
EndFunction

Actor Function Aimed(Float range)
	Actor player = Game.GetPlayer()
	Actor a = Game.GetCurrentCrosshairRef() as Actor
	If a && a != player && !a.IsDead() && player.GetDistance(a) <= range && player.HasLOS(a)
		Return a
	EndIf
	Return None
EndFunction

; The Tsukuyomi sound the Uchiha Clan's Tsukuyomi plays (Naruto Overhaul A0tsukuyomimarker -> tsukuyomi.wav).
Function GenjutsuSound()
	Sound snd = Game.GetFormFromFile(0x01C7F3, "naruto overhaul.esp") as Sound
	If snd
		snd.Play(Game.GetPlayer())
	EndIf
EndFunction

Bool Function Pay(Float cost)
	Actor player = Game.GetPlayer()
	If player.GetActorValue("Magicka") < cost
		Debug.Notification("Genjutsu: not enough chakra.")
		Return False
	EndIf
	player.DamageActorValue("Magicka", cost)
	Return True
EndFunction

; ---------------- A: Genjutsu: Sharingan ----------------

Function Gaze()
	Actor player = Game.GetPlayer()
	If !SharinganOpen()
		Debug.Notification("Genjutsu: open your Sharingan first.")
		Return
	EndIf
	Float left = Ready(LastGaze, GazeCooldown)
	If left > 0.0
		Debug.Notification("Genjutsu: not ready (" + ((left + 0.99) as Int) + "s).")
		Return
	EndIf
	Actor a = Aimed(GazeRange)
	If !a
		Debug.Notification("Genjutsu: no one in your sight.")
		Return
	EndIf
	If UchihaBoss(a)
		Debug.Notification("Genjutsu: " + a.GetDisplayName() + " sees through your Sharingan.")
		Return
	EndIf
	If Math.Abs(a.GetHeadingAngle(player)) > GazeFacing
		Debug.Notification("Genjutsu: " + a.GetDisplayName() + " is not looking at you.")
		Return
	EndIf
	If !Pay(GazeMagicka)
		Return
	EndIf
	LastGaze = Now()
	Int secs = GazeSeconds
	If MangekyoAwakened()
		secs = GazeSecondsMangekyo
	EndIf
	Spell freeze = Own(0x812) as Spell
	freeze.SetNthEffectDuration(0, secs)
	freeze.Cast(player, a)
	GenjutsuSound()
	Debug.Trace("CTOB genjutsu: gaze on " + a + " for " + secs + " s")
	Debug.Notification(a.GetDisplayName() + " is caught in your genjutsu.")
EndFunction

; ---------------- B / C: Sharingan Puppet ----------------

Function PuppetPower()
	Actor player = Game.GetPlayer()
	Actor a = Aimed(PuppetRange)
	If a && a == Puppet
		Debug.Notification("Genjutsu: you release " + a.GetDisplayName() + ".")
		a.DispelSpell(Own(0x814) as Spell)       ; ends the effect -> EndPuppet
		Return
	EndIf
	If !SharinganOpen()
		Debug.Notification("Genjutsu: open your Sharingan first.")
		Return
	EndIf
	If !a
		Debug.Notification("Genjutsu: no one in your sight.")
		Return
	EndIf
	If Puppet && !Puppet.IsDead()
		Debug.Notification("Genjutsu: you already hold " + Puppet.GetDisplayName() + ". Aim at them to release.")
		Return
	EndIf
	If UchihaBoss(a)
		Debug.Notification("Genjutsu: " + a.GetDisplayName() + " sees through your Sharingan.")
		Return
	EndIf
	If a.HasKeyword(Game.GetFormFromFile(0x01397A, "Skyrim.esm") as Keyword)
		Debug.Notification("Genjutsu: a machine has no mind to seize.")
		Return
	EndIf
	Bool beast = !a.HasKeyword(Game.GetFormFromFile(0x013794, "Skyrim.esm") as Keyword)
	If beast && !MangekyoAwakened()
		Debug.Notification("Genjutsu: only the Mangekyou can bend a beast's will.")
		Return
	EndIf
	Float cooldown = PuppetCooldown
	Float cost = PuppetMagicka
	Int secs = PuppetSeconds
	If beast
		cooldown = BeastCooldown
		cost = BeastMagicka
		secs = BeastSeconds
	ElseIf MangekyoAwakened()
		secs = PuppetSecondsMangekyo
	EndIf
	Float left = Ready(LastPuppet, PuppetCooldownUsed)
	If left > 0.0
		Debug.Notification("Genjutsu: Puppet not ready (" + ((left + 0.99) as Int) + "s).")
		Return
	EndIf
	If !Pay(cost)
		Return
	EndIf
	LastPuppet = Now()
	PuppetCooldownUsed = cooldown
	Spell s = Own(0x814) as Spell
	s.SetNthEffectDuration(0, secs)
	s.Cast(player, a)
	GenjutsuSound()
	Debug.Trace("CTOB genjutsu: puppet " + a + " for " + secs + " s (beast " + beast + ")")
EndFunction

; From CTOB_PuppetEffect.OnEffectStart: take the actor out of its factions and onto your side.
Function BeginPuppet(Actor a)
	Actor player = Game.GetPlayer()
	If Puppet && Puppet != a
		Return
	EndIf
	Puppet = a
	SavedFactions = a.GetFactions(-128, 127)
	SavedCount = 0
	If SavedFactions
		SavedCount = SavedFactions.Length
		SavedRanks = Utility.CreateIntArray(SavedCount)
		Int i = 0
		While i < SavedCount
			SavedRanks[i] = a.GetFactionRank(SavedFactions[i])
			i += 1
		EndWhile
	EndIf
	WasTeammate = a.IsPlayerTeammate()
	a.StopCombat()
	a.RemoveFromAllFactions()
	a.AddToFaction(Game.GetFormFromFile(0x000DB1, "Skyrim.esm") as Faction)     ; PlayerFaction
	a.SetPlayerTeammate(True, True)
	a.StopCombatAlarm()
	a.EvaluatePackage()
	Debug.Notification(a.GetDisplayName() + " is now your puppet.")
	; turn it on the nearest enemy that is fighting you
	Actor foe = NearestFoe(a)
	If foe
		a.StartCombat(foe)
	EndIf
EndFunction

Actor Function NearestFoe(Actor from)
	Actor player = Game.GetPlayer()
	Cell c = player.GetParentCell()
	If !c
		Return None
	EndIf
	Actor best = None
	Float bestDist = 4000.0
	Int n = c.GetNumRefs(62)
	Int i = 0
	While i < n
		Actor x = c.GetNthRef(i, 62) as Actor
		If x && x != from && x != player && !x.IsDead() && x.IsHostileToActor(player) && x.Is3DLoaded()
			Float d = from.GetDistance(x)
			If d < bestDist
				best = x
				bestDist = d
			EndIf
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction

; From CTOB_PuppetEffect.OnEffectFinish (time up, released, or the puppet died): restore it, then the after-effect.
Function EndPuppet(Actor a)
	If a != Puppet
		Return
	EndIf
	Puppet = None
	Actor player = Game.GetPlayer()
	If a.IsDead()
		Return
	EndIf
	a.SetPlayerTeammate(WasTeammate)
	a.RemoveFromFaction(Game.GetFormFromFile(0x000DB1, "Skyrim.esm") as Faction)
	Int i = 0
	While i < SavedCount
		If SavedFactions[i]
			a.SetFactionRank(SavedFactions[i], SavedRanks[i])
		EndIf
		i += 1
	EndWhile
	a.StopCombat()
	a.EvaluatePackage()
	; let follower / healer handlers react to the teammate change first, then the after-effect lands
	Utility.Wait(0.5)
	AfterEffect(a)
EndFunction

; Yagura did not survive his. Half the puppet's full health and all its stamina; lethal if it is already weak.
; Traces the health right after and 3 s later, so anything that undoes it shows in the Papyrus log.
Function AfterEffect(Actor a)
	Actor player = Game.GetPlayer()
	If a.IsDead()
		Return
	EndIf
	Float hp = a.GetActorValue("Health")
	Float pct = a.GetActorValuePercentage("Health")
	Float full = hp
	If pct > 0.01
		full = hp / pct
	EndIf
	Float dmg = AfterEffectShare * full
	Bool lethal = dmg >= hp && !a.IsEssential() && !a.GetActorBase().IsProtected()
	Debug.Trace("CTOB genjutsu: after-effect on " + a + ": " + dmg + " vs health " + hp + " (lethal " + lethal + ", teammate " + a.IsPlayerTeammate() + ")")
	If lethal
		If a.IsHostileToActor(player)
			a.Kill(player)
		Else
			a.Kill()
		EndIf
		Utility.Wait(0.5)
		If !a.IsDead()
			Debug.Trace("CTOB genjutsu: Kill() did not take on " + a + ", draining health instead")
			a.DamageActorValue("Health", a.GetActorValue("Health") + 10.0)
			Utility.Wait(0.5)
		EndIf
		Debug.Trace("CTOB genjutsu: " + a + " dead " + a.IsDead())
		If a.IsDead()
			Debug.Notification(a.GetDisplayName() + " did not survive the genjutsu's after-effects.")
		EndIf
	Else
		a.DamageActorValue("Health", dmg)
		a.DamageActorValue("Stamina", a.GetActorValue("Stamina"))
		Debug.Trace("CTOB genjutsu: " + a + " health now " + a.GetActorValue("Health"))
		Debug.Notification(a.GetDisplayName() + " wakes from the genjutsu, broken.")
		Utility.Wait(3.0)
		Debug.Trace("CTOB genjutsu: " + a + " health 3 s later " + a.GetActorValue("Health"))
	EndIf
EndFunction

; ---------------- D / E: Rinnegan Preta Path ----------------

Float LastSeal = -100.0
Float LastDrain = -100.0

Bool Function RinneganActive()
	Spell r = Game.GetFormFromFile(0x04144E, "UchihaClan.esp") as Spell      ; aaaRinneganAbility
	Return r && Game.GetPlayer().HasSpell(r)
EndFunction

Function PretaSeal()
	If !RinneganActive()
		Debug.Notification("Preta Path: needs the Rinnegan.")
		Return
	EndIf
	Float left = Ready(LastSeal, 25.0)
	If left > 0.0
		Debug.Notification("Preta Path: the seal is not ready (" + ((left + 0.99) as Int) + "s).")
		Return
	EndIf
	LastSeal = Now()
	Actor player = Game.GetPlayer()
	(Own(0x81A) as Spell).Cast(player, player)
	Debug.Trace("CTOB preta: absorption seal")
	Debug.Notification("Preta Path: Absorption Seal. Jutsu that strike you become your chakra.")
EndFunction

; The enemy you aim at within reach, else the nearest hostile actor in front of you within reach.
Actor Function PretaTarget(Float reach)
	Actor player = Game.GetPlayer()
	Actor a = Aimed(reach)
	If a
		Return a
	EndIf
	Cell c = player.GetParentCell()
	If !c
		Return None
	EndIf
	Actor best = None
	Float bestDist = reach
	Int n = c.GetNumRefs(62)
	Int i = 0
	While i < n
		Actor x = c.GetNthRef(i, 62) as Actor
		If x && x != player && !x.IsDead() && x.IsHostileToActor(player) && Math.Abs(player.GetHeadingAngle(x)) < 50.0
			Float d = player.GetDistance(x)
			If d < bestDist
				best = x
				bestDist = d
			EndIf
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction

Function PretaDrain()
	If !RinneganActive()
		Debug.Notification("Preta Path: needs the Rinnegan.")
		Return
	EndIf
	Float left = Ready(LastDrain, 15.0)
	If left > 0.0
		Debug.Notification("Preta Path: not ready (" + ((left + 0.99) as Int) + "s).")
		Return
	EndIf
	Actor a = PretaTarget(300.0)
	If !a
		Debug.Notification("Preta Path: no one within reach.")
		Return
	EndIf
	LastDrain = Now()
	Actor player = Game.GetPlayer()
	(Own(0x81D) as Spell).Cast(player, a)
	Debug.Trace("CTOB preta: draining " + a)
	Debug.Notification("Preta Path: absorbing " + a.GetDisplayName() + "'s chakra.")
	Utility.Wait(4.2)
	; drained dry (no chakra and no stamina left): they collapse, as the Preta body's victims did
	If !a.IsDead() && a.GetActorValue("Magicka") < 5.0 && a.GetActorValue("Stamina") < 5.0
		Spell paralysis = Own(0x812) as Spell
		paralysis.SetNthEffectDuration(0, 3)
		paralysis.Cast(player, a)
		Debug.Trace("CTOB preta: " + a + " drained dry, collapses")
	EndIf
EndFunction

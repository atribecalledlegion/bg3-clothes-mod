Scriptname CLF_Brain extends Quest
{Companion Life (2026-10-16): downtime AI for Serana and Ashe.
Every Tick s: works out the PLACE (home, inn, city, camp or none), whether it is DOWNTIME (home/inn interiors always;
elsewhere once the player has settled), and each companion's hidden NEEDS (rest, comfort, thirst, social), which grow
while adventuring and fall while an activity serves them. In downtime the most pressing need, weighted by the place,
picks an ACTIVITY = her rank in ActivityFaction, which switches on one of the CLF_Quest alias packages (rest = sit,
comfort = idle markers/fire/lean, drink = sit + ChairDrinkingStart, social = walk up and chat or sandbox conversation,
sleep = bed). Rank 0 = their own follow/sandbox AI as before.
Barefoot: as soon as she is home (v3; v1-v2 waited until she had sat BarefootAfter s), her boots and calf pieces come off (feet-only items, never a one-piece outfit) and
go back on when you leave home, draw a weapon or a fight starts.
Never acts while she is in a scene (SDA, Ashe's quests), in dialogue with you, or in combat.
Off switch: set CLF_Enabled to 0. Trace lines start with "CLF:".}

Actor Property PlayerRef Auto
Faction Property ActivityFaction Auto
GlobalVariable Property Enabled Auto
GlobalVariable Property GameHour Auto
Idle Property ChairDrink Auto
Idle Property StandDrink Auto
Idle Property WarmHands Auto
Idle Property WarmHandsCrouched Auto
Idle Property Stretch Auto
Idle Property TalkHappy Auto
Idle Property TalkNeutral Auto
Idle Property Laugh Auto
Idle Property ResponsePositive Auto
Idle Property LookFar Auto
Idle Property Wave Auto
Keyword Property LocTypePlayerHouse Auto
Keyword Property LocTypeInn Auto
Keyword Property LocTypeCity Auto
Keyword Property LocTypeTown Auto
Keyword Property LocTypeHabitation Auto
Keyword Property LocTypeDwelling Auto
Keyword Property LocTypeDungeon Auto

Float Property Tick = 2.0 AutoReadOnly
Float Property SettleSeconds = 6.0 AutoReadOnly
{Player standing (nearly) still this long outside home/inn = downtime.}
Float Property SettleRadius = 450.0 AutoReadOnly
{Walk further than this from where you settled and they go back to following.}
Float Property BarefootAfter = 15.0 AutoReadOnly
Float Property ChatSeconds = 14.0 AutoReadOnly
Float Property ChatCooldown = 50.0 AutoReadOnly
Float Property MinScore = 18.0 AutoReadOnly
{Below this no need is pressing: at home/inn she still does something light, elsewhere their own sandbox runs.}

; activities = ActivityFaction ranks (CLF_Quest alias packages)
Int Property A_NONE = 0 AutoReadOnly
Int Property A_REST = 1 AutoReadOnly
Int Property A_COMFORT = 2 AutoReadOnly
Int Property A_DRINK = 3 AutoReadOnly
Int Property A_SOCIAL = 4 AutoReadOnly
Int Property A_VISIT = 5 AutoReadOnly
Int Property A_SLEEP = 6 AutoReadOnly
Int Property A_HOLD = 7 AutoReadOnly
Int Property A_FOLLOW = 8 AutoReadOnly
{v4: at home/inn while you walk about they follow you (CLF_FollowHome, 280-420 units), then relax when you stop.}
Int Property A_OWN = 9 AutoReadOnly
{v5 (user, 2026-10-17): at home our sandbox packages left them standing (tests 1-4), so when you stop at home they run
THEIR OWN home AI again (rank 0: DLC1/MM mental-model sandbox - chairs, grindstones, alchemy tables). Ours only adds
barefoot, the longer follow while you walk, and the occasional chat between the two.}
Bool Property HomeABTest = True AutoReadOnly
{v5 test: Serana gets her own AI (A_OWN), Ashe gets CLF_Comfort (their sandbox settings, held steady - their own
settle check flips settled/moving every few seconds even while you stand still, restarting their sandbox).}
Float Property HomeSettleSeconds = 2.0 AutoReadOnly
Float Property HomeSettleRadius = 700.0 AutoReadOnly

Int Property P_NONE = 0 AutoReadOnly
Int Property P_HOME = 1 AutoReadOnly
Int Property P_INN = 2 AutoReadOnly
Int Property P_CITY = 3 AutoReadOnly
Int Property P_CAMP = 4 AutoReadOnly

Actor[] Comp
Float[] NRest
Float[] NComfort
Float[] NThirst
Float[] NSocial
Int[] CurAct          ; chosen activity
Int[] CurRank         ; package rank in use (social can run as visit/hold)
Float[] ActStart
Float[] ActUntil
Int[] Phase        ; drink: 1 drinking | chat: 1 walking, 2 talking, 3 listening
Float[] PhaseTime
Float[] NextGesture
Actor[] ChatWith
Form[] Boots       ; v1/v2, unused (Shoes holds 3 per companion)
Form[] Shoes
Bool[] PkgLogged
Bool[] Barefoot
Float[] SatSince
Float[] NextChat
Int[] LastAct

Actor AsheRef
Float LastX
Float LastY
Float AnchorX
Float AnchorY
Float StillFor
Bool Settled
Bool HomeLike
Int LastPlace = -1
Float Now
Bool PlayerFighting

Event OnInit()
	If !Comp
		Setup()             ; start-game-enabled quests can run OnInit twice
	EndIf
	RegisterForSingleUpdate(5.0)
EndEvent

Function Setup()
	Comp = new Actor[2]
	NRest = new Float[2]
	NComfort = new Float[2]
	NThirst = new Float[2]
	NSocial = new Float[2]
	CurAct = new Int[2]
	CurRank = new Int[2]
	ActStart = new Float[2]
	ActUntil = new Float[2]
	Phase = new Int[2]
	PhaseTime = new Float[2]
	NextGesture = new Float[2]
	ChatWith = new Actor[2]
	Boots = new Form[2]
	Barefoot = new Bool[2]
	SatSince = new Float[2]
	NextChat = new Float[2]
	LastAct = new Int[2]
	Int i = 0
	While i < 2
		NRest[i] = 30.0
		NComfort[i] = 30.0
		NThirst[i] = 25.0
		NSocial[i] = 35.0
		i += 1
	EndWhile
	Debug.Trace("CLF: started")
EndFunction

Event OnUpdate()
	If !Comp
		Setup()
	EndIf
	If Enabled.GetValue() > 0.0
		Step()
	Else
		ReleaseAll()
	EndIf
	RegisterForSingleUpdate(Tick)
EndEvent

; ---------------- main loop ----------------

Function Step()
	Now = Utility.GetCurrentRealTime()
	Comp[0] = (GetAlias(0) as ReferenceAlias).GetActorReference()
	Comp[1] = AsheActor()
	If Comp[1] == Comp[0]
		Comp[1] = None      ; v1 bug: the Ashe slot held Serana, so two brains fought over her
	EndIf
	PlayerFighting = PlayerRef.IsInCombat()
	Int place = Place()
	HomeLike = place == P_HOME || place == P_INN
	UpdateSettle()
	If place != LastPlace
		LastPlace = place
		Debug.Trace("CLF: place " + PlaceName(place) + " " + PlayerRef.GetCurrentLocation())
	EndIf
	Int i = 0
	While i < 2
		If Comp[i]
			StepOne(i, Comp[i], place)
		EndIf
		i += 1
	EndWhile
EndFunction

; Ashe straight from her plugin (not a master); her alias (which runs our packages on her) is forced to her
; whenever it holds anything else - in v1 it came up holding Serana
Actor Function AsheActor()
	If !AsheRef
		AsheRef = Game.GetFormFromFile(0x2D4A35, "Ashe - Fire and Blood.esp") as Actor
		If !AsheRef
			Return None
		EndIf
		Debug.Trace("CLF: Ashe found " + AsheRef)
	EndIf
	ReferenceAlias al = GetAlias(1) as ReferenceAlias
	If al.GetReference() != AsheRef
		Debug.Trace("CLF: Ashe alias held " + al.GetReference() + " - forcing Ashe")
		al.ForceRefTo(AsheRef)
	EndIf
	Return AsheRef
EndFunction

Function UpdateSettle()
	Float x = PlayerRef.GetPositionX()
	Float y = PlayerRef.GetPositionY()
	Float moved = Dist2(x, y, LastX, LastY)
	LastX = x
	LastY = y
	Bool sitting = PlayerRef.GetSitState() >= 2
	If PlayerFighting || PlayerRef.IsWeaponDrawn()
		StillFor = 0.0
		If Settled
			Settled = False
			Debug.Trace("CLF: player busy (combat or weapon out)")
		EndIf
		Return
	EndIf
	If Settled
		Float radius = SettleRadius
		If HomeLike
			radius = HomeSettleRadius
		EndIf
		If !sitting && Dist2(x, y, AnchorX, AnchorY) > radius
			Settled = False
			StillFor = 0.0
			Debug.Trace("CLF: player moving on")
		EndIf
		Return
	EndIf
	If moved < 60.0 || sitting
		StillFor += Tick
	Else
		StillFor = 0.0
	EndIf
	Float need = SettleSeconds
	If HomeLike
		need = HomeSettleSeconds
	EndIf
	If StillFor >= need || (sitting && StillFor >= Tick)
		Settled = True
		AnchorX = x
		AnchorY = y
		Debug.Trace("CLF: player settled")
	EndIf
EndFunction

Int Function Place()
	Location loc = PlayerRef.GetCurrentLocation()
	Bool inside = PlayerRef.IsInInterior()
	If loc
		If loc.HasKeyword(LocTypePlayerHouse) && inside
			Return P_HOME
		ElseIf loc.HasKeyword(LocTypeInn) && inside
			Return P_INN
		ElseIf loc.HasKeyword(LocTypeDungeon)
			Return P_NONE
		ElseIf loc.HasKeyword(LocTypeCity) || loc.HasKeyword(LocTypeTown) || loc.HasKeyword(LocTypeHabitation) || loc.HasKeyword(LocTypeDwelling)
			Return P_CITY
		EndIf
	EndIf
	If !inside && Settled && (StillFor >= 20.0 || PlayerRef.GetSitState() >= 2)
		Return P_CAMP           ; out in the wilds and you have stopped for a while (or sat down)
	EndIf
	Return P_NONE
EndFunction

Bool Function Downtime(Int place)
	If place == P_HOME || place == P_INN
		Return Settled && !PlayerRef.IsWeaponDrawn()     ; v4: they follow while you walk (v1-v3 relaxed in place)
	EndIf
	Return place != P_NONE && Settled
EndFunction

Function StepOne(Int i, Actor a, Int place)
	Bool ok = a.Is3DLoaded() && !a.IsDead() && a.IsPlayerTeammate() && !a.IsInCombat() && !PlayerFighting
	If ok
		ok = a.GetDistance(PlayerRef) < 3000.0 && !a.GetCurrentScene()
	EndIf
	If a.GetSitState() == 3
		If SatSince[i] == 0.0
			SatSince[i] = Now
		EndIf
	Else
		SatSince[i] = 0.0
	EndIf
	ShoeCheck(i, a, place, ok)
	Bool down = ok && Downtime(place)
	UpdateNeeds(i, a, down)
	If !down
		If ok && HomeLike && !PlayerRef.IsWeaponDrawn()
			If CurAct[i] != A_FOLLOW
				If CurAct[i] != A_NONE
					Release(i, a, "you are walking")
				EndIf
				CurAct[i] = A_FOLLOW
				CurRank[i] = A_FOLLOW
				a.SetFactionRank(ActivityFaction, A_FOLLOW)
				a.EvaluatePackage()
				Debug.Trace("CLF: " + a.GetDisplayName() + " follows you around the " + PlaceName(place))
			EndIf
			Return
		EndIf
		If CurAct[i] != A_NONE
			Release(i, a, "no downtime: " + WhyNot(a, place))
		EndIf
		Return
	EndIf
	If CurAct[i] == A_FOLLOW
		Release(i, a, "you stopped")
	EndIf
	If a.IsInDialogueWithPlayer()
		Return
	EndIf
	If CurAct[i] != A_NONE
		If Now < ActUntil[i] && !Satisfied(i)
			Perform(i, a, place)
			Return
		EndIf
		Release(i, a, "done")
	EndIf
	If Phase[i] == 0
		Choose(i, a, place)
	EndIf
EndFunction

; ---------------- needs ----------------

Function UpdateNeeds(Int i, Actor a, Bool down)
	If a.IsInCombat() || PlayerFighting
		NRest[i] = NRest[i] + 0.6
		NThirst[i] = NThirst[i] + 0.25
		NComfort[i] = NComfort[i] + 0.2
	ElseIf !down
		NRest[i] = NRest[i] + 0.12             ; on the road: ~45 rest per 10 minutes of travel
		NThirst[i] = NThirst[i] + 0.07
		NSocial[i] = NSocial[i] + 0.05
		NComfort[i] = NComfort[i] + 0.06
		Location loc = PlayerRef.GetCurrentLocation()
		If loc && loc.HasKeyword(LocTypeDungeon)
			NComfort[i] = NComfort[i] + 0.08    ; dark, cold, dead things
			NSocial[i] = NSocial[i] + 0.03
		EndIf
	Else
		NSocial[i] = NSocial[i] + 0.03
		NThirst[i] = NThirst[i] + 0.02
	EndIf
	Bool seated = a.GetSitState() == 3
	Int act = CurAct[i]
	If act == A_REST && seated
		NRest[i] = NRest[i] - 1.2
		NComfort[i] = NComfort[i] - 0.3
	ElseIf act == A_COMFORT
		NComfort[i] = NComfort[i] - 0.8
		If seated
			NRest[i] = NRest[i] - 0.4
		EndIf
	ElseIf act == A_DRINK && Phase[i] >= 1
		NThirst[i] = NThirst[i] - 1.5
		NSocial[i] = NSocial[i] - 0.2
		NRest[i] = NRest[i] - 0.4
	ElseIf act == A_SOCIAL
		If Phase[i] >= 2
			NSocial[i] = NSocial[i] - 1.6
		Else
			NSocial[i] = NSocial[i] - 0.4
		EndIf
	ElseIf act == A_OWN
		If seated
			NRest[i] = NRest[i] - 1.0
			NComfort[i] = NComfort[i] - 0.5
		Else
			NComfort[i] = NComfort[i] - 0.3
		EndIf
	ElseIf act == A_SLEEP && a.GetSleepState() >= 3
		NRest[i] = NRest[i] - 2.0
		NComfort[i] = NComfort[i] - 0.5
	EndIf
	If Barefoot[i]
		NComfort[i] = NComfort[i] - 0.2
	EndIf
	NRest[i] = Clamp(NRest[i])
	NComfort[i] = Clamp(NComfort[i])
	NThirst[i] = Clamp(NThirst[i])
	NSocial[i] = Clamp(NSocial[i])
EndFunction

Bool Function Satisfied(Int i)
	Int act = CurAct[i]
	If act == A_REST || act == A_SLEEP
		Return NRest[i] < 8.0
	ElseIf act == A_COMFORT
		Return NComfort[i] < 8.0
	ElseIf act == A_DRINK
		Return NThirst[i] < 8.0
	EndIf
	Return False        ; social ends by itself (chat done / time)
EndFunction

; ---------------- choosing ----------------

Function Choose(Int i, Actor a, Int place)
	If place == P_HOME
		If NSocial[i] >= 40.0 && Now >= NextChat[i] && Utility.RandomInt(0, 2) == 0 && ChatPartner(i, a, place)
			BeginAct(i, a, A_SOCIAL, place)
		ElseIf HomeABTest && i == 1
			BeginAct(i, a, A_COMFORT, place)
		Else
			BeginAct(i, a, A_OWN, place)
		EndIf
		Return
	EndIf
	Float hour = GameHour.GetValue()
	Bool night = hour >= 22.0 || hour < 6.0
	Float wRest = 0.9
	Float wComfort = 0.8
	Float wDrink = 0.0
	Float wSocial = 0.9
	Float wSleep = 0.0
	If place == P_HOME
		wRest = 1.0
		wComfort = 1.0
		wDrink = 0.5
		wSocial = 0.8
		If night
			wSleep = 1.4
		EndIf
	ElseIf place == P_INN
		wRest = 0.8
		wComfort = 0.4
		wDrink = 1.4
		wSocial = 1.1
	ElseIf place == P_CITY
		wRest = 0.7
		wComfort = 0.6
		wSocial = 1.2
	ElseIf place == P_CAMP
		wRest = 0.9
		wComfort = 1.3
		wSocial = 0.8
	EndIf
	If Now < NextChat[i]
		wSocial = 0.0
	EndIf
	Int pick = A_NONE
	Float best = 0.0
	Float sc = Score(i, A_REST, NRest[i] * wRest)
	If sc > best
		best = sc
		pick = A_REST
	EndIf
	sc = Score(i, A_COMFORT, NComfort[i] * wComfort)
	If sc > best
		best = sc
		pick = A_COMFORT
	EndIf
	sc = Score(i, A_DRINK, NThirst[i] * wDrink)
	If sc > best
		best = sc
		pick = A_DRINK
	EndIf
	sc = Score(i, A_SOCIAL, NSocial[i] * wSocial)
	If sc > best
		best = sc
		pick = A_SOCIAL
	EndIf
	If wSleep > 0.0 && NRest[i] > 55.0
		sc = Score(i, A_SLEEP, NRest[i] * wSleep)
		If sc > best
			best = sc
			pick = A_SLEEP
		EndIf
	EndIf
	If best < MinScore
		If place == P_HOME
			pick = A_COMFORT        ; nothing pressing: potter about the house (idle markers, sit)
		ElseIf place == P_INN
			pick = A_REST
		Else
			Return                  ; their own sandbox is fine
		EndIf
	EndIf
	BeginAct(i, a, pick, place)
EndFunction

Float Function Score(Int i, Int act, Float base)
	Float s = base * Utility.RandomFloat(0.85, 1.15)
	If act == LastAct[i]
		s = s * 0.7                 ; variety: not the same thing twice in a row
	EndIf
	Return s
EndFunction

Function BeginAct(Int i, Actor a, Int act, Int place)
	If PkgLogged
		PkgLogged[i] = False
	EndIf
	Int rank = act
	If act == A_OWN
		rank = A_NONE
	EndIf
	Phase[i] = 0
	ChatWith[i] = None
	If act == A_SOCIAL
		Actor who = ChatPartner(i, a, place)
		If who
			ChatWith[i] = who
			(GetAlias(2 + i) as ReferenceAlias).ForceRefTo(who)
			rank = A_VISIT
			Phase[i] = 1
		ElseIf place == P_HOME || place == P_CAMP
			act = A_COMFORT          ; nobody to talk to
			rank = A_COMFORT
		EndIf
	EndIf
	CurAct[i] = act
	CurRank[i] = rank
	ActStart[i] = Now
	PhaseTime[i] = Now
	Float dur = Utility.RandomFloat(60.0, 120.0)
	If act == A_DRINK
		dur = Utility.RandomFloat(90.0, 150.0)
	ElseIf act == A_SLEEP
		dur = 600.0
	ElseIf act == A_SOCIAL && Phase[i] == 1
		dur = 45.0
	EndIf
	ActUntil[i] = Now + dur
	a.SetFactionRank(ActivityFaction, rank)
	a.EvaluatePackage()
	String extra = ""
	If ChatWith[i]
		extra = " with " + ChatWith[i].GetDisplayName()
	EndIf
	Debug.Trace("CLF: " + a.GetDisplayName() + " -> " + ActName(act) + extra + " at " + PlaceName(place) + " (rest " + NRest[i] as Int + " comfort " + NComfort[i] as Int + " thirst " + NThirst[i] as Int + " social " + NSocial[i] as Int + ")")
EndFunction

Actor Function ChatPartner(Int i, Actor a, Int place)
	Int j = 1 - i
	Actor other = Comp[j]
	; at home or camp: the other companion, if she is free (not already chatting, not asleep)
	If other && other.Is3DLoaded() && other.GetDistance(a) < 2000.0 && Phase[j] == 0 && other.GetSleepState() < 3 && !other.GetCurrentScene()
		If place == P_HOME || place == P_CAMP || Utility.RandomInt(0, 2) == 0
			Return other
		EndIf
	EndIf
	If place == P_HOME || place == P_CAMP
		Return None
	EndIf
	; in town or the inn: someone nearby
	Int tries = 0
	While tries < 6
		Actor who = Game.FindRandomActorFromRef(a, 1200.0)
		If GoodPartner(who, a)
			Return who
		EndIf
		tries += 1
	EndWhile
	Return None
EndFunction

Bool Function GoodPartner(Actor who, Actor a)
	If !who || who == a || who == PlayerRef || who == Comp[0] || who == Comp[1]
		Return False
	EndIf
	If who.IsDead() || who.IsInCombat() || who.IsHostileToActor(a) || who.IsHostileToActor(PlayerRef) || who.IsChild()
		Return False
	EndIf
	If !who.HasKeywordString("ActorTypeNPC") || who.IsInDialogueWithPlayer() || who.GetCurrentScene() || who.GetSleepState() >= 3
		Return False
	EndIf
	Return who.IsPlayerTeammate() == False && who.IsGuard() == False
EndFunction

; ---------------- doing ----------------

Function Perform(Int i, Actor a, Int place)
	If !PkgLogged
		PkgLogged = new Bool[2]
	EndIf
	If !PkgLogged[i] && Now - ActStart[i] > 8.0
		PkgLogged[i] = True        ; diagnostic: is our package really the one running?
		Debug.Trace("CLF: " + a.GetDisplayName() + " doing " + ActName(CurAct[i]) + ", package " + a.GetCurrentPackage() + ", sit state " + a.GetSitState() + ", rank " + a.GetFactionRank(ActivityFaction))
	EndIf
	Int act = CurAct[i]
	Int s = a.GetSitState()
	If act == A_DRINK
		If Phase[i] == 0
			If s == 3 && Now - SatSince[i] > 2.0
				a.PlayIdle(ChairDrink)
				Phase[i] = 1
				PhaseTime[i] = Now
				Debug.Trace("CLF: " + a.GetDisplayName() + " drinking")
			ElseIf s == 0 && Now - ActStart[i] > 25.0
				Debug.Trace("CLF: " + a.GetDisplayName() + " found no seat to drink at -> comfort")
				Switch(i, a, A_COMFORT, A_COMFORT)
			EndIf
		EndIf
	ElseIf act == A_SOCIAL && ChatWith[i]
		PerformChat(i, a)
	EndIf
EndFunction

Function PerformChat(Int i, Actor a)
	Actor who = ChatWith[i]
	If !who || who.IsDead() || who.IsInCombat() || who.GetDistance(a) > 2500.0 || who.IsInDialogueWithPlayer()
		EndChat(i, a, "partner left")
		Return
	EndIf
	If Phase[i] == 1
		If a.GetDistance(who) < 190.0
			Phase[i] = 2
			PhaseTime[i] = Now
			ActUntil[i] = Now + ChatSeconds + 2.0
			CurRank[i] = A_HOLD
			a.SetFactionRank(ActivityFaction, A_HOLD)
			a.EvaluatePackage()
			a.SetLookAt(who)
			Listen(i, who, a)
			Debug.Trace("CLF: " + a.GetDisplayName() + " chatting with " + who.GetDisplayName())
		ElseIf Now - ActStart[i] > 35.0
			EndChat(i, a, "could not reach")
		EndIf
		Return
	EndIf
	If Phase[i] == 2 || Phase[i] == 3
		If Now - PhaseTime[i] > ChatSeconds
			EndChat(i, a, "done")
			Return
		EndIf
		If Now >= NextGesture[i] && a.GetSitState() == 0
			NextGesture[i] = Now + Utility.RandomFloat(3.0, 5.0)
			If Phase[i] == 2
				Gesture(a, Utility.RandomInt(0, 9))
			Else
				Gesture(a, Utility.RandomInt(5, 11))     ; the listener nods and laughs more than she talks
			EndIf
		EndIf
	EndIf
EndFunction

; the other companion stops what she is doing and listens (faces the speaker, answers with gestures)
Function Listen(Int i, Actor who, Actor speaker)
	Int j = 1 - i
	If who != Comp[j]
		who.SetLookAt(speaker)
		Return
	EndIf
	If CurAct[j] != A_NONE
		Release(j, who, "listening to " + speaker.GetDisplayName())
	EndIf
	CurAct[j] = A_SOCIAL
	CurRank[j] = A_HOLD
	Phase[j] = 3
	ChatWith[j] = speaker
	ActStart[j] = Now
	PhaseTime[j] = Now
	NextGesture[j] = Now + 2.0
	ActUntil[j] = Now + ChatSeconds + 2.0
	If who.GetSitState() == 0
		who.SetFactionRank(ActivityFaction, A_HOLD)
		who.EvaluatePackage()
	EndIf
	who.SetLookAt(speaker)
EndFunction

Function Gesture(Actor a, Int n)
	If n <= 3
		a.PlayIdle(TalkNeutral)
	ElseIf n <= 6
		a.PlayIdle(TalkHappy)
	ElseIf n <= 9
		a.PlayIdle(ResponsePositive)
	Else
		a.PlayIdle(Laugh)
	EndIf
EndFunction

Function EndChat(Int i, Actor a, String why)
	Actor who = ChatWith[i]
	Int j = 1 - i
	If a.GetSitState() == 0
		a.PlayIdle(ResponsePositive)        ; one-shot: leaves the talking loop cleanly
	EndIf
	NSocial[i] = Clamp(NSocial[i] - 20.0)
	NextChat[i] = Now + ChatCooldown
	If who && who == Comp[j] && ChatWith[j] == a
		NSocial[j] = Clamp(NSocial[j] - 20.0)
		NextChat[j] = Now + ChatCooldown
		If who.GetSitState() == 0
			who.PlayIdle(ResponsePositive)
		EndIf
		Release(j, who, "chat over")
	ElseIf who
		who.ClearLookAt()
	EndIf
	Release(i, a, "chat " + why)
EndFunction

Function Switch(Int i, Actor a, Int act, Int rank)
	CurAct[i] = act
	CurRank[i] = rank
	Phase[i] = 0
	a.SetFactionRank(ActivityFaction, rank)
	a.EvaluatePackage()
EndFunction

Function Release(Int i, Actor a, String why)
	If CurAct[i] == A_NONE && Phase[i] == 0
		Return
	EndIf
	Debug.Trace("CLF: " + a.GetDisplayName() + " stops " + ActName(CurAct[i]) + " (" + why + ")")
	If ChatWith[i]
		a.ClearLookAt()
		ChatWith[i] = None
	EndIf
	(GetAlias(2 + i) as ReferenceAlias).Clear()
	LastAct[i] = CurAct[i]
	CurAct[i] = A_NONE
	CurRank[i] = A_NONE
	Phase[i] = 0
	a.SetFactionRank(ActivityFaction, 0)
	a.EvaluatePackage()
EndFunction

Function ReleaseAll()
	Int i = 0
	While i < 2
		If Comp && Comp[i]
			Release(i, Comp[i], "switched off")
			If Barefoot[i]
				ShoesOn(i, Comp[i])
			EndIf
		EndIf
		i += 1
	EndWhile
EndFunction

; ---------------- barefoot at home ----------------

Function ShoeCheck(Int i, Actor a, Int place, Bool ok)
	If !Shoes
		Shoes = new Form[6]         ; v3 (saves from v1/v2 lack it)
	EndIf
	Bool home = place == P_HOME
	If Barefoot[i]
		If !home || a.IsInCombat() || PlayerFighting || PlayerRef.IsWeaponDrawn() || a.IsDead()
			ShoesOn(i, a)
			Return
		EndIf
		StripFeet(i, a, False)      ; her outfit script put something back on: off again
		Return
	EndIf
	; v3 (user, 2026-10-17): completely barefoot as soon as she is home - also the sign that the home AI is on
	If home && a.Is3DLoaded() && !a.IsDead() && a.IsPlayerTeammate() && !a.IsInCombat() && !PlayerFighting && !PlayerRef.IsWeaponDrawn()
		If StripFeet(i, a, True)
			Barefoot[i] = True
		EndIf
	EndIf
EndFunction

; takes off whatever covers her feet: the feet slot (37) and calf pieces (38: socks, greaves, tall boots) - never an
; item that is part of the body piece (32), and a calf item only if it is feet+calf or calf-only (not trousers)
Bool Function StripFeet(Int i, Actor a, Bool remember)
	Int n = 0
	Int k = 0
	While k < 2
		Int mask = 0x80
		If k == 1
			mask = 0x100
		EndIf
		Armor w = a.GetWornForm(mask) as Armor
		If w && FeetOnly(w)
			Int m = w.GetSlotMask()
			If mask == 0x80 || Math.LogicalAnd(m, 0x80) != 0 || m == 0x100
				If remember
					Remember(i, w)
					Debug.Trace("CLF: " + a.GetDisplayName() + " takes off " + w.GetName() + " (barefoot at home)")
				EndIf
				a.UnequipItem(w, False, True)
				n += 1
			EndIf
		ElseIf w && remember && mask == 0x80
			Debug.Trace("CLF: " + a.GetDisplayName() + "'s " + w.GetName() + " covers her feet but is part of her body piece - left on")
		EndIf
		k += 1
	EndWhile
	Return n > 0
EndFunction

Function Remember(Int i, Form f)
	Int k = 0
	While k < 3
		If Shoes[i * 3 + k] == f
			Return
		EndIf
		k += 1
	EndWhile
	k = 0
	While k < 3
		If !Shoes[i * 3 + k]
			Shoes[i * 3 + k] = f
			Return
		EndIf
		k += 1
	EndWhile
EndFunction

Bool Function FeetOnly(Armor b)
	Return Math.LogicalAnd(b.GetSlotMask(), 0x4) == 0     ; not part of a body piece (slot 32)
EndFunction

Function ShoesOn(Int i, Actor a)
	Barefoot[i] = False
	Int k = 0
	While k < 3
		Form f = Shoes[i * 3 + k]
		Shoes[i * 3 + k] = None
		If f && a.GetItemCount(f) > 0 && !a.IsDead()
			a.EquipItem(f, False, True)
			Debug.Trace("CLF: " + a.GetDisplayName() + " puts " + f.GetName() + " back on")
		EndIf
		k += 1
	EndWhile
EndFunction

; ---------------- helpers ----------------

String Function WhyNot(Actor a, Int place)
	If !a.Is3DLoaded()
		Return "not loaded"
	ElseIf !a.IsPlayerTeammate()
		Return "not following"
	ElseIf a.IsInCombat() || PlayerFighting
		Return "combat"
	ElseIf a.GetDistance(PlayerRef) >= 3000.0
		Return "far"
	ElseIf a.GetCurrentScene()
		Return "in scene " + a.GetCurrentScene()
	ElseIf place == P_NONE
		Return "place none"
	ElseIf PlayerRef.IsWeaponDrawn()
		Return "weapon out"
	ElseIf !Settled
		Return "player not settled"
	EndIf
	Return "?"
EndFunction

Float Function Dist2(Float x1, Float y1, Float x2, Float y2)
	Return Math.Sqrt((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2))
EndFunction

Float Function Clamp(Float v)
	If v < 0.0
		Return 0.0
	ElseIf v > 100.0
		Return 100.0
	EndIf
	Return v
EndFunction

String Function PlaceName(Int p)
	If p == P_HOME
		Return "home"
	ElseIf p == P_INN
		Return "inn"
	ElseIf p == P_CITY
		Return "city"
	ElseIf p == P_CAMP
		Return "camp"
	EndIf
	Return "none"
EndFunction

String Function ActName(Int act)
	If act == A_REST
		Return "rest"
	ElseIf act == A_COMFORT
		Return "comfort"
	ElseIf act == A_DRINK
		Return "drink"
	ElseIf act == A_SOCIAL
		Return "social"
	ElseIf act == A_VISIT
		Return "visit"
	ElseIf act == A_SLEEP
		Return "sleep"
	ElseIf act == A_HOLD
		Return "hold"
	ElseIf act == A_FOLLOW
		Return "follow"
	ElseIf act == A_OWN
		Return "own home AI"
	EndIf
	Return "none"
EndFunction

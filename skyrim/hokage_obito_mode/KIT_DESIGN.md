# Hokage Obito: ability kit (DRAFT for the user's OK, 2026-10-20)

The what-if Obito who saved Rin, kept both eyes, and became Hokage. He fights like his two role models: Minato's
space-time warps plus Kakashi's copy-ninja style. Nothing below is built yet.

## How it differs from Ronin Obito

| | Ronin Obito (built) | Hokage Obito (this kit) |
|---|---|---|
| Fantasy | a lone swordsman, cutting through space with his eye | a Leaf commander, using ninja tools and many styles |
| Moveset | Vergil Yamato, one style | Jetstream Sam as the base + styles copied from Kagutsuchi and Mitsunari |
| Movement | Vergil's Trick = Kamui vanish | **marked kunai** + Kamui warps (Hiraishin) |
| Jutsu | Issen, Wood Spear, Flame Formation | Fire Release, Wood Release support, Rasengan / Chidori |
| Gauge | Resolve | **Will of Fire** |
| Ultimates | Heaven Slash, Focused Slash, Judgement Cut End | Kamui Shuriken, Flying Raijin x Kamui chain |
| Colour | purple | Leaf colours: white/red flame cloak, orange-red fire, blue chakra; Kamui stays colourless |

The two modes switch each other off (they share hotkeys). Mode toggle = a lesser power, as Ronin's is.

## 1. Base: Jetstream Sam as "Leaf style"
- Sam's 61 OAR sets are moved from the Ebony Blade onto a Hokage weapon (a one-handed blade with our own keyword) and
  only while the mode is on. Ronin and Vergil are untouched.
- Sam's own dashes, counters, block break, air dashes and Zandatsu stay as they are. We only add effects on top.
- Chakra = Magicka, like Ronin's Ki.

## 2. Copy Wheel (copy-ninja style switching)
Three styles. Each one is a mode effect that the OAR folders check, so a switch changes which animations play.
- **Leaf** (Sam): the balanced default, with counters and gap closers.
- **Fire Release** (Kagutsuchi's animations moved onto our weapon): directional skills with fire. Hits ignite and
  feed the Fire jutsu.
- **Copied** (Sam as the base, with chosen Mitsunari moves put in its gaps): Mitsunari's Pursuit teleport, his
  battojutsu and his aerial set. A fast, aggressive style for a single target.
- Switching: a **Copy Wheel key** cycles the styles, with a Sharingan flash and a sound.
- The Sharingan copy part: once Obito has **read** an enemy (Serana's Read logic: watch N actions), a switch made
  while fighting that enemy gives the new style a damage and poise bonus for 10 s. That rewards switching to counter
  what he has read.

## 3. Hiraishin: marked kunai (Minato's half)
- **Throw kunai** (a key): an Iron Kunai projectile (Naruto Overhaul). An enemy it hits gets the **Hiraishin seal**
  (a visible mark, 30 s). Up to 3 seals.
- **Plant a seal** (the same key held down): drops a seal kunai where he stands, as an escape anchor.
- **Warp** (a key): he flashes to the newest seal. On an enemy, he lands behind it facing its back and his next
  attack is a guaranteed stagger. On a planted seal, he lands at that spot, so it can be used to escape.
- **Risk:** moving the player by script T-posed him in all 3 Ronin tests (Ichishun). So stage 2 starts with **one
  control test** of a teleport made while he is standing still, out of any dodge. If it still T-poses, the warp rides
  on Mitsunari's Pursuit animation instead: the animation moves him, and we only add the flash and the seal.

## 4. Twin-eye Kamui (Obito's half, both eyes)
Reuses the Kamui pieces already in Sharingan Copy (phase, swirl, distortion VFX, Obito-no-Kamui sound) rather than
building new ones.
- **Phase step:** a dodge with the Mangekyo open turns him intangible for its i-frames and refunds chakra. Two
  eyes = a shorter cooldown than the one-eyed Sharingan Copy Instinct.
- **Kamui Hiraishin (the fan-dream combo):** a warp to a seal, with the Mangekyo open, goes through a Kamui swirl
  and costs no chakra if he warps again within 2 s. He can chain up to 3 seals.
- **Portal (phase 2):** an enemy projectile caught while he is phased goes into Kamui and comes back out at his
  current target.

## 5. Leaf jutsu (one key, plus a modifier)
Mostly reused spells; Ronin's Wood Spear, Issen and Flame Formation are left alone.

| Key | Leaf style | Fire Release style | Copied style |
|---|---|---|---|
| B | **Rasengan** on the next hit (Naruto Overhaul Rasengan, Minato's legacy) | **Gokakyu** fireball (Naruto Overhaul) | **Chidori** on the next hit (Kakashi's, copied) |
| Shift+B | **Wood Release: Deep Forest Emergence** (Uchiha Clan), which roots a group | **Ryuka**, the dragon flame (Naruto Overhaul) | the last spell he **copied** with the Sharingan |

Built the way Serana's Chidori and Ronin's Issen are: a pending "next hit" charge or a script cast. No attack
animation events are sent (the MCO lesson from Ronin).

## 6. Sharingan Read (Kakashi's half, adapted from Serana)
- Per enemy, he watches power attacks, casts, blocks and arrows. After N actions he has **read** that enemy (fewer
  actions with the Mangekyo open).
- A read enemy's power attack, if he has a seal on it, triggers an **auto-warp behind it** (Minato vs Tobi), with a
  cooldown.
- A read also feeds the Copy Wheel bonus (section 2) and the Will of Fire gauge.

## 7. Will of Fire gauge and ultimates
Fills on hits, reads, seal warps and kills. It also gains extra while an ally (Serana or a follower) is below 50%
health, because the Hokage protects his people. It is spent by the two ultimates:
- **Kamui Shuriken** (the ultimate key, Ronin's H key reused): a giant spinning shuriken (the Sharingan Copy barrage
  model, scaled up) flies at his target. Weak enemies get pulled into Kamui (the Focused Slash swallow rule); strong
  ones take heavy damage and a stagger.
- **Flying Raijin x Kamui chain** (the warp key with a full gauge and 2 or more seals): he warps through every seal,
  striking each sealed enemy, then lands back where he started.

## 8. Later (not in the first build)
Hokage cloak (search for an existing one first), Sharingan / Mangekyo eyes on the toggle, a Leaf-colour pass on the
Kagutsuchi VFX if they clash, a Wood Clone decoy.

## Build stages (each one tested in game before the next)
0. **Spikes:** move Sam's OAR sets onto the Hokage weapon + mode effect; the player-teleport control test.
1. Mode skeleton: ESP, quest, toggle power, Ronin exclusion, Sam on the weapon, chakra, logging hooks.
2. Kunai, seals and the warp (Hiraishin).
3. Copy Wheel: the three styles and their OAR folders.
4. Jutsu keys.
5. Sharingan Read, the auto-warp counter and the twin-Kamui phase step.
6. Will of Fire and the two ultimates.
7. Polish and balance; logging off.

## Open questions for the user
1. Weapon: which blade carries the moveset?
2. Hotkeys: kunai / warp / Copy Wheel / jutsu / ultimate keys (known taken: G, V, C, Z, X; Ronin uses B, Shift+B, H).
3. The Copy Wheel: a key to cycle styles, or styles that change on their own from what he reads?
4. Anything to cut or add before stage 0.

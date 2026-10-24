# Personalized Music: prep notes (2026-10-20)

Mod: MO2 `Personalized Music - Skyrim Special Edition No Vanilla` (esp v6.0). Tracks go in `Music/<category>/`,
named `MM<Category><NN>.xwm` with a two-digit number (the readme in each folder lists the exact pattern and the
limit, 20 or 40 per folder). A folder must be all `.xwm` or all `.wav`, never both.

Tools available: Bethesda `xwmaencode.exe` (Skyrim SE `Tools/Audio`), ffmpeg/ffprobe 9.0.1 (WinGet).

Source: `C:\Users\harvey\Downloads\Music` (447 MB). Full listing with titles/durations: `inventory.tsv`.
Installed tracks with durations: `installed.tsv`.

## What is there
- Ghost of Tsushima OST, 21 mp3 (incl. the 5-part Tsushima Suite; `05. Lord Shimura (1).mp3` is a duplicate).
- `Naruto part 2/`: 42 mp3 (Shippuden themes: Sasori, Itachi, Pain, Konan, Obito Death Theme, Kokuten, Girei...),
  plus 6 already-converted `.xwm` copies.
- `Naruto Skyrim music/`: 35 `.xwm` = converted copies of `Naruto part 2/07-43` (durations match).
- Misc: C418 lullaby/Sweden edits, `Dry Hands.mp3`, 2 YouTube `.mp4` (Retire, wind ambience), Audacity installer.

## Already installed (68 tracks)
Matching durations show many of these are already in the game: most Naruto part 2 tracks, the Tsushima Suite
and several Tsushima tracks (Combat - All, Combat - Dragon, Explore - All Hours, Castle...).

## Likely naming bugs in the installed set (not fixed, ask the user first)
- `Combat - All/MMCombatAll010.xwm` .. `MMCombatAll016.xwm` (7 files) use THREE digits; the readme pattern is
  `MMCombatAll10.xwm`. These probably never play.
- `Explore - All Hours/MMExploreAllHours010.xwm` (the Tsushima Suite V. Seiiki), same problem.
- `Explore - All Areas` skips 06 (01-05, 07, 08); a gap may or may not matter (unverified).

## Plan for the session
1. User assigns songs to categories (subfolders named after the mod's folders, or a list).
2. Script: skip duplicates of installed tracks (duration + title match), convert mp3/mp4 -> wav (ffmpeg) -> xwm
   (xwmaencode), number after each folder's last track, respect limits, never mix wav/xwm, back up `Music/` first,
   print a song -> slot table.
3. Offer to rename the 3-digit tracks above (renames only, with the user's OK).

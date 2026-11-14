# 🦁 The Lost Temple

A terminal-based adventure game. You play **Leo**, a lion exploring an ancient temple: navigate mazes, solve puzzles, collect keys, and face a guardian at the end of every level.

**Course:** 1330 · **Subclass:** D · **Group:** 7

---

## Table of Contents

- [Story Background](#story-background)
- [Game Objective](#game-objective)
- [Main Features](#main-features)
- [Game Progression](#game-progression)
- [Controls](#controls)
- [Gameplay Details](#gameplay-details)
  - [Maze Exploration](#maze-exploration)
  - [Puzzles and Keys](#puzzles-and-keys)
  - [Items and Random Events](#items-and-random-events)
  - [Boss Battles](#boss-battles)
  - [Progress and Restarting](#progress-and-restarting)
- [Runtime Environment](#runtime-environment)
- [Compatibility](#compatibility)
- [Testing](#testing)
- [Known Limitations](#known-limitations)
- [Member Contributions](#member-contributions)

---

## Story Background

Long ago, ancient guardians built a temple to protect a powerful treasure. They filled its passages with mazes and trials to challenge anyone who entered. Leo discovers the forgotten temple and begins a journey through its dangers, hoping to uncover its secrets.

## Game Objective

Complete four levels and defeat the **Evil Panda** to claim the treasure.

- **Levels 1–3:** Explore a maze, solve a puzzle to obtain a key, and reach the exit while surviving enemy encounters. If a thief steals your map, you must recover it. After leaving the maze, Leo faces that level's Boss. Defeating the Boss unlocks the next level.
- **Level 4:** A pillared corridor leads to the final battle against the Evil Panda.

## Main Features

- **Three themed mazes:** explore the Starry Canyon, the Spooky Manor, and the Mysterious Forest using WASD or the arrow keys.
- **Three puzzle challenges:** solve the Guardian's Riddle, the Three Doors logic puzzle, and the Sphinx's Riddle to earn keys.
- **Enemies and exploration events:** avoid roaming enemies, recover a stolen map, and encounter random blessings or traps.
- **Health and energy resources:** collect healing items and lightning charges that increase starting energy in Boss battles.
- **Four distinct Bosses:** face the Meteor Golem, Manor Wraith, Thorn Treant, and Evil Panda, each with different combat behaviour.
- **Turn-based combat:** choose attacks, defence, healing, or energy recovery while watching the Boss's next intended move.
- **Terminal presentation:** play within an 80 × 24 terminal area, with scrolling views for larger mazes and an animated corridor before the final battle.

## Game Progression

1. Only **Level 1** is unlocked when the program starts.
2. For **Levels 1–3**, explore the maze, solve its puzzle to obtain a key, and reach the exit. Leaving the maze requires **both the key and the map**. A Boss battle follows the maze, and winning unlocks the next level.
3. **Level 4** begins with a corridor scene. Pressing `W` starts Leo's automatic charge towards the gate, followed by the final battle against the Evil Panda.
4. After completing a level, you return to the menu to select an unlocked level. Defeating the Evil Panda completes the game.

## Controls

| Context | Input | Action |
|---|---|---|
| Main menu | `1`–`4` | Select an unlocked level |
| Main menu | `0` or `Q` | Exit the game |
| Maze | `W` `A` `S` `D` or arrow keys | Move Leo |
| Maze | `Q` | Return to the menu |
| Puzzle 1 | `A` / `B` / `C` / `D` | Select an answer |
| Puzzle 2 | `A` / `B` / `C` | Select a door |
| Puzzles 1–2 | `Q` | Leave the puzzle temporarily |
| Puzzle 3 | English text, then `Enter` | Submit an answer |
| Puzzle 3 | `Enter` with an empty answer | Leave the puzzle temporarily |
| Corridor | `W` | Start the automatic charge towards the gate |
| Corridor | `Q` | Return to the menu |
| Boss battle | `1`–`5` | Use a combat action |
| Boss battle | `Q`, then `Y` or `N` | Confirm or cancel fleeing |
| During play | `Ctrl+C` | Exit the game |

---

## Gameplay Details

### Maze Exploration

- Leo starts each maze with **100 HP**, a **map**, and **zero Boss charge**.
- Walls block movement. After each successful movement, enemies take a turn. Colliding with an active enemy costs **25 HP** and temporarily puts that enemy to sleep.
- In Levels 2 and 3, approaching the central area can trigger a **thief** who steals Leo's map. Reach the thief's position to recover it. You need both the key and the map to leave the maze.
- If Leo's HP reaches zero, you can restart the maze or return to the menu.

### Puzzles and Keys

Stepping onto a key tile starts the puzzle for the current level.

| Level | Puzzle | Format |
|---|---|---|
| 1 | The Guardian's Riddle | Multiple-choice word riddle |
| 2 | The Three Doors | Identify the door hiding the key when exactly one statement is true |
| 3 | The Sphinx's Riddle | Type an English answer to a riddle about the stages of life |

- Incorrect answers allow another attempt.
- Solving a puzzle adds the key to your inventory, removes its tile from the maze, and awards **100 XP**.
- If you leave a puzzle before solving it, the key remains available. Move away and step onto the key tile again to retry.

### Items and Random Events

| Symbol | Effect |
|---|---|
| 🔑 | Starts a puzzle and is collected after a correct answer |
| 🗺️ | Required alongside the key to leave the maze |
| 💟 | Restores 20 HP, up to the maximum of 100 |
| 🍇 | Restores HP to 100 |
| ⚡ | Adds one Boss charge, up to a maximum of three |
| ❓ | Triggers a random event |
| ⛺ | Maze exit |

A mystery event (❓) randomly provides one of four outcomes:

- Restore 20 HP
- Gain 40 XP
- Gain one Boss charge
- Lose 15 HP

Lightning items can also appear randomly after movement. Ordinary movement onto a path awards **5 XP**. XP is accumulated as your score.

### Boss Battles

Each Boss battle starts Leo at **100 HP** with **zero armour**. Starting energy is **5 + the maze's collected Boss charge**. In Level 4, the corridor provides the maximum charge bonus of three.

**Player actions**

| Key | Action | Energy cost | Base effect |
|---|---|---|---|
| `1` | Claw Strike | 2 | Deal 12 damage |
| `2` | Guard Stance | 1 | Gain 12 armour |
| `3` | Herbal Heal | 3 | Restore up to 15 HP |
| `4` | Sun Fang | 4 | Deal 22 damage |
| `5` | Focus Breath | 0 | Restore up to 3 energy |

**Combat rules**

- Energy is capped at 10, and HP is capped at 100. An action requires sufficient energy.
- The Boss acts after each successfully used action, unless that action defeats it. Its upcoming move is shown as **Intent**.
- Attacks have a 12% chance to deal double base damage.
- A shielded attack deals half damage, rounded down.
- An unshielded attack restores one energy.
- Blocking damage with armour restores one energy.
- Armour expires after the Boss's response.
- Energy-draining moves cannot reduce energy below two.

**Bosses**

| Boss | Starting HP | Behaviour |
|---|---|---|
| Meteor Golem | 60 | Repeats two attacks followed by a rest turn |
| Manor Wraith | 75 | Uses random attacks or energy drain and has a 35% shield chance |
| Thorn Treant | 80 | Uses random attacks or self-healing and has a 15% shield chance |
| The Evil Panda | 100 | Has a 20% shield chance and enters rage at half HP or below, increasing attack damage by approximately 25% |

After defeat, you may retry the Boss battle. Winning unlocks the next level, or completes the game after the final Boss.

### Progress and Restarting

- Unlocked levels and XP are retained while the program remains open.
- Re-entering a maze resets its layout, items, enemies, health, inventory, and Boss charge.
- Progress is stored in memory. Restarting the program resets XP and makes only Level 1 available again.

---

## Runtime Environment

### Python Libraries

The game uses Python's standard library only (`os`, `sys`, `time`, `random`, `re`, `shutil`, `textwrap`, `unicodedata`, `collections`, `contextlib`). **No third-party packages are required.**

Keyboard handling uses `msvcrt` on Windows and `tty`, `termios`, and `select` on macOS and Linux. The correct modules are selected automatically according to the operating system.

### Terminal Requirements

- **Minimum terminal size:** 80 columns × 24 rows
- **Display support:** ANSI colour and cursor-control sequences, Unicode characters, and emoji
- **Input support:** interactive keyboard input for movement, menu selections, and typed puzzle answers

The game pauses and displays a resize message when the terminal becomes smaller than 80 × 24. Play resumes after you enlarge the terminal.

When running through Docker, an interactive terminal must be allocated using the appropriate `-it` options.

## Compatibility

The code includes keyboard handling for Windows, macOS, and Linux.

> **Tested environments:** _TODO: record the operating systems, Python versions, and terminals you actually tested on._

## Testing

The group tested the complete gameplay sequence, including maze exploration, all three puzzles, key collection, map recovery, the corridor scene, and all four Boss battles.

Movement, answer checking, item effects, combat actions, level unlocking, and restart options worked as expected during playtesting. Transitions between mazes, puzzles, Boss battles, and menus also worked correctly, allowing the game to be played through to the final victory.

## Known Limitations

- **Session-only progress:** progress is stored in memory. Closing the program resets XP and unlocked levels.
- **Terminal requirements:** the game requires an interactive terminal of at least 80 × 24 characters. Emoji appearance and alignment may vary between terminal fonts.
- **Fixed puzzle answers:** the three puzzles use fixed questions and answers, so their replay challenge is limited.
- **English text input:** the Sphinx's Riddle accepts a predefined set of English answers. Other wording may be rejected even if it expresses the same idea.

## Member Contributions

| Member | Main Responsibilities |
|---|---|
| Ma Lo | Background story and the three puzzles, including question design, answer checking, and integration with key collection |
| _TODO_ | Documentation and video production |

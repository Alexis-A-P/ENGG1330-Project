# AI Use

Generative AI used: Yes

## Entry 1

- Member and date: Ma Lo, October–November 2026
- Tool and model/version: ChatGPT / Codex
- Purpose: Explore story and puzzle ideas, understand Python logic, and debug.
- Substantial parts affected (files/materials): Story text and puzzle-related code in `project.py` (now `main.py`).
- What was kept, changed, or rejected, and how results were checked (tests or corrections): AI provided explanations and draft code snippets. Selected puzzle ideas were adapted to the group's game, while alternative ideas were rejected. The final implementation was playtested to check answer handling, retries, key collection, and transitions back to the maze.

## Entry 2

- Member and date: Ma Lo, November 2026
- Tool and model/version: ChatGPT / Codex
- Purpose: Generate a README outline, summarise game features and rules, and improve English wording.
- Substantial parts affected (files/materials): README draft and AI-use documentation.
- What was kept, changed, or rejected, and how results were checked (tests or corrections): The outline and selected draft wording were adapted for the shared document. Descriptions were checked against the supplied game code and submission requirements. Unconfirmed environment details were left out, and the draft was shared with group members for review and correction.

## Entry 3

- Member and date: Xue Leshan, November 2026
- Tool and model/version: DeepSeek
- Purpose: Polish the boss fight interface and text descriptions to improve player immersion, engagement, and smooth operation.
- Substantial parts affected (files/materials): Boss battle (combat loop) in `main.py`.
- What was kept, changed, or rejected, and how results were checked (tests or corrections): AI suggestions for descriptive text and layout formatting were adopted and adapted. The updated interface flow was verified through manual playtesting across all four boss battles to ensure smooth text prompts and responsiveness. Overly complex UI additions that conflicted with the terminal style were rejected.

## Entry 4

- Member and date: Xue Leshan, November 2026
- Tool and model/version: Gemini
- Purpose: Refine the pseudo-3D corridor rendering effect by adjusting the pillar perspective and projection for better visual realism.
- Substantial parts affected (files/materials): Level 4 corridor scene in `main.py`.
- What was kept, changed, or rejected, and how results were checked (tests or corrections): Mathematical adjustments suggested by the AI for column scaling and spacing were integrated. Results were checked by running the scene in the terminal to confirm proper depth perception and correct alignment.

## Entry 5

- Member and date: Xue Leshan, November 2026
- Tool and model/version: Gemini
- Purpose: Create and refine visual diagrams, stage overviews, and the demo video poster to make the demo clearer.
- Substantial parts affected (files/materials): Demo/technical video.
- What was kept, changed, or rejected, and how results were checked (tests or corrections): Generated visual concepts matching the game's core theme were kept and polished. Layouts and text placement were reviewed against the video editing timeline and group requirements to ensure visual consistency.

## Entry 6

- Member and date: Aadarsha Pudasaini, October–November 2026
- Tool and model/version: Claude and Claude Code (Anthropic)
- Purpose: Tidy my boss battle design into data tables, draw the boss ASCII art, and merge our maze, battle, and puzzle files into one program.
- Substantial parts affected (files/materials): Boss battle section and structure of `main.py`; boss ASCII art.
- What was kept, changed, or rejected, and how results were checked (tests or corrections): I designed the battle rules and game flow before using AI. I kept the tidied structure and the art, tuned boss HP, damage, and card costs myself after playtesting, chose turn-based enemy movement over my earlier real-time timer, and rejected extra features. I read every change and can explain each line. I tested in a fresh course container at 80 × 24, playing all four levels including wrong keys and restarts.

## Entry 7

- Member and date: Aadarsha Pudasaini, 15–16 November 2026
- Tool and model/version: Claude (Claude Opus 5.5 and Claude Fable 5.2)
- Purpose: Slides and assembly for the demo video; background music for the trailer; polishing the README, acknowledgements, and trailer outline.
- Substantial parts affected (files/materials): Demo video slides and final joined file; trailer background music; `README.md`; `acknowledgements.md`; trailer outline.
- What was kept, changed, or rejected, and how results were checked (tests or corrections): We recorded all footage and voice-over ourselves, and I decided the content of each section. AI made some slides from our code, joined and sped up our clips to fit five minutes, and generated an original music track for the trailer. I supplied the facts, corrected the drafts, checked every statement against `main.py`, and watched both final videos in full.

## Entry 8

- Member and date: Yinyuan Li, October–November 2026
- Tool and model/version: Google Gemini and Canva AI
- Purpose: Make the trailer more vivid, and make keyboard input work on both macOS and Windows.
- Substantial parts affected (files/materials): Illustrated scenes in the trailer; keyboard-input code in `main.py`.
- What was kept, changed, or rejected, and how results were checked (tests or corrections): I recorded all the gameplay footage myself. To make the trailer more vivid, I used Gemini to generate pictures based on my background story for each map, then turned them into short animated clips with Canva AI. To make the game run smoothly on every device, I generated code that detects the user's operating system and uses the matching standard-library method to read keyboard input, so no extra packages are needed.

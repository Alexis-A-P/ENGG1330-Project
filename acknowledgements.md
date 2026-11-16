# Acknowledgements

**The Lost Temple** · ENGG1330 Group Project · Subclass 1D · Group 7

This file explains what our group made ourselves, what we borrowed, and what we adapted from elsewhere. Our use of generative AI is recorded separately in `ai_use.md`.

## What we created

Apart from the items listed further down, everything in `main.py` is our group's own work: the three mazes, the turn system, the map thief, the mystery events, the puzzle logic, the card battle system, the four Bosses' behaviour, the corridor scene, and the story text. Where generative AI helped with any of this, the details are in `ai_use.md`.

## What we borrowed

| Item | Source | How we used it |
|---|---|---|
| Course container files (`compose.yaml`, `dockerfile`, `entrypoint.sh`, `requirements.txt`, `vimrc`) | ENGG1330 teaching team, project starter, environment `engg1330-project:2026-v03` | Used as provided. Our only change was setting the default command to `python main.py`. |
| Python 3.13 standard library | [Python Software Foundation](https://docs.python.org/3.13/library/), PSF licence | The game imports standard-library modules only. It uses none of the extra packages installed in the container. |
| Emoji characters (🦁, 🧱, 🔑 and others) | [Unicode Standard](https://home.unicode.org/emoji/) | Printed as ordinary text and drawn by the terminal's font. The game has no image files. |

## What we adapted

| Part of the game | Where the idea comes from | What is ours |
|---|---|---|
| The Sphinx's Riddle (Level 3) | The riddle of the Sphinx from the Greek myth of Oedipus. It is ancient and in the public domain. One classical account is [Apollodorus, *Library* 3.5.8](https://cts.perseids.org/read/greekLit/tlg0548/tlg001/perseus-eng2/3.5.8-3.6.6). | The wording used in the game, the hint, the typed-answer format, and the list of accepted answers. |
| The Guardian's Riddle (Level 1) | A traditional wordplay riddle ("What has keys but cannot open locks?") with no known author. It appears in many riddle collections, for example [Mental Floss](https://www.mentalfloss.com/entertainment/riddles-with-answers). | The four answer options and the feedback messages. |
| The Three Doors (Level 2) | The classic style of logic puzzle in which exactly one statement is true. | How the puzzle is checked in the game and how it leads to the key. |
| Boss ASCII art (Meteor Golem, Manor Wraith, Thorn Treant, Evil Panda) | Made with help from generative AI. See `ai_use.md`. | `ai_use.md` records what we kept, changed, and checked. |

## Tools

We wrote and tested the game with Visual Studio Code, GitHub, GitHub Codespaces, and Docker.

## Thanks

Thank you to the ENGG1330 teaching team and our student teaching assistant for the starter environment and for their support during the project.

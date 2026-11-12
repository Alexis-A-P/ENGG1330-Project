"""
The Lost Temple - a turn-based console puzzle adventure (ENGG1330 group project).

Leo the lion clears three mazes (solve a riddle to get the key, then reach the
exit), charges down the temple corridor, and fights a different boss at the end
of every level. Everything is drawn inside an 80 x 24 terminal area.

Run:  python project.py
"""
import os
import re
import sys
import time
import random
import shutil
import textwrap
import unicodedata
from collections import deque
from contextlib import contextmanager

IS_WINDOWS = os.name == "nt"

if IS_WINDOWS:
    import msvcrt
    os.system("")  # turns on ANSI colour codes in the Windows console
else:
    import tty
    import termios
    import select

SCREEN_W, SCREEN_H = 80, 24  # the play area required by the brief


# ============================================================ keyboard ======

WIN_ARROWS = {b"H": "\x1b[A", b"P": "\x1b[B", b"K": "\x1b[D", b"M": "\x1b[C"}
ARROWS = {"A": "W", "B": "S", "C": "D", "D": "A"}  # escape-code letter -> WASD


def read_raw():
    """Return the keys waiting in the input buffer as text, or None. Never blocks."""
    if IS_WINDOWS:
        if not msvcrt.kbhit():
            return None
        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):  # arrow keys arrive as two bytes
            return WIN_ARROWS.get(msvcrt.getch())
        data = ch.decode("utf-8", errors="ignore")
    else:
        fd = sys.stdin.fileno()
        if not select.select([fd], [], [], 0)[0]:
            return None
        data = os.read(fd, 32).decode("utf-8", errors="ignore")
    if "\x03" in data:  # Ctrl+C arriving as a character
        raise KeyboardInterrupt
    return data.replace("\r", "\n") or None


def get_single_keypress():
    """One key as an upper-case character (arrows become WASD), or None."""
    data = read_raw()
    if not data:
        return None
    if data.startswith(("\x1b[", "\x1bO")) and len(data) >= 3:
        return ARROWS.get(data[2])
    if data[0] == "\x1b":
        return None
    return data[0].upper()


def flush_input():
    """Throw away keys pressed while the game was busy (e.g. during animations)."""
    if IS_WINDOWS:
        while msvcrt.kbhit():
            msvcrt.getch()
    else:
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)


def wait_for_key(valid=None):
    """Block until a key in `valid` (any key if None) is pressed.
    The size check runs while waiting, so play pauses if the terminal shrinks."""
    while True:
        ensure_size()
        key = get_single_keypress()
        if key and (valid is None or key in valid):
            return key
        time.sleep(0.02)


def read_line(max_len):
    """Read a typed answer with echo and Backspace. The length is capped so the
    text can never wrap past column 80. Only printable ASCII is accepted."""
    text = ""
    sys.stdout.write("\033[?25h")  # show the cursor while typing
    sys.stdout.flush()
    try:
        while True:
            if ensure_size():  # screen was redrawn after a resize
                sys.stdout.write(text)
            data = read_raw()
            if not data:
                sys.stdout.flush()
                time.sleep(0.02)
                continue
            if data[0] == "\x1b":  # ignore arrow keys and other escape codes
                continue
            for ch in data:
                if ch == "\n":
                    return text
                if ch in ("\x7f", "\b"):
                    if text:
                        text = text[:-1]
                        sys.stdout.write("\b \b")
                elif ch.isascii() and ch.isprintable() and len(text) < max_len:
                    text += ch
                    sys.stdout.write(ch)
            sys.stdout.flush()
    finally:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()


@contextmanager
def game_terminal():
    """Read keys one at a time with a hidden cursor. The terminal is always
    restored afterwards, even after Ctrl+C or an unexpected error."""
    old = None
    if not IS_WINDOWS:
        old = termios.tcgetattr(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
    sys.stdout.write("\033[?25l\033[2J\033[H")
    sys.stdout.flush()
    try:
        yield
    finally:
        sys.stdout.write("\033[0m\033[?25h\033[2J\033[H")
        sys.stdout.flush()
        flush_input()
        if old is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)


# ============================================================ drawing =======

R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
B = "\033[94m"
M = "\033[95m"
C = "\033[96m"
WHITE = "\033[97m"
DIM = "\033[90m"
W = "\033[0m"
BOLD = "\033[1m"

ANSI_RE = re.compile(r"\033\[[0-9;?]*[A-Za-z]")


def char_widths(text):
    """Yield (char, columns) for text without colour codes. Wide emoji use 2
    columns; an emoji selector (U+FE0F) widens the symbol before it to 2."""
    prev = 0
    for ch in text:
        if ch == "\ufe0f":
            w = 1 if prev == 1 else 0
            prev = 2
        elif ch == "\u200d" or unicodedata.combining(ch):
            w = 0
        else:
            w = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
            prev = w
        yield ch, w


def vis_len(text):
    """Number of terminal columns `text` occupies."""
    return sum(w for _, w in char_widths(ANSI_RE.sub("", text)))


def clip(text, width):
    """Cut text to `width` columns (keeping colour codes) so it never wraps."""
    if vis_len(text) <= width:
        return text
    out, used = [], 0
    for part in re.split(f"({ANSI_RE.pattern})", text):
        if ANSI_RE.fullmatch(part):
            out.append(part)
            continue
        for ch, w in char_widths(part):
            if used + w > width:
                return "".join(out) + W
            out.append(ch)
            used += w
    return "".join(out) + W


def pad(text, width, align="left"):
    gap = max(0, width - vis_len(text))
    if align == "center":
        left = gap // 2
        return " " * left + text + " " * (gap - left)
    if align == "right":
        return " " * gap + text
    return text + " " * gap


def box(lines, width=50):
    out = ["╔" + "═" * width + "╗"]
    out += ["║" + pad(clip(l, width), width, "center") + "║" for l in lines]
    out.append("╚" + "═" * width + "╝")
    return out


last_frame = []  # remembered so the screen can be redrawn after a resize


def term_size():
    """The real terminal size. shutil.get_terminal_size() trusts the COLUMNS and
    LINES variables, which the course container always sets to 80x24, so the
    terminal itself is asked first."""
    try:
        cols, rows = os.get_terminal_size(sys.stdout.fileno())
    except (OSError, ValueError):
        cols = rows = 0
    if cols <= 0 or rows <= 0:
        cols, rows = shutil.get_terminal_size((SCREEN_W, SCREEN_H))
    return cols, rows


def write_frame(lines, clear=True):
    # No newline after the last line, so a full 24-row frame never scrolls.
    sys.stdout.write(("\033[H\033[J" if clear else "\033[H") + "\n".join(lines))
    sys.stdout.flush()


def ensure_size():
    """While the terminal is smaller than 80x24, pause and show a resize message
    cut to fit the space available. Returns True if play was paused."""
    paused = False
    while True:
        cols, rows = term_size()
        if cols >= SCREEN_W and rows >= SCREEN_H:
            break
        paused = True
        msg = [f"Terminal is {cols}x{rows}.",
               f"Please resize to {SCREEN_W}x{SCREEN_H}.",
               "The game is paused."]
        write_frame([m[:max(1, cols - 1)] for m in msg[:max(1, rows - 1)]])
        time.sleep(0.25)
    if paused:
        flush_input()
        write_frame(last_frame)
    return paused


def render(lines, frame_w=0, clear=True):
    """Draw a full screen inside the 80x24 area, centred horizontally.
    Anything beyond row 24 or column 80 is cut off instead of scrolling."""
    global last_frame
    lines = lines[:SCREEN_H]
    widest = max([frame_w] + [vis_len(l) for l in lines])
    margin = max(0, min((SCREEN_W - (frame_w or widest)) // 2, SCREEN_W - widest))
    last_frame = [clip(" " * margin + l, SCREEN_W) for l in lines]
    ensure_size()
    write_frame(last_frame, clear)


def pause_screen(lines, frame_w=0, valid=None):
    """Show a screen, ignore keys typed earlier, and return the next valid key."""
    render(lines, frame_w)
    flush_input()
    return wait_for_key(valid)


def bar(cur, mx, length=20, color=G):
    cur = max(0, min(cur, mx))
    filled = int(length * cur / mx) if mx else 0
    if cur > 0 and filled == 0:
        filled = 1
    return f"{color}{'█'*filled}{DIM}{'░'*(length-filled)}{W}"


# ============================================================ story =========

STORY_TITLE = f"{BOLD}Game Title: The Lost Temple{W}"
STORY_PARAGRAPHS = [
    "Long ago, an ancient temple was built to protect a mysterious treasure "
    "with extraordinary powers. To keep the treasure safe, the ancient guardians "
    "created a complex maze filled with magical creatures and hidden trials.",
    "Over time, the temple was forgotten, but its ghostly guardians continued "
    "to patrol the maze and protect its secrets.",
    "One day, Leo, a brave young lion, discovered the entrance to the lost temple. "
    "Determined to uncover its mysteries, he decided to venture into the maze and "
    "search for the legendary treasure.",
    "However, the journey would not be easy. Leo must navigate the maze, avoid "
    "wandering ghosts, collect ancient items, and solve puzzles left behind by "
    "the guardians. Will Leo succeed in discovering the temple's hidden treasure? "
    "His adventure begins now.",
]


def story_lines():
    lines = [STORY_TITLE, ""]
    for para in STORY_PARAGRAPHS:
        lines += textwrap.wrap(para, 70) + [""]
    return lines + [f"{Y}Press any key to continue...{W}"]


def story_screen():
    pause_screen(box(story_lines(), width=74))


LEVEL_NAMES = ["THE STARRY CANYON", "THE SPOOKY MANOR",
               "THE MYSTERIOUS FOREST", "THE INNER THRONE"]
LEVEL_EMOJIS = ['⛰️', '🌋', '⛈️', '🏯']
NUM_LEVELS = len(LEVEL_NAMES)

LEVEL_INTROS = {
    1: [
        "Leo decides to rest in a quiet nearby village for the night.",
        "However, he is unaware that a strange meteorite struck the",
        "nearby river upstream just hours before.",
        "After drinking the tainted river water, the villagers have",
        "begun to transform and behave abnormally...",
    ],
    2: [
        "While tracking the lost temple, a grand yet chilling manor",
        "suddenly looms ahead in Leo's path.",
        "As he approaches, he notices an eerie lack of life: plants",
        "are withered, windows shattered, and dark vines choke the walls.",
        "Though filled with dread, he knows he must step inside.",
    ],
    3: [
        "Consulting his map, Leo realizes the temple is near. But a bizarre,",
        "uncharted forest blocks his only route between towering cliffs.",
        "Stepping inside, the air grows warm and thick with heavy fog,",
        "and colossal, glowing flora tower above him.",
        "He spots a vivid, unknown fruit; taking a single bite, a sudden",
        "surge of primal energy courses through his veins.",
    ],
    4: [
        "Having endured trials of stars, shadows, and ancient flora,",
        "Leo finally stands before the golden gates of the Inner Sanctuary.",
        "The legendary treasure gleams in the distance - but guarding it",
        "sits the ultimate master of the temple:",
        "The ruthless, cosmic-powered Evil Panda.",
        "Draw your sword, brave Leo. The final battle for glory begins now!",
        "",
        f"{C}Press W to charge down the pillared corridor.{W}",
    ],
}


def level_intro(level):
    lines = ["", f"{BOLD}{LEVEL_EMOJIS[level - 1]} LEVEL {level}: "
             f"{LEVEL_NAMES[level - 1]} {LEVEL_EMOJIS[level - 1]}{W}", ""]
    lines += LEVEL_INTROS[level] + ["", f"{Y}Press any key to begin.{W}", ""]
    pause_screen(["", ""] + box(lines, width=72))


# ============================================================ maze ==========

wall_1 = "🌠"
path = "⬛"
player = "🦁"
enemy_1 = "🧟"
maze_key = "🔑"
mystery = "❓"
termina_l = "⛺"
sleeping = "💤"
lightning = "⚡"
wall_2 = "🧱"
wall_3 = "🌳"
enemy_2 = "👻"
enemy_3 = "🦖"
medkit = "💟"
ambulance = "🍇"
map_icon = "🗺️"
thief = "🦹"

TILES = {
    "#": wall_1, ".": path, "P": player, "E": enemy_1,
    "K": maze_key, "?": mystery, "T": termina_l, "L": lightning,
    "$": wall_2, "@": wall_3, "F": enemy_2, "G": enemy_3, "M": medkit, "A": ambulance
}
wallist = {wall_1, wall_2, wall_3}

maze1 = [
    "#########T#########",
    "#P......#.....M...#",
    "#.####..#.#####...#",
    "#......##.....#...#",
    "#.###......##.#...#",
    "#...#E.##.....#...#",
    "#.#....#.M.##.....#",
    "#.#.##...#....###.#",
    "#...#....#..?...#.#",
    "#.###.##.#..##.#K.#",
    "#M..E....#.....M..#",
    "###################"
]
maze2 = [
    "$$$$$$$$$$$$$$$$$$$$$$$$$$",
    "$P...M..$...F.....$.....T$",
    "$.$$$$..$.$$$$$...$.$$$..$",
    "$...F..$$.M...$...$...$..$",
    "$.$$$......$$.$...$.$.$..$",
    "$...$..$$.....$.....$.F..$",
    "$......$...$$.....$$$...$$",
    "$.$.$$...$....$$$...F.$..$",
    "$...$....$..?..F$.....$..$",
    "$.$$$.$$....$$...K....$..$",
    "$...E....$............$..$",
    "$$$$$$$..$$$$$$$$$$$$..$$$",
    "$.....$..M...M....F...$M.$",
    "$.$$$.$.$$$$$$$$$$$$..$..$",
    "$F..$.......$.......$....$",
    "$$..$$$$$$..$.$$$$$.$$$..$",
    "$...$....$..$...F.$...$..$",
    "$.$$$.$..$.$$$$.$.$$$.$..$",
    "$F..M.$F...M.......F..E..$",
    "$$$$$$$$$$$$$$$$$$$$$$$$$$"
]
maze3 = [
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    "@P.....@M....G.....@.....M...@",
    "@.@@@@.@.@@@@@@@.@.@@@@@@@.@@@",
    "@...@..@.......@.@.....@..G..@",
    "@.@.@.@@@@@@@.@@.@.@@@...@@@@@",
    "@.@.@..@.....@...A.@.@...@...@",
    "@.@.@@@@.@...@@@@@@@.@.@.@.@.@",
    "@...@....@...@.......@.@.@.@.@",
    "@.@@@.@@@@...@.@@@@@@@.@.@.@.@",
    "@.M.@....@...@.....@...@.@.@.@",
    "@.@@@@@@.@.@@@@@@@...@.@.@.@@@",
    "@.G....@.@.M.....@.@.@.@.....@",
    "@@@@@@.@.@.@@@@@.@.@.@.@@@@@@@",
    "@..M.@.@.@.@.G.@.@.@.@......G@",
    "@.@@.@.@.@.@.@.@.@.@.@@@@@@@.@",
    "@.@@.@.@.@.@.@M@.@.@.@.....M.@",
    "@.@@.@...@.@.@.@.@.@.@.@.@@@@@",
    "@.@@.@@@@@.@.@.@.@.@.@.@.....@",
    "@....@...@.@...@.@.@.@.@.@.@@@",
    "@@@@@@.@.@.@.@@@...@.@.@.@.G.@",
    "@....@.@.@.@...@.@.@.@.@.@@@.@",
    "@.@@.@.@.@.@.@@@@@M@.@.@.@.K.@",
    "@....@.@...@..G....@.@A@.@.@.@",
    "@.M..@.@.@@@@@@@@@@@@@T@.@...@",
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
]

mazetotal = [maze1, maze2, maze3]  # level 4 is the corridor + final boss
unlocked_level = [1]
MAX_HEALTH = 100
REQUIRE_KEY = True
DORMANT_TURNS = 3
LIGHTNING_RESPAWN_CHANCE = 0.12
MAX_BATTLE_CHARGE = 3
VIEW_H = 16  # maze rows shown at once; taller mazes scroll with Leo

exp = 0
health_level = MAX_HEALTH
battle_charge = 0
inventory = [map_icon]

current_level_num = 1
base_grid = []
player_pos = (0, 0)
enemies = []
reachable = set()
thief_pos = None
thief_active = False

message_text = ""
message_until = 0

DIRS = {"W": (0, -1), "S": (0, 1), "A": (-1, 0), "D": (1, 0)}
ENEMY_DIRS = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}
OPPOSITE = {"left": "right", "right": "left", "up": "down", "down": "up"}


def set_message(text, seconds=2.4):
    global message_text, message_until
    message_text = text
    message_until = time.time() + seconds


def heal(emoji):
    global health_level
    if emoji == medkit:
        health_level = min(MAX_HEALTH, health_level + 20)
    elif emoji == ambulance:
        health_level = MAX_HEALTH


def gain_battle_charge(n=1):
    global battle_charge
    battle_charge = min(MAX_BATTLE_CHARGE, battle_charge + n)


def in_grid(x, y):
    return 0 <= y < len(base_grid) and 0 <= x < len(base_grid[0])


def find_reachable(start):
    """Every cell Leo can walk to from `start` (breadth-first search).
    Random spawns use this so nothing lands somewhere Leo cannot reach."""
    seen, queue = {start}, deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in DIRS.values():
            nxt = (x + dx, y + dy)
            if (nxt not in seen and in_grid(*nxt)
                    and base_grid[nxt[1]][nxt[0]] not in wallist):
                seen.add(nxt)
                queue.append(nxt)
    return seen


def load_level(number):
    global current_level_num, base_grid, player_pos, enemies, inventory
    global reachable, thief_pos, thief_active
    current_level_num = number
    base_grid = []
    enemies = []
    inventory = [map_icon]
    thief_pos, thief_active = None, False
    for y, row in enumerate(mazetotal[number - 1]):
        cells = []
        for x, ch in enumerate(row):
            if ch == "P":
                player_pos = (x, y)
                ch = "."
            elif ch in ("E", "F", "G"):
                enemies.append({"pos": (x, y), "icon": TILES[ch], "dir": None, "dazed": 0})
                ch = "."
            cells.append(TILES[ch])
        base_grid.append(cells)
    reachable = find_reachable(player_pos)
    spawn_lightning(4)


def all_open_cells():
    return [(x, y) for (x, y) in reachable
            if base_grid[y][x] == path and (x, y) != player_pos]


def spawn_lightning(count=1):
    cells = all_open_cells()
    random.shuffle(cells)
    for x, y in cells[:count]:
        base_grid[y][x] = lightning


def maybe_respawn_lightning():
    if random.random() < LIGHTNING_RESPAWN_CHANCE:
        spawn_lightning(1)


def tile_at(x, y):
    if (x, y) == player_pos:
        return player
    if thief_active and thief_pos == (x, y):
        return thief
    for en in enemies:
        if en["pos"] == (x, y):
            return sleeping if en["dazed"] > 0 else en["icon"]
    return base_grid[y][x]


def check_theif_trigger():
    """In levels 2 and 3 a thief steals the map near the middle of the maze."""
    global thief_active, thief_pos
    if current_level_num in (2, 3) and not thief_active and map_icon in inventory:
        cx, cy = len(base_grid[0]) // 2, len(base_grid) // 2
        px, py = player_pos
        if abs(px - cx) <= 2 and abs(py - cy) <= 2:
            open_cells = all_open_cells()
            if not open_cells:  # nowhere for the thief to hide: no theft
                return
            inventory.remove(map_icon)
            thief_active = True
            thief_pos = random.choice(open_cells)
            set_message(f"{R}🦹 A sneaky Thief stole your {map_icon} Map! Chase him down!{W}", 4.0)


def draw_maze():
    rows, cols = len(base_grid), len(base_grid[0])
    inner = cols * 2
    # Vertical scrolling window that follows Leo, so tall mazes fit in 24 rows.
    top = min(max(0, player_pos[1] - VIEW_H // 2), max(0, rows - VIEW_H))
    bottom = min(rows, top + VIEW_H)
    up = "▲" if top > 0 else "═"
    down = "▼" if bottom < rows else "═"
    half = inner // 2 - 1

    lvl_emoji = LEVEL_EMOJIS[current_level_num - 1]
    lines = [f"{BOLD}{C}{pad(f'{lvl_emoji} THE LOST TEMPLE - LEVEL {current_level_num} {lvl_emoji}', inner + 2, 'center')}{W}"]
    lines.append("╔" + "═" * half + up + "═" * (inner - half - 1) + "╗")
    for y in range(top, bottom):
        lines.append("║" + "".join(tile_at(x, y) for x in range(cols)) + "║")
    lines.append("╚" + "═" * half + down + "═" * (inner - half - 1) + "╝")

    msg = message_text if time.time() < message_until else ""
    items = " ".join(inventory) if inventory else f"{DIM}(empty){W}"
    charge = f"{Y}{'⚡' * battle_charge}{DIM}{'·' * (MAX_BATTLE_CHARGE - battle_charge)}{W}"
    lines += [
        f" HP {bar(health_level, MAX_HEALTH, 20, G)} {max(0, health_level):>3}/{MAX_HEALTH}"
        f"   XP {Y}{exp}{W}   Boss Charge {charge}",
        f" Items: {items}",
        f" {msg}",
        f" {DIM}WASD/arrows move, Q menu   {maze_key} key  {mystery} mystery  "
        f"{lightning} charge  {termina_l} exit{W}",
    ]
    render(lines, SCREEN_W - 4)


def getexp(method):
    global exp
    if method == "moveblock":
        exp += 5
    elif method == "solvepuzzle":
        exp += 100
    elif method == "heal1":
        exp += 20
    elif method == "heal2":
        exp += 40


def mystery_event():
    global health_level, exp
    roll = random.choice(["heal", "xp", "trap", "charge"])
    if roll == "heal":
        health_level = min(MAX_HEALTH, health_level + 20)
        set_message(f"{G}❓ Blessing! +20 HP{W}")
    elif roll == "xp":
        exp += 40
        set_message(f"{Y}❓ Ancient insight! +40 XP{W}")
    elif roll == "charge":
        gain_battle_charge(1)
        set_message(f"{Y}❓ Temple spark! +1 Boss Charge{W}")
    else:
        health_level -= 15
        set_message(f"{R}❓ Cursed trap! -15 HP{W}")


def combat():
    global health_level
    health_level -= 25
    return False


def check_collision():
    global thief_active, thief_pos
    if thief_active and player_pos == thief_pos:
        thief_active = False
        thief_pos = None
        if map_icon not in inventory:
            inventory.append(map_icon)
        set_message(f"{G}🦹 You caught the thief and got your {map_icon} map back!{W}", 3.0)
        return True
    for en in enemies:
        if en["dazed"] <= 0 and player_pos == en["pos"]:
            combat()
            en["dazed"] = DORMANT_TURNS
            set_message(f"{R}{en['icon']} Enemy strikes! -25 HP. It sleeps for {DORMANT_TURNS} turns.{W}")
            return True
    return False


def enemy_move():
    for en in enemies:
        if en["dazed"] > 0:
            en["dazed"] -= 1
            continue

        x, y = en["pos"]
        options = {}
        for name, (dx, dy) in ENEMY_DIRS.items():
            nx, ny = x + dx, y + dy
            if in_grid(nx, ny) and base_grid[ny][nx] not in wallist and base_grid[ny][nx] != termina_l:
                options[name] = (nx, ny)
        if not options:
            continue

        junction = len(options) >= 3
        keep = en["dir"] in options and not (junction and random.random() < 0.35)
        if not keep:
            choices = [d for d in options if d != OPPOSITE.get(en["dir"])] or list(options)
            en["dir"] = random.choice(choices)
        en["pos"] = options[en["dir"]]


# ------------------------------------------------------------ riddles -------

def puzzle_screen(title, body, feedback="", prompt=""):
    lines = box(["", f"{BOLD}{title}{W}", ""] + body + ["", feedback, ""], width=70)
    render([""] + lines + ["", prompt])


def choice_puzzle(title, body, options, answer, success):
    """Multiple-choice riddle. Returns True when solved, False if Leo steps away."""
    feedback = ""
    flush_input()
    while True:
        puzzle_screen(title, body, feedback,
                      f"  Press {', '.join(sorted(options))} to answer, or Q to step away.")
        key = wait_for_key(options | {"Q"})
        if key == "Q":
            return False
        if key == answer:
            puzzle_screen(title, body, f"{G}{success}{W}", "  Press any key to return to the maze.")
            flush_input()
            wait_for_key()
            return True
        feedback = f"{R}{key} is wrong! Try again.{W}"


def puzzle1():
    return choice_puzzle(
        "=== The Guardian's Riddle ===",
        ["Answer correctly to claim the key!", "",
         "What has keys but cannot open locks?", "",
         "A. A clock", "B. A piano", "C. A book", "D. A candle"],
        {"A", "B", "C", "D"}, "B", "Correct! You obtained the key.")


def puzzle2():
    return choice_puzzle(
        "=== The Three Doors ===",
        ["The key is hidden behind exactly one door.",
         "Exactly ONE of these statements is true.", "",
         "Door A: The key is behind Door B.",
         "Door B: The key is NOT behind Door B.",
         "Door C: The key is NOT behind Door A.", "",
         "Which door hides the key?"],
        {"A", "B", "C"}, "A", "Correct! Door A opens and reveals the key.")


SPHINX_ANSWERS = {"human", "a human", "humans", "person", "a person",
                  "man", "a man", "human being", "a human being"}


def puzzle3():
    """Typed riddle. An empty answer lets Leo step away and come back later."""
    title = "=== The Sphinx's Riddle ==="
    body = ["Deep in the forest, a sphinx guards an ancient key.",
            "Sphinx: Solve my riddle to claim the key.", "",
            "What creature walks on four legs in the morning,",
            "two at noon, and three in the evening?", "",
            f"{DIM}Type in English and press Enter (empty answer = step away).{W}"]
    feedback = ""
    flush_input()
    while True:
        puzzle_screen(title, body, feedback, "  Your answer: ")
        answer = " ".join(read_line(30).lower().split())  # tidy extra spaces
        if not answer:
            return False
        if answer in SPHINX_ANSWERS:
            puzzle_screen(title, [
                "Correct! The answer is a human.",
                "A baby crawls on hands and knees.",
                "An adult walks on two legs.",
                "An elderly person may use a walking stick.", "",
                "The sphinx allows you to take the key."],
                "", "  Press any key to return to the maze.")
            flush_input()
            wait_for_key()
            return True
        feedback = f"{R}Wrong! Hint: think about the stages of life, not the time of day.{W}"


PUZZLES = {1: puzzle1, 2: puzzle2, 3: puzzle3}


def handle_move(k):
    global player_pos
    dx, dy = DIRS[k]
    tx, ty = player_pos[0] + dx, player_pos[1] + dy

    if not in_grid(tx, ty):
        return None, False
    target = base_grid[ty][tx]
    if target in wallist:
        return None, False

    if target == termina_l:
        if REQUIRE_KEY and maze_key not in inventory:
            set_message(f"{Y}⛺ The gate is sealed. Find the {maze_key} first.{W}")
            return None, False
        if map_icon not in inventory:
            set_message(f"{R}{map_icon} You lost your Map! Catch the thief before leaving!{W}", 3.0)
            return None, False
        player_pos = (tx, ty)
        return "win", True

    player_pos = (tx, ty)

    if target == maze_key:
        if PUZZLES[current_level_num]():
            inventory.append(maze_key)
            base_grid[ty][tx] = path
            getexp("solvepuzzle")
            set_message(f"{Y}🔑 You obtained the relic key! +100 XP{W}")
        else:
            set_message(f"{DIM}The riddle waits. Step on the {maze_key} again to retry.{W}", 3.0)
    elif target == mystery:
        base_grid[ty][tx] = path
        mystery_event()
    elif target == lightning:
        base_grid[ty][tx] = path
        gain_battle_charge(1)
        set_message(f"{Y}⚡ Collected! +1 Boss Charge{W}")
    elif target == medkit:
        heal(medkit)
        base_grid[ty][tx] = path
        set_message(f"{G}💟 +20 HP{W}")
    elif target == ambulance:
        heal(ambulance)
        base_grid[ty][tx] = path
        set_message(f"{G}🍇 Fully healed!{W}")
    else:
        getexp("moveblock")

    check_theif_trigger()
    return None, True


def play_level(level_number):
    global health_level, battle_charge, message_text
    load_level(level_number)
    health_level = MAX_HEALTH
    battle_charge = 0
    message_text = ""

    flush_input()
    draw_maze()
    while True:
        k = wait_for_key()
        if k == "Q":
            return "quit"

        acted = False
        if k in DIRS:
            status, acted = handle_move(k)
            if status == "win":
                set_message(f"{G}⛺ Leo reaches the inner shrine!{W}", 1.1)
                draw_maze()
                time.sleep(0.9)
                return "won"

        if acted:
            check_collision()  # Leo walked into an enemy
            enemy_move()
            check_collision()  # an enemy walked into Leo
            maybe_respawn_lightning()

        draw_maze()
        if health_level <= 0:
            time.sleep(0.6)
            return "lost"


# ============================================================ corridor ======

CORRIDOR_STEPS = 16 * 4          # quarter-steps from the entrance to the gate
CORRIDOR_PILLARS = [1, 3, 5, 7, 9, 11, 13, 15]


def corridor_frame(pos_sub):
    """One 80x24 frame of the pillared corridor seen from Leo's position."""
    pos = pos_sub / 4.0
    screen = [[' ' for _ in range(SCREEN_W)] for _ in range(SCREEN_H)]

    # 1. Floor: a trapezium whose stripes scroll as Leo moves forward.
    for y in range(13, SCREEN_H - 1):
        dy = y - 12
        half_w = int(dy * 3.8)
        for x in range(max(0, 40 - half_w), min(SCREEN_W, 40 + half_w)):
            grid_z = int(dy + pos * 2) % 4
            if grid_z == 0:
                screen[y][x] = '-' if x % 4 != 0 else '+'
            elif grid_z == 2:
                screen[y][x] = '.' if x % 2 == 0 else '_'

    # 2. The glowing gate grows as Leo gets closer.
    dist_to_door = (CORRIDOR_STEPS - pos_sub) / 4.0
    if dist_to_door <= 0:
        door_msg = " * YOU REACHED THE ANCIENT GATE! * "
        start_x = (SCREEN_W - len(door_msg)) // 2
        for i, char in enumerate(door_msg):
            screen[11][start_x + i] = char
    else:
        gate_half_w = min(35, max(3, int(28 / dist_to_door)))
        gate_half_h = min(10, max(2, int(9 / dist_to_door)))
        door_top, door_bottom = 12 - gate_half_h, 12 + gate_half_h
        door_left, door_right = 40 - gate_half_w, 40 + gate_half_w
        shimmer = int(time.time() * 6)
        for y in range(max(0, door_top), min(SCREEN_H - 1, door_bottom)):
            for x in range(max(0, door_left), min(SCREEN_W, door_right)):
                if y in (door_top, door_bottom - 1) or x in (door_left, door_right - 1):
                    screen[y][x] = '#'
                else:
                    screen[y][x] = '*' if (x + y + shimmer) % 3 == 0 else 'o'

    # 3. Pillars on both sides: nearer pillars are wider, taller and further out.
    for p_pos in CORRIDOR_PILLARS:
        rel_dist = p_pos - pos
        if rel_dist <= 0:
            continue
        offset = max(2, int(35 / rel_dist))
        half_h = min(11, max(1, int(11 / rel_dist)))
        p_width = max(1, min(7, int(8 - rel_dist)))
        for start in (40 - offset - p_width + 1, 40 + offset):
            for y in range(max(0, 12 - half_h), min(SCREEN_H - 1, 12 + half_h)):
                for w in range(p_width):
                    x = start + w
                    if not 0 <= x < SCREEN_W:
                        continue
                    if p_width == 1:
                        screen[y][x] = '|'
                    elif w == 0:
                        screen[y][x] = '['
                    elif w == p_width - 1:
                        screen[y][x] = ']'
                    else:
                        screen[y][x] = '#' if y % 2 != 0 else '='

    # 4. Status bar on the last row.
    status = f" [POS: {pos:.2f}/{CORRIDOR_STEPS / 4}] Press [W] to Charge | [Q] Quit "
    screen[SCREEN_H - 1] = list(status[:SCREEN_W].ljust(SCREEN_W))
    return ["".join(row) for row in screen]


def corridor_scene():
    """Level 4 cut-scene: press W once and Leo charges down the corridor to the
    ancient gate. Returns False if the player quits to the menu."""
    pos_sub, moving = 0, False
    flush_input()
    render(corridor_frame(pos_sub))
    while pos_sub < CORRIDOR_STEPS:
        ensure_size()
        key = get_single_keypress()
        if key == "Q":
            return False
        if key == "W":
            moving = True
        if moving:
            pos_sub += 1
            render(corridor_frame(pos_sub), clear=False)  # overwrite: no flicker
        time.sleep(0.075)
    time.sleep(1.5)       # show the gate message
    render([])            # fade to black
    time.sleep(1.0)
    return True


# ============================================================ boss battle ===

INNER = 76
FRAME_W = INNER + 2
LOG_ROWS = 4
ENERGY_FLOOR = 2      # energy drains never take Leo below this
SHIELD_FACTOR = 0.5   # a shielded hit still deals half damage

DECK = [
    {"name": "Claw Strike", "icon": "🐾", "cost": 2, "type": "dmg", "val": 12},
    {"name": "Guard Stance", "icon": "✋", "cost": 1, "type": "armor", "val": 12},
    {"name": "Herbal Heal", "icon": "💚", "cost": 3, "type": "heal", "val": 15},
    {"name": "Sun Fang", "icon": "🔥", "cost": 4, "type": "dmg", "val": 22},
    {"name": "Focus Breath", "icon": "✨", "cost": 0, "type": "energy", "val": 3},
]
CARD_KEYS = {str(i) for i in range(1, len(DECK) + 1)}

# One boss per level, each with its own look and behaviour. Difficulty rises
# with the level: more HP, harder hits, more shielding, then RAGE at level 4.
#   pattern: "cycle" repeats moves in order, "random" picks one each turn
#   shield:  chance an attack is shielded (deals SHIELD_FACTOR damage)
#   rage:    damage multiplier once the boss drops to half HP (1.0 = none)
#   eyes:    (calm, enraged) eyes drawn into the art
BOSSES = {
    1: {"name": "METEOR GOLEM", "icon": "🗿", "hp": 60, "pattern": "cycle",
        "shield": 0.0, "shield_text": "", "rage": 1.0, "eyes": ("o   o", "o   o"),
        "trait": "Slow and predictable: its moves repeat in the same order.",
        "moves": [{"name": "Rock Slam", "kind": "dmg", "value": 9},
                  {"name": "Pebble Toss", "kind": "dmg", "value": 5},
                  {"name": "Cooling Down", "kind": "rest", "value": 0}],
        "art": [r"   _________   ",
                r"  /  {eyes}  \  ",
                r" |   [===]   | ",
                r"/|___________|\ ",
                r"   _|_|  |_|_   "]},
    2: {"name": "MANOR WRAITH", "icon": "👻", "hp": 75, "pattern": "random",
        "shield": 0.35, "shield_text": "The wraith fades out of reach!", "rage": 1.0,
        "eyes": ("O   O", "O   O"),
        "trait": "Fades often: faded hits only deal half damage.",
        "moves": [{"name": "Ghost Claw", "kind": "dmg", "value": 9},
                  {"name": "Grave Chill", "kind": "dmg", "value": 6},
                  {"name": "Chilling Wail", "kind": "drain", "value": 1}],
        "art": [r"   .-~~~~~-.   ",
                r"  (  {eyes}  )  ",
                r"   |   o   |   ",
                r"   |       |   ",
                r"   \/\/\/\/\   "]},
    3: {"name": "THORN TREANT", "icon": "🌲", "hp": 80, "pattern": "random",
        "shield": 0.15, "shield_text": "Bark armour hardens!", "rage": 1.0,
        "eyes": ("@   @", "@   @"),
        "trait": "Regrows: it can heal itself, so keep up the pressure.",
        "moves": [{"name": "Vine Lash", "kind": "dmg", "value": 9},
                  {"name": "Thorn Burst", "kind": "dmg", "value": 12},
                  {"name": "Root Mend", "kind": "heal", "value": 8}],
        "art": [r" \\|//   \\|// ",
                r"  (  {eyes}  )  ",
                r"   \  ___  /   ",
                r" --|=======|-- ",
                r"   /|\   /|\   "]},
    4: {"name": "THE EVIL PANDA", "icon": "🐼", "hp": 100, "pattern": "random",
        "shield": 0.2, "shield_text": "Panda raises a cursed shield!", "rage": 1.25,
        "eyes": ("ಠ ಠ", "◣ ◢"),
        "trait": "Below half HP it enters RAGE and hits 25% harder.",
        "moves": [{"name": "Shadow Swipe", "kind": "dmg", "value": 10},
                  {"name": "Bamboo Crush", "kind": "dmg", "value": 13},
                  {"name": "Dread Howl", "kind": "drain", "value": 2}],
        "art": [r"     ʕ{eyes}ʔ      ",
                r"    /|  _  |\     ",
                r"   / | |_| | \    ",
                r"  /  |_____|  \   ",
                r"     /_____\      "]},
}

hero = {}
boss = {}
battle_logs = []
battle_turn = 1
boss_pose = 0
boss_shield = False


def pick_boss_move():
    """Choose the boss's next move (shown to the player as its Intent).
    A drain is never picked twice in a row, so energy loss stays manageable."""
    cfg = boss["cfg"]
    if cfg["pattern"] == "cycle":
        move = cfg["moves"][boss["move_i"] % len(cfg["moves"])]
        boss["move_i"] += 1
        return move
    last = boss.get("next_move")
    choices = [m for m in cfg["moves"]
               if not (last and last["kind"] == "drain" and m["kind"] == "drain")]
    return random.choice(choices)


def reset_battle(level, start_bonus_energy=0):
    global hero, boss, battle_logs, battle_turn, boss_pose, boss_shield
    hero = {
        "hp": 100, "max_hp": 100,
        "armor": 0,
        "energy": min(10, 5 + start_bonus_energy), "max_energy": 10
    }
    cfg = BOSSES[level]
    boss = {"cfg": cfg, "name": cfg["name"], "hp": cfg["hp"], "max_hp": cfg["hp"],
            "phase": 1, "move_i": 0, "next_move": None}
    boss["next_move"] = pick_boss_move()
    battle_logs = []
    battle_turn = 1
    boss_pose = 0
    boss_shield = False


def blog(msg):
    battle_logs.append(msg)
    if len(battle_logs) > LOG_ROWS:
        battle_logs.pop(0)


def boss_art():
    """The boss picture, swaying left/right each turn and centred in the frame."""
    cfg = boss["cfg"]
    eyes = cfg["eyes"][boss["phase"] - 1]
    rows = [row.replace("{eyes}", eyes) for row in cfg["art"]]
    if boss_shield:
        rows[1] += " [#]"
    shift = 2 if boss_pose % 2 else -2
    left = max(0, (INNER - max(vis_len(r) for r in rows)) // 2 + shift)
    return [" " * left + r for r in rows]


def move_effect(move):
    """Short description of a boss move for the Intent line."""
    if move["kind"] == "dmg":
        return f"{boss_damage(move)} dmg"
    if move["kind"] == "drain":
        return f"-{move['value']} energy"
    if move["kind"] == "heal":
        return f"+{move['value']} HP"
    return "no attack"


def boss_damage(move):
    return round(move["value"] * boss["cfg"]["rage"]) if boss["phase"] == 2 else move["value"]


def card_label(i, card):
    effect = {"dmg": f"{card['val']} dmg", "armor": f"+{card['val']} armor",
              "heal": f"+{card['val']} HP", "energy": f"+{card['val']} EN"}[card["type"]]
    label = f"[{i}] {card['icon']} {card['name']} ({card['cost']}EN, {effect})"
    return label if card["cost"] <= hero["energy"] else f"{DIM}{label}{W}"


def boxline(content):
    return "║" + pad(clip(content, INNER), INNER) + "║"


def two_col(left, right):
    gap = max(1, INNER - vis_len(left) - vis_len(right))
    return left + " " * gap + right


def section(title):
    label = f" {title} "
    side = (INNER - len(label)) // 2
    return "╟" + "─"*side + label + "─"*(INNER - side - len(label)) + "╢"


def draw_battle(flash=None, status=None):
    cfg = boss["cfg"]
    enraged = boss["phase"] == 2
    phase = f"{R}{BOLD}[RAGE]{W}" if enraged else f"{DIM}[CALM]{W}"
    move = boss["next_move"]

    lines = ["╔" + "═"*INNER + "╗"]
    lines.append(boxline(two_col(f" {BOLD}{cfg['icon']} {boss['name']}{W} {phase}",
                                 f"{DIM}Turn {battle_turn}{W} ")))
    lines.append(boxline(f"  Boss HP: {bar(boss['hp'], boss['max_hp'], 40, R)} "
                         f"{max(0, boss['hp'])}/{boss['max_hp']}"))
    lines.append(boxline(f"  Intent: {Y}{move['name']} ({move_effect(move)}){W}"
                         f"   {DIM}the boss acts after each card{W}"))

    art_color = Y if flash == "boss" else (R if enraged else WHITE)
    for row in boss_art():
        lines.append(boxline(f"{art_color}{row}{W}"))

    lines.append(section("LEO"))
    lines.append(boxline(
        f"  HP {bar(hero['hp'], hero['max_hp'], 20, G)} {max(0, hero['hp'])}/{hero['max_hp']}   "
        f"Armor {B}{hero['armor']}{W}   "
        f"Energy {bar(hero['energy'], hero['max_energy'], 10, Y)} {hero['energy']}/{hero['max_energy']}"
    ))

    lines.append(section("ACTIONS"))
    labels = [card_label(i, c) for i, c in enumerate(DECK, 1)] + ["[Q] Flee to menu"]
    for i in range(0, len(labels), 2):
        pair = labels[i:i + 2]
        lines.append(boxline("  " + "".join(pad(l, 37) for l in pair)))
    lines.append(boxline(f"  {DIM}Clean hit or block: +1 EN.  Drains never take you below "
                         f"{ENERGY_FLOOR} EN.{W}"))

    lines.append(section("BATTLE LOG"))
    for i in range(LOG_ROWS):
        lines.append(boxline("  " + (battle_logs[i] if i < len(battle_logs) else "")))
    lines.append("╚" + "═"*INNER + "╝")
    lines.append(status if status is not None
                 else f"  {DIM}Press 1-{len(DECK)} to play a card, Q to flee.{W}")
    render(lines, FRAME_W)


def animate(msg, flash=None, t=0.24):
    blog(msg)
    draw_battle(flash=flash)
    time.sleep(t)


def check_phase():
    cfg = boss["cfg"]
    if (cfg["rage"] > 1 and boss["phase"] == 1
            and 0 < boss["hp"] <= boss["max_hp"] // 2):
        boss["phase"] = 2
        animate(f"{R}{BOLD}{cfg['icon']} {boss['name']} enters RAGE mode!{W}", flash="boss", t=0.45)


def resolve_player_attack(base_dmg, label):
    global boss_shield
    boss_shield = random.random() < boss["cfg"]["shield"]
    if boss_shield:
        animate(f"{B}{boss['cfg']['shield_text']}{W}", flash="boss", t=0.22)
        dmg = max(1, int(base_dmg * SHIELD_FACTOR))
    else:
        dmg = base_dmg
        hero["energy"] = min(hero["max_energy"], hero["energy"] + 1)
        animate(f"{Y}⚡ Clean hit! Leo gains +1 energy.{W}", flash="hero", t=0.18)

    boss["hp"] = max(0, boss["hp"] - dmg)
    animate(f"{R}{label} deals {dmg} damage!{W}", flash="boss", t=0.24)
    boss_shield = False
    check_phase()


def play_card(card):
    global boss_pose
    if card["cost"] > hero["energy"]:
        blog(f"{R}Not enough energy for {card['name']}! Try ✨ Focus Breath.{W}")
        return False

    hero["energy"] -= card["cost"]
    boss_pose += 1

    if card["type"] == "dmg":
        crit = random.random() < 0.12
        dmg = card["val"] * 2 if crit else card["val"]
        label = f"{card['icon']} {card['name']}" + (f" {BOLD}(CRIT){W}{R}" if crit else "")
        resolve_player_attack(dmg, label)
    elif card["type"] == "armor":
        hero["armor"] += card["val"]
        animate(f"{B}{card['icon']} +{card['val']} armor{W}", flash="hero", t=0.2)
    elif card["type"] == "heal":
        amt = min(card["val"], hero["max_hp"] - hero["hp"])
        hero["hp"] += amt
        animate(f"{G}{card['icon']} Leo heals {amt} HP{W}", flash="hero", t=0.2)
    elif card["type"] == "energy":
        hero["energy"] = min(hero["max_energy"], hero["energy"] + card["val"])
        animate(f"{C}{card['icon']} +{card['val']} energy{W}", flash="hero", t=0.2)

    return True


def boss_action():
    global boss_pose
    if boss["hp"] <= 0:
        return
    boss_pose += 1
    move = boss["next_move"]

    if move["kind"] == "dmg":
        raw = boss_damage(move)
        blocked = min(hero["armor"], raw)
        actual = raw - blocked
        hero["hp"] = max(0, hero["hp"] - actual)
        if blocked > 0:
            hero["energy"] = min(hero["max_energy"], hero["energy"] + 1)
            animate(f"{B}✋ You blocked {blocked}! Counter-focus +1 energy.{W}", flash="hero", t=0.2)
        animate(f"{R}💥 {move['name']} hits for {actual} ({blocked} blocked){W}", flash="hero", t=0.3)
    elif move["kind"] == "drain":
        drain = max(0, min(move["value"], hero["energy"] - ENERGY_FLOOR))
        hero["energy"] -= drain
        if drain:
            animate(f"{M}😱 {move['name']} drains {drain} energy!{W}", flash="hero", t=0.28)
        else:
            animate(f"{M}😱 {move['name']}... Leo holds his focus!{W}", flash="hero", t=0.28)
    elif move["kind"] == "heal":
        amt = min(move["value"], boss["max_hp"] - boss["hp"])
        boss["hp"] += amt
        animate(f"{G}🌿 {move['name']}: the boss regrows {amt} HP{W}", flash="boss", t=0.28)
    else:
        animate(f"{DIM}{boss['name']} is {move['name'].lower()}... no attack.{W}", t=0.28)

    hero["armor"] = 0
    boss["next_move"] = pick_boss_move()


def boss_intro(level, charge_bonus):
    cfg = BOSSES[level]
    where = "the temple core" if level == NUM_LEVELS else "the guardian's lair"
    lines = box([
        "",
        f"{BOLD}Leo reaches {where}...{W}",
        "",
        f"{R}{BOLD}{cfg['icon']} {cfg['name']} APPEARS!{W}",
        f"{C}{cfg['trait']}{W}",
        "",
        "Rules:",
        "• Each card costs energy (EN). The boss acts after every card.",
        "• Watch the boss Intent: guard big hits, heal when low.",
        "• A clean (unshielded) hit or a block gives +1 energy.",
        f"• Energy drains never take you below {ENERGY_FLOOR} EN.",
        f"• Temple Charge bonus: +{charge_bonus} starting energy.",
        "",
        f"{Y}Press any key to fight.{W}",
        "",
    ], width=68)
    pause_screen(["", ""] + lines)


def boss_battle(level, charge_bonus):
    global battle_turn
    reset_battle(level, start_bonus_energy=charge_bonus)
    boss_intro(level, charge_bonus)
    blog(f"{Y}Battle starts!{W}")

    while hero["hp"] > 0 and boss["hp"] > 0:
        draw_battle()
        k = wait_for_key()

        if k == "Q":
            draw_battle(status=f"  {Y}Really flee to the menu? (Y/N){W}")
            if wait_for_key({"Y", "N"}) == "Y":
                return "quit"
            continue

        if k in CARD_KEYS:
            if play_card(DECK[int(k) - 1]):
                boss_action()
                battle_turn += 1
        else:
            blog(f"{DIM}Press 1-{len(DECK)} to play a card, or Q to flee.{W}")
        flush_input()  # ignore keys mashed during the animations

    won = boss["hp"] <= 0
    if won:
        status = f"  {G}{BOLD}🎉 VICTORY! Leo defeated {boss['name']}!{W}  {DIM}(press any key){W}"
    else:
        status = f"  {R}{BOLD}💀 DEFEAT... Leo has fallen.{W}  {DIM}(press any key){W}"
    draw_battle(status=status)
    time.sleep(0.5)
    flush_input()
    wait_for_key()
    return "victory" if won else "defeat"


# ============================================================ game flow =====

def ask_yes_no(lines):
    """Show a small boxed question; returns True for Y, False for N."""
    return pause_screen(["", ""] + box(lines, width=56), valid={"Y", "N"}) == "Y"


def run_level_with_boss(level):
    global exp
    while True:  # loops only when the player chooses to restart the level
        level_intro(level)

        if level == NUM_LEVELS:  # final level: corridor cut-scene, then the boss
            if not corridor_scene():
                return
            charge = MAX_BATTLE_CHARGE  # the ancient gate fully charges Leo
        else:
            result = play_level(level)
            if result == "quit":
                return
            if result == "lost":
                if ask_yes_no(["", f"{R}{BOLD}💀 YOU LOST IN THE MAZE{W}", "",
                               "Restart this level? (Y/N)", ""]):
                    continue
                return
            charge = battle_charge

        outcome = boss_battle(level, charge)
        while outcome == "defeat":
            if not ask_yes_no(["", f"{R}{BOLD}💀 Leo was defeated.{W}", "",
                               "Try the boss again? (Y/N)", ""]):
                return
            outcome = boss_battle(level, charge)
        if outcome == "quit":
            return

        exp += 200
        if level < NUM_LEVELS and (level + 1) not in unlocked_level:
            unlocked_level.append(level + 1)
        if level == NUM_LEVELS:
            ending = ["Leo claims the Lost Temple treasure!", "",
                      f"{G}{BOLD}🎉 YOU WIN! Thanks for playing.{W}"]
        else:
            ending = [f"Level {level + 1} is now unlocked!"]
        pause_screen(["", ""] + box([
            "",
            f"{G}{BOLD}🏆 LEVEL {level} COMPLETE!{W}",
            "",
            f"{Y}+200 XP   (Total: {exp}){W}",
            "",
        ] + ending + ["", f"{DIM}Press any key to return to the menu.{W}", ""], width=56))
        return


def main_menu():
    feedback = ""
    while True:
        lines = box([
            "",
            f"{BOLD}🏛️  THE LOST TEMPLE  🦁{W}",
            f"{DIM}Navigate the maze. Survive the ghosts. Defeat the guardians.{W}",
            "",
            f"Goal: clear all {NUM_LEVELS} levels and claim the temple treasure.",
            f"Maze: WASD/arrows move. Solve the {maze_key} riddle, then reach {termina_l}.",
            f"Avoid enemies. {lightning} = boss energy, {medkit} {ambulance} = healing.",
            "Boss: press 1-5 to play cards. Win to unlock the next level.",
            "",
        ], width=70)
        lines.append("")
        for n in range(1, NUM_LEVELS + 1):
            tag = "" if n in unlocked_level else f"  {R}(Locked 🔒){W}"
            lines.append(f"     {n}. Level {n} {LEVEL_EMOJIS[n - 1]} {LEVEL_NAMES[n - 1].title()}{tag}")
        lines += ["     0. Exit Game", "", f"  {feedback}",
                  f"  Select an option (0-{NUM_LEVELS})."]
        render(lines, 72)
        flush_input()

        choice = wait_for_key()
        feedback = ""
        if choice in {str(n) for n in range(1, NUM_LEVELS + 1)}:
            lv = int(choice)
            if lv not in unlocked_level:
                feedback = f"{R}Level {lv} is locked! Complete level {lv - 1} first.{W}"
                continue
            run_level_with_boss(lv)
        elif choice in ("0", "Q"):
            return
        else:
            feedback = f"{R}Invalid choice. Press a number from 0 to {NUM_LEVELS}.{W}"


def main():
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print("This game needs an interactive terminal. (Use -it with Docker)")
        return
    try:
        with game_terminal():
            story_screen()
            main_menu()
    except KeyboardInterrupt:
        pass
    print("Goodbye! Thanks for playing The Lost Temple.")


if __name__ == "__main__":
    main()

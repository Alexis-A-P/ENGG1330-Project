import os
import re
import sys
import time
import random
import shutil
import unicodedata
from contextlib import contextmanager

IS_WINDOWS = os.name == "nt"

if IS_WINDOWS:
    import msvcrt
    os.system("")
else:
    import tty
    import termios
    import select

ARROWS_WIN = {b"H": "W", b"P": "S", b"K": "A", b"M": "D"}
ARROWS_POSIX = {"A": "W", "B": "S", "C": "D", "D": "A"}

if IS_WINDOWS:
    def get_single_keypress():
        if not msvcrt.kbhit():
            return None
        ch = msvcrt.getch()
        if ch == b"\x03":
            raise KeyboardInterrupt
        if ch in (b"\x00", b"\xe0"):
            return ARROWS_WIN.get(msvcrt.getch())
        try:
            return ch.decode("utf-8").upper()
        except UnicodeDecodeError:
            return None

    def flush_input():
        while msvcrt.kbhit():
            msvcrt.getch()
else:
    def get_single_keypress():
        fd = sys.stdin.fileno()
        if not select.select([fd], [], [], 0)[0]:
            return None
        data = os.read(fd, 32).decode("utf-8", errors="ignore")
        if not data:
            return None
        if data.startswith(("\x1b[", "\x1bO")) and len(data) >= 3:
            return ARROWS_POSIX.get(data[2])
        if data[0] == "\x1b":
            return None
        return data[0].upper()

    def flush_input():
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)


def wait_for_key(valid=None):
    while True:
        key = get_single_keypress()
        if key and (valid is None or key in valid):
            return key
        time.sleep(0.02)


@contextmanager
def game_terminal():
    if not IS_WINDOWS:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    try:
        yield
    finally:
        sys.stdout.write("\033[?25h\033[0m")
        sys.stdout.flush()
        flush_input()
        if not IS_WINDOWS:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


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


def char_width(ch):
    if ch in ("\ufe0f", "\u200d") or unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F", "A") else 1


def vis_len(text):
    return sum(char_width(c) for c in ANSI_RE.sub("", text))


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
    out += ["║" + pad(l, width, "center") + "║" for l in lines]
    out.append("╚" + "═" * width + "╝")
    return out


def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def render(lines, frame_width=0):
    cols, rows = shutil.get_terminal_size()
    margin = " " * max(0, (cols - frame_width) // 2) if frame_width else ""
    out = "\033[H\033[J" + "".join(margin + ln + "\033[K\n" for ln in lines)
    sys.stdout.write(out)
    sys.stdout.flush()


def check_size(min_cols=96, min_rows=30):
    while True:
        cols, rows = shutil.get_terminal_size()
        if cols >= min_cols and rows >= min_rows:
            return
        clear_screen()
        print(f"{R}Terminal too small!{W}")
        print(f"Need at least {min_cols}x{min_rows}, current is {cols}x{rows}.")
        print("Resize and press any key, or Q to continue anyway.")
        if wait_for_key() == "Q":
            return


def bar(cur, mx, length=20, color=G):
    cur = max(0, min(cur, mx))
    filled = int(length * cur / mx) if mx else 0
    if cur > 0 and filled == 0:
        filled = 1
    return f"{color}{'█'*filled}{DIM}{'░'*(length-filled)}{W}"


STORY_LINES = [
    f"{BOLD}Game Title: The Lost Temple{W}",
    "",
    "Long ago, an ancient temple was built to protect a mysterious treasure",
    "with extraordinary powers. To keep the treasure safe, the ancient guardians",
    "created a complex maze filled with magical creatures and hidden trials.",
    "",
    "Over time, the temple was forgotten, but its ghostly guardians continued",
    "to patrol the maze and protect its secrets.",
    "",
    "One day, Leo, a brave young lion, discovered the entrance to the lost temple.",
    "Determined to uncover its mysteries, he decided to venture into the maze and",
    "search for the legendary treasure.",
    "",
    "However, the journey would not be easy. Leo must navigate the maze, avoid",
    "wandering ghosts, collect ancient items, and solve puzzles left behind by",
    "the guardians.",
    "",
    "Through exploration and problem-solving, Leo gains experience and develops",
    "the skills needed to overcome the challenges ahead.",
    "",
    "Will Leo succeed in discovering the temple's hidden treasure?",
    "His adventure begins now.",
]

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
wall_4 = "🏯"
door = "🚪"
enemy_2 = "👻"
enemy_3 = "🦖"
medkit = "💟"
ambulance = "🍇"
map = "🗺️"
thief = "🦹"
thief_pos = None
thief_active = False

TILES = {
    "#": wall_1, ".": path, "P": player, "E": enemy_1,
    "K": maze_key, "?": mystery, "T": termina_l, "L": lightning,
    "$": wall_2, "@": wall_3, "^": wall_4, "F": enemy_2, "G": enemy_3, "D": door, "M": medkit, "A": ambulance
}
wallist = {wall_1, wall_2, wall_3, wall_4}
enemylist = {enemy_1, enemy_2, enemy_3}
LEVEL_EMOJIS = ['⛰️', '🌋', '⛈️', '🏯']

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
    "@.@@.@...@.@.@.@.@.@.@.@@@@@@@",
    "@.@@.@@@@@.@.@.@.@.@.@.@.....@",
    "@....@...@.@...@.@.@.@.@.@@@@@",
    "@@@@@@.@.@.@.@@@...@.@.@.@.G.@",
    "@....@.@.@.@...@.@.@.@.@.@@@.@",
    "@.@@.@.@.@.@.@@@@@M@.@.@.@.K.@",
    "@....@.@...@..G....@.@A@.@.@.@",
    "@.M..@.@.@@@@@@@@@@@@@T@.@...@",
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
]
maze4 = [
    "^^^^^^^^^^^^^^^^",
    "^.............D^",
    "^^^^^^^^^^^^^^^^"
]

enemies = []
mazetotal = [maze1, maze2, maze3, maze4]
unlocked_level = [1]
MAX_HEALTH = 100
REQUIRE_KEY = True
DORMANT_TURNS = 3
LIGHTNING_RESPAWN_CHANCE = 0.12
MAX_BATTLE_CHARGE = 3

exp = 0
health_level = MAX_HEALTH
battle_charge = 0
inventory = [map]

current_level_num = 1
base_grid = []
player_pos = (0, 0)
enemy_pos = None
enemy_direction = None
enemy_dazed_turns = 0

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
    global MAX_HEALTH
    global health_level
    if emoji == medkit:
        health_level += 20
        if health_level > MAX_HEALTH:
            health_level = MAX_HEALTH
    elif emoji == ambulance:
        health_level = MAX_HEALTH


def gain_battle_charge(n=1):
    global battle_charge
    battle_charge = min(MAX_BATTLE_CHARGE, battle_charge + n)


def load_level(number):
    global current_level_num, base_grid, player_pos, enemies, inventory
    current_level_num = number
    base_grid = []
    enemies = []
    inventory = [map]
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
    spawn_lightning(4)


def all_open_cells():
    cells = []
    for y in range(len(base_grid)):
        for x in range(len(base_grid[0])):
            if base_grid[y][x] == path and (x, y) != player_pos and (x, y) != enemy_pos:
                cells.append((x, y))
    return cells


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
    global thief_active, thief_pos, inventory
    if current_level_num in (2, 3) and not thief_active and map in inventory:
        cols = len(base_grid[0])
        rows = len(base_grid)
        cx, cy = cols // 2, rows // 2
        
        px, py = player_pos
        if abs(px - cx) <= 2 and abs(py - cy) <= 2:
            inventory.remove(map)
            thief_active = True
            
            open_cells = all_open_cells()
            if open_cells:
                thief_pos = random.choice(open_cells)
            else:
                thief_pos = (1, 1)
                
            set_message(f"{R}🦹 A sneaky Thief appeared and stole your {map} Map! Chase him down!{W}", 4.0)


def draw_maze():
    cols = len(base_grid[0])
    inner = cols * 2
    lvl_emoji = LEVEL_EMOJIS[current_level_num - 1] 
    
    lines = [f"{BOLD}{C}{pad(f'{lvl_emoji} THE LOST TEMPLE - LEVEL {current_level_num} {lvl_emoji}', inner, 'center')}{W}"]
    
    lines.append("╔" + "═"*inner + "╗")
    for y in range(len(base_grid)):
        lines.append("║" + "".join(tile_at(x, y) for x in range(cols)) + "║")
    lines.append("╚" + "═"*inner + "╝")

    msg = message_text if time.time() < message_until else ""
    items = " ".join(inventory) if inventory else f"{DIM}(empty){W}"

    lines += [
        f" HP  {bar(health_level, MAX_HEALTH, 20, G)} {max(0,health_level):>3}/{MAX_HEALTH}",
        f" XP  {Y}{exp}{W}   Boss Charge: {Y}{'⚡'*battle_charge}{DIM}{'·'*(MAX_BATTLE_CHARGE-battle_charge)}{W}",
        f" Items: {items}",
        f" {msg}",
        f" {DIM}{maze_key} key  {mystery} mystery  {lightning} boss-charge  {enemy_1} enemy  {termina_l} exit{W}",
        f" {DIM}WASD/Arrows move, Q quit{W}",
    ]
    render(lines, inner + 2)


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
    global thief_active, thief_pos, inventory
    if thief_active and current_level_num in (2, 3) and player_pos == thief_pos:
        thief_active = False
        thief_pos = None
        if map not in inventory:
            inventory.append(map)
        set_message(f"{G}🦹 You caught the thief and retrieved your {map} map!{W}", 3.0)
        return True
    for en in enemies:
        if en["dazed"] <= 0 and player_pos == en["pos"]:
            combat()
            en["dazed"] = DORMANT_TURNS
            getexp("lost")
            set_message(f"{R}{en['icon']} Enemy strikes! Dazed for {DORMANT_TURNS} turns.{W}")
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
            if base_grid[ny][nx] not in wallist and base_grid[ny][nx] != termina_l:
                options[name] = (nx, ny)
        if not options:
            continue

        junction = len(options) >= 3
        keep = en["dir"] in options and not (junction and random.random() < 0.35)
        if not keep:
            choices = [d for d in options if d != OPPOSITE.get(en["dir"])] or list(options)
            en["dir"] = random.choice(choices)
        en["pos"] = options[en["dir"]]


def handle_move(k):
    global player_pos
    dx, dy = DIRS[k]
    tx, ty = player_pos[0] + dx, player_pos[1] + dy

    if not (0 <= ty < len(base_grid) and 0 <= tx < len(base_grid[0])):
        return None, False
    target = base_grid[ty][tx]
    if target in wallist:
        return None, False

    if target == termina_l: 
        if REQUIRE_KEY and maze_key not in inventory:
            set_message(f"{Y}⛺ The gate is sealed. Find {maze_key}.{W}")
            return None, False
            
        if map not in inventory:
            set_message(f"{R}🗺️ You lost your Map! Find the thief and get it back before leaving!{W}", 3.0)
            return None, False

        player_pos = (tx, ty)
        return "win", True

    player_pos = (tx, ty)

    if target == maze_key:
        inventory.append(maze_key)
        base_grid[ty][tx] = path
        getexp("solvepuzzle")
        set_message(f"{Y}🔑 You found the relic key! +50 XP{W}")
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
    elif target == ambulance:
        heal(ambulance)
        base_grid[ty][tx] = path
    else:
        getexp("moveblock")
        
    check_theif_trigger()
    return None, True


def play_level(level_number):
    global health_level, inventory, battle_charge, enemy_direction, message_text
    load_level(level_number)
    health_level = MAX_HEALTH
    battle_charge = 0
    enemy_direction = None
    message_text = ""

    with game_terminal():
        check_size()
        clear_screen()
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
                enemy_move()
                check_collision()
                maybe_respawn_lightning()

            if health_level <= 0:
                draw_maze()
                return "lost"

            draw_maze()


INNER = 92
FRAME_W = INNER + 2

BOSS_MOVES = [
    {"name": "Shadow Swipe", "value": 10, "kind": "dmg"},
    {"name": "Bamboo Crush", "value": 14, "kind": "dmg"},
    {"name": "Dread Howl", "value": 2, "kind": "drain"},
]

DECK = [
    {"name": "Claw Strike", "icon": "🗡️", "cost": 2, "type": "dmg", "val": 10},
    {"name": "Guard Stance", "icon": "🛡️", "cost": 2, "type": "armor", "val": 9},
    {"name": "Herbal Heal", "icon": "💚", "cost": 3, "type": "heal", "val": 12},
    {"name": "Sun Fang", "icon": "🔥", "cost": 4, "type": "dmg", "val": 18},
    {"name": "Focus Breath", "icon": "✨", "cost": 0, "type": "energy", "val": 2},
]

hero = {}
boss = {}
battle_logs = []
battle_turn = 1
panda_pose = 0
panda_shield = False


def reset_battle(level, start_bonus_energy=0):
    global hero, boss, battle_logs, battle_turn, panda_pose, panda_shield
    hero = {
        "hp": 100, "max_hp": 100,
        "armor": 0,
        "energy": min(10, 5 + start_bonus_energy), "max_energy": 10
    }
    boss_hp = 100 + (level - 1) * 15
    boss = {
        "name": "THE EVIL PANDA",
        "hp": boss_hp, "max_hp": boss_hp,
        "phase": 1,
        "next_move": random.choice(BOSS_MOVES)
    }
    battle_logs = []
    battle_turn = 1
    panda_pose = 0
    panda_shield = False


def blog(msg):
    battle_logs.append(msg)
    if len(battle_logs) > 6:
        battle_logs.pop(0)


def panda_art(enraged=False, pose=0, shield=False):
    eyes = "◣◢" if enraged else "ಠ ಠ"
    if pose % 2 == 0:
        lines = [
            f"              ʕ{eyes}ʔ",
            r"             /|  _  |\ ",
            r"            / | |_| | \ ",
            r"           /  |_____|  \ ",
            r"              /   \      ",
            r"             /_____\     ",
        ]
    else:
        lines = [
            f"          ʕ{eyes}ʔ",
            r"         /|  _  |\      ",
            r"        / | |_| | \     ",
            r"       /  |_____|  \    ",
            r"          /   \         ",
            r"         /_____\        ",
        ]
    if shield:
        lines[1] += "   🛡️"
    return lines


def boxline(content):
    return "║" + pad(content, INNER) + "║"


def two_col(left, right):
    gap = max(1, INNER - vis_len(left) - vis_len(right))
    return left + " " * gap + right


def section(title):
    label = f" {title} "
    side = (INNER - len(label)) // 2
    return "╟" + "─"*side + label + "─"*(INNER - side - len(label)) + "╢"


def draw_battle(flash=None):
    enraged = boss["phase"] == 2
    phase = f"{R}{BOLD}[RAGE]{W}" if enraged else f"{DIM}[CALM]{W}"

    lines = ["╔" + "═"*INNER + "╗"]
    lines.append(boxline(two_col(
        f" {BOLD}🐼 {boss['name']}{W} {phase}",
        f"{DIM}Turn {battle_turn}{W} "
    )))
    lines.append(boxline(f"  Boss HP: {bar(boss['hp'], boss['max_hp'], 42, R)} {max(0,boss['hp'])}/{boss['max_hp']}"))
    lines.append(boxline(f"  Intent: {Y}{boss['next_move']['name']}{W}    {DIM}(Boss retaliates after each player action){W}"))

    art_color = R if flash == "boss" else WHITE
    for row in panda_art(enraged, panda_pose, panda_shield):
        lines.append(boxline(f"{art_color}{pad(row, INNER, 'center')}{W}"))

    lines.append(section("LEO"))
    lines.append(boxline(
        f"  HP {bar(hero['hp'], hero['max_hp'], 24, G)} {hero['hp']}/{hero['max_hp']}   "
        f"Armor {B}{hero['armor']}{W}   "
        f"Energy {bar(hero['energy'], hero['max_energy'], 18, Y)} {hero['energy']}/{hero['max_energy']}"
    ))

    lines.append(section("ACTIONS"))
    lines.append(boxline("  [1]🗡️ Claw Strike(2EN,10dmg)  [2]🛡️ Guard Stance(2EN,+9 armor)  [3]💚 Herbal Heal(3EN,+12HP)"))
    lines.append(boxline("  [4]🔥 Sun Fang(4EN,18dmg)      [5]✨ Focus Breath(0EN,+2EN)     [Q] Flee"))
    lines.append(boxline(f"  {DIM}Tip: If your attack isn't shielded, you gain +1 energy. If you block boss damage, you gain +1 energy.{W}"))

    lines.append(section("BATTLE LOG"))
    show = battle_logs[-6:]
    for i in range(6):
        lines.append(boxline("  " + (show[i] if i < len(show) else "")))

    lines.append("╚" + "═"*INNER + "╝")
    render(lines, FRAME_W)


def animate(msg, flash=None, t=0.24):
    blog(msg)
    draw_battle(flash=flash)
    time.sleep(t)


def check_phase():
    if boss["phase"] == 1 and boss["hp"] > 0 and boss["hp"] <= boss["max_hp"] // 2:
        boss["phase"] = 2
        animate(f"{R}{BOLD}🐼 The Evil Panda enters RAGE mode!{W}", flash="boss", t=0.45)


def resolve_player_attack(base_dmg, label):
    global panda_shield
    panda_shield = (random.random() < (1 / 3))
    if panda_shield:
        animate(f"{B}🛡️ Panda raises a cursed shield!{W}", flash="boss", t=0.22)
        dmg = max(1, int(base_dmg * 0.35))
    else:
        dmg = base_dmg
        hero["energy"] = min(hero["max_energy"], hero["energy"] + 1)
        animate(f"{Y}⚡ Clean hit! Leo gains +1 energy.{W}", flash="hero", t=0.18)

    boss["hp"] -= dmg
    animate(f"{R}{label} deals {dmg} damage!{W}", flash="boss", t=0.24)
    panda_shield = False
    check_phase()


def play_card(card):
    global panda_pose
    if card["cost"] > hero["energy"]:
        blog(f"{R}Not enough energy!{W}")
        return False

    hero["energy"] -= card["cost"]
    panda_pose += 1

    if card["type"] == "dmg":
        crit = random.random() < 0.12
        dmg = card["val"] * 2 if crit else card["val"]
        label = f"{card['icon']} {card['name']}" + (f" {BOLD}(CRIT){W}" if crit else "")
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
    global panda_pose
    if boss["hp"] <= 0:
        return
    panda_pose += 1
    move = boss["next_move"]

    if move["kind"] == "dmg":
        raw = int(move["value"] * 1.4) if boss["phase"] == 2 else move["value"]
        blocked = min(hero["armor"], raw)
        actual = raw - blocked
        hero["hp"] -= actual

        if blocked > 0:
            hero["energy"] = min(hero["max_energy"], hero["energy"] + 1)
            animate(f"{B}🛡️ You blocked {blocked}! Counter-focus +1 energy.{W}", flash="hero", t=0.2)

        animate(f"{R}💥 {move['name']} hits for {actual} ({blocked} blocked){W}", flash="hero", t=0.3)
    else:
        drain = min(move["value"], hero["energy"])
        hero["energy"] -= drain
        animate(f"{M}😱 Dread Howl drains {drain} energy!{W}", flash="hero", t=0.28)

    hero["armor"] = 0
    boss["next_move"] = random.choice(BOSS_MOVES)


def boss_intro(charge_bonus):
    clear_screen()
    lines = box([
        "",
        f"{BOLD}⛺ Leo reaches the temple core...{W}",
        "The legendary treasure is near.",
        "",
        f"{R}{BOLD}🐼 THE EVIL PANDA GUARDIAN APPEARS!{W}",
        "",
        "Rules:",
        "• Boss retaliates after each player action.",
        "• Boss shield chance on your hits: 1/3.",
        "• If your hit is NOT shielded: +1 energy.",
        "• If you block boss damage: +1 energy.",
        f"• Temple Charge bonus: +{charge_bonus} starting energy.",
        "",
        f"{Y}Press any key to fight.{W}",
        "",
    ], width=66)
    render(["", ""] + lines, 68)
    wait_for_key()
    flush_input()
    clear_screen()


def boss_battle(level, charge_bonus):
    global battle_turn
    reset_battle(level, start_bonus_energy=charge_bonus)

    with game_terminal():
        check_size()
        boss_intro(charge_bonus)
        blog(f"{Y}Battle starts!{W}")

        while hero["hp"] > 0 and boss["hp"] > 0:
            draw_battle()
            k = wait_for_key()

            if k == "Q":
                blog(f"{Y}Really flee? (Y/N){W}")
                draw_battle()
                if wait_for_key({"Y", "N"}) == "Y":
                    return "quit"
                if battle_logs:
                    battle_logs.pop()
                continue

            acted = False
            if k.isdigit():
                idx = int(k)
                if 1 <= idx <= len(DECK):
                    acted = play_card(DECK[idx - 1])

            if acted:
                boss_action()
                battle_turn += 1

            flush_input()

        draw_battle()
        if boss["hp"] <= 0:
            print(f"\n  {G}{BOLD}🎉 VICTORY! Leo defeated the Evil Panda!{W}   {DIM}(press any key){W}")
            wait_for_key()
            return "victory"

        print(f"\n  {R}{BOLD}💀 DEFEAT... Leo has fallen in the temple.{W}   {DIM}(press any key){W}")
    wait_for_key()
    return "defeat"


def story_screen():
    clear_screen()
    lines = box([""] + STORY_LINES + ["", f"{Y}Press any key to continue...{W}"], width=90)
    render([""] + lines, 92)
    wait_for_key()


def run_level_with_boss(level):
    global exp, unlocked_level
    while True:
        clear_screen()
        
        introlines_1 = box([
            "",
            f"{BOLD}🌠 LEVEL 1: THE STARRY CANYON 🌠{W}",
            "",
            "Leo decides to rest in a quiet nearby village for the night.",
            "However, he is unaware that a strange meteorite struck the",
            "nearby river upstream just hours before.",
            "After drinking the tainted river water, the villagers have",
            "begun to transform and behave abnormally...",
            "",
        ], width=64)
        
        introlines_2 = box([
            "",
            f"{BOLD}🧱 LEVEL 2: THE SPOOKY MANOR 🧱{W}",
            "",
            "While tracking the lost temple, a grand yet chilling manor",
            "suddenly looms ahead in Leo's path.",
            "As he approaches, he notices an eerie lack of life: plants",
            "are withered, windows shattered, and dark vines choke the walls.",
            "Though filled with dread, he knows he must step inside.",
            "",
        ], width=64)
        
        introlines_3 = box([
            "",
            f"{BOLD}🌳 LEVEL 3: THE MYSTERIOUS FOREST 🌳{W}",
            "",
            "Consulting his map, Leo realizes the temple is near. But a bizarre,",
            "uncharted forest blocks his only route between towering cliffs.",
            "Stepping inside, the air grows warm and thick with heavy fog,",
            "and colossal, glowing flora tower above him.",
            "He spots a vivid, unknown fruit; taking a single bite, a sudden,",
            "surge of primal energy courses through his veins.",
            "",
        ], width=64)
        
        introlines_4 = box([
            "",
            f"{BOLD}🏯 LEVEL 4: THE INNER THRONE 🏯{W}",
            "",
            "Having endured trials of stars, shadows, and ancient flora,",
            "Leo finally stands before the golden gates of the Inner Sanctuary.",
            "The legendary treasure gleams in the distance—but guarding it",
            "sits the ultimate master of the temple:",
            "The ruthless, cosmic-powered Evil Panda.",
            "Draw your sword, brave Leo. The final battle for glory begins now!",
            "",
        ], width=64)

        introlinelist = [None, introlines_1, introlines_2, introlines_3, introlines_4]
        
        render(["", ""] + introlinelist[level], 66)
        input("\n  Press Enter to start level...")

        result = play_level(level)

        if result == "quit":
            return

        if result == "lost":
            clear_screen()
            print(f"\n  {R}{BOLD}💀 YOU LOST IN THE MAZE{W}")
            if input("  Restart level? (y/n): ").strip().lower() == "y":
                continue
            sys.exit(0)

        while True:
            outcome = boss_battle(level, battle_charge)
            if outcome == "defeat":
                clear_screen()
                if input("Try boss again? (y/n): ").strip().lower() == "y":
                    continue
            break

        if outcome == "victory":
            exp += 200
            if level + 1 <= len(mazetotal) and (level + 1) not in unlocked_level:
                unlocked_level.append(level + 1)

            clear_screen()
            print("\n".join(box([
                "",
                f"{G}{BOLD}🏆 LEVEL {level} COMPLETE!{W}",
                "",
                f"{Y}+200 XP   (Total: {exp}){W}",
                "",
                "Leo claims the Lost Temple treasure!",
                "",
            ], width=46)))
            input("\nPress Enter to return to menu...")
        return


def main_menu():
    while True:
        clear_screen()
        print("\n".join(box([
            "",
            f"{BOLD}🏛️  THE LOST TEMPLE  🦁{W}",
            f"{DIM}Navigate the maze. Survive the ghosts. Defeat the Evil Panda.{W}",
            "",
        ], width=82)))
        print()
        for n in range(1, 5):
            if n in unlocked_level:
                tag = f"  {DIM}(coming soon){W}" if not mazetotal[n - 1] else ""
            else:
                tag = f"  {R}(Locked 🔒){W}"
                
            emoji = LEVEL_EMOJIS[n - 1] 
            print(f"  {n}. Level {n} {emoji}{tag}")
        print("  0. Exit Game\n")

        choice = input("Select an option (0-4): ").strip()

        if choice in ["1", "2", "3", "4"]:
            lv = int(choice)
            if lv not in unlocked_level:
                print(f"\n{R}Level {lv} is locked! You must complete the previous level first.{W}")
                time.sleep(1.2)
                continue

            run_level_with_boss(lv)
        elif choice == "0":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice.")
            time.sleep(0.8)


def main():
    if not sys.stdin.isatty():
        print("This game needs an interactive terminal. (Use -it with Docker)")
        return

    try:
        d = input("Start Leo's Lost Temple adventure? (y/n): ").strip().lower()
        if d != "y":
            print("Goodbye!")
            return
        story_screen()
        main_menu()
    except KeyboardInterrupt:
        print("\nGame Over")


if __name__ == "__main__":
    main()

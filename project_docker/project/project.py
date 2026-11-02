import os
import re
import sys
import time
import random
import shutil
import unicodedata
from contextlib import contextmanager

# ============================================================
#  TERMINAL LAYER
# ============================================================
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


# ============================================================
#  UI HELPERS
# ============================================================
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
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


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
    cols = shutil.get_terminal_size().columns
    margin = " " * max(0, (cols - frame_width) // 2) if frame_width else ""
    out = "".join(margin + ln + "\033[K\n" for ln in lines)
    sys.stdout.write("\033[H" + out + "\033[J")
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


# ============================================================
#  STORY
# ============================================================
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

# ============================================================
#  MAZE
# ============================================================
wall = "🧱"
path = "⚪"
player = "🦁"
enemy = "👻"
maze_key = "🔑"
mystery = "❓"
terminal = "⛺"
sleeping = "💤"
lightning = "⚡"

TILES = {
    "#": wall, ".": path, "P": player, "E": enemy,
    "K": maze_key, "?": mystery, "T": terminal, "L": lightning
}

# simpler, more open maze
maze1 = [
    "#########T#########",
    "#P......#.........#",
    "#.####..#.#####...#",
    "#......##.....#...#",
    "#.###......##.#...#",
    "#...#..##.....#...#",
    "#.#....#...##.....#",
    "#.#.##...#....###.#",
    "#...#....#..?...#.#",
    "#.###.##.#..##.#K.#",
    "#...E....#........#",
    "###################",
]
maze2, maze3, maze4, maze5, maze6 = [], [], [], [], []
mazetotal = [maze1, maze2, maze3, maze4, maze5, maze6]

MAX_HEALTH = 100
REQUIRE_KEY = True
DORMANT_TURNS = 3
LIGHTNING_RESPAWN_CHANCE = 0.12
MAX_BATTLE_CHARGE = 3

exp = 0
health_level = MAX_HEALTH
battle_charge = 0
inventory = []

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


def gain_battle_charge(n=1):
    global battle_charge
    battle_charge = min(MAX_BATTLE_CHARGE, battle_charge + n)


def load_level(number):
    global current_level_num, base_grid, player_pos, enemy_pos, enemy_dazed_turns
    current_level_num = number
    base_grid = []
    enemy_pos = None
    enemy_dazed_turns = 0
    for y, row in enumerate(mazetotal[number - 1]):
        cells = []
        for x, ch in enumerate(row):
            if ch == "P":
                player_pos = (x, y)
                ch = "."
            elif ch == "E":
                enemy_pos = (x, y)
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
    if (x, y) == enemy_pos:
        return sleeping if enemy_dazed_turns > 0 else enemy
    return base_grid[y][x]


def draw_maze():
    cols = len(base_grid[0])
    inner = cols * 2
    lines = [f"{BOLD}{C}{pad(f'🏛️ THE LOST TEMPLE - LEVEL {current_level_num}', inner+2, 'center')}{W}"]
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
        f" {DIM}{maze_key} key  {mystery} mystery  {lightning} boss-charge  {enemy} ghost  {terminal} exit{W}",
        f" {DIM}WASD/Arrows move, Q quit{W}",
    ]
    render(lines, inner+2)


def getexp(method):
    global exp
    if method == "moveblock":
        exp += 5
    elif method == "solvepuzzle":
        exp += 50
    elif method == "lost":
        exp += 20


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
    global enemy_dazed_turns
    if enemy_pos is None or enemy_dazed_turns > 0:
        return False
    if player_pos != enemy_pos:
        return False
    result = combat()
    if result:
        set_message(f"{G}You defeated the ghost!{W}")
    else:
        enemy_dazed_turns = DORMANT_TURNS
        getexp("lost")
        set_message(f"{R}👻 Ghost strikes! Dazed for {DORMANT_TURNS} turns.{W}")
    return True


def enemy_move():
    global enemy_pos, enemy_direction, enemy_dazed_turns
    if enemy_pos is None:
        return
    if enemy_dazed_turns > 0:
        enemy_dazed_turns -= 1
        return

    x, y = enemy_pos
    options = {}
    for name, (dx, dy) in ENEMY_DIRS.items():
        nx, ny = x + dx, y + dy
        if base_grid[ny][nx] not in (wall, terminal):
            options[name] = (nx, ny)
    if not options:
        return

    junction = len(options) >= 3
    keep = enemy_direction in options and not (junction and random.random() < 0.35)
    if not keep:
        choices = [d for d in options if d != OPPOSITE.get(enemy_direction)] or list(options)
        enemy_direction = random.choice(choices)
    enemy_pos = options[enemy_direction]


def handle_move(k):
    global player_pos
    dx, dy = DIRS[k]
    tx, ty = player_pos[0] + dx, player_pos[1] + dy

    if not (0 <= ty < len(base_grid) and 0 <= tx < len(base_grid[0])):
        return None, False
    target = base_grid[ty][tx]
    if target == wall:
        return None, False

    if target == terminal:
        if REQUIRE_KEY and maze_key not in inventory:
            set_message(f"{Y}⛺ The gate is sealed. Find {maze_key}.{W}")
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
    else:
        getexp("moveblock")
    return None, True


def play_level(level_number):
    global health_level, inventory, battle_charge, enemy_direction, message_text
    load_level(level_number)
    health_level = MAX_HEALTH
    inventory = []
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
                enemy_move()      # same speed as player
                check_collision()
                maybe_respawn_lightning()

            if health_level <= 0:
                draw_maze()
                return "lost"

            draw_maze()


# ============================================================
#  BOSS BATTLE (POLISHED)
# ============================================================
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
    # 1/3 shield chance
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

        # reward for successful shielding/blocking
        if blocked > 0:
            hero["energy"] = min(hero["max_energy"], hero["energy"] + 1)
            animate(f"{B}🛡️ You blocked {blocked}! Counter-focus +1 energy.{W}", flash="hero", t=0.2)

        animate(f"{R}💥 {move['name']} hits for {actual} ({blocked} blocked){W}", flash="hero", t=0.3)
    else:
        drain = min(move["value"], hero["energy"])
        hero["energy"] -= drain
        animate(f"{M}😱 Dread Howl drains {drain} energy!{W}", flash="hero", t=0.28)

    hero["armor"] = 0  # armor lasts through one boss retaliation
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
                # boss attacks after every player turn/action
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


# ============================================================
#  GAME FLOW
# ============================================================
def story_screen():
    clear_screen()
    lines = box([""] + STORY_LINES + ["", f"{Y}Press any key to continue...{W}"], width=90)
    render([""] + lines, 92)
    wait_for_key()


def run_level_with_boss(level):
    global exp
    while True:
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
        for n in range(1, 7):
            tag = f"  {DIM}(coming soon){W}" if not mazetotal[n - 1] else ""
            print(f"  {n}. Level {n}{tag}")
        print("  0. Exit Game\n")

        choice = input("Select an option (0-6): ").strip()

        if choice in ["1", "2", "3", "4", "5", "6"]:
            lv = int(choice)
            if not mazetotal[lv - 1]:
                print(f"\nLevel {lv} is not built yet.")
                time.sleep(1.0)
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
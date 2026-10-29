import random
import time
import shutil

R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
B = "\033[94m"
C = "\033[96m"
W = "\033[0m"
BOLD = "\033[1m"

def clear():
    print("\033[2J\033[H", end="")

def check_size():
    cols, rows = shutil.get_terminal_size()
    if cols < 80 or rows < 24:
        clear()
        print(f"{R}Terminal too small!{W}")
        print(f"Please resize to 80x24 (current: {cols}x{rows})")
        input("Press Enter to retry...")
        return check_size()
    return True

p = {"hp": 30, "max_hp": 30, "armor": 0, "energy": 3, "max_energy": 3}

b = {
    "name": "🐲 Dragon",
    "hp": 60, "max_hp": 60,
    "phase": 1,
    "next_move": None,
    "is_fake": False
}

deck = [
    {"name": "Slash", "icon": "⚔️", "cost": 1, "type": "dmg", "val": 6},
    {"name": "Block", "icon": "🛡️", "cost": 1, "type": "armor", "val": 5},
    {"name": "Heal", "icon": "💚", "cost": 1, "type": "heal", "val": 5},
    {"name": "Flame", "icon": "🔥", "cost": 2, "type": "dmg", "val": 12},
]

logs = []

def log(msg):
    logs.append(msg)
    if len(logs) > 4:
        logs.pop(0)

def bar(cur, mx, length=20):
    f = int(length * (cur / mx))
    return f"[{'█' * f}{'░' * (length - f)}]"

def draw():
    clear()
    print(BOLD + "=" * 80 + W)
    
    phase_str = f"{R}[ENRAGED]{W}" if b["phase"] == 2 else "[NORMAL]"
    print(f" {b['name']} {phase_str} HP: {bar(b['hp'], b['max_hp'])} {b['hp']}/{b['max_hp']}")
    
    if b["next_move"]:
        print(f" {Y}⚠️ Warning: Boss is preparing [{b['next_move']['name']}]...{W}")
    else:
        print(" " * 80)
    print(BOLD + "=" * 80 + W)
    
    print(f" YOU: ❤️ {p['hp']}/{p['max_hp']}  🛡️ {p['armor']}  ⚡ {p['energy']}/{p['max_energy']}")
    print("-" * 80)

    print(f" {C}--- Battle Log ---{W}")
    for l in logs:
        print(f"  {l}")
    for _ in range(4 - len(logs)):
        print()
    print("-" * 80)

    print(" Hand:")
    for i, c in enumerate(deck, 1):
        col = R if c["type"] == "dmg" else B if c["type"] == "armor" else G
        print(f"  [{i}] {col}{c['icon']} {c['name']}{W}(Cost:{c['cost']})", end="")
    print("\n" + "=" * 80)
    print(f" Input 1-4 | {Y}e{W} to end turn | {Y}q{W} to quit")

def boss_action():
    if b["next_move"] and not b["is_fake"]:
        move = b["next_move"]
        dmg = move["value"]
        if b["phase"] == 2:
            dmg = int(dmg * 1.5)
        
        if random.random() < 0.1:
            log(f"{C}💨 You dodged the Boss's [{move['name']}]!{W}")
            time.sleep(0.5)
        else:
            actual = max(0, dmg - p["armor"])
            p["hp"] -= actual
            log(f"{R}💥 Boss used [{move['name']}], dealing {actual} damage!{W}")
            time.sleep(0.5)
    elif b["is_fake"]:
        log(f"{Y}👻 Boss's warning was a fake! It did nothing!{W}")
        time.sleep(0.5)

    b["next_move"] = random.choice([
        {"name": "Claw", "value": 8},
        {"name": "Fire Breath", "value": 12}
    ])
    b["is_fake"] = (random.random() < 0.2)

def check_phase():
    if b["hp"] <= b["max_hp"] / 2 and b["phase"] == 1:
        b["phase"] = 2
        log(f"{R}{BOLD}🚨 Dragon roars, entering [ENRAGED]! Damage increased!{W}")
        time.sleep(1)

def end_turn():
    p["armor"] = 0
    boss_action()
    if p["hp"] <= 0:
        return
    p["energy"] = p["max_energy"]

def main():
    check_size()
    log(f"{Y}You encountered a wild Dragon! Battle Start!{W}")
    
    b["next_move"] = {"name": "Claw", "value": 8}
    
    while p["hp"] > 0 and b["hp"] > 0:
        draw()
        cmd = input(f"\n {G}Your action > {W}").strip().lower()
        
        if cmd == "q":
            break
        elif cmd == "e":
            log(f"{Y}You ended your turn.{W}")
            end_turn()
        elif cmd.isdigit() and 1 <= int(cmd) <= len(deck):
            card = deck[int(cmd) - 1]
            if card["cost"] <= p["energy"]:
                p["energy"] -= card["cost"]
                
                if card["type"] == "dmg":
                    crit = random.random() < 0.15
                    dmg = card["val"] * 2 if crit else card["val"]
                    b["hp"] -= dmg
                    
                    c_txt = f"{R}{BOLD}💥 CRITICAL! {W}" if crit else ""
                    log(f"{c_txt}You used [{card['icon']}{card['name']}], dealing {dmg} damage!")
                    time.sleep(0.3)
                    check_phase()
                elif card["type"] == "armor":
                    p["armor"] += card["val"]
                    log(f"{B}You used [{card['icon']}{card['name']}], gained {card['val']} armor.{W}")
                    time.sleep(0.2)
                elif card["type"] == "heal":
                    amt = min(card["val"], p["max_hp"] - p["hp"])
                    p["hp"] += amt
                    log(f"{G}You used [{card['icon']}{card['name']}], healed {amt} HP.{W}")
                    time.sleep(0.2)
            else:
                log(f"{R}Not enough energy!{W}")
                time.sleep(0.5)

    draw()
    if b["hp"] <= 0:
        print(f"\n{G}{BOLD}🎉 VICTORY! You defeated the {b['name']}!{W}\n")
    elif p["hp"] <= 0:
        print(f"\n{R}{BOLD}💀 DEFEAT... You have fallen.{W}\n")

if __name__ == "__main__":
    main()

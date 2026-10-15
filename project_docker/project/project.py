import os
import random
import time
import sys

### Cross-platform single key reader setup
if os.name == 'nt':
    import msvcrt
    def get_single_keypress():
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            try:
                return ch.decode('utf-8').upper()
            except:
                return None
        return None
else:
    import tty
    import termios
    import select
    
    # Configure terminal to raw mode once globally during gameplay to prevent blocking
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    def set_raw_terminal():
        tty.setcbreak(fd)
        
    def restore_terminal():
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def get_single_keypress():
        if select.select([sys.stdin], [], [], 0)[0]:
            ch = sys.stdin.read(1)
            return ch.upper()
        return None

game_running = True
wall = "🧱"
path = "⚪"
player = "🦁"
enemy = "👻"
maze_key = "🔑" 
mystery = "❓"
terminal = "⛺"
maze1 = [
    [wall, wall, wall, wall, terminal, wall, wall, wall],
    [wall, player, wall, path, path, enemy, path, wall],
    [wall, path, wall, path, wall, path, wall, wall],
    [wall, path, wall, maze_key, wall, path, path, wall],
    [wall, path, wall, path, wall, mystery, path, wall],
    [wall, path, wall, path, wall, wall, path, wall],
    [wall, path, path, path, path, path, path, wall],
    [wall, wall, wall, wall, wall, wall, wall, wall],
]
maze2 = []
maze3 = []
maze4 = []
maze5 = []
maze6 = []
npclist = [enemy]
mazetotal = [maze1, maze2, maze3, maze4, maze5, maze6]

exp = 0
health_level = 100
inventory = "|"
level1unlock = True
level2unlock = False
level3unlock = False
level4unlock = False
level5unlock = False
level6unlock = False

current_level_num = 1
mazegame = None

dormanttime = 0

def selectlevel(number):
    global current_level_num, mazegame
    current_level_num = number
    mazegame = mazetotal[number - 1]
    draw(number)

def draw(number=None):
    if number is None:
        number = current_level_num
    os.system("cls" if os.name == "nt" else "clear")
    for row in mazetotal[number - 1]:
        print("".join(row))
    print(f"Current Experience {exp} xp")
    print(f"Current Health Level {health_level} %")
    print(f"Your Inventory:{inventory}")


def launchgame(level_number):
    selectlevel(level_number)


def position(symbol):
    for i in range(len(mazegame)):
        for j in range(len(mazegame[1])):
            if mazegame[i][j] == symbol:
                return {"x": j, "y": i}


def getexp(method):
    global exp
    if method == "moveblock":
        exp += 5
    if method == "solvepuzzle":
        exp += 50
    if method == "lost":
        exp += 20

###### COMBAT MODE CODE BELOW ######

def combat(npctype):
    global health_level
    health_level -= 90
    return(False)

###### COMBAT MODE CODE ABOVE ######

def trigger_combat_if_collided():
    global dormanttime
    if time.time() < dormanttime:
        return
    player_pos = position(player)
    enemy_pos = position(enemy)
    
    if player_pos and enemy_pos and player_pos == enemy_pos:
        result = combat(current_level_num - 1)
        if not result:
            dormanttime = time.time() + 10

###### MISTERY CODE BELOW ######
#def mistery():
###### MISTERY CODE ABOVE ######

enemydirection = None
replaced = None
replacedposition = None
def enemy_move():
    global enemydirection
    global replaced
    global replacedposition
    global dormanttime

    if time.time() < dormanttime:
        return

    pos = position(enemy)
    if not pos:
        return
    if replaced is not None:
        old_tile = replaced
        replaced = None
        replacedposition = None
    else:
        old_tile = path

    leftok = mazegame[pos["y"]][pos["x"] - 1] != wall
    rightok = mazegame[pos["y"]][pos["x"] + 1] != wall
    upok = mazegame[pos["y"] - 1][pos["x"]] != wall
    downok = mazegame[pos["y"] + 1][pos["x"]] != wall

    currentdirectionok = (
        (enemydirection == "left" and leftok)
        or (enemydirection == "right" and rightok)
        or (enemydirection == "up" and upok)
        or (enemydirection == "down" and downok)
    )
    if not currentdirectionok:
        choose = []
        if leftok:
            choose.append("left")
        if rightok:
            choose.append("right")
        if upok:
            choose.append("up")
        if downok:
            choose.append("down")
        if not choose:
            return
        enemydirection = random.choice(choose)

    if enemydirection == "left" and leftok:
        if mazegame[pos["y"]][pos["x"] - 1] == path:
            mazegame[pos["y"]][pos["x"] - 1] = enemy
            mazegame[pos["y"]][pos["x"]] = old_tile  
        else:
            replaced = mazegame[pos["y"]][pos["x"] - 1]
            replacedposition = {"y": pos["y"], "x": pos["x"] - 1}
            mazegame[pos["y"]][pos["x"] - 1] = enemy
            mazegame[pos["y"]][pos["x"]] = old_tile 
            
    elif enemydirection == "right" and rightok:
        if mazegame[pos["y"]][pos["x"] + 1] == path:
            mazegame[pos["y"]][pos["x"] + 1] = enemy
            mazegame[pos["y"]][pos["x"]] = old_tile  
        else:
            replaced = mazegame[pos["y"]][pos["x"] + 1]
            replacedposition = {"y": pos["y"] + 1, "x": pos["x"] + 1}
            mazegame[pos["y"]][pos["x"] + 1] = enemy
            mazegame[pos["y"]][pos["x"]] = old_tile

    elif enemydirection == "up" and upok:  
        if mazegame[pos["y"] - 1][pos["x"]] == path:
            mazegame[pos["y"] - 1][pos["x"]] = enemy
            mazegame[pos["y"]][pos["x"]] = old_tile  
        else:
            replaced = mazegame[pos["y"] - 1][pos["x"]]
            replacedposition = {"y": pos["y"] - 1, "x": pos["x"]}
            mazegame[pos["y"] - 1][pos["x"]] = enemy
            mazegame[pos["y"]][pos["x"]] = old_tile  

    elif enemydirection == "down" and downok:
        if mazegame[pos["y"] + 1][pos["x"]] == path:
            mazegame[pos["y"] + 1][pos["x"]] = enemy
            mazegame[pos["y"]][pos["x"]] = old_tile  
        else:
            replaced = mazegame[pos["y"] + 1][pos["x"]]
            replacedposition = {"y": pos["y"] + 1, "x": pos["x"]}
            mazegame[pos["y"] + 1][pos["x"]] = enemy
            mazegame[pos["y"]][pos["x"]] = old_tile 
    
    trigger_combat_if_collided()

def getxp_beat_npc(number):
    global exp
    exp += number

position_mys = None
stepped_on_enemy = False

def handle_move(direction):
    global dormanttime
    global position_mys
    global stepped_on_enemy
    global game_running
    
    direction = direction.upper()

    pos = position(player)
    currentx, currenty = pos["x"], pos["y"]
    targetx, targety = pos["x"], pos["y"]

    if direction == "W":
        targety -= 1
    elif direction == "S":
        targety += 1
    elif direction == "A":
        targetx -= 1
    elif direction == "D":
        targetx += 1
    else:
        return

    target_tile = mazegame[targety][targetx]

    if target_tile == wall:
        return

    if stepped_on_enemy:
        mazegame[currenty][currentx] = enemy
        stepped_on_enemy = False
    elif replacedposition and currentx == replacedposition["x"] and currenty == replacedposition["y"]:
        mazegame[currenty][currentx] = enemy
    elif position_mys and currentx == position_mys["x"] and currenty == position_mys["y"]:
        mazegame[currenty][currentx] = mystery
    else:
        mazegame[currenty][currentx] = path

    if target_tile == maze_key:
        global inventory
        inventory += maze_key
        inventory += "|"
        mazegame[targety][targetx] = player
    elif target_tile == mystery:
        position_mys = {"x": targetx, "y": targety}
        mazegame[targety][targetx] = player
    elif target_tile == enemy:
        stepped_on_enemy = True
        dormanttime = time.time() + 10
        mazegame[targety][targetx] = player
        getexp("lost")
        combat(current_level_num - 1)
        trigger_combat_if_collided()
    elif target_tile == terminal:
        mazegame[targety][targetx] = player
        draw()
        print("\nYOU WIN!")
        time.sleep(1.5)
        game_running = False
    else:
        mazegame[targety][targetx] = player
        getexp("moveblock")

player_response = None
def main_menu():
    global game_running
    global player_response
    global health_level
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=== GAME MENU ===")
        print("1. Level 1")
        print("2. Level 2")
        print("3. Level 3")
        print("4. Level 4")
        print("5. Level 5")
        print("6. Level 6")
        print("0. Exit Game")
        
        choice = input("Select an option (0-6): ").strip()
        
        if choice in ["1", "2", "3", "4", "5", "6"]:
            selected_level = int(choice)
            if not mazetotal[selected_level - 1]:
                print(f"\nLevel {selected_level} map is empty! Please construct the maze map first.")
                time.sleep(0.5)
                continue
                
            game_running = True
            launchgame(selected_level)
            
            if os.name != 'nt':
                set_raw_terminal()
                
            last_enemy_move_time = time.time()
            
            try:
                while game_running:
                    key = get_single_keypress()
                    if key:
                        if key == 'Q':
                            game_running = False
                            break
                        elif key in ['W', 'A', 'S', 'D']:
                            handle_move(key)
                            draw()
                    
                    if time.time() - last_enemy_move_time >= 1.0:
                        enemy_move()
                        last_enemy_move_time = time.time()
                        draw()
                    
                    trigger_combat_if_collided()
                    
                    if health_level <= 0:
                        if os.name != 'nt':
                            restore_terminal()
                        draw()
                        print("YOU LOST")
                        player_response = input("Do you want to restart?(y/n) ").lower()
                        if player_response == 'y':
                            health_level = 100
                            game_running = False
                        else:
                            sys.exit(0)
                            
                    time.sleep(0.03)

            except KeyboardInterrupt:
                print("\nGame Over")
            finally:
                if os.name != 'nt':
                    restore_terminal()
                
        elif choice == "0":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice, please select 0-6.")
            time.sleep(1)

decision = input("DO YOU WANT TO START THE GAME(y/n)? ").lower()
if decision == "y":
    main_menu()
else:
    print("Goodbye!")
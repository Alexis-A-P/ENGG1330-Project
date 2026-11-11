import os
import sys
import time

# 终端尺寸设置
WIDTH = 80
HEIGHT = 24

# 跨平台无阻塞按键读取
if os.name == 'nt':
    import msvcrt
    def get_key():
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            try:
                return ch.decode('utf-8').lower()
            except:
                return ''
        return None
else:
    import termios
    import tty
    import select
    def get_key():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
            if rlist:
                return sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return None

def clear_screen():
    sys.stdout.write("\033[H")

class TempleGame:
    def __init__(self):
        self.max_pos_logical = 16 * 4  
        self.player_pos_sub = 0        
        self.running = True
        self.is_moving = False  # 初始为静止等待状态
        self.move_counter = 0
        self.move_speed_delay = 5  # 冲锋节奏

    @property
    def player_pos_display(self):
        return self.player_pos_sub / 4.0

    def render_frame(self):
        screen = [[' ' for _ in range(WIDTH)] for _ in range(HEIGHT)]

        # 1. 绘制梯形地板
        for y in range(13, HEIGHT - 1):
            dy = y - 12
            half_w = int(dy * 3.8)
            left_bound = max(0, 40 - half_w)
            right_bound = min(WIDTH, 40 + half_w)
            
            for x in range(left_bound, right_bound):
                grid_z = int(dy + self.player_pos_display * 2) % 4
                if grid_z == 0:
                    screen[y][x] = '-' if x % 4 != 0 else '+'
                elif grid_z == 2:
                    screen[y][x] = '.' if x % 2 == 0 else '_'

        # 2. 绘制发光大门
        dist_to_door = (self.max_pos_logical - self.player_pos_sub) / 4.0
        
        if dist_to_door <= 0:
            door_msg = " * YOU REACHED THE ANCIENT GATE! * "
            start_x = (WIDTH - len(door_msg)) // 2
            for i, char in enumerate(door_msg):
                if 0 <= start_x + i < WIDTH:
                    screen[11][start_x + i] = char
        else:
            gate_half_w = min(35, max(3, int(28 / dist_to_door)))
            gate_half_h = min(10, max(2, int(9 / dist_to_door)))
            
            door_top = 12 - gate_half_h
            door_bottom = 12 + gate_half_h
            door_left = 40 - gate_half_w
            door_right = 40 + gate_half_w

            for y in range(max(0, door_top), min(HEIGHT - 1, door_bottom)):
                for x in range(max(0, door_left), min(WIDTH, door_right)):
                    if y == door_top or y == door_bottom - 1 or x == door_left or x == door_right - 1:
                        screen[y][x] = '#'
                    else:
                        screen[y][x] = '*' if (x + y + int(time.time() * 6)) % 3 == 0 else 'o'

        # 3. 绘制柱廊
        pillar_positions = [1, 3, 5, 7, 9, 11, 13, 15]

        for p_pos in pillar_positions:
            rel_dist = p_pos - self.player_pos_display
            
            if rel_dist > 0:
                offset = max(2, int(35 / rel_dist))
                half_h = min(11, max(1, int(11 / rel_dist)))
                p_width = max(1, min(7, int(8 - rel_dist)))
                
                top_y = 12 - half_h
                bot_y = 12 + half_h
                
                left_start = 40 - offset - p_width + 1
                right_start = 40 + offset

                for y in range(max(0, top_y), min(HEIGHT - 1, bot_y)):
                    for w in range(p_width):
                        curr_x = left_start + w
                        if 0 <= curr_x < WIDTH:
                            if p_width == 1:
                                screen[y][curr_x] = '|'
                            else:
                                if w == 0:
                                    screen[y][curr_x] = '['
                                elif w == p_width - 1:
                                    screen[y][curr_x] = ']'
                                else:
                                    screen[y][curr_x] = '#' if y % 2 != 0 else '='

                for y in range(max(0, top_y), min(HEIGHT - 1, bot_y)):
                    for w in range(p_width):
                        curr_x = right_start + w
                        if 0 <= curr_x < WIDTH:
                            if p_width == 1:
                                screen[y][curr_x] = '|'
                            else:
                                if w == 0:
                                    screen[y][curr_x] = '['
                                elif w == p_width - 1:
                                    screen[y][curr_x] = ']'
                                else:
                                    screen[y][curr_x] = '#' if y % 2 != 0 else '='

        # 4. 底部状态栏
        status = f" [POS: {self.player_pos_display:.2f}/{self.max_pos_logical/4}] Press [W] to Charge | [Q] Quit "
        for i, char in enumerate(status[:WIDTH]):
            screen[HEIGHT - 1][i] = char

        return "\n".join("".join(row) for row in screen)

    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.write("\033[?25l") # 隐藏光标
        
        try:
            # 刚进入游戏时，先静态渲染一帧初始画面，不进行任何无谓的循环刷新
            clear_screen()
            print(self.render_frame(), end="")

            while self.running:
                key = get_key()
                if key:
                    if key == 'w':
                        self.is_moving = True  # 按下 W 后，正式唤醒冲锋！
                    elif key == 'q':
                        self.running = False

                # 只有在唤醒冲锋后，才开始自动步进和连续渲染动画
                if self.is_moving:
                    self.move_counter += 1
                    if self.move_counter >= self.move_speed_delay:
                        self.move_counter = 0
                        if self.player_pos_sub < self.max_pos_logical:
                            self.player_pos_sub += 1
                        else:
                            self.is_moving = False

                    clear_screen()
                    print(self.render_frame(), end="")

                    # 到达终点后自动全黑过渡
                    if self.player_pos_sub >= self.max_pos_logical:
                        time.sleep(1.5)  # 停留 1.5 秒展示胜利画卷
                        clear_screen()
                        sys.stdout.write("\n".join([" " * WIDTH for _ in range(HEIGHT)]))
                        sys.stdout.flush()
                        time.sleep(1.0)
                        break

                time.sleep(0.015)
        finally:
            sys.stdout.write("\033[?25h")
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n")

if __name__ == "__main__":
    game = TempleGame()
    game.run()
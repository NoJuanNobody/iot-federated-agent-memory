#!/usr/bin/env python3
"""
AI Mesíah - Fullscreen Cyberpunk AI Monkey Screensaver & TUI
Rendered directly from the Gemini Generated Cyber-Ape Art asset.
"""

import curses
import random
import sys
import time

MONKEY_ASCII_FRAMES = [
[
    r"       .---.                                           .---.       ",
    r"      /     \           .-----------------.           /     \      ",
    r"     | () () |         /     AI MESÍAH     \         | () () |     ",
    r"      \  -  /         |   CYBER-APE MESH    |         \  -  /      ",
    r"       \___/           \  CORE RELAY ACTIVE/           \___/       ",
    r"     .---'-.            '-----------------'            .-'---.     ",
    r"    / / _ \ \       .:::---==+++++#*+*+**###.         / / _ \ \    ",
    r"   | | ( ) | |   ##****#######%%%%%%%%*@*+++++++     | | ( ) | |   ",
    r"   | |  `  | |   @@*@@@@@@@%#*+#%@@@@@*@:    ..      | |  `  | |   ",
    r"    \ \___/ /    @@#@@@@@*-:--:---+%@@*@: ..:--::.    \ \___/ /    ",
    r"     '-----'     @@#@@@#--::::.:.:.:*%*@: .::--...     '-----'     ",
    r"                 @@#@%#--:--:-:.:.. :+*@:..::::..:                 ",
    r"                 @@*%#=-:-:::::..::. -*@:..-=-..:                  ",
    r"   .---------.   @@#@=-==-=- .- ...-.-*@: :+--+:.:   .---------.   ",
    r"  /  CYBER    \  @@#%+... ..: .....=.:+@:.-:..:-.:  /   MESH    \  ",
    r" |  TELEMETRY  | @@**#=---=++. . .-: :+@:--. -#-.  |  RECEIPT    | ",
    r"  \  ONLINE   /  @@*#@-+=:---::....  .=@:.=::=..=:  \  VALID    /  ",
    r"   '---------'   @@#@@++*=: .--.:    .-@:.:- :++:    '---------'   ",
    r"                 @@#@##@%+-. :...    :-@: .=:-==-                  ",
    r"                 @@*#*--+--: . .  .::=*@:..:=.*%*                  ",
    r"                 @@=*%--*+-.     ..--**@: .::----                  ",
    r"                 @@*%%=-=:         .:**@: ...:-.                   ",
    r"                 @@#%++--:.   ..:---#@*@:    ..::                  ",
    r"                 @@*#**+*--..-+***%%%%*@:    ..                    ",
    r"                 @@#****#**#*****#****#@#*+++#*+#                  ",
    r"                 @@%%%#*+=+==+++==+###%@@%%%**==+                  ",
    r"           ⚡  A I   M E S Í A H   //   C Y B E R - A P E  ⚡        ",
],
[
    r"       .---.                                           .---.       ",
    r"      /     \           .-----------------.           /     \      ",
    r"     | [o] [o]|        /     AI MESÍAH     \         | [o] [o]|    ",
    r"      \  =  /         |   CYBER-APE MESH    |         \  =  /      ",
    r"       \___/           \  NEURAL UDP SYNC  /           \___/       ",
    r"     .---'-.            '-----------------'            .-'---.     ",
    r"    / / ✦ \ \       .:::---==+++++#*+*+**###.         / / ✦ \ \    ",
    r"   | | ( ) | |   ##****#######%%%%%%%%*@*+++++++     | | ( ) | |   ",
    r"   | |  `  | |   @@*@@@@@@@%#*+#%@@@@@*@:   ...      | |  `  | |   ",
    r"    \ \___/ /    @@#@@@@@*-:--:---+%@@*@: ..:==::.    \ \___/ /    ",
    r"     '-----'     @@#@@@#--::::.:.:.:*%*@: .::--...     '-----'     ",
    r"                 @@#@%#--:--:-:.:.. :+*@:..::::..:                 ",
    r"                 @@*%#=-:-:::::..::. -*@:..-=-..:                  ",
    r"   .---------.   @@#@=-==-=- .- ...-.-*@: :+--+:.:   .---------.   ",
    r"  /  WEBRTC   \  @@#%+... ..: .....=.:+@:.-:..:-.:  /   CLAUDE  \  ",
    r" |   UDP 60FPS | @@**#=---=++. . .-: :+@:--. -#-.  |  & GROK POOL| ",
    r"  \  SUB-80MS /  @@*#@-+=:---::....  .=@:.=::=..=:  \   ACTIVE  /  ",
    r"   '---------'   @@#@@++*=: .--.:    .-@:.:- :++:    '---------'   ",
    r"                 @@#@##@%+-. :...    :-@: .=:-==-                  ",
    r"                 @@*#*--+--: . .  .::=*@:..:=.*%*                  ",
    r"                 @@=*%--*+-.     ..--**@: .::----                  ",
    r"                 @@*%%=-=:         .:**@: ...:-.                   ",
    r"                 @@#%++--:.   ..:---#@*@:    ..::                  ",
    r"                 @@*#**+*--..-+***%%%%*@:    ..                    ",
    r"                 @@#****#**#*****#****#@#*+++#*+#                  ",
    r"                 @@%%%#*+=+==+++==+###%@@%%%**==+                  ",
    r"           ◈  A I   M E S Í A H   //   C Y B E R - A P E  ◈        ",
]
]

MATRIX_CHARS = "0123456789ABCDEF!@#$%^&*()_+-=[]{}|;:,.<>?"

def main_curses(stdscr, duration=None):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()

    # Color pairs
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_MAGENTA, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)

    max_y, max_x = stdscr.getmaxyx()
    columns = max_x
    drops = [random.randint(-25, 0) for _ in range(columns)]
    speeds = [random.uniform(0.7, 1.4) for _ in range(columns)]

    start_time = time.time()
    frame = 0

    while True:
        if duration and (time.time() - start_time) > duration:
            break

        key = stdscr.getch()
        if key in [ord('q'), ord('Q'), 27]:
            break

        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        # 1. Render Matrix Rain Background
        for i in range(0, min(columns, max_x), 2):
            drop_y = int(drops[i])
            for tail in range(12):
                y = drop_y - tail
                if 0 <= y < max_y:
                    char = random.choice(MATRIX_CHARS)
                    if tail == 0:
                        stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
                    elif tail < 4:
                        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
                    else:
                        stdscr.attron(curses.color_pair(3))
                    try:
                        stdscr.addch(y, i, char)
                    except curses.error:
                        pass
            drops[i] += speeds[i]
            if drops[i] - 12 > max_y:
                drops[i] = random.randint(-20, 0)

        # 2. Render Centered Cyber-Monkey Box
        active_monkey = MONKEY_ASCII_FRAMES[(frame // 6) % len(MONKEY_ASCII_FRAMES)]
        box_w = max(len(l) for l in active_monkey) + 4
        box_h = len(active_monkey) + 2
        box_y = max(1, (max_y - box_h) // 2)
        box_x = max(1, (max_x - box_w) // 2)

        # Draw dark clearing behind the monkey
        for y in range(box_y - 1, min(max_y, box_y + box_h + 1)):
            for x in range(box_x - 1, min(max_x, box_x + box_w + 1)):
                try:
                    stdscr.addch(y, x, ' ')
                except curses.error:
                    pass

        # Border
        border_col = curses.color_pair(1 if (frame // 4) % 2 == 0 else 2) | curses.A_BOLD
        stdscr.attron(border_col)
        try:
            stdscr.addstr(box_y - 1, box_x - 1, "╭" + "─" * (box_w) + "╮")
            for r in range(box_h):
                if box_y + r < max_y:
                    stdscr.addstr(box_y + r, box_x - 1, "│")
                    stdscr.addstr(box_y + r, box_x + box_w, "│")
            stdscr.addstr(box_y + box_h, box_x - 1, "╰" + "─" * (box_w) + "╯")
        except curses.error:
            pass

        # Render Monkey Lines
        for idx, line in enumerate(active_monkey):
            y = box_y + idx
            x = box_x + (box_w - len(line)) // 2
            if y < max_y and x < max_x:
                try:
                    if "⚡" in line or "◈" in line:
                        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
                    elif idx < 6:
                        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
                    else:
                        stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                    stdscr.addstr(y, x, line)
                except curses.error:
                    pass

        # Controls Hint
        try:
            stdscr.attron(curses.color_pair(5) | curses.A_DIM)
            stdscr.addstr(max_y - 1, 2, "[Press 'Q' or 'ESC' to exit AI Monkey Screensaver]")
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.04)
        frame += 1

def run_tui(duration=None):
    curses.wrapper(main_curses, duration)

if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else None
    run_tui(dur)

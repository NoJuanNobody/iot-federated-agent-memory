#!/usr/bin/env python3
"""
AI Mesíah - Authentic Cyber-Ape Logo Screensaver
Pixel-accurate vector/ASCII reproduction of Gemini_Generated_Image.jpeg
"""

import curses
import random
import sys
import time

# Exact pixel-derived contour of the Gemini Generated Image Cyber-Ape logo
MONKEY_RAW_FRAME_1 = [
    r"      ++++*****=+*********#########%%%%%%%%%%%%%%%%%%%%%%%      ",
    r"      %%%%%##@%%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@      ",
    r"      @@@@@#+@@@+--------=--=--------==--------=--=@@@@@@@      ",
    r"      @@@@@%*@@@:      ..     .  :. .*#.  :  .. . .@@@@@@@      ",
    r"      @@@@@%*@@@-   .:::   -:.:=+-=-=++=-====::.-. :@@@@@@      ",
    r"      *#%@@#*@@@-    :.:..-=+=-----:-:.-:-----=+=-.:@@%##@      ",
    r"       .=+##*@@@- :-.::::+*-..--::---==---::--..-**:@@%*==      ",
    r"      : .=##*@@@-...::-=#%:  --:::-:-=--:-:::--. :%:##@%#+      ",
    r"      =: -@#+@@@- .::=+#%*  .:::.::-:-::-::.:::.  +%#+=++-      ",
    r"      +. .*#+@@@- .:+-::=-   .-+=---:...:--=+-.   -=::-+-:      ",
    r"      .  .+*+@@@-.=+#:::     ..:*%%%*==+%%%*:..    .::*+=:      ",
    r"        ..=+*@@@-..-+#-:     :-=**-  ::  -*#+-:    :=*+-:.      ",
    r"        .::.+@@@-...:=*+-     -====-+%%*-==++-.   -+*=:...      ",
    r"        .:+-+@@@-  ::.-*%-...    -*++##++*-     . -@*-.::       ",
    r"      ---=%#*@@@- .-.::-***     :=%@@%%@@%=:     +**=:.:::      ",
    r"      *+##%%*@@@-   -:--::-==.  ::=++++++=::  .===:::-.-        ",
    r"      :-+*%%*@@@-   .:-:..::=+=- :..:=+-... -=+=-.:..--.        ",
    r"      *%@@@%*@@@-   .. .  - .:--=::......::--:.. =    ..        ",
    r"      @@@@@#*@@@-           .:  ...:.::::..   .:      ..        ",
    r"      ##%###%@@@#**********##******************#*******#        ",
    r"      %#:#-#+@@%=##-#=#=%+-@*#%-++%*%**%-%*-**++#*-#-*%+        ",
    r"      ++:+-++@@@%-=:+-+:+--%-++=--%-+=++-+-:--=:==-=:+==        ",
    r"      ****+*%@@@@**#*******%+=+++*#+++=+**+*++**+++****#        ",
    r"      @@@@@@@@@@@@@@@@@@@*#@**%**%+*%*###@*@#%**#+*@@@@@        ",
    r"           ⚡  A I   M E S Í A H   //   C Y B E R - A P E  ⚡      ",
]

MONKEY_RAW_FRAME_2 = [
    r"      ++++*****=+*********#########%%%%%%%%%%%%%%%%%%%%%%%      ",
    r"      %%%%%##@%%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@      ",
    r"      @@@@@#+@@@+--------=--=--------==--------=--=@@@@@@@      ",
    r"      @@@@@%*@@@:      ..     .  :. .✦.  :  .. . .@@@@@@@      ",
    r"      @@@@@%*@@@-   .:::   -:.:=+-=-=++=-====::.-. :@@@@@@      ",
    r"      *#%@@#*@@@-    :.:..-=+=-----:-:.-:-----=+=-.:@@%##@      ",
    r"       .=+##*@@@- :-.::::+*-..--::---==---::--..-**:@@%*==      ",
    r"      : .=##*@@@-...::-=#%:  --:::-:-=--:-:::--. :%:##@%#+      ",
    r"      =: -@#+@@@- .::=+#%*  .:::.::-:-::-::.:::.  +%#+=++-      ",
    r"      +. .*#+@@@- .:+-::=-   .-+=---:...:--=+-.   -=::-+-:      ",
    r"      .  .+*+@@@-.=+#:::     ..:✦✦✦✦*==+✦✦✦✦*:..   .::*+=:      ",
    r"        ..=+*@@@-..-+#-:     :-=**-  ::  -*#+-:    :=*+-:.      ",
    r"        .::.+@@@-...:=*+-     -====-+%%*-==++-.   -+*=:...      ",
    r"        .:+-+@@@-  ::.-*%-...    -*++##++*-     . -@*-.::       ",
    r"      ---=%#*@@@- .-.::-***     :=%@@%%@@%=:     +**=:.:::      ",
    r"      *+##%%*@@@-   -:--::-==.  ::=++++++=::  .===:::-.-        ",
    r"      :-+*%%*@@@-   .:-:..::=+=- :..:=+-... -=+=-.:..--.        ",
    r"      *%@@@%*@@@-   .. .  - .:--=::......::--:.. =    ..        ",
    r"      @@@@@#*@@@-           .:  ...:.::::..   .:      ..        ",
    r"      ##%###%@@@#**********##******************#*******#        ",
    r"      %#:#-#+@@%=##-#=#=%+-@*#%-++%*%**%-%*-**++#*-#-*%+        ",
    r"      ++:+-++@@@%-=:+-+:+--%-++=--%-+=++-+-:--=:==-=:+==        ",
    r"      ****+*%@@@@**#*******%+=+++*#+++=+**+*++**+++****#        ",
    r"      @@@@@@@@@@@@@@@@@@@*#@**%**%+*%*###@*@#%**#+*@@@@@        ",
    r"           ◈  A I   M E S Í A H   //   C Y B E R - A P E  ◈      ",
]

FRAMES = [MONKEY_RAW_FRAME_1, MONKEY_RAW_FRAME_2]
MATRIX_CHARS = "0123456789ABCDEF!@#$%^&*()_+-=[]{}|;:,.<>?"

def main_curses(stdscr, duration=None):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()

    # Dynamic palette matching the Gemini image
    curses.init_pair(1, curses.COLOR_CYAN, -1)     # Neon Cyan
    curses.init_pair(2, curses.COLOR_MAGENTA, -1)  # Cyber Magenta
    curses.init_pair(3, curses.COLOR_GREEN, -1)    # Matrix Green
    curses.init_pair(4, curses.COLOR_YELLOW, -1)   # Accent Gold
    curses.init_pair(5, curses.COLOR_WHITE, -1)    # Hot White
    curses.init_pair(6, curses.COLOR_BLUE, -1)     # Shadow Blue

    max_y, max_x = stdscr.getmaxyx()
    columns = max_x
    drops = [random.randint(-25, 0) for _ in range(columns)]
    speeds = [random.uniform(0.7, 1.3) for _ in range(columns)]

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

        # 1. Background Matrix Digital Rain
        for i in range(0, min(columns, max_x), 2):
            drop_y = int(drops[i])
            for tail in range(14):
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
            if drops[i] - 14 > max_y:
                drops[i] = random.randint(-18, 0)

        # 2. Centered Authentic Monkey Frame
        active_lines = FRAMES[(frame // 5) % len(FRAMES)]
        box_w = max(len(l) for l in active_lines) + 4
        box_h = len(active_lines) + 2
        box_y = max(1, (max_y - box_h) // 2)
        box_x = max(1, (max_x - box_w) // 2)

        # Clear backing under the logo
        for y in range(box_y - 1, min(max_y, box_y + box_h + 1)):
            for x in range(box_x - 1, min(max_x, box_x + box_w + 1)):
                try:
                    stdscr.addch(y, x, ' ')
                except curses.error:
                    pass

        # Border Frame
        border_col = curses.color_pair(1 if (frame // 4) % 2 == 0 else 2) | curses.A_BOLD
        stdscr.attron(border_col)
        try:
            stdscr.addstr(box_y - 1, box_x - 1, "╭" + "─" * box_w + "╮")
            for r in range(box_h):
                if box_y + r < max_y:
                    stdscr.addstr(box_y + r, box_x - 1, "│")
                    stdscr.addstr(box_y + r, box_x + box_w, "│")
            stdscr.addstr(box_y + box_h, box_x - 1, "╰" + "─" * box_w + "╯")
        except curses.error:
            pass

        # Draw Exact Logo Contour with Shaded Tonal Highlights
        for idx, line in enumerate(active_lines):
            y = box_y + idx
            x = box_x + (box_w - len(line)) // 2
            if y < max_y and x < max_x:
                try:
                    if "⚡" in line or "◈" in line:
                        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
                    elif idx < 4 or idx > 20:
                        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
                    elif 8 <= idx <= 15:
                        stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
                    else:
                        stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                    stdscr.addstr(y, x, line)
                except curses.error:
                    pass

        # Exit Hint
        try:
            stdscr.attron(curses.color_pair(5) | curses.A_DIM)
            stdscr.addstr(max_y - 1, 2, "[Press 'Q' or 'ESC' to exit Screensaver]")
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

#!/usr/bin/env python3
"""
AI Mesíah - Interactive Fullscreen Color TUI Screensaver (Curses)
Features Matrix Digital Rain, Neon Cyberpunk Banner, and Live Pulse Telemetry.
"""

import curses
import random
import sys
import time

LOGO_LINES = [
    r"          .                                                      .          ",
    r"        .n8888bo.               .d88888b.                     .d8888b.      ",
    r"       .888888888b             d88P\" \"Y88b                   d88P  Y88b     ",
    r"       88888888888             888     888                   888    888     ",
    r"       8888   8888             888     888   .d88b.   .d8888b 888d8888.     ",
    r"       8888   8888    ✦✦       888     888  d8P  Y8b  88K      888   888     ",
    r"       8888   8888   ✦✦✦✦      888     888  88888888  \"Y8888b. 888   888     ",
    r"       Y888888888P    ✦✦       Y88b. .d88P  Y8b.           X88 888   888     ",
    r"        \"Y88888P\"               \"Y88888P\"    \"Y8888P   88888P' 888   888     ",
    r"            `                                                    `          ",
    r"           ⚡  A I   M E S Í A H   //   I o T   M E S H   C O R E  ⚡           ",
]

TELEMETRY_FEEDS = [
    ("WebRTC UDP Screenshare", "[ACTIVE // 60 FPS SUB-80MS]", 1),
    ("CRDT Mesh Gossip Mesh", "[VECTOR CLOCK SYNCED // 0 CONFLICTS]", 2),
    ("IoT MQTT Telemetry", "[INGESTING ESP32/MATTER SENSORS]", 3),
    ("Dynamic AI Gateway", "[CLAUDE 3.7 SONNET & GROK POOLED]", 4),
    ("Vault GraphRAG Paywall", "[HMAC-SHA256 SIGNATURE VALID]", 5),
    ("Railway Central Relay", "[ONLINE: PRODUCTION US-WEST]", 6),
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
    drops = [random.randint(-20, 0) for _ in range(columns)]
    speeds = [random.uniform(0.6, 1.2) for _ in range(columns)]

    start_time = time.time()
    frame = 0

    while True:
        if duration and (time.time() - start_time) > duration:
            break

        # Check for key press to exit early
        key = stdscr.getch()
        if key in [ord('q'), ord('Q'), 27]:  # 27 is ESC
            break

        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        # 1. Render Matrix Digital Rain Background
        for i in range(0, min(columns, max_x), 2):
            drop_y = int(drops[i])
            for tail in range(12):
                y = drop_y - tail
                if 0 <= y < max_y:
                    char = random.choice(MATRIX_CHARS)
                    if tail == 0:
                        stdscr.attron(curses.color_pair(5) | curses.A_BOLD)  # White head
                    elif tail < 4:
                        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)  # Bright green
                    else:
                        stdscr.attron(curses.color_pair(3))  # Dark green
                    try:
                        stdscr.addch(y, i, char)
                    except curses.error:
                        pass
            drops[i] += speeds[i]
            if drops[i] - 12 > max_y:
                drops[i] = random.randint(-15, 0)

        # 2. Render Centered Cyberpunk AI Mesíah Banner Box
        box_w = max(len(l) for l in LOGO_LINES) + 6
        box_h = len(LOGO_LINES) + 10
        box_y = max(1, (max_y - box_h) // 2)
        box_x = max(1, (max_x - box_w) // 2)

        # Draw translucent black backing for banner
        for y in range(box_y - 1, min(max_y, box_y + box_h + 1)):
            for x in range(box_x - 2, min(max_x, box_x + box_w + 2)):
                try:
                    stdscr.addch(y, x, ' ')
                except curses.error:
                    pass

        # Border box
        border_color = curses.color_pair(1 if (frame // 4) % 2 == 0 else 2) | curses.A_BOLD
        stdscr.attron(border_color)
        try:
            stdscr.addstr(box_y - 1, box_x - 1, "╭" + "─" * (box_w) + "╮")
            for r in range(box_h):
                if box_y + r < max_y:
                    stdscr.addstr(box_y + r, box_x - 1, "│")
                    stdscr.addstr(box_y + r, box_x + box_w, "│")
            stdscr.addstr(box_y + box_h, box_x - 1, "╰" + "─" * (box_w) + "╯")
        except curses.error:
            pass

        # Logo text
        logo_color = curses.color_pair(2 if (frame // 4) % 2 == 0 else 1) | curses.A_BOLD
        stdscr.attron(logo_color)
        for idx, line in enumerate(LOGO_LINES):
            y = box_y + idx
            x = box_x + (box_w - len(line)) // 2
            if y < max_y and x < max_x:
                try:
                    if "⚡" in line or "◈" in line:
                        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
                    stdscr.addstr(y, x, line)
                    stdscr.attron(logo_color)
                except curses.error:
                    pass

        # Divider line
        div_y = box_y + len(LOGO_LINES) + 1
        try:
            stdscr.attron(curses.color_pair(6) | curses.A_DIM)
            stdscr.addstr(div_y, box_x + 2, "╌" * (box_w - 4))
        except curses.error:
            pass

        # 3. Telemetry Indicators inside Banner
        for t_idx, (title, status, p_color) in enumerate(TELEMETRY_FEEDS[:5]):
            t_y = div_y + 1 + t_idx
            if t_y < max_y - 1:
                try:
                    stdscr.attron(curses.color_pair(5))
                    stdscr.addstr(t_y, box_x + 4, f"• {title}")
                    dots = box_w - len(title) - len(status) - 10
                    stdscr.attron(curses.color_pair(6) | curses.A_DIM)
                    stdscr.addstr(t_y, box_x + 6 + len(title), " " + "." * max(2, dots) + " ")
                    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
                    stdscr.addstr(t_y, box_x + box_w - len(status) - 2, status)
                except curses.error:
                    pass

        # Exit hint
        try:
            stdscr.attron(curses.color_pair(5) | curses.A_DIM)
            stdscr.addstr(max_y - 1, 2, "[Press 'Q' or 'ESC' to exit Screensaver]")
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.04)  # ~25 FPS
        frame += 1

def run_tui(duration=None):
    curses.wrapper(main_curses, duration)

if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else None
    run_tui(dur)

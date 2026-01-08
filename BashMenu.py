#!/usr/bin/env python3
import os
import sys
import subprocess
import re

# ---------------- Constants ----------------
# ANSI escape sequences
ANSI_CLEAR_SCREEN = "\x1b[2J"
ANSI_CURSOR_HOME = "\x1b[H"
ANSI_HIDE_CURSOR = "\x1b[?25l"
ANSI_SHOW_CURSOR = "\x1b[?25h"
ANSI_BOLD = "\x1b[1m"
ANSI_RESET = "\x1b[0m"
ANSI_REVERSE = "\x1b[7m"

# Colors
COLOR_HEADER = "\x1b[36m"      # Cyan
COLOR_SELECTED = "\x1b[30;47m" # Black text on white background
COLOR_ITEM = "\x1b[37m"        # Light gray
COLOR_PROMPT = "\x1b[33m"      # Yellow
COLOR_INFO = "\x1b[32m"        # Green
COLOR_ERROR = "\x1b[31m"       # Red

# Windows console constants
STD_OUTPUT_HANDLE = -11
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

# Key constants
KEY_UP = "UP"
KEY_DOWN = "DOWN"
KEY_ENTER = "ENTER"
KEY_QUIT = "Q"
KEY_OTHER = "OTHER"

# ---------------- Windows console niceties ----------------
def enable_ansi_on_windows():
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except Exception:
        pass

def clear_screen():
    sys.stdout.write(ANSI_CLEAR_SCREEN + ANSI_CURSOR_HOME)
    sys.stdout.flush()

def hide_cursor():
    sys.stdout.write(ANSI_HIDE_CURSOR)
    sys.stdout.flush()

def show_cursor():
    sys.stdout.write(ANSI_SHOW_CURSOR)
    sys.stdout.flush()

# ---------------- Parsing ----------------
HEADER_RE = re.compile(r"^\s*---+\s*(.+?)\s*---+\s*$")
BRACKET_HEADER_RE = re.compile(r"^\s*\[(.+?)\]\s*$")
HASH_HEADER_RE = re.compile(r"^\s*##+\s*(.+?)\s*$")

def parse_line(line: str):
    """
    Returns:
      {"type": "header", "text": "..."} OR
      {"type": "item", "label": "...", "cmd": "..."|None}
    Or None for ignorable lines.
    """
    s = line.strip()
    if not s or s.startswith("#"):
        return None

    m = HEADER_RE.match(s) or BRACKET_HEADER_RE.match(s) or HASH_HEADER_RE.match(s)
    if m:
        return {"type": "header", "text": m.group(1).strip()}

    # Item line: Label | command
    if "|" in s:
        label, cmd = s.split("|", 1)
        label = label.strip()
        cmd = cmd.strip()
    else:
        label, cmd = s, ""

    return {"type": "item", "label": label, "cmd": cmd if cmd else None}

def load_menu_file(path: str):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            parsed = parse_line(raw)
            if parsed:
                items.append(parsed)

    if not items:
        raise ValueError(f"No menu entries found in {path}")

    if not any(it["type"] == "item" for it in items):
        raise ValueError(f"No selectable menu items found in {path}")

    return items

# ---------------- Key reading (Windows) ----------------
def read_key_windows():
    import msvcrt
    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):  # special keys
        ch2 = msvcrt.getwch()
        return {"H": KEY_UP, "P": KEY_DOWN}.get(ch2, KEY_OTHER)
    if ch == "\r":
        return KEY_ENTER
    if ch in ("q", "Q"):
        return KEY_QUIT
    return ch

# ---------------- Running commands ----------------
def in_git_bash_like_env() -> bool:
    return bool(os.environ.get("MSYSTEM")) or "bash" in os.environ.get("SHELL", "").lower()

def run_command(cmd: str) -> int:
    # If you're in Git Bash/MSYS, run via bash so Unix-ish commands work.
    if in_git_bash_like_env():
        completed = subprocess.run(["C:/Program Files/Git/bin/bash.exe", "-lc", cmd])
    else:
        completed = subprocess.run(cmd, shell=True)
    return completed.returncode

# ---------------- Navigation helpers ----------------
def is_selectable(items, idx: int) -> bool:
    return items[idx]["type"] == "item"

def first_selectable_index(items) -> int:
    for i, it in enumerate(items):
        if it["type"] == "item":
            return i
    raise ValueError("No selectable items")

def move_selection(items, selected: int, direction: int) -> int:
    """
    direction: +1 (down) or -1 (up)
    Skips headers. Wraps around.
    """
    n = len(items)
    i = selected
    for _ in range(n):
        i = (i + direction) % n
        if is_selectable(items, i):
            return i
    return selected  # should never happen if there is at least one selectable item

# ---------------- UI ----------------
def draw(items, selected: int):
    clear_screen()
    sys.stdout.write(f"{COLOR_PROMPT}Use ↑/↓ to move, Enter to select, q to quit{ANSI_RESET}\n\n")

    for i, it in enumerate(items):
        if it["type"] == "header":
            sys.stdout.write(f"{ANSI_BOLD}{COLOR_HEADER}{it['text']}{ANSI_RESET}\n")
        else:
            label = it["label"]
            if i == selected:
                sys.stdout.write(f"  {COLOR_SELECTED}{label}{ANSI_RESET}\n")
            else:
                sys.stdout.write(f"   {COLOR_ITEM}{label}{ANSI_RESET}\n")

    sys.stdout.flush()

def main():
    enable_ansi_on_windows()

    menu_path = sys.argv[1] if len(sys.argv) > 1 else "menu.txt"
    items = load_menu_file(menu_path)
    selected = first_selectable_index(items)

    try:
        hide_cursor()
        while True:
            draw(items, selected)
            key = read_key_windows()

            if key == KEY_UP:
                selected = move_selection(items, selected, -1)
            elif key == KEY_DOWN:
                selected = move_selection(items, selected, +1)
            elif key == KEY_ENTER:
                choice = items[selected]
                label = choice["label"].strip()
                cmd = choice["cmd"]

                if label.lower() == "exit":
                    return

                clear_screen()
                print(f"{COLOR_INFO}You chose: {label}{ANSI_RESET}\n")

                if cmd:
                    print(f"{COLOR_PROMPT}Running: {cmd}{ANSI_RESET}\n")
                    rc = run_command(cmd)
                    color = COLOR_INFO if rc == 0 else COLOR_ERROR
                    print(f"{color}\nExit code: {rc}{ANSI_RESET}")
                else:
                    print(f"{COLOR_ERROR}(No command configured for this item.){ANSI_RESET}")

                input(f"\n{COLOR_PROMPT}Press Enter to return to menu...{ANSI_RESET}")
            elif key == KEY_QUIT:
                return
    finally:
        show_cursor()
        clear_screen()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import os
import curses
import time
import stat
import subprocess
import pwd
from datetime import datetime
from typing import List, Dict

class FkFiles:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.current_path = os.getcwd()
        self.files: List[Dict] = []
        self.selected_idx = 0
        self.top_idx = 0
        self.command_mode = False
        self.command = ""
        self.message = ""
        self.message_time = 0
        self.show_hidden = False
        self.clipboard = []
        self.clipboard_is_cut = False
        self.init_colors()
        self.check_terminal_size()
        self.refresh_files()
        self.setup_mouse()

    def setup_mouse(self):
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        curses.mouseinterval(0)

    def check_terminal_size(self):
        min_height, min_width = 10, 40
        h, w = self.stdscr.getmaxyx()
        if h < min_height or w < min_width:
            curses.endwin()
            print(f"Terminal too small. Minimum size: {min_width}x{min_height}")
            print(f"Current size: {w}x{h}")
            exit(1)
        self.panel_width = w // 2 - 1

    def init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_BLUE, -1)  
        curses.init_pair(3, curses.COLOR_WHITE, -1) 
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_YELLOW, -1)
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE)  # selected item lol
        curses.init_pair(7, curses.COLOR_GREEN, -1)  
        curses.init_pair(8, curses.COLOR_MAGENTA, -1) 
        curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_BLACK) 

    def safe_add_str(self, y: int, x: int, text: str, attr=0) -> bool:
        h, w = self.stdscr.getmaxyx()
        if y < 0 or y >= h or x < 0 or x >= w:
            return False
        try:
            text = text[:w-x-1]
            self.stdscr.addstr(y, x, text, attr)
            return True
        except curses.error:
            return False

    def draw_borders(self):
        h, w = self.stdscr.getmaxyx()
        self.safe_add_str(0, 0, "┌")
        self.safe_add_str(0, w-1, "┐")
        self.safe_add_str(h-3, 0, "├")
        self.safe_add_str(h-3, w-1, "┤")
        self.safe_add_str(h-1, 0, "└")
        self.safe_add_str(h-1, w-1, "┘")
        for x in range(1, w-1):
            self.safe_add_str(0, x, "─")
            self.safe_add_str(h-3, x, "─")
            self.safe_add_str(h-1, x, "─")
        for y in range(1, h-3):
            self.safe_add_str(y, 0, "│")
            self.safe_add_str(y, w-1, "│")
            self.safe_add_str(y, self.panel_width, "│")

    def refresh_files(self):
        self.files = []
        if self.current_path != "/":
            self.files.append({
                'name': '..',
                'is_dir': True,
                'size': 0,
                'mtime': 0,
                'mode': '',
                'full_path': os.path.join(self.current_path, '..')
            })
        try:
            for entry in os.listdir(self.current_path):
                if not self.show_hidden and entry.startswith('.'):
                    continue
                full_path = os.path.join(self.current_path, entry)
                try:
                    stat_info = os.stat(full_path)
                    is_dir = os.path.isdir(full_path)
                    self.files.append({
                        'name': entry,
                        'is_dir': is_dir,
                        'size': stat_info.st_size,
                        'mtime': stat_info.st_mtime,
                        'mode': self.get_mode_str(stat_info.st_mode),
                        'full_path': full_path
                    })
                except OSError:
                    continue
            self.files[1:] = sorted(
                self.files[1:], 
                key=lambda x: (not x['is_dir'], x['name'].lower())
            )
        except OSError as e:
            self.show_message(f"Error: {str(e)}", is_error=True)

    def get_mode_str(self, mode: int) -> str:
        perms = ['-'] * 9
        mode_map = [
            (stat.S_IRUSR, 0), (stat.S_IWUSR, 1), (stat.S_IXUSR, 2),
            (stat.S_IRGRP, 3), (stat.S_IWGRP, 4), (stat.S_IXGRP, 5),
            (stat.S_IROTH, 6), (stat.S_IWOTH, 7), (stat.S_IXOTH, 8)
        ]
        for perm, pos in mode_map:
            if mode & perm:
                perms[pos] = 'rwx'[pos % 3]
        if stat.S_ISDIR(mode):
            perms.insert(0, 'd')
        else:
            perms.insert(0, '-')
        return ''.join(perms)

    def format_size(self, size: int) -> str:
        for unit in ['B', 'K', 'M', 'G']:
            if size < 1024:
                return f"{size:4.0f}{unit}"
            size /= 1024
        return f"{size:4.1f}T"

    def format_time(self, timestamp: float) -> str:
        if timestamp == 0:
            return " " * 12
        return datetime.fromtimestamp(timestamp).strftime('%d.%m.%y %H:%M')

    def show_message(self, msg: str, is_error: bool = False):
        self.message = msg
        self.message_time = time.time()
        self.color = curses.color_pair(4) if is_error else curses.color_pair(5)

    def draw_interface(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        if h < 10 or w < 40:
            self.safe_add_str(0, 0, "Terminal too small! Resize and restart.", curses.color_pair(4))
            self.stdscr.refresh()
            return
        self.draw_borders()
        left_header = f" {os.path.basename(self.current_path)[:self.panel_width-3]} "
        right_header = " Commands "
        self.safe_add_str(0, 1, left_header.ljust(self.panel_width-1), curses.color_pair(1))
        self.safe_add_str(0, self.panel_width+1, right_header.ljust(w-self.panel_width-2), curses.color_pair(1))
        items_to_show = min(len(self.files), h - 5)
        for i in range(items_to_show):
            idx = self.top_idx + i
            if idx >= len(self.files):
                break
            file = self.files[idx]
            y = i + 1
            attr = curses.color_pair(6) if idx == self.selected_idx else 0
            if file['is_dir']:
                attr |= curses.color_pair(2) | curses.A_BOLD
            elif file['mode'][3] == 'x' or file['mode'][6] == 'x' or file['mode'][9] == 'x':
                attr |= curses.color_pair(7)
            elif file['name'].startswith('.'):
                attr |= curses.color_pair(8)
            else:
                attr |= curses.color_pair(3)
            name = file['name'][:20] + ("/" if file['is_dir'] else "")
            size_str = self.format_size(file['size']) if not file['is_dir'] else "<DIR>"
            time_str = self.format_time(file['mtime'])
            line = f"{name.ljust(22)} {size_str} {time_str}"
            self.safe_add_str(y, 1, line[:self.panel_width-1], attr)
        commands = [
            "Navigation:",
            " h       - Parent dir",
            " j/k     - Down/Up",
            " l/Enter - Open",
            " gg/G    - Top/End",
            "",
            "Commands:",
            " dd      - Delete",
            " yy      - Copy",
            " pp      - Paste",
            " :q      - Quit",
            " :ren    - Rename",
            " :hdn    - Toggle hidden",
            " ?       - Help"
        ]
        for i, cmd in enumerate(commands[:h-5]):
            self.safe_add_str(i+1, self.panel_width+2, cmd)
        user = pwd.getpwuid(os.getuid()).pw_name
        status_left = f" {self.selected_idx + 1}/{len(self.files)} "
        status_right = f" {user} "
        self.safe_add_str(h-3, 1, status_left.ljust(self.panel_width-1), curses.color_pair(1))
        self.safe_add_str(h-3, self.panel_width+1, status_right.ljust(w-self.panel_width-2), curses.color_pair(1))
        if self.command_mode:
            cmd_line = f":{self.command}"
            self.safe_add_str(h-2, 1, cmd_line.ljust(w-3), curses.color_pair(9))
            self.stdscr.move(min(h-2, curses.LINES-1), min(len(cmd_line)+1, curses.COLS-1))
        elif time.time() - self.message_time < 3:
            self.safe_add_str(h-2, 1, self.message.ljust(w-3), self.color)
        else:
            help_text = " j/k:Navigate  l:Open  dd:Delete  yy:Copy  pp:Paste  :q:Quit  ?:Help "
            self.safe_add_str(h-2, 1, help_text.ljust(w-3), curses.color_pair(1))
        self.stdscr.refresh()

    def navigate_to(self, path: str):
        try:
            self.current_path = os.path.abspath(path)
            self.selected_idx = 0
            self.top_idx = 0
            self.refresh_files()
        except Exception as e:
            self.show_message(f"Error: {str(e)}", is_error=True)

    def open_file(self, file_path: str) -> bool:
        try:
            if os.path.isdir(file_path):
                self.navigate_to(file_path)
                return True
            if os.name == 'nt':
                os.startfile(file_path)
            else:
                opener = "xdg-open" if os.name == "posix" else "open"
                subprocess.run([opener, file_path], check=True)
            return True
        except Exception as e:
            self.show_message(f"Error: {str(e)}", is_error=True)
            return False

    def delete_file(self):
        if self.selected_idx >= len(self.files):
            return
        file = self.files[self.selected_idx]
        if file['name'] == '..':
            return
        full_path = file['full_path']
        try:
            if file['is_dir']:
                if len(os.listdir(full_path)) == 0:
                    os.rmdir(full_path)
                    self.show_message(f"Directory deleted: {file['name']}")
                else:
                    self.show_message("Directory not empty!", is_error=True)
                    return
            else:
                os.unlink(full_path)
                self.show_message(f"File deleted: {file['name']}")
            self.refresh_files()
            self.selected_idx = min(self.selected_idx, len(self.files) - 1)
        except Exception as e:
            self.show_message(f"Error: {str(e)}", is_error=True)

    def copy_file(self):
        if self.selected_idx < len(self.files):
            self.clipboard = [self.files[self.selected_idx]['full_path']]
            self.clipboard_is_cut = False
            self.show_message("Copied to clipboard")

    def cut_file(self):
        if self.selected_idx < len(self.files):
            self.clipboard = [self.files[self.selected_idx]['full_path']]
            self.clipboard_is_cut = True
            self.show_message("Cut to clipboard")

    def paste_files(self):
        if not self.clipboard:
            self.show_message("Clipboard is empty", is_error=True)
            return
        for src_path in self.clipboard:
            try:
                dst_path = os.path.join(self.current_path, os.path.basename(src_path))
                if self.clipboard_is_cut:
                    os.rename(src_path, dst_path)
                    self.show_message(f"Moved: {os.path.basename(src_path)}")
                else:
                    if os.path.isdir(src_path):
                        subprocess.run(["cp", "-r", src_path, dst_path], check=True)
                    else:
                        subprocess.run(["cp", src_path, dst_path], check=True)
                    self.show_message(f"Copied: {os.path.basename(src_path)}")
            except Exception as e:
                self.show_message(f"Error: {str(e)}", is_error=True)
        self.clipboard = []
        self.refresh_files()

    def rename_file(self, new_name: str):
        if self.selected_idx >= len(self.files):
            return
        file = self.files[self.selected_idx]
        if file['name'] == '..':
            return
        old_path = file['full_path']
        new_path = os.path.join(self.current_path, new_name)
        try:
            os.rename(old_path, new_path)
            self.refresh_files()
            self.show_message(f"Renamed to: {new_name}")
        except Exception as e:
            self.show_message(f"Error: {str(e)}", is_error=True)

    def create_directory(self, dir_name: str):
        try:
            os.makedirs(os.path.join(self.current_path, dir_name))
            self.refresh_files()
            self.show_message(f"Directory created: {dir_name}")
        except Exception as e:
            self.show_message(f"Error: {str(e)}", is_error=True)

    def search_file(self, pattern: str):
        matches = []
        pattern = pattern.lower()
        for idx, file in enumerate(self.files):
            if pattern in file['name'].lower():
                matches.append(idx)
                if len(matches) >= 5:
                    break
        if matches:
            self.selected_idx = matches[0]
            self.top_idx = max(0, self.selected_idx - 2)
            self.show_message(f"Found {len(matches)} matches")
        else:
            self.show_message("No matches found", is_error=True)

    def view_file(self, file_path: str):
        if not os.path.isfile(file_path):
            self.show_message("Not a file", is_error=True)
            return
        try:
            with open(file_path, 'r') as f:
                content = f.readlines()
                curses.endwin()
                print(f"\n--- Viewing: {file_path} ---")
                print(''.join(content[:100]))
                input("\nPress Enter to continue...")
        except Exception as e:
            curses.endwin()
            print(f"Error: {str(e)}")
            input("Press Enter to continue...")
        finally:
            self.stdscr.refresh()

    def show_about(self):
        h, w = self.stdscr.getmaxyx()
        about_text = [
            "Fk-Files - File Manager",
            "───────────────────────",
            "Part of FikusTools project",
            "Developed by FikusPI",
            "License: BSD 3-Clause",
            "",
            "Main developer: Fedor Shimorov",
            "",
            "A hybrid file manager combining",
            "Norton Commander interface with",
            "Vim-like keybindings.",
            "",
            "Press any key to continue..."
        ]
        self.stdscr.clear()
        for i, text in enumerate(about_text):
            if i < h - 1:
                self.safe_add_str(i, 0, text[:w-1])
        self.stdscr.refresh()
        self.stdscr.getch()

    def show_help(self):
        h, w = self.stdscr.getmaxyx()
        help_texts = [
            "Fk-Files Help",
            "───────────────────────",
            "Navigation:",
            " h       - Parent directory",
            " j/k     - Move down/up",
            " l/Enter - Open file/dir",
            " gg/G    - Jump to top/bottom",
            " /pattern - Quick search",
            "",
            "File Operations:",
            " dd      - Delete file/dir",
            " yy      - Yank (copy) file",
            " pp      - Paste yanked files",
            " v       - View file content",
            " :ren    - Rename file/dir",
            "",
            "Command Mode (:) Commands:",
            " :q      - Quit",
            " :hdn    - Toggle hidden files",
            " :mkdir  - Create directory",
            " :ren    - Rename file/dir",
            " :about  - Show about info",
            " :p path - Change directory",
            "",
            "Mouse Controls:",
            " Left click - Select item",
            " Double click - Open item",
            " Right click - Context menu",
            "",
            "Press any key to continue..."
        ]
        self.stdscr.clear()
        for i, text in enumerate(help_texts):
            if i < h - 1:
                self.safe_add_str(i, 0, text[:w-1])
        self.stdscr.refresh()
        self.stdscr.getch()

    def execute_command(self):
        if self.command.startswith('/'):
            self.search_file(self.command[1:])
            return
        cmd_parts = self.command.split()
        if not cmd_parts:
            return
        cmd = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        if cmd == "q":
            raise KeyboardInterrupt
        elif cmd == "hdn":
            self.show_hidden = not self.show_hidden
            self.refresh_files()
            status = "ON" if self.show_hidden else "OFF"
            self.show_message(f"Hidden files: {status}")
        elif cmd == "mkdir" and args:
            self.create_directory(' '.join(args))
        elif cmd == "ren" and args:
            self.rename_file(' '.join(args))
        elif cmd == "about":
            self.show_about()
        elif cmd == "ss" and args:
            self.search_file(' '.join(args))
        elif cmd == "p" and args:
            path = ' '.join(args)
            if os.path.isdir(path):
                self.navigate_to(path)
            else:
                self.show_message("Invalid path", is_error=True)
        else:
            self.show_message(f"Unknown command: {cmd}", is_error=True)

    def handle_mouse_event(self):
        try:
            _, x, y, _, bstate = curses.getmouse()
            
            h, w = self.stdscr.getmaxyx()
            if y == 0 or y >= h - 3 or x == 0 or x >= w - 1 or x == self.panel_width:
                return
                
            if bstate & curses.BUTTON1_CLICKED:
                if y >= 1 and y < h - 3:
                    idx = self.top_idx + (y - 1)
                    if idx < len(self.files):
                        self.selected_idx = idx
                        
                        if bstate & curses.BUTTON1_DOUBLE_CLICKED:
                            file = self.files[self.selected_idx]
                            curses.endwin()
                            try:
                                self.open_file(file['full_path'])
                            finally:
                                self.stdscr.refresh()
            
            elif bstate & curses.BUTTON3_CLICKED:
                if self.selected_idx < len(self.files):
                    file = self.files[self.selected_idx]
                    if file['name'] != '..':
                        self.show_message(f"Right click on: {file['name']}")
        except:
            pass

    def handle_input(self):
        try:
            key = self.stdscr.getch()
        except:
            return
            
        if key == curses.KEY_MOUSE:
            self.handle_mouse_event()
            return
            
        if self.command_mode:
            if key == 27:
                self.command_mode = False
                self.command = ""
            elif key == curses.KEY_BACKSPACE or key == 127:
                self.command = self.command[:-1]
            elif key == 10:
                self.execute_command()
                self.command_mode = False
                self.command = ""
            elif 32 <= key <= 126:
                self.command += chr(key)
            return
            
        if key == ord('j') or key == curses.KEY_DOWN:
            if self.selected_idx < len(self.files) - 1:
                self.selected_idx += 1
                if self.selected_idx >= self.top_idx + (curses.LINES - 5):
                    self.top_idx += 1
        elif key == ord('k') or key == curses.KEY_UP:
            if self.selected_idx > 0:
                self.selected_idx -= 1
                if self.selected_idx < self.top_idx:
                    self.top_idx -= 1
        elif key == ord('l') or key == 10:
            if len(self.files) > 0:
                file = self.files[self.selected_idx]
                curses.endwin()
                try:
                    self.open_file(file['full_path'])
                finally:
                    self.stdscr.refresh()
        elif key == ord('h'):
            if self.current_path != "/":
                self.navigate_to(os.path.join(self.current_path, '..'))
        elif key == ord('g'):
            next_key = self.stdscr.getch()
            if next_key == ord('g'):
                self.selected_idx = 0
                self.top_idx = 0
        elif key == ord('G'):
            self.selected_idx = len(self.files) - 1
            self.top_idx = max(0, len(self.files) - (curses.LINES - 5))
        elif key == ord(':'):
            self.command_mode = True
            self.command = ""
        elif key == ord('/'):
            self.command_mode = True
            self.command = "/"
        elif key == ord('?'):
            self.show_help()
        elif key == ord('d'):
            next_key = self.stdscr.getch()
            if next_key == ord('d'):
                self.delete_file()
        elif key == ord('y'):
            next_key = self.stdscr.getch()
            if next_key == ord('y'):
                self.copy_file()
        elif key == ord('p'):
            next_key = self.stdscr.getch()
            if next_key == ord('p'):
                self.paste_files()
        elif key == ord('v'):
            if len(self.files) > 0:
                file = self.files[self.selected_idx]
                if not file['is_dir']:
                    self.view_file(file['full_path'])

def main(stdscr):
    curses.curs_set(0)
    curses.use_default_colors()
    try:
        app = FkFiles(stdscr)
        while True:
            app.draw_interface()
            try:
                app.handle_input()
            except KeyboardInterrupt:
                break
    except Exception as e:
        curses.endwin()
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    curses.wrapper(main)

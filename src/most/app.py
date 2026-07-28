import curses
import signal
import time

from . import document
from . import terminal
from . import window

KEY_CTRL_C = 3

SCROLL_KEYS = {
    'up':     ['KEY_UP'],
    'down':   ['KEY_DOWN'],
    'top':    ['KEY_HOME'],
    'goto':   ['g'],
    'bottom': ['KEY_END',   'G'],
    'pgup':   ['KEY_PPAGE', 'w'],
    'pgdn':   ['KEY_NPAGE', 'z', ' '],
}
SCROLL_MAP = {v: k for k, l in SCROLL_KEYS.items() for v in l}


class App:
    def __init__(self, doc):
        self.doc = doc
        self.window = None
        self.terminal = None
        self._exiting = False
        self._redraw = False

        self.input_buffer = ''
        self.input_mode = None

        self.timestamp = ''
        self.status_msg = ''
        self.show_line_numbers = False
        self.line_number_width = 0
        self.select_line_i = None
        self.lines = []
        self.line_i = 0

    def scroll_n(self, default=1):
        if self.input_mode == 'n':
            return int(self.input_buffer) or default
        return default

    def lines_per_page(self):
        return self.window.body_height - self.doc.n_header_lines

    def redraw(self):
        self._redraw = True

    def log(self, fmt, *args):
        self.status_msg = fmt % args
        self.redraw()

    def select_line(self, i):
        page_len = self.lines_per_page()
        if i is not None:
            assert 0 <= i < self.doc.n_lines
            if i < self.line_i:
                self.set_line_i(i)
            if i >= self.line_i + page_len:
                self.set_line_i(i - page_len + 1)
        self.select_line_i = i
        self.redraw()

    def set_input_buffer(self, s):
        self.input_buffer = s
        self.redraw()

    def set_input_mode(self, input_mode):
        self.input_mode = input_mode
        self.redraw()

    def reset_input(self):
        self.set_input_buffer('')
        self.set_input_mode(None)

    def handle_scroll(self, scroll_type):
        if not self.lines:
            return

        n = self.scroll_n(1)
        page_len = self.lines_per_page()
        last_page = max(0, self.doc.n_lines - page_len)
        last_line = self.doc.n_lines - 1
        if scroll_type == 'resize':
            self.set_line_i(self.line_i)
            self.select_line(self.select_line_i)
        elif scroll_type == 'up':
            if self.select_line_i is not None:
                self.select_line(max(0, self.select_line_i - n))
            else:
                self.set_line_i(max(0, self.line_i - n))
        elif scroll_type == 'down':
            if self.select_line_i is not None:
                self.select_line(min(last_line, self.select_line_i + n))
            else:
                self.set_line_i(min(last_page, self.line_i + n))
        elif scroll_type == 'pgup':
            if self.line_i > 0:
                self.set_line_i(max(0, self.line_i - n * page_len))
            if self.select_line_i is not None:
                self.select_line(max(0, self.select_line_i - n * page_len))
        elif scroll_type == 'pgdn':
            if self.line_i < last_page:
                self.set_line_i(min(last_page, self.line_i + n * page_len))
            if self.select_line_i is not None:
                self.select_line(min(last_line, self.select_line_i + n * page_len))
        elif scroll_type in ['top', 'goto']:
            if scroll_type == 'goto':
                line_i = min(n, self.doc.n_lines) - 1
            else:
                line_i = 0
            if self.select_line_i is not None:
                self.select_line(line_i)
            else:
                self.set_line_i(line_i)
        elif scroll_type == 'bottom':
            if self.select_line_i is not None:
                self.select_line(last_line)
            else:
                self.set_line_i(last_page)

    def handle_resize(self):
        self.log("Size: %d x %d", self.terminal.width, self.terminal.height)
        self.handle_scroll('resize')

    def handle_exit(self):
        self._exiting = True

    def handle_text(self, name):
        if name == '^C':
            self.reset_input()
        elif name == 'KEY_BACKSPACE' and self.input_buffer:
            self.set_input_buffer(self.input_buffer[:-1])
            if self.input_mode == 'n' and not self.input_buffer:
                self.reset_input()
        elif self.input_mode in [None, 'n'] and name.isdigit():
            if self.input_mode is None:
                self.set_input_mode('n')
            self.set_input_buffer(self.input_buffer + name)
        else:
            return False
        return True

    def handle_key(self, key):
        self.log("")
        name = curses.keyname(key).decode()
        if self.handle_text(name):
            return

        if name == 'q':
            self.handle_exit()
        elif name in SCROLL_MAP:
            self.handle_scroll(SCROLL_MAP[name])
            self.reset_input()
        elif name in 'Ll':
            self.toggle_line_numbers()
        elif name in 'eE':
            self.select_line(self.line_i if self.select_line_i is None else None)
        elif name == '^L':
            if self.select_line_i is not None:
                page_len = self.lines_per_page()
                offset = self.select_line_i - self.line_i
                midpoint = page_len // 2
                if offset == midpoint:
                    new_offset = 0
                elif offset == 0:
                    new_offset = page_len - 1
                else:
                    new_offset = midpoint
                self.set_line_i(self.select_line_i - new_offset)

    def handle_sigint(self, *_):
        self.handle_key(KEY_CTRL_C)

    def toggle_line_numbers(self):
        self.show_line_numbers = not self.show_line_numbers
        self.line_number_width = (len(str(self.doc.n_lines)) + 1) if self.show_line_numbers else 0
        self.redraw()

    def update_timestamp(self):
        timestamp = time.strftime('%H:%M:%S')
        if timestamp != self.timestamp:
            self.timestamp = timestamp
            self.redraw()
            return True

    def set_line_i(self, line_i):
        if not self.doc.n_lines:
            return
        assert 0 <= line_i < self.doc.n_lines
        self.line_i = line_i
        self.lines = self.doc.read_lines(self.line_i, self.lines_per_page())
        self.redraw()

    def reset(self):
        self.doc.init(self)
        self.set_line_i(0)
        self.select_line(None)

    def background_work(self):
        return self.update_timestamp()

    def main(self, scr):
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.terminal = terminal.Terminal(scr)
        self.window = window.Window(self)
        self.reset()

        while not self._exiting:
            key = self.terminal.get_input()
            if not key:
                if not self.background_work():
                    time.sleep(0.01)
            elif key == curses.KEY_RESIZE:
                self.handle_resize()
            else:
                self.handle_key(key)
            if self._redraw:
                self.window.redraw()
                self._redraw = False

    def run(self):
        curses.wrapper(self.main)

import curses
import time

from . import document
from . import terminal
from . import window

SCROLL_KEYS = {
    'up':     ['KEY_UP'],
    'down':   ['KEY_DOWN'],
    'top':    ['KEY_HOME',  'g'],
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

        self.timestamp = ''
        self.status_msg = ''
        self.show_line_numbers = False
        self.line_number_width = 0
        self.lines = []
        self.line_i = 0

    def lines_per_page(self):
        return self.window.body_height

    def redraw(self):
        self._redraw = True

    def log(self, fmt, *args):
        self.status_msg = fmt % args
        self.redraw()

    def handle_scroll(self, scroll_type):
        if not self.lines:
            return

        page_len = self.lines_per_page()
        last_page = max(0, self.doc.n_lines - page_len)
        if scroll_type == 'resize':
            self.set_line_i(self.line_i)
        elif scroll_type == 'up':
            if self.line_i > 0:
                self.set_line_i(self.line_i - 1)
        elif scroll_type == 'down':
            if self.line_i < last_page:
                self.set_line_i(self.line_i + 1)
        elif scroll_type == 'pgup':
            if self.line_i > 0:
                self.set_line_i(max(0, self.line_i - page_len))
        elif scroll_type == 'pgdn':
            if self.line_i < last_page:
                self.set_line_i(min(last_page, self.line_i + page_len))
        elif scroll_type == 'top':
            self.set_line_i(0)
        elif scroll_type == 'bottom':
            self.set_line_i(last_page)

    def handle_resize(self):
        self.log("Size: %d x %d", self.terminal.width, self.terminal.height)
        self.handle_scroll('resize')

    def handle_exit(self):
        self._exiting = True

    def handle_key(self, key):
        self.log("")
        name = curses.keyname(key).decode()
        if name == 'q':
            self.handle_exit()
        elif name in SCROLL_MAP:
            self.handle_scroll(SCROLL_MAP[name])
        elif name in 'Ll':
            self.toggle_line_numbers()

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

    def background_work(self):
        return self.update_timestamp()

    def main(self, scr):
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

import curses
import time

from . import document
from . import terminal
from . import window


class App:
    def __init__(self, doc):
        self.doc = doc
        self.window = None
        self.terminal = None
        self._exiting = False
        self._redraw = False

        self.timestamp = ''
        self.status_msg = ''
        self.lines = []
        self.line_i = 0

    def lines_per_page(self):
        return self.window.body_height

    def redraw(self):
        self._redraw = True

    def log(self, fmt, *args):
        self.status_msg = fmt % args
        self.redraw()

    def handle_resize(self):
        self.log("Size: %d x %d", self.terminal.width, self.terminal.height)
        self.set_line_i(self.line_i)

    def handle_exit(self):
        self._exiting = True

    def handle_key(self, key):
        self.log("")
        name = curses.keyname(key).decode()
        if name == 'q':
            self.handle_exit()

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

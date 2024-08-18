import curses
import time

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
    REDRAW_TIMEOUT_S = 0.1

    def __init__(self, path):
        self.path = path
        self.lines = open(path).read().split('\n')
        if self.lines and not self.lines[-1]:
            self.lines = self.lines[:-1]
        self.line_i = 0
        self.scr = None
        self.screen_width = None
        self.screen_height = None
        self.exiting = False
        self.status_msg = ''

    def log(self, fmt, *args):
        self.status_msg = fmt % args

    def handle_resize(self):
        self.screen_height, self.screen_width = self.scr.getmaxyx()
        self.log("Size: %d x %d", self.screen_width, self.screen_height)

    def handle_scroll(self, scroll_type):
        max_line_i = max(0, len(self.lines) - (self.screen_height - 2))
        distances = {
            'up': -1, 'down': 1,
            'top': -len(self.lines), 'bottom': len(self.lines),
            'pgup': -(self.screen_height - 2), 'pgdn': self.screen_height - 2
        }
        self.line_i = max(0, min(self.line_i + distances[scroll_type], max_line_i))

    def handle_exit(self, _=None):
        self.exiting = True

    def draw_header(self):
        left = self.path
        right = time.strftime('%H:%M:%S')
        msg = left + ' ' * (self.screen_width - len(left + right)) + right
        self.scr.addstr(0, 0, msg, curses.A_REVERSE)

    def draw_body(self):
        for i in range(self.screen_height - 2):
            line_i = self.line_i + i
            if 0 <= line_i < len(self.lines):
                self.scr.addstr(i + 1, 0, self.lines[line_i])

    def draw_footer(self):
        msg = (self.status_msg + ' ' * self.screen_width)[:self.screen_width - 1]
        self.scr.addstr(self.screen_height - 1, 0, msg, curses.A_REVERSE)

    def redraw(self):
        self.scr.erase()
        self.draw_header()
        self.draw_body()
        self.draw_footer()

    def handle_input(self, key):
        name = curses.keyname(key).decode()
        if name == 'q':
            self.handle_exit()
        elif name in SCROLL_MAP:
            self.handle_scroll(SCROLL_MAP[name])
        else:
            self.log("Got key: %r (%s)", key, name)

    def main(self, scr):
        self.scr = scr
        self.scr.timeout(int(self.REDRAW_TIMEOUT_S * 1000))
        curses.curs_set(False)
        curses.use_default_colors()
        self.handle_resize()
        while not self.exiting:
            self.redraw()
            key = self.scr.getch()
            if key == curses.ERR:
                pass
            elif key == curses.KEY_RESIZE:
                self.handle_resize()
            else:
                self.handle_input(key)

    def run(self):
        curses.wrapper(self.main)

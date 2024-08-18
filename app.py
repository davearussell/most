import curses
import math
import time
import doc

SCROLL_KEYS = {
    'up':     ['KEY_UP'],
    'down':   ['KEY_DOWN'],
    'top':    ['KEY_HOME',  'g'],
    'bottom': ['KEY_END',   'G'],
    'pgup':   ['KEY_PPAGE', 'w'],
    'pgdn':   ['KEY_NPAGE', 'z', ' '],
}
SCROLL_MAP = {v: k for k, l in SCROLL_KEYS.items() for v in l}


COLORS = [
    ('default', -1, -1),
    ('grey', 249, -1),
    ('dark-blue', 19, -1),
]


class App:
    REDRAW_TIMEOUT_S = 0.1

    def __init__(self, path):
        self.path = path
        self.doc = doc.Document(path)
        self.line_i = 0
        self.scr = None
        self.screen_width = None
        self.screen_height = None
        self.show_line_numbers = True
        self.exiting = False
        self.status_msg = ''

    def log_n_lines(self):
        return math.ceil(math.log(len(self.doc) + 1, 10))

    def init_colors(self):
        self.colors = {}
        for i, (name, fg, bg) in enumerate(COLORS):
            curses.init_pair(i + 1, fg, bg)
            self.colors[name] = curses.color_pair(i + 1)

    def log(self, fmt, *args):
        self.status_msg = fmt % args

    def handle_resize(self):
        self.screen_height, self.screen_width = self.scr.getmaxyx()
        self.log("Size: %d x %d", self.screen_width, self.screen_height)

    def handle_scroll(self, scroll_type):
        max_line_i = max(0, len(self.doc) - (self.screen_height - 2))
        distances = {
            'up': -1, 'down': 1,
            'top': -len(self.doc), 'bottom': len(self.doc),
            'pgup': -(self.screen_height - 2), 'pgdn': self.screen_height - 2
        }
        self.line_i = max(0, min(self.line_i + distances[scroll_type], max_line_i))

    def handle_exit(self, _=None):
        self.exiting = True

    def line_pos(self, line_i, pos='end'):
        if not self.doc:
            return '(empty) |'
        if line_i >= len(self.doc):
            line_i = len(self.doc) - 1
        spacing = self.log_n_lines() - len(str(line_i + 1))
        percent = (line_i + (1 if pos == 'end' else 0)) * 100 // len(self.doc)
        return '(%3d%%) L%d %s|' % (percent, line_i + 1, ' ' * spacing)

    def draw_header(self):
        left = "%s %s" % (self.line_pos(self.line_i, pos='start'), self.path)
        right = time.strftime('%H:%M:%S')
        msg = left + ' ' * (self.screen_width - len(left + right)) + right
        self.scr.addstr(0, 0, msg, curses.A_REVERSE)

    def draw_line(self, i, line_i):
        x = 0
        if self.show_line_numbers:
            fmt = '%%%dd  ' % (self.log_n_lines(),)
            prefix = fmt % (line_i + 1,)
            self.scr.addstr(i, x, prefix, self.colors['grey'])
            x += len(prefix)

        line = self.doc[line_i]
        if len(line) > self.screen_width - x:
            line = line[:self.screen_width - x - 1]
            self.scr.addstr(i, self.screen_width - 1, '>', curses.A_REVERSE)
        self.scr.addstr(i, x, line)

    def draw_body(self):
        for i in range(self.screen_height - 2):
            line_i = self.line_i + i
            if 0 <= line_i < len(self.doc):
                self.draw_line(i + 1, line_i)

    def draw_footer(self):
        msg = '%s %s%s' % (self.line_pos(self.line_i + self.screen_height - 3),
                            self.status_msg, ' ' * self.screen_width)
        msg = msg[:self.screen_width - 1]
        y = min(self.screen_height - 1, len(self.doc) + 1)
        self.scr.addstr(y, 0, msg, curses.A_REVERSE)

    def redraw(self):
        self.scr.erase()
        self.draw_header()
        self.draw_body()
        self.draw_footer()

    def draw_box(self, x0, y0, x1, y1, color='default'):
        attr = self.colors[color]
        width = x1 - x0 + 1
        height = y1 - y0 + 1
        assert width > 1 and height > 1
        self.scr.addstr(y0, x0, '┏' + '━' * (width - 2) + '┓', attr)
        for y in range(y0 + 1, y1):
            self.scr.addstr(y, x0, '┃' + ' ' * (width - 2) + '┃', attr)
        self.scr.addstr(y1, x0, '┗' + '━' * (width - 2) + '┛', attr)

    def popup(self, msg, color='default'):
        lines = msg.split('\n')
        width = max(map(len, lines))
        height = len(lines)
        y = self.screen_height // 2
        x = (self.screen_width - width) // 2
        self.draw_box(x - 2, y - 1, x + width + 1, y + height, color=color)
        for i, line in enumerate(lines):
            self.scr.addstr(y + i, x, line)

    def handle_input(self, key):
        name = curses.keyname(key).decode()
        if name == 'q':
            self.handle_exit()
        elif name in SCROLL_MAP:
            self.handle_scroll(SCROLL_MAP[name])
        elif name in 'Ll':
            self.show_line_numbers = not self.show_line_numbers
        else:
            self.log("Got key: %r (%s)", key, name)

    def main(self, scr):
        self.scr = scr
        self.scr.timeout(int(self.REDRAW_TIMEOUT_S * 1000))
        curses.curs_set(False)
        curses.use_default_colors()
        self.init_colors()
        self.handle_resize()

        import time
        t0 = time.time()
        while not self.doc.load_chunk():
            self.redraw()
            percent = self.doc.parsed_bytes * 100 // self.doc.n_bytes
            self.popup('Loading: %3d%%' % (percent,), 'dark-blue')
            self.scr.refresh()
        self.log("Loaded document in %.2fs", time.time() - t0)

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

import curses

from . import color

class Terminal:
    def __init__(self, scr):
        self.scr = scr
        curses.curs_set(False)
        curses.use_default_colors()
        self.scr.nodelay(True)
        self.handle_resize()

    def handle_resize(self):
        self.height, self.width = self.scr.getmaxyx()

    def erase(self):
        self.scr.erase()

    def draw(self, y, x, text, attr):
        if y >= self.height:
            return
        for i, c in enumerate(text):
            if 0 <= x + i < self.width:
                # Curses limitation: addstr does not work on the bottom-rightmost cell in the
                # terminal, so we must use insstr here. However insstr is not suitable in general
                # as it shifts existing text right rather than replacing it, which is not the
                # behaviour we want.
                if y == self.height - 1 and x + i == self.width - 1:
                    self.scr.insstr(y, x + i, c, attr)
                else:
                    self.scr.addstr(y, x + i, c, attr)

    def text(self, text, y=0, x=None, align='left', fill=False, invert=False, fg=None, bg=None):
        text = str(text)
        attr = curses.A_REVERSE if invert else 0
        if fg or bg:
            attr |= color.get_pair(fg, bg)
        if x is None:
            x = (self.width - 1) if align == 'right' else 0
        if y < 0:
            y += self.height
        if x < 0:
            x += self.width
        if align == 'right':
            x -= (len(text) - 1)
            end = x - 1
        else:
            end = x + len(text)
        if fill:
            filler = ' ' * self.width
            if align == 'right':
                text = filler + text
                x -= len(filler)
            else:
                text += filler
        self.draw(y, x, text, attr)
        return end

    def get_input(self):
        key = self.scr.getch()
        if key == curses.ERR:
            return None
        if key == curses.KEY_RESIZE:
            self.handle_resize()
        return key

import curses
import time


class Window:
    def __init__(self, app):
        self.app = app
        self.terminal = app.terminal

    def draw_header(self):
        self.terminal.text(self.app.timestamp, align='right', fill=True, invert=True)

    def draw_footer(self):
        self.terminal.text(self.app.status_msg, y=-1, fill=True, invert=True)

    def redraw(self):
        self.terminal.erase()
        self.draw_header()
        self.draw_footer()

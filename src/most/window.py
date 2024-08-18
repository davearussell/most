import curses
import time


class Window:
    def __init__(self, app):
        self.app = app
        self.terminal = app.terminal

    @property
    def body_height(self):
        return self.terminal.height - 2

    def draw_header(self):
        self.terminal.text(self.app.doc.path, fill=True, invert=True)
        self.terminal.text(self.app.timestamp, align='right', invert=True)

    def draw_body(self):
        for i, line in enumerate(self.app.lines):
            self.terminal.text(line, y=i+1)
        for j in range(len(self.app.lines), self.body_height):
            self.terminal.text('', y=j+1, bg='light_grey', fill=True)

    def draw_footer(self):
        self.terminal.text(self.app.status_msg, y=-1, fill=True, invert=True)

    def redraw(self):
        self.terminal.erase()
        self.draw_header()
        self.draw_body()
        self.draw_footer()

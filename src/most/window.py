import curses
import time


class Window:
    def __init__(self, app):
        self.app = app
        self.terminal = app.terminal

    @property
    def body_height(self):
        return self.terminal.height - 2

    def line_status(self, bottom=False):
        if self.app.doc.n_lines == 0:
            return '(100%) L0'
        line_i = min(self.app.doc.n_lines - 1,
                     self.app.line_i + bottom * (self.body_height - 1))
        percent = (line_i + bottom) * 100 // self.app.doc.n_lines
        line_s = str(line_i + 1)
        padding = ' ' * (len(str(self.app.doc.n_lines)) - len(line_s))
        return '(%3d%%) L%s%s' % (percent, line_s, padding)

    def draw_header(self):
        lhs = "%s │ %s" % (self.line_status(), self.app.doc.path)
        self.terminal.text(lhs, fill=True, invert=True)
        self.terminal.text(self.app.timestamp, align='right', invert=True)

    def draw_body(self):
        ln_width = self.app.line_number_width
        for i, line in enumerate(self.app.lines):
            if ln_width:
                self.terminal.text(self.app.line_i + i + 1, y=i+1, x=ln_width - 2, align='right', fg='grey')
            self.terminal.text(line, y=i+1, x=ln_width)
            if len(line) > self.terminal.width - ln_width:
                self.terminal.text('>', y=i+1, x=-1, invert=True)
        for j in range(len(self.app.lines), self.body_height):
            self.terminal.text('', y=j+1, bg='light_grey', fill=True)

    def draw_footer(self):
        text = '%s │ %s' % (self.line_status(bottom=True), self.app.status_msg)
        self.terminal.text(text, y=-1, fill=True, invert=True)

    def redraw(self):
        self.terminal.erase()
        self.draw_header()
        self.draw_body()
        self.draw_footer()

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
            line_i = self.app.line_i + i - self.app.doc.n_header_lines
            if ln_width and i >= self.app.doc.n_header_lines:
                self.terminal.text(line_i + 1, y=i+1, x=ln_width - 2, align='right', fg='grey')

            attr = {}
            if line_i == self.app.select_line_i:
                attr = {'bg': 'light_blue', 'fill': True}
            self.terminal.text(line, y=i+1, x=ln_width, **attr)
            if len(line) > self.terminal.width - ln_width:
                self.terminal.text('>', y=i+1, x=-1, invert=True)
        for j in range(len(self.app.lines), self.body_height):
            self.terminal.text('', y=j+1, bg='light_grey', fill=True)

    def draw_footer(self):
        mode_char = {'n': ':', None: ' '}[self.app.input_mode]
        msg = mode_char + self.app.input_buffer
        if self.app.status_msg:
            msg = '%s │ %s' % (self.app.status_msg, msg)
        text = '%s │ %s' % (self.line_status(bottom=True), msg)
        self.terminal.text(text, y=-1, fill=True, invert=True)

    def redraw(self):
        self.terminal.erase()
        self.draw_header()
        self.draw_body()
        self.draw_footer()

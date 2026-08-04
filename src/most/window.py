import curses
import time


def highlight_words(words, highlight_ranges, debug=0):
    word_start = 0
    words_out = []
    for word, word_attr in words:
        highlight_attr = dict(word_attr, invert=not word_attr.get('invert'))
        word_end = word_start + len(word)
        if debug:
            print(f"next word {word!r}[{word_start}:{word_end}]")
        while highlight_ranges and highlight_ranges[0][0] < word_end:
            inv_start, inv_end = highlight_ranges.pop(0)
            if debug:
                print(f"next inv[{inv_start}:{inv_end}]")
            if inv_start > word_start:
                offset = inv_start - word_start
                if debug:
                    print(f"  prefix not inv {word[:offset]!r}[0:{offset}]")
                words_out.append((word[:offset], word_attr))
                word = word[offset:]
                word_start = inv_start
            assert inv_start == word_start
            if inv_end < word_end:
                offset = inv_end - inv_start
                if debug:
                    print(f"  partial inv {word[:offset]!r}[0:{offset}]")
                words_out.append((word[:offset], highlight_attr))
                word = word[offset:]
                word_start += offset
            else:
                if debug:
                    print(f"  full inv {word!r}[{word_start}:{word_end}]")
                words_out.append((word, highlight_attr))
                inv_start += len(word)
                assert inv_start <= inv_end
                assert inv_start == word_end
                highlight_ranges.insert(0, (inv_start, inv_end))
                word = ''
                word_start = word_end
        if word:
            if debug:
                print(f"  suffix not inv {word!r}[{word_start}:{word_end}]")
            words_out.append((word, word_attr))
            word_start = word_end
    return words_out


class Window:
    def __init__(self, app):
        self.app = app
        self.terminal = app.terminal

    @property
    def body_height(self):
        return self.terminal.height - 2

    def line_status(self, bottom=False):
        if self.app.doc.n_lines == 0:
            return '(100%) L0  C0'
        line_i = min(self.app.doc.n_lines - 1,
                     self.app.line_i + bottom * (self.body_height - 1))
        percent = (line_i + bottom) * 100 // self.app.doc.n_lines
        line_s = str(line_i + 1)
        padding = ' ' * (len(str(self.app.doc.n_lines)) - len(line_s))
        return '(%3d%%) L%s%s  C%d' % (percent, line_s, padding, self.app.col_i)

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

            # Line is either a plain str, or a sequence of (str, attr) tuples
            if isinstance(line, str):
                text = line
                words = [(line, {})]
            else:
                text = ''.join(text for (text, _) in line)
                words = line

            if self.app.search_pat:
                invert_ranges = []
                search_pos = 0
                for word in self.app.search_pat.findall(text):
                    word_start_pos = text.find(word, search_pos)
                    word_end_pos = word_start_pos + len(word)
                    invert_ranges.append((word_start_pos, word_end_pos))
                    search_pos = word_end_pos
                words = highlight_words(words, invert_ranges)

            x = ln_width
            skip = self.app.col_i
            for word, word_attr in words:
                if skip:
                    old_len = len(word)
                    word = word[skip:]
                    skip -= (old_len - len(word))
                self.terminal.text(word, y=i+1, x=x, **(attr | word_attr))
                x += len(word)

            if len(line) > self.terminal.width - ln_width + self.app.col_i:
                self.terminal.text('>', y=i+1, x=-1, invert=True)
        for j in range(len(self.app.lines), self.body_height):
            self.terminal.text('', y=j+1, bg='light_grey', fill=True)

    def draw_footer(self):
        mode_char = {'search': '/', 'n': ':', None: ' '}[self.app.input_mode]
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

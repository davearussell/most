from . import cmost

class Document:
    n_header_lines = 0

    def __init__(self, path):
        self.path = path
        self.app = None
        self.n_lines = 0

    def init(self, app):
        self.app = app

    def read_line(self, line_i):
        raise NotImplementedError()

    def read_lines(self, line_i, n_lines):
        raise NotImplementedError()

    def search(self, pat, line_i, direction):
        while 0 <= line_i < self.n_lines:
            if pat.search(self.read_line(line_i)):
                return line_i
            line_i += direction

    def handle_key(self, name):
        return False

class StringDocument(Document):
    def __init__(self, text, name='(untitled)'):
        super().__init__(name)
        self.lines = text.split('\n')
        self.n_lines = len(self.lines)

    def read_line(self, line_i):
        return self.lines[line_i]

    def read_lines(self, line_i, n_lines):
        return self.lines[line_i : line_i + n_lines]

class TextDocument(Document):
    def __init__(self, path):
        super().__init__(path)
        self.n_lines = cmost.read_file(self.path)

    def read_line(self, line_i):
        return cmost.read_line(line_i)

    def read_lines(self, line_i, n_lines):
        n_lines = min(n_lines, self.n_lines - line_i)
        return [cmost.read_line(line_i + i) for i in range(n_lines)]

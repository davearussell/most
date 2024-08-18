class Document:
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


class TextDocument(Document):
    def __init__(self, path):
        super().__init__(path)
        self.lines = list(open(self.path))
        self.n_lines = len(self.lines)

    def read_line(self, line_i):
        return self.lines[line_i]

    def read_lines(self, line_i, n_lines):
        return self.lines[line_i : line_i + n_lines]

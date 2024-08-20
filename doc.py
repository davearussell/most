import array
import mmap
import os
import re


class Document:
    CHUNK_SIZE = 1 << 25

    def __init__(self, path):
        self.path = path
        if os.stat(path).st_size == 0:
            self.data = b''
        else:
            self.fd = os.open(self.path, os.O_RDONLY)
            self.data = mmap.mmap(self.fd, 0, prot=mmap.PROT_READ)
        self.n_bytes = len(self.data)
        self.parsed_bytes = 0
        self.offsets = array.array('q', [-1])

    def load_chunk(self):
        i = self.offsets[-1]
        stop_at = min(self.n_bytes - 1, i + self.CHUNK_SIZE)
        while i < stop_at:
            j = self.data.find(b'\n', i + 1)
            if j == -1:
                j = self.n_bytes
            self.offsets.append(j)
            i = j
        self.parsed_bytes = min(self.n_bytes, self.offsets[-1] + 1)
        return self.parsed_bytes == self.n_bytes

    def __len__(self):
        return len(self.offsets) - 1

    def __getitem__(self, idx):
        return self.data[self.offsets[idx] + 1 : self.offsets[idx + 1]]



class Sectioner:
    CHUNK_SIZE = 1000

    pats = [
        ('setup', 'START setup', 'END setup'),
        ('preamble', 'START preamble', 'END preamble'),
        ('model setup', 'START model setup', 'END model setup'),
        ('dol setup', 'START dol setup', 'END dol setup'),
        ('tests', 'START tests', 'END tests'),
        ('test', r'START test \d+', r'END test \d+'),
        ('test setup', 'START test setup', 'END test setup'),
        ('test body', 'START test body', 'END test body'),
        ('dump', 'START .* dump', 'END .* dump'),
        ('verify', 'START verify', 'END verify'),
        ('teardown', 'START teardown', 'END teardown'),
    ]

    def __init__(self, doc):
        self.doc = doc
        self.sections = array.array('Q')
        self.sections.frombytes(bytes(len(self.doc) * self.sections.itemsize))
        self.parsed_lines = 0
        self.n_lines = len(self.sections)
        self.stack = []
        self.s_start = 0
        self.s_type = 0
        self._pats = [((i + 1) << 32, re.compile(s.encode()), re.compile(e.encode()))
                      for i, (_, s, e) in enumerate(self.pats)]
        
    def parse_chunk(self):
        start_at = self.parsed_lines
        self.parsed_lines = min(self.n_lines, start_at + self.CHUNK_SIZE)

        for line_i in range(start_at, self.parsed_lines):
            line = self.doc[line_i]
            for _type, start_pat, end_pat in self._pats:
                if start_pat.search(line):
                    self.stack.append((self.s_start, self.s_type))
                    self.s_start, self.s_type = line_i, _type
                    break
                elif end_pat.search(line):
                    assert _type == self.s_type, (line_i, (self.s_start, self.s_type), self.stack)
                    self.sections[self.s_start] = self.s_type | (line_i + 1)
                    self.s_start, self.s_type = self.stack.pop()
                    break

            self.sections[line_i] = self.s_type | self.s_start

        if self.parsed_lines == self.n_lines:
            if self.s_type:
                self.sections[self.s_start] = self.s_type | self.n_lines
            while self.stack:
                s_start, s_type = self.stack.pop()
                if s_type:
                    self.sections[s_start] = s_type | self.n_lines

        return self.parsed_lines == self.n_lines

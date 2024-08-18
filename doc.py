import array
import mmap
import os


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

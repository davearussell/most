import array
import mmap
import os


class Document:
    def __init__(self, path):
        self.path = path
        if os.stat(path).st_size == 0:
            self.data = b''
        else:
            self.fd = os.open(self.path, os.O_RDONLY)
            self.data = mmap.mmap(self.fd, 0, prot=mmap.PROT_READ)
        self.n_bytes = len(self.data)
        self.offsets = array.array('q', [-1])
        self.load()

    def load(self):
        i = -1
        while i < self.n_bytes - 1:
            j = self.data.find(b'\n', i + 1)
            if j == -1:
                j = self.n_bytes
            self.offsets.append(j)
            i = j

    def __len__(self):
        return len(self.offsets) - 1

    def __getitem__(self, idx):
        return self.data[self.offsets[idx] + 1 : self.offsets[idx + 1]]

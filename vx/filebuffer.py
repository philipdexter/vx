from vx.buffer import buffer

class filebuffer(buffer):
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.attach_file(filename)

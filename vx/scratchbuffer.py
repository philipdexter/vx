from vx.buffer import buffer

class scratchbuffer(buffer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.blank()

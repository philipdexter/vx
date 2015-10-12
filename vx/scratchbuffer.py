from vx.buffer import buffer

class scratchbuffer(buffer):
    def __init__(self, *args, **kwargs):
        super(scratchbuffer, self).__init__(*args, **kwargs)

        self.blank()

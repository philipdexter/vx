import vx

import os.path

def mode_from_filename(file):
    root, ext = os.path.splitext(file)
    ext = ext if ext else root

    mode = None
    if ext == '.c':
        return c_mode

class mode:
    def __init__(self, window):
        self.breaks = ('_', ' ', '\n')

class c_mode(mode):
    def __init__(self, window):
        super(c_mode, self).__init__(window)

        self.breaks = ('_', ' ', '\n', '(', ')', '<', '>', '.', ',', '#')

        self.keywords = ('return', 'goto', 'break', 'continue')

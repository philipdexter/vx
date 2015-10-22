import vx

import os.path

def mode_from_filename(file):
    root, ext = os.path.splitext(file)
    ext = ext if ext else root

    mode = None
    if ext == '.c':
        return c_mode
    elif ext == '.py':
        return python_mode

class mode:
    def __init__(self, window):
        self.breaks = ('_', ' ', '\n', '\t')
        self.keywords = ()

class python_mode(mode):
    def __init__(self, window):
        super().__init__(window)

        self.breaks = ('_', ' ', '\n', '\t', '(', ')', '{', '}', '.', ',', '#')

        self.keywords = ('class', 'return', 'for', 'while', 'break', 'continue', 'def', 'from', 'import')

class c_mode(mode):
    def __init__(self, window):
        super().__init__(window)

        self.breaks = ('_', ' ', '\n', '\t', '(', ')', '<', '>', '.', ',', '#')

        self.keywords = ('#include', '#define', 'if', 'else', 'return', 'goto', 'break', 'continue', r'"(?:[^"\\]|\\.)*"')

import editor

def C(c):
    return chr(0x1f & ord(c))

def M(c):
    return chr(0x80 | ord(c))

class keybinding:
    def __init__(self, key):
        self.key = key

    def __str__(self):
        return str(self.key)

class control(keybinding):
    def __init__(self):
        pass

    def __add__(self, other):
        if type(other) is str:
            other = keybinding(other)
        other.key = C(other.key)
        return other

class meta(keybinding):
    def __init__(self):
        pass

    def __add__(self, other):
        if type(other) is str:
            other = keybinding(other)
        other.key = M(other.key)
        return other

def bind(key, command=None):
    if command is None:
        def g(func):
            editor.keymap[str(key)] = func
            def h(*args, **kwargs):
                return func(*args, **kwargs)
            return h
        return g
    else:
        editor.keymap[str(key)] = command

editor.bind = bind
editor.ctrl = control()
editor.alt = meta()

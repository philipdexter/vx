import editor

def _C(c):
    return chr(0x1f & ord(c))

def _M(c):
    return chr(0x80 | ord(c))

def _tobinding(s):
    class donothing:
        def __init__(self): pass
        def __add__(self, other): return other
    binding = donothing()
    for c,n in zip(s,s[1:]+' '):
        if c == '-':
            continue
        elif c == 'C' and n == '-':
            c = control()
        elif c == 'M' and n == '-':
            c = meta()
        binding = binding + c
    return binding
editor.tobinding = _tobinding

class _keybinding:
    def __init__(self, key):
        self.key = key

    def __str__(self):
        return str(self.key)

class _keymodifier:
    def __init__(self, mod):
        self.mod = mod
        pass

    def __add__(self, other):
        if type(other) is str:
            other = _keybinding(other)
        other.key = self.mod(other.key)
        return other

    def __radd__(self, other):
        if type(other) is str:
            other = _keybinding(other)
        other.key = self.mod(other.key)
        return other

def _bind(key, command=None):
    if type(key) is str:
        key = tobinding(key)
    if command is None:
        def g(func):
            editor.keymap[str(key)] = func
            def h(*args, **kwargs):
                return func(*args, **kwargs)
            return h
        return g
    else:
        editor.keymap[str(key)] = command

editor.bind = _bind
editor.ctrl = _keymodifier(_C)
editor.alt = _keymodifier(_M)

def _repeat(c, times=4):
    for _ in range(times):
        c()

editor.repeat = _repeat

class _keys:
    def __init__(self):
        for i in range(26):
            char = chr(ord('a') + i)
            setattr(_keys, char, char)
        for i in range(26):
            char = chr(ord('A') + i)
            setattr(_keys, char, char)
        _keys.le = '<'
        _keys.ge = '>'
editor.keys = _keys()

import vx
from enum import Enum
from sys import argv
from functools import partial

vx.register_key = lambda x: None
vx.my_vx = lambda: None

_keys = {
    'langle':       '<', 'rangle':   '>',
    'lparen':       '(', 'rparen':   ')',
    'lbrace':       '{', 'rbrace':   '}',
    'lbracket':     '[', 'rbracket': ']',
    'grave':        '`',
    'backtick':     '`',
    'tilde':        '~',
    'bang':         '!',
    'exclamation':  '!',
    'at':           '@',
    'hash':         '#',
    'dollar':       '$',
    'percent':      '%',
    'carrot':       '^',
    'carat':        '^',
    'and':          '&',
    'ampersand':    '&',
    'star':         '*',
    'asterisk':     '*',
    'hyphen':       '-',
    'dash':         '-',
    'minus':        '-',
    'underscore':   '_',
    'equals':       '=',
    'equal':        '=',
    'plus':         '+',
    'pipe':         '|',
    'backslash':    '\\',
    'forwardslash': '/',
    'slash':        '/',
    'quote':        '"',
    'apostrophe':   '\'',
    'question':     '?',
    'dot':          '.',
    'period':       '.',
    'comma':        ',',
    'backspace':    chr(127),
    'enter':        chr(13),
    'return':       chr(13), # this one is funky
    'escape':       chr(27),
}

for x in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
  _keys[x] = x

Keys = Enum('Keys', _keys)

class _keybinding:
    def __init__(self, key):
        if isinstance(key, Keys):
            self.key = key.value
        else:
            self.key = key

    def __str__(self):
        return str(self.key)

class _keymodifier:
    def __init__(self, mod):
        self.mod = mod
        pass

    def __add__(self, other):
        if not isinstance(other, _keybinding):
            other = _keybinding(other)
        other.key = self.mod(other.key)
        return other

    __radd__ = __add__

_ctrl = _keymodifier(lambda c: chr(0x1f & ord(c)))
_alt =  _keymodifier(lambda c: chr(0x80 | ord(c)))

def _tobinding(s):
    '''Convert a key string (C-o) to a keycode.'''
    class donothing:
        def __init__(self): pass
        def __add__(self, other): return other
    binding = donothing()
    for c,n in zip(s,s[1:]+' '):
        if c == '-':
            continue
        elif c == 'C' and n == '-':
            c = _ctrl
        elif c == 'M' and n == '-':
            c = _alt
        binding = binding + c
    return binding

def _realbind(key, func):
    '''Bind a key to a function. Cannot be used as a decorator.'''
    if type(key) is str:
        key = _tobinding(key)
    # kinda hacky
    if isinstance(key, Keys):
        key = key.value

    vx.keymap[str(key)] = func

def _bind(key, command=None):
    '''Bind a key to a function. Can be used as a decorator.'''
    if command is None:
        def decorator(func):
            _realbind(key, func)
            return func
        return decorator
    else:
        _realbind(key, command)

def _quick_bind(key):
    '''Bind a keycode to insert itself as text.'''
    _bind(key, partial(vx.add_string, key))

# Quick-bind letter keys
for i in range(26):
    char = chr(ord('a') + i)
    _quick_bind(char)

    char = chr(ord('A') + i)
    _quick_bind(char)

# ...number keys
for i in range(10):
    _quick_bind(str(i))

# ...symbols
for char in ['?', '<', '>', '\'', '/', '"', ':',
             ';', '.', ',', '!', '@', '#', '$',
             '%', '^', '&', '*', '(', ')', '-',
             '_', '+', '=', '\\', '|', '`', '~',
             ' ']:
    _quick_bind(char)

# ...return/backspace
_bind(chr(13), partial(vx.add_string, '\n'))
_bind(chr(127), vx.backspace)

def _repeat(c, times=4):
    for _ in range(times):
        c()

class _window:
    def __init__(self, rows, columns, x, y):
        self._c_window = vx.new_window(rows, columns, x, y)

    def attach_file(self, filename):
        vx.attach_window(self._c_window, filename)

    def blank(self):
        vx.attach_window_blank(self._c_window)

    def focus(self):
        vx.focus_window(self._c_window)

    def update(self):
        vx.update_window(self._c_window)


_windows = []

_current_window = -1
def _next_window():
    global _current_window
    _current_window += 1
    if _current_window >= len(_windows):
        _current_window = 0
    _windows[_current_window].focus()

vx.next_window = _next_window
vx.windows = _windows
vx.files = argv[1:]
vx.window = _window
vx.keys = Keys
vx.repeat = _repeat
vx.tobinding = _tobinding
vx.bind = _bind
vx.ctrl = _ctrl
vx.alt = _alt

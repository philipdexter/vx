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
    def __init__(self, key, printable):
        if isinstance(key, Keys):
            self.key = key.value
        else:
            self.key = key
        self.printable = printable

    def __str__(self):
        return str(self.key)

    def __sub__(self, other):
        return self + _keyseparator() + other

class _keymodifier:
    def __init__(self, mod, printable):
        self.mod = mod
        self.printable = printable

    def __add__(self, other):
        if not isinstance(other, _keybinding):
            other = _keybinding(other, str(other))
        other.key = self.mod(other.key)
        other.printable = self.printable + '-' + other.printable
        return other

_ctrl = _keymodifier(lambda c: chr(0x1f & ord(c)), 'C')
_alt =  _keymodifier(lambda c: chr(0x80 | ord(c)), 'M')

class _keyseparator:
    def __init__(self):
        self.left = None
        self.right = None

    def __add__(self, other):
        if isinstance(other, Keys):
            other = _keybinding(other, str(other))
        if type(other) is _keyseparator:
            other.left = self
            return other
        if self.right:
            self.right += other
        else:
            self.right = other
        return self

    def __radd__(self, other):
        if type(other) is str:
            other = _keybinding(other)
        if self.left:
            self.left += other
        else:
            self.left = other
        return self

    def __sub__(self, other):
        if isinstance(other, Keys):
            other = _keybinding(other, other)
        return self + _keyseparator() + other

    def __str__(self):
        ret = ''
        if self.left:
            ret += str(self.left)
        ret += ' '
        if self.right:
            ret += str(self.right)
        return ret


def _tobinding(s):
    '''Convert a key string (C-o) to a keycode.'''
    class donothing:
        def __add__(self, other): return other
    binding = donothing()
    for c,n in zip(s,s[1:]+' '):
        if c == '-':
            continue
        elif c == 'C' and n == '-':
            c = _ctrl
        elif c == 'M' and n == '-':
            c = _alt
        elif c == ' ':
            c = _keyseparator()
        binding = binding + c
    return binding

_keyscotch = {}
_current_square = _keyscotch

def _bind(keys, command=None):
    """Bind a key to a command. Can be used as a decorator"""
    if command is None:
        def wrapper(func):
            _bind(keys, func)
            return func
        return wrapper
    keys = str(keys)
    if type(keys) is str:
        squares = list(map(lambda x: str(_tobinding(x)), keys.split(' ')))
    else:
        squares = [keys]
    prehops = squares[0:-1]
    finalhop = squares[-1]
    cur = _keyscotch
    for h in prehops:
        if cur.get(h) is None:
            cur[h] = {}
        cur = cur[h]
    cur[finalhop] = command

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

def _base_register_key(key):
    global _current_square
    _current_square = _current_square.get(key)
    if callable(_current_square):
        _current_square()
        _current_square = _keyscotch
    elif _current_square is None:
        _current_square = _keyscotch
        raise Exception('not found')
        return False
    return True

_key_callbacks = []
_key_callbacks.append(_base_register_key)
vx.key_callbacks = _key_callbacks

def _register_key(key):
    for c in _key_callbacks:
        if c(key): break
vx.register_key = _register_key

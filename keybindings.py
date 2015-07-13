import vx

from unicodedata import category

from functools import partial
from enum import Enum

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

    def bytes(self):
        return bytes(self.key)

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

_ctrl = _keymodifier(lambda c: bytes([0x1f & ord(c)]), 'C')
_alt =  _keymodifier(lambda c: bytes([0x80 | ord(c)]), 'M')

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

    def flatten(self):
        ret = b''
        if self.left:
            ret += self.left.key
        ret += b' '
        if self.right:
            ret += self.right.key
        return ret

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

_keybindings = {}
_keybinding_traverser = _keybindings

def _bind(keys, command=None):
    """Bind a key to a command. Can be used as a decorator"""
    if command is None:
        def wrapper(func):
            _bind(keys, func)
            return func
        return wrapper
    # we split on space below so handle it here
    if keys == ' ':
        _keybindings[' '] = command
        return
    if isinstance(keys, Keys):
        keys = keys.value

    if isinstance(keys, str):
        squares = [_tobinding(keys)]
        if isinstance(squares[0], _keyseparator):
            squares = squares[0].flatten().split(b' ')
    elif isinstance(keys, _keybinding):
        squares = [keys.bytes()]
    elif isinstance(keys, _keyseparator):
        squares = keys.flatten().split(b' ')
    else:
        squares = [keys]
    if isinstance(squares[0], str):
        squares[0] = bytes(squares[0], 'utf8')
    prehops = squares[0:-1]
    finalhop = squares[-1]
    cur = _keybindings
    for h in prehops:
        if cur.get(h) is None:
            cur[h] = {}
        elif not isinstance(cur[h], dict):
            print('Warning, overwriting old keybinding')
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

def _register_key(key):
    global _keybinding_traverser
    first = _keybinding_traverser is _keybindings
    _keybinding_traverser = _keybinding_traverser.get(key)
    if callable(_keybinding_traverser):
        _keybinding_traverser()
        _keybinding_traverser = _keybindings
    elif _keybinding_traverser is None:
        _keybinding_traverser = _keybindings
        # if this is a first key and not a control character then try to print it
        try:
            if first and category(key.decode('utf8'))[0] != 'C':
                vx.add_string(key.decode('utf8'))
            else:
                raise Exception(b'not found ' + key)
        except:
            raise Exception(b'invalid unicode entered ' + key)
        _keybinding_traverser = _keybindings
        return False
    return True

_key_callbacks = []
_key_callbacks.append(_register_key)

def _register_key(key):
    for c in _key_callbacks:
        if c(key): break

vx.key_callbacks = _key_callbacks
vx.register_key = _register_key
vx.tobinding = _tobinding
vx.bind = _bind
vx.ctrl = _ctrl
vx.alt = _alt
vx.keys = Keys

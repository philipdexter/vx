import vx
import windows

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
    'tab':          chr(9),
}

for x in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
    _keys[x] = x

Keys = Enum('Keys', _keys)

class _keybinding:
    def __init__(self, key, printable):
        if isinstance(key, Keys):
            self.key = bytes(key.value, 'utf8')
        else:
            self.key = key
        self.printable = printable

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
            if isinstance(self.right, str):
                self.right = _keybinding(bytes(self.right, 'utf8'), self.right)
            ret += self.right.key
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

class _keybinding_table:
    class MATCH_STATE(Enum):
        reject = 1
        keep_going = 2
        accept = 3

    def __init__(self):
        self._keybindings = {}

    def bind(self, keys, command):
        """Bind a key to a command."""
        # we split on space below so handle it here
        if keys == ' ':
            self._keybindings[' '] = command
            return
        if isinstance(keys, Keys):
            keys = keys.value

        if isinstance(keys, str):
            squares = [_tobinding(keys)]
            if isinstance(squares[0], _keyseparator):
                squares = squares[0].flatten().split(b' ')
            elif isinstance(squares[0], _keybinding):
                squares = [squares[0].bytes()]
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
        cur = self._keybindings
        for h in prehops:
            if cur.get(h) is None:
                cur[h] = {}
            elif not isinstance(cur[h], dict):
                print('Warning, overwriting old keybinding')
                cur[h] = {}
            cur = cur[h]
        cur[finalhop] = command

    def match_key_sequence(self, key_sequence):
        cur = self._keybindings
        for key in key_sequence:
            cur = cur.get(key)
            if cur is None:
                return _keybinding_table.MATCH_STATE.reject
            elif callable(cur):
                cur()
                return _keybinding_table.MATCH_STATE.accept
        return _keybinding_table.MATCH_STATE.keep_going

_global_keybinding_table = _keybinding_table()

@vx.expose
def _bind(keys, command=None, *args, **kwargs):
    """Bind a key to the global keybinding table. Can be used as a decorator"""

    # used as a decorator
    if command is None:
        return partial(_bind, keys)

    _global_keybinding_table.bind(keys, command)


_keybinding_tables = []
_keybinding_tables.append(_global_keybinding_table)

_keybinding_queue = []

@vx.expose
def _register_key(key):
    global _keybinding_queue
    _keybinding_queue.append(key)

    for table in _keybinding_tables:
        match = table.match_key_sequence(_keybinding_queue)
        if match == _keybinding_table.MATCH_STATE.accept:
            break

    if match == _keybinding_table.MATCH_STATE.reject:
        try:
            if category(key.decode('utf8')[0])[0] != 'C':
                vx.add_string(key.decode('utf8'))
        except UnicodeDecodeError:
            # Invalid unicode, don't print
            pass
        _keybinding_queue = []
    elif match == _keybinding_table.MATCH_STATE.accept:
        _keybinding_queue = []

## Exports and defaults

vx.expose(_keybinding_table, 'keybinding_table')
vx.expose(_keybinding_tables, 'keybinding_tables')
vx.expose(_ctrl, 'ctrl')
vx.expose(_alt, 'alt')
vx.expose(Keys, 'keys')

# bind return and backspace
vx.bind(Keys.enter, partial(vx.add_string, '\n'))
vx.bind(Keys.backspace, vx.backspace)

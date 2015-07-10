import editor
from sys import argv
from functools import partial

editor.register_key = lambda x: None
editor.my_editor = lambda: None

def _C(c):
    return chr(0x1f & ord(c))

def _M(c):
    return chr(0x80 | ord(c))

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
_ctrl = _keymodifier(_C)
_alt =  _keymodifier(_M)

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
    editor.keymap[str(key)] = func

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
    _bind(key, partial(editor.add_string, key))

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
_bind(chr(13), partial(editor.add_string, '\n'))
_bind(chr(127), editor.backspace)

def _repeat(c, times=4):
    for _ in range(times):
        c()

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
        _keys.question_mark = '?'
        _keys.period = '.'
        _keys.comma = ','
        _keys.left_parenthesis = '('
        _keys.right_parenthesis = ')'
        _keys.left_curly_bracket = '{'
        _keys.right_curly_bracket = '}'
        _keys.left_square_bracket = '['
        _keys.right_square_bracket = ']'
        _keys.plus = '+'
        _keys.minus = '-'
        _keys.equals = '='
        _keys.underscore = '_'
        _keys.backslash = '\\'
        _keys.forwardslash = '/'
        _keys.quote = '\''
        _keys.doublequote = '"'
        _keys.pipe = '|'
        _keys.backspace = chr(127)
        _keys.enter = chr(13)
        _keys.escape = chr(27)

class _window:
    def __init__(self, rows, columns, x, y):
        self._c_window = editor.new_window(rows, columns, x, y)

    def attach_file(self, filename):
        editor.attach_window(self._c_window, filename)

    def blank(self):
        editor.attach_window_blank(self._c_window)

    def focus(self):
        editor.focus_window(self._c_window)

    def update(self):
        editor.update_window(self._c_window)


_windows = []

_current_window = -1
def _next_window():
    global _current_window
    _current_window += 1
    if _current_window >= len(_windows):
        _current_window = 0
    _windows[_current_window].focus()

editor.next_window = _next_window
editor.windows = _windows
editor.files = argv[1:]
editor.window = _window
editor.keys = _keys()
editor.repeat = _repeat
editor.tobinding = _tobinding
editor.bind = _bind
editor.maybebind = _maybebind
editor.ctrl = _ctrl
editor.alt = _alt

import vx
import vx.movement as move

from functools import partial
from vx.keybindings import KeybindingTable
from vx.keybindings import alt
from vx.keybindings import bind
from vx.keybindings import ctrl
from vx.keybindings import keys

def load(window):
    return Vigor(window)

class Vigor(KeybindingTable):
    def __init__(self, win):
        super().__init__()

        self.win = win

        self.bind(keys.h, move.left)
        self.bind(keys.j, move.down)
        self.bind(keys.k, move.up)
        self.bind(keys.l, move.right)

        self.bind(keys.backspace, self.win.backspace)
        self.bind(keys.enter, partial(self.win.add_string, '\n'))

        self.bind(ctrl + keys.x, vx.quit)
        self.bind(ctrl + keys.s, self.win.save)

# old trash code that I might want to look at later
"""
from functools import partial
from enum import Enum

vx.print_printable = False

class Mode(Enum):
    normal = 0
    insert = 1

class VigorBinding(object):
    '''A class that supports multiple callbacks depending on mode.'''
    def __init__(self, key):
        self.key = key
        self.callbacks = {}

        if isinstance(key, keybindings.Keys):
          string = key.value
        else:
          string = key

        self.callbacks[Mode.insert] = partial(text.add_string, string)

        vx.bind(self.key, self)

    def bind(self, mode=Mode.normal):
        def decorator(func):
            self.callbacks[mode] = func
            return func
        return decorator

    def __call__(self, *args, **kwargs):
        mode = getattr(vx.window.focused, 'mode', Mode.normal)

        if mode in self.callbacks:
            self.callbacks[mode](*args, **kwargs)

vbinds = {}

def vbind(key, command=None, mode=Mode.normal):
    '''Helper to ensure only one VigorBinding is created per key.'''
    if key not in vbinds:
        vbinds[key] = VigorBinding(key)

    if command:
        vbinds[key].bind(mode)(command)
    else:
        return vbinds[key].bind(mode)

# Insert mode
@vbind(vx.keys.i)
def insert():
    '''Enter insert mode'''
    vx.window.focused.mode = Mode.insert
    vx.print_printable = True

@vbind(vx.keys.I)
def bol_insert():
    '''Move to beginning of line and enter insert mode'''
    # FIXME should move to first non-whitespace character
    move.bol()
    insert()

@vbind(vx.keys.a)
def append():
    '''Enter insert mode to the right'''
    move.right()
    insert()

@vbind(vx.keys.A)
def eol_append():
    '''Move to end of line and enter insert mode'''
    move.eol()
    insert()

# hjkl
vbind(vx.keys.h, move.left)
vbind(vx.keys.j, move.down)
vbind(vx.keys.k, move.up)
vbind(vx.keys.l, move.right)

vbind('0', move.bol)
vbind('^', move.bol) # FIXME should move to first non-ws char
vbind('$', move.eol)

@vx.bind(vx.keys.escape)
def escape():
    '''Return to normal mode'''
    vx.window.focused.mode = Mode.normal
    vx.print_printable = False

# quit
vx.bind('C-x', vx.quit)

# vx prompt
vx.bind(';', vx.exec_prompt)

# FIXME add vigor prompt
"""

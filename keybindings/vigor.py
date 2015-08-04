import vx
import keybindings
import prompt
import math
import sys

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

        self.callbacks[Mode.insert] = partial(vx.add_string, string)

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
    vx.move_bol()
    insert()

@vbind(vx.keys.a)
def append():
    '''Enter insert mode to the right'''
    vx.move_right()
    insert()

@vbind(vx.keys.A)
def eol_append():
    '''Move to end of line and enter insert mode'''
    vx.move_eol()
    insert()

# hjkl
vbind(vx.keys.h, vx.move_left)
vbind(vx.keys.j, vx.move_down)
vbind(vx.keys.k, vx.move_up)
vbind(vx.keys.l, vx.move_right)

vbind('0', vx.move_bol)
vbind('^', vx.move_bol) # FIXME should move to first non-ws char
vbind('$', vx.move_eol)

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

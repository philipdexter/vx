import vx

import math
from sys import argv

_tick_functions = []
def _register_tick_function(f, front=False):
    if front:
        _tick_functions.insert(0, f)
    else:
        _tick_functions.append(f)
def _tick():
    for f in _tick_functions:
        f()

vx.my_vx = _tick
vx.register_tick_function = _register_tick_function

vx.files = argv[1:]

def _resize():
    pass
vx.resize_handler = _resize

import vx.utils
import vx.scheduler
import vx.keybindings
from vx.window import window
import vx.status_bar
import vx.prompt
import vx.test

def _default_start():
    if len(vx.files) == 0:
        win = window(vx.rows, vx.cols, 0, 0)
        win.blank()
        win.focus()
    else:
        d = math.floor(vx.rows / (len(vx.files)))
        y = 0
        for f in vx.files:
            win = window(d, vx.cols, y, 0)
            win.attach_file(f)
            y += d
            win.focus()
vx.default_start = _default_start

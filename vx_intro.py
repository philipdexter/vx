import vx

import math
import os
import sys

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

vx.files = sys.argv[1:]

import utils
import scheduler
import keybindings
import windows
import prompt

def _default_start():
    if len(vx.files) == 0:
        win = vx.window(vx.rows, vx.cols, 0, 0)
        win.blank()
        win.focus()
    else:
        d = math.floor(vx.rows / (len(vx.files)))
        y = 0
        for f in vx.files:
            win = vx.window(d, vx.cols, y, 0)
            win.attach_file(f)
            y += d
            win.focus()
vx.default_start = _default_start

sys.path.append(os.path.expanduser('~/.python'))
try:
  import rc
except ImportError:
  pass # just means there was no ~/.python/rc module

import vx

from sys import argv

_tick_functions = []
def _register_tick_function(f):
    _tick_functions.append(f)
def _tick():
    for f in _tick_functions:
        f()

vx.my_vx = _tick
vx.register_tick_function = _register_tick_function

vx.files = argv[1:]

import utils
import keybindings
import windows
import status_bar

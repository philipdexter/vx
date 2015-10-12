import vx
import os.path
import math
from sys import argv

import vx.logger
import datetime
import subprocess
vx.logger.info('''----------------
Starting vx
{time}
----------------
'''.format(time=datetime.datetime.now()))

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

def _normal_start():
    vx.logger.info('starting normally')

    from vx.pane import pane
    from vx.filebuffer import filebuffer
    from vx.scratchbuffer import scratchbuffer
    from vx.pointer import organizer
    if len(vx.files) == 0:
        sb = scratchbuffer(vx.rows, vx.cols, 0, 0)
        win = pane(sb, vx.rows, vx.cols, 0, 0)
        organizer.add_pane(win)
        organizer.switch_to_pane(win)
    else:
        d = math.floor(vx.rows / (len(vx.files)))
        y = 0
        for f in vx.files:
            fb = filebuffer(f, d, vx.cols, y, 0)
            win = pane(fb, d, vx.cols, y, 0)
            y += d
            organizer.add_pane(win)
            organizer.switch_to_pane(win)
def _default_start():
    if not os.path.isfile(os.path.expanduser('~/.vx/rc.py')):
        import vx.new_user
        vx.new_user.start()
    else:
        _normal_start()
vx.default_start = _default_start

import vx.pointer

import vx
from vx import bind, alt, ctrl, keys, window

import sys
import math
from functools import partial

# which keybinding do we want
from keybindings import hopscotch

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


bind(ctrl + keys.x - '4', lambda: vx.prompt(vx.get_focused_window()))

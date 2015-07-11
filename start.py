import vx
import sys
import math
from vx import bind, alt, ctrl, keys, window

from functools import partial

bind(ctrl + keys.v, partial(vx.repeat, vx.move_down))
bind(alt + keys.v, partial(vx.repeat, vx.move_up))

bind(ctrl + keys.n, vx.move_down)
bind(ctrl + keys.p, vx.move_up)
bind(ctrl + keys.b, vx.move_left)
bind(ctrl + keys.f, vx.move_right)

bind(ctrl + keys.a, vx.move_bol)
bind(ctrl + keys.e, vx.move_eol)

bind(ctrl + keys.s, vx.save)

bind(alt + keys.langle, vx.move_beg)
bind(alt + keys.rangle, vx.move_end)

bind(alt + keys.s, vx.move_beg)

if len(vx.files) == 0:
    win = window(vx.rows - 1, vx.cols, 0, 0)
    win.blank()
    win.focus()
    vx.windows.append(win)
else:
    d = math.floor((vx.rows - 1) / (len(vx.files)))
    y = 0
    for f in vx.files:
        win = window(d, vx.cols, y, 0)
        y += d
        win.attach_file(f)
        win.focus()
        vx.windows.append(win)

vx.bind('C-q', vx.quit)

vx.bind('C-o', vx.next_window)

def my_vx():
    for w in vx.windows:
        w.update()

vx.my_vx = my_vx

vx.status_line = lambda: 'line: {} col: {} / rows: {} cols: {}'.format(vx.line,
                                                                           vx.col,
                                                                           vx.rows,
                                                                           vx.cols)

bind(ctrl + keys.x - ctrl + keys.c, vx.quit)

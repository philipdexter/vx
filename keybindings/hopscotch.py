import vx
from vx import bind, alt, ctrl, keys

from functools import partial

# simple movement

bind(ctrl + keys.n, vx.move_down)
bind(ctrl + keys.p, vx.move_up)
bind(ctrl + keys.b, vx.move_left)
bind(ctrl + keys.f, vx.move_right)

bind(ctrl + keys.a, vx.move_bol)
bind(ctrl + keys.e, vx.move_eol)

bind(ctrl + keys.v, partial(vx.repeat, vx.move_down))
bind(alt + keys.v, partial(vx.repeat, vx.move_up))

bind(alt + keys.langle, vx.move_beg)
bind(alt + keys.rangle, vx.move_end)

bind(ctrl + keys.l, vx.center)

# text manipulation

bind(ctrl + keys.d, vx.delete)

bind(ctrl + keys.k, vx.kill_to_end)

# window management

vx.bind(ctrl + keys.x - keys.o, vx.next_window)

bind(ctrl + keys.x - '2', vx.split_h)
bind(ctrl + keys.x - '3', vx.split_v)
bind(ctrl + keys.x - '0', vx.close_window)

# misc.

bind(ctrl + keys.x - ctrl + keys.c, vx.quit)
bind(alt + keys.x, vx.prompt)

bind(ctrl + keys.x - ctrl + keys.f, vx.file_prompt)

# undo/redo

bind(ctrl + keys.underscore, vx.undo)

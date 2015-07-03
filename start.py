import editor
from editor import bind, alt, ctrl, keys

from functools import partial

editor.status_line = 'status line-------'

bind(ctrl + keys.l, editor.move_down)

bind(ctrl + keys.v, partial(editor.repeat, editor.move_down))
bind(alt + keys.v, partial(editor.repeat, editor.move_up))

bind(ctrl + keys.n, editor.move_down)
bind(ctrl + keys.p, editor.move_up)
bind(ctrl + keys.b, editor.move_left)
bind(ctrl + keys.f, editor.move_right)

bind(ctrl + keys.a, editor.move_bol)
bind(ctrl + keys.e, editor.move_eol)

bind(ctrl + keys.s, editor.save)

bind(alt + keys.le, editor.move_beg)
bind(alt + keys.ge, editor.move_end)

bind(alt + keys.s, editor.move_beg)

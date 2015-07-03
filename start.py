import editor
import sys
from editor import bind, alt, ctrl, keys, window

from functools import partial

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

win = window(editor.rows - 1, editor.cols, 0, 0)
win.attach_file(editor.files[0] if len(editor.files) > 0 else 'README.md')
win.focus()

editor.windows.append(win)

editor.bind('C-o', editor.next_window)

def my_editor():
    for w in editor.windows:
        w.update()

editor.my_editor = my_editor

editor.status_line = lambda: 'line: {} col: {} / rows: {} cols: {}'.format(editor.line,
                                                                           editor.col,
                                                                           editor.rows,
                                                                           editor.cols)

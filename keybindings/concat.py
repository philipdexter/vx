import vx
from vx import bind, alt, ctrl, keys

from enum import Enum
from functools import partial, wraps

_stack = []

def concat_bind(command):
    def h():
        fi = getattr(vx.window.focused_window, 'force_insert', False)
        if fi:
            return vx.keybinding_table.MATCH_STATE.reject
        else:
            command()
        if not _stack:
            vx.window.focused_window.status_bar.reset_default_text()
        else:
            vx.window.focused_window.status_bar.set_status_text(' '.join(list(map(str, _stack))))
    return h

def save_typing(b):
    vx.window.focused_window.force_insert = b

def cb(key, command):
    bind(key, concat_bind(command))

def beginning():
    if not _stack:
        vx.move_bol()
    else:
        i = _stack.pop()
        if i == Place.line:
            vx.move_bol()
        elif i == Place.window:
            vx.move_beg()

def times_default():
    _stack.append(Times(4))

def end():
    if not _stack:
        vx.move_eol()
    else:
        i = _stack.pop()
        if i == Place.line:
            vx.move_eol()
        elif i == Place.window:
            vx.move_end()

def forward():
    if not _stack:
        vx.move_right()
    else:
        command = vx.move_right
        x = 1

        i = _stack.pop(0)
        if isinstance(i, Times):
            x = i.i
            if _stack:
                i = _stack.pop()
        if isinstance(i, Place):
            if i == Place.word:
                command = vx.forward_word
        vx.repeat(command, times=x)

def backward():
    if not _stack:
        vx.move_left()
    else:
        command = vx.move_left
        x = 1

        i = _stack.pop(0)
        if isinstance(i, Times):
            x = i.i
            if _stack:
                i = _stack.pop()
        if isinstance(i, Place):
            if i == Place.word:
                command = vx.backward_word
        vx.repeat(command, times=x)

def previous():
    if not _stack:
        vx.move_up()
    else:
        command = vx.move_up
        x = 1

        i = _stack.pop(0)
        if isinstance(i, Times):
            x = i.i
            if _stack:
                i = _stack.pop(0)
        if isinstance(i, Place):
            if i == Place.word:
                command = vx.backward_word
        vx.repeat(command, times=x)

def next():
    if not _stack:
        vx.move_down()
    else:
        command = vx.move_down
        x = 1

        i = _stack.pop(0)
        if isinstance(i, Times):
            x = i.i
            if _stack:
                i = _stack.pop(0)
        if isinstance(i, Place):
            if i == Place.word:
                command = vx.forward_word
            elif i == Place.window:
                command = vx.next_window
        vx.repeat(command, times=x)

def concat(default_command, f=None):
    if f is None:
        return partial(concat, default_command)
    @wraps(f)
    def g():
        if not _stack:
            default_command()
        else:
            x = 1
            extra = []

            while _stack:
                i = _stack.pop(0)
                if isinstance(i, Times):
                    x = i.i
                else:
                    extra.append(i)
            return f(default_command, x, extra)
    return g

@concat(vx.delete)
def delete(command, times, other):
    i = None
    if other:
        i = other.pop(0)
    if isinstance(i, Place):
        if i == Place.word:
            command = vx.kill_to_forward
    vx.repeat(command, times=times)

@concat(vx.backspace)
def backspace(command, times, other):
    i = None
    if other:
        i = other.pop(0)
    if isinstance(i, Place):
        if i == Place.word:
            command = vx.kill_to_backward
    vx.repeat(command, times=times)

def kill():
    if not _stack:
        vx.kill_to_end()
    else:
        command = vx.kill_to_end
        x = 1

        i = _stack.pop(0)
        if isinstance(i, Times):
            x = i.i
            if _stack:
                i = _stack.pop(0)
        if isinstance(i, Place):
            if i == Place.line:
                def _kill_total_line():
                    vx.move_bol()
                    vx.kill_to_end()
                    vx.kill_to_end()
                command = _kill_total_line
            elif i == Place.word:
                command = vx.kill_to_forward
            if _stack:
                i = _stack.pop(0)
        vx.repeat(command, times=x)

def line():
    _stack.append(Place.line)
def window():
    _stack.append(Place.window)
def word():
    _stack.append(Place.word)

def clear():
    global _stack
    _stack = []

class Place(Enum):
    line = 0
    window = 1
    word = 2
    paragraph = 3

class Times:
    def __init__(self, i):
        self.i = i
    def __str__(self):
        return '{}-times'.format(self.i)

def times(i):
    if not _stack:
        _stack.append(Times(i))
    else:
        n = _stack.pop().i
        n *= 10
        n += i
        _stack.append(Times(n))

cb(keys['0'], partial(times, 0))
cb(keys['1'], partial(times, 1))
cb(keys['2'], partial(times, 2))
cb(keys['3'], partial(times, 3))
cb(keys['4'], partial(times, 4))
cb(keys['5'], partial(times, 5))
cb(keys['6'], partial(times, 6))
cb(keys['7'], partial(times, 7))
cb(keys['8'], partial(times, 8))
cb(keys['9'], partial(times, 9))

cb(keys.i, partial(save_typing, True))
bind(ctrl + keys.i, partial(save_typing, False))

cb(keys.l, line)
cb(keys.r, window)
cb(keys.w, word)

cb(keys.g, clear)

cb(keys.n, next)
cb(keys.p, previous)
cb(keys.f, forward)
cb(keys.b, backward)
cb(keys.a, beginning)
cb(keys.e, end)

cb(keys.q, vx.quit)

cb(keys.s, lambda: vx.window.focused_window.save())

cb(keys.u, times_default)

def raise_stack():
    raise Exception(_stack)
cb(keys.o, raise_stack)

cb(keys.k, kill)
bind(keys.backspace, backspace)
cb(keys.d, delete)

cb(keys.forwardslash, vx.undo)
bind(ctrl + keys.underscore, vx.undo)

bind(alt + keys.x, vx.exec_prompt)

bind(ctrl + keys.x - keys['2'], vx.split_h)
bind(ctrl + keys.x - keys['3'], vx.split_v)
bind(ctrl + keys.x - keys['0'], vx.close_window)

cb(keys.z, vx.suspend)

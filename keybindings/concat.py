import vx
from vx import bind, alt, ctrl, keys
import undo

from enum import Enum
from functools import partial, wraps

_stack = []

def concat_bind(command):
    def h():
        fi = getattr(vx.window.focused, 'force_insert', False)
        if fi:
            return vx.keybinding_table.MATCH_STATE.reject
        else:
            command()
        if not _stack:
            if vx.window.focused.status_bar:
                vx.window.focused.status_bar.reset_default_text()
        else:
            if vx.window.focused.status_bar:
                vx.window.focused.status_bar.set_status_text(' '.join(list(map(str, _stack))))
    return h

def save_typing(b):
    vx.window.focused.force_insert = b

def cb(key, command):
    bind(key, concat_bind(command))

def beginning():
    beginning_pm()
    line()
    analyze(move_me)

def times_default():
    _stack.append(Times(4))

def end():
    end_pm()
    line()
    analyze(move_me)

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
        vx.repeat(command, times=x)

def next():
    analyze(move_me, partial(line_grabber, restore_column=True))

def delete_me(what=None):
    if what is None:
        vx.delete()
    else:
        direction = 1
        ra, ca, rb, cb = what()
        if (ra == rb and ca > cb) or rb < ra:
            rb, cb, ra, ca = ra, ca, rb, cb
            direction = 0
            vx.window.focused.cursor = (ra, ca)
        removed = vx.get_str_linecol_to_linecol_window(vx.window.focused, ra, ca, rb, cb)
        vx.remove_text_linecol_to_linecol(ra, ca, rb, cb)
        vx.window.focused.dirty = True
        undo.register_removal(removed, ra, ca, hold=bool(direction))
def delete():
    analyze(delete_me, character_grabber)

def move_me(what=None):
    global _set_column
    if what is None:
        vx.move_right()
    else:
        _, _, rb, cb = what()
        vx.window.focused.cursor = (rb, cb)
        if _set_column:
            vx.window.focused.last_seeked_column = cb
        _set_column = True
def move():
    analyze(move_me, character_grabber)
def backward():
    backward_pm()
    analyze(move_me, character_grabber)

def center_me(what=None):
    if what is None:
        vx.center()
    else:
        _, _, rb, cb = what()
        r, _ = vx.get_window_size(vx.window.focused)
        _, x = vx.get_linecol_start_window(vx.window.focused)
        new_top = max(rb - r // 2, 1)
        vx.window.focused.set_start_linecol(new_top, x)
def center():
    analyze(center_me)

def character_grabber(x, part):
    if part == PlaceModifier.backward:
        direction = False
    else:
        direction = True
    with vx.cursor_wander():
        ra, ca = vx.window.focused.cursor
        for _ in range(x):
            vx.move_right() if direction else vx.move_left()
            rb, cb = vx.window.focused.cursor
        return ra, ca, rb, cb

def window_grabber(x, part):
    if part == PlaceModifier.backward or part == PlaceModifier.beginning:
        direction = False
    else:
        direction = True
    with vx.cursor_wander():
        ra, ca = vx.window.focused.cursor
        vx.move_end() if direction else vx.move_beg()
        rb, cb = vx.window.focused.cursor
        return ra, ca, rb, cb

_set_column = True

def line_grabber(x, part, restore_column=False):
    global _set_column
    _set_column = not restore_column
    if part == PlaceModifier.backward:
        direction = False
    else:
        direction = True
    with vx.cursor_wander():
        # Can only move to the beginning of a line once
        if part == PlaceModifier.beginning:
            ra, ca = vx.window.focused.cursor
            vx.move_bol()
            rb, cb = vx.window.focused.cursor
            return ra, ca, rb, cb
        # Same with moving to the end
        if part == PlaceModifier.end:
            ra, ca = vx.window.focused.cursor
            vx.move_eol()
            rb, cb = vx.window.focused.cursor
            return ra, ca, rb, cb
        # Same with findint the absolute line
        if part == PlaceModifier.absolute:
            ra, ca = vx.window.focused.cursor
            vx.window.focused.cursor = (x, ca)
            rb, cb = vx.window.focused.cursor
            return ra, ca, rb, cb
        # Handle a whole line, forwards or backwards
        if restore_column:
            _, column = vx.window.focused.cursor
        vx.move_bol() if direction else vx.move_eol()
        ra, ca = vx.window.focused.cursor
        for _ in range(x):
            if direction:
                vx.move_down()
            else:
                vx.move_up()
            if restore_column:
                r, c = vx.window.focused.cursor
                vx.window.focused.cursor = (r, column)
                _, c = vx.window.focused.cursor
                if c < vx.window.focused.last_seeked_column:
                    vx.window.focused.cursor = (r, vx.window.focused.last_seeked_column)
            rb, cb = vx.window.focused.cursor
        return ra, ca, rb, cb

def word_grabber(x, part):
    if part == PlaceModifier.backward:
        direction = False
    else:
        direction = True
    with vx.cursor_wander():
        ra, ca = vx.window.focused.cursor
        breaks = ('_', ' ', '\n')
        for _ in range(x):
            offsets = list(map(lambda x: x[1], vx.get_offsets_of(breaks, direction)))
            if len(offsets) == 0:
                vx.move_end() if direction else vx.move_beg()
                rb, cb = vx.window.focused.cursor
            else:
                o = min(offsets)
                vx.repeat(vx.move_right if direction else vx.move_left, times=o)
                rb, cb = vx.window.focused.cursor
        return ra, ca, rb, cb

def analyze(command, default_grabber=None):
    previous = []
    grabber = default_grabber
    x = 1
    part = PlaceModifier.whole
    while _stack:
        i = _stack.pop(0)
        # How many objects do we get?
        if isinstance(i, Times):
            previous.append(i)
            x = i.i
            continue
        # What part of the object do we get?
        if isinstance(i, PlaceModifier):
            previous.append(i)
            part = i
            continue
        # What object do we get?
        if isinstance(i, Place):
            if i == Place.line:
                grabber = line_grabber
            elif i == Place.word:
                grabber = word_grabber
            elif i == Place.window:
                grabber = window_grabber
    command(partial(grabber, x, part) if grabber else None)
cb(keys.y, partial(analyze, delete_me))

def absolute_line():
    absolute_pm()
    line()
    analyze(move_me)

def backspace():
    backward_pm()
    analyze(delete_me, character_grabber)

def line():
    _stack.append(Place.line)
def window():
    _stack.append(Place.window)
def word():
    _stack.append(Place.word)
def beginning_pm():
    _stack.append(PlaceModifier.beginning)
def end_pm():
    _stack.append(PlaceModifier.end)
def backward_pm():
    _stack.append(PlaceModifier.backward)
def absolute_pm():
    _stack.append(PlaceModifier.absolute)

def clear():
    global _stack
    _stack = []

class Place(Enum):
    line = 0
    window = 1
    word = 2
    paragraph = 3

class PlaceModifier(Enum):
    whole = 0
    beginning = 1
    end = 2
    backward = 3
    absolute = 4

class String:
    def __init__(self, s):
        self.s = s
    def __str__(self):
        return '"{}"'.format(self.s)

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
cb(keys.m, move)
cb(keys.b, backward)
cb(keys.a, beginning)
cb(keys.e, end)

cb(keys.A, beginning_pm)
cb(keys.E, end_pm)
cb(keys.B, backward_pm)
cb(keys.N, absolute_pm)

cb(keys.q, vx.quit)

cb(keys.s, lambda: vx.window.focused.save())

cb(keys.u, times_default)

def raise_stack():
    raise Exception(_stack)
cb(keys.o, raise_stack)

cb(keys.L, absolute_line)

bind(keys.backspace, backspace)
cb(keys.d, delete)

cb(keys.forwardslash, vx.undo)
bind(ctrl + keys.underscore, vx.undo)

bind(alt + keys.x, vx.exec_prompt)

cb(keys.c, center)

bind(ctrl + keys.x - keys['2'], vx.split_h)
bind(ctrl + keys.x - keys['3'], vx.split_v)
bind(ctrl + keys.x - keys['0'], vx.close_window)

cb(keys.z, vx.suspend)

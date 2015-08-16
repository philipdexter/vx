import vx
from vx.keybindings import bind, alt, ctrl, keys, keybinding_table
from vx.keybindings.utils import is_printable
import vx.undo as undo
import vx.movement as move
import vx.text as text
import vx.window as window
import vx.test as test
import vx.utils as utils
import vx.prompt as prompt

from ..pointer import panes, organizer

from enum import Enum
from functools import partial, wraps

def load(window):
    return concat_keybindings(window)

class Place(Enum):
    line = 0
    window = 1
    word = 2
    paragraph = 3
    whitespace = 4
    content = 5

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

class concat_keybindings(keybinding_table):
    def __init__(self, for_window):
        super(concat_keybindings, self).__init__()

        self.for_window = for_window

        self.force_insert = False

        self._stack = []
        self._quoting = False
        self._set_column = True

        self._graveyard = []

        def _catch_all(key):
            if self.force_insert:
                return keybinding_table.MATCH_STATE.reject
            if is_printable(key):
                def g():
                    self.for_window.add_string('X')
                self.concat_bind(g)(key)
                return keybinding_table.MATCH_STATE.accept
            return keybinding_table.MATCH_STATE.reject
        self.catch_all = _catch_all

        self.cb(keys.quote, self.toggle_quoting)

        self.cb(keys['0'], partial(self.times, 0))
        self.cb(keys['1'], partial(self.times, 1))
        self.cb(keys['2'], partial(self.times, 2))
        self.cb(keys['3'], partial(self.times, 3))
        self.cb(keys['4'], partial(self.times, 4))
        self.cb(keys['5'], partial(self.times, 5))
        self.cb(keys['6'], partial(self.times, 6))
        self.cb(keys['7'], partial(self.times, 7))
        self.cb(keys['8'], partial(self.times, 8))
        self.cb(keys['9'], partial(self.times, 9))

        self.cb(keys.i, partial(self.save_typing, True))
        super(concat_keybindings, self).bind(ctrl + keys.k, partial(self.save_typing, False))

        self.bind(keys.enter, partial(self.for_window.add_string, '\n'))
        self.bind(keys.backspace, self.for_window.backspace)
        self.bind(keys.tab, partial(self.for_window.add_string, '\t'))

        self.cb(keys.l, self.line)
        self.cb(keys.r, self.window)
        self.cb(keys.w, self.word)
        self.cb(keys.W, self.whitespace)
        self.cb(keys.C, self.content)

        self.cb(keys.g, self.clear)

        self.cb(keys.n, self.next)
        self.cb(keys.p, self.previous)
        self.cb(keys.m, self.move)
        self.cb(keys.b, self.backward)
        self.cb(keys.a, self.beginning)
        self.cb(keys.e, self.end)

        self.cb(keys.A, self.beginning_pm)
        self.cb(keys.E, self.end_pm)
        self.cb(keys.B, self.backward_pm)
        self.cb(keys.N, self.absolute_pm)

        self.cb(keys.q, vx.quit)

        self.cb(keys.s, lambda: self.for_window.save())

        self.cb(keys.u, self.times_default)

        self.cb(keys.o, self.raise_stack)

        self.cb(keys.L, self.absolute_line)

        super(concat_keybindings, self).bind(keys.backspace, self.backspace)
        self.cb(keys.d, self.delete)
        self.cb(keys.y, self.pop_graveyard)

        self.cb(keys.forwardslash, undo.undo)
        super(concat_keybindings, self).bind(ctrl + keys.underscore, undo.undo)

        self.cb(keys.c, self.center)

        self.cb(keys.z, vx.suspend)

        self.cb(keys.f, self._open_search)
        self.cb(keys.F, partial(self._open_search, forwards=False))
        self.cb(keys.O, self._open_file)
        super(concat_keybindings, self).bind(alt + keys.x, self._open_exec)

        self.cb(ctrl + keys.t, test.run_tests)

        self.bind(ctrl + keys.x - keys['0'], lambda: organizer.remove_pane(panes.focused))
        self.bind(ctrl + keys.x - keys['2'], lambda: panes.focused.split())
        self.bind(ctrl + keys.x - keys.o, lambda: organizer.next_pane())

    def cb(self, key, command):
        super(concat_keybindings, self).bind(key, self.concat_bind(command))

    def concat_bind(self, command):
        def h(key):
            if self._quoting and key != b'"':
                from keybindings import utils
                if utils.is_printable(key):
                    if not self._stack:
                        self._stack.append(String(key.decode('utf8')))
                    else:
                        s = self._stack.pop()
                        s = s.s + key.decode('utf8')
                        self._stack.append(String(s))
            else:
                fi = self.force_insert
                if fi:
                    return keybinding_table.MATCH_STATE.reject
                else:
                    command()
            # if not self._stack:
            #     if self.for_window.status_bar:
            #         self.for_window.status_bar.reset_default_text()
            # else:
            #     if self.for_window.status_bar:
            #         self.for_window.status_bar.set_status_text(' '.join(list(map(str, self._stack))))
        return h

    def toggle_quoting(self):
            self._quoting = not self._quoting

    def save_typing(self, b):
        if not self._stack:
            self.force_insert = b
        else:
            s = self._stack.pop(0)
            s = s.s
            self.for_window.add_string(s)

    def beginning(self):
        self.beginning_pm()
        self.line()
        self.analyze(self.move_me)

    def times_default(self):
        self._stack.append(Times(4))

    def end(self):
        self.end_pm()
        self.line()
        self.analyze(self.move_me)

    def next(self):
        self.analyze(self.move_me, partial(self.line_grabber, restore_column=True))
    def previous(self):
        self.backward_pm()
        self.analyze(self.move_me, partial(self.line_grabber, restore_column=True))

    def pop_graveyard(self):
        if len(self._graveyard) > 0:
            g = self._graveyard.pop()
            self.for_window.add_string(g)

    def delete_me(self, what=None):
        if what is None:
            vx.delete()
        else:
            direction = 1
            ra, ca, rb, cb = what()
            if (ra == rb and ca > cb) or rb < ra:
                rb, cb, ra, ca = ra, ca, rb, cb
                direction = 0
                self.for_window.cursor = (ra, ca)
            removed = vx.get_str_linecol_to_linecol_window(self.for_window, ra, ca, rb, cb)
            self._graveyard.append(removed)
            self.for_window.remove_text(ra, ca, rb, cb)
            self.for_window.dirty = True
            undo.register_removal(removed, ra, ca, hold=bool(direction))
    def delete(self):
        self.analyze(self.delete_me, self.character_grabber)

    def move_me(self, what=None):
        if what is None:
            move.right()
        else:
            _, _, rb, cb = what()
            self.for_window.cursor = (rb, cb)
            if self._set_column:
                self.for_window.last_seeked_column = cb
            self._set_column = True
    def move(self):
        self.analyze(self.move_me, self.character_grabber)
    def backward(self):
        self.backward_pm()
        self.analyze(self.move_me, self.character_grabber)

    def center_me(self, what=None):
        if what is None:
            window.center()
        else:
            _, _, rb, cb = what()
            r, _ = vx.get_window_size(self.for_window)
            _, x = self.for_window.topleft
            new_top = max(rb - r // 2, 1)
            self.for_window.topleft = (new_top, x)
            y, x = self.for_window.cursor
            if y < new_top: self.for_window.cursor = (new_top, x)
            elif y > new_top + r: self.for_window.cursor = (new_top + r, x)
    def center(self):
        self.analyze(self.center_me)

    def character_grabber(self, x, part):
        if part == PlaceModifier.backward:
            direction = False
        else:
            direction = True
        with self.for_window.cursor_wander():
            ra, ca = self.for_window.cursor
            for _ in range(x):
                move.right() if direction else move.left()
                rb, cb = self.for_window.cursor
            return ra, ca, rb, cb

    def window_grabber(self, x, part):
        if part == PlaceModifier.backward or part == PlaceModifier.beginning:
            direction = False
        else:
            direction = True
        with self.for_window.cursor_wander():
            ra, ca = self.for_window.cursor
            move.end() if direction else move.beg()
            rb, cb = self.for_window.cursor
            return ra, ca, rb, cb

    def line_grabber(self, x, part, restore_column=False):
        self._set_column = not restore_column
        if part == PlaceModifier.backward:
            direction = False
        else:
            direction = True
        with self.for_window.cursor_wander():
            # Can only move to the beginning of a line once
            if part == PlaceModifier.beginning:
                ra, ca = self.for_window.cursor
                move.bol()
                rb, cb = self.for_window.cursor
                return ra, ca, rb, cb
            # Same with moving to the end
            if part == PlaceModifier.end:
                ra, ca = self.for_window.cursor
                move.eol()
                rb, cb = self.for_window.cursor
                return ra, ca, rb, cb
            # Same with findint the absolute line
            if part == PlaceModifier.absolute:
                ra, ca = self.for_window.cursor
                self.for_window.cursor = (x, ca)
                rb, cb = self.for_window.cursor
                return ra, ca, rb, cb
            # Handle a whole line, forwards or backwards
            if restore_column:
                _, column = self.for_window.cursor
            move.bol() if direction else move.eol()
            ra, ca = self.for_window.cursor
            if not direction:
                move.bol()
                rb, cb = self.for_window.cursor
            for _ in range(x if direction else x):
                if direction:
                    move.down()
                else:
                    move.up()
                    move.eol()
                if restore_column:
                    r, c = self.for_window.cursor
                    self.for_window.cursor = (r, column)
                    _, c = self.for_window.cursor
                    if c < self.for_window.last_seeked_column:
                        self.for_window.cursor = (r, self.for_window.last_seeked_column)
                rb, cb = self.for_window.cursor
            return ra, ca, rb, cb

    def whitespace_grabber(self, x, part):
        if part == PlaceModifier.backward:
            direction = False
        else:
            direction = True
        with self.for_window.cursor_wander():
            ra, ca = self.for_window.cursor
            for _ in range(x):
                if part == PlaceModifier.absolute:
                    regex = r'^$'
                else:
                    regex = r'\s'
                offset = text.get_offset_regex(self.for_window, regex, forwards=direction)
                if offset is  None:
                    move.eol() if direction else move.bol()
                else:
                    utils.repeat(move.right if direction else move.left, times=offset)
                rb, cb = self.for_window.cursor
            return ra, ca, rb, cb

    def word_grabber(self, x, part):
        if part == PlaceModifier.backward:
            direction = False
        else:
            direction = True
        with self.for_window.cursor_wander():
            ra, ca = self.for_window.cursor
            breaks = self.for_window.mode.breaks
            for _ in range(x):
                offset = text.get_offset_regex(self.for_window, '[{}]'.format(''.join(breaks)), forwards=direction)
                if offset is None:
                    move.eol() if direction else move.bol()
                else:
                    utils.repeat(move.right if direction else move.left, times=offset)
                rb, cb = self.for_window.cursor
            return ra, ca, rb, cb

    def content_grabber(self, x, part):
        with self.for_window.cursor_wander():
            ra, ca = self.for_window.cursor
            move.bol()
            offset = text.get_offset_regex(self.for_window, r'[^\s]', ignore_pos=False)
            if offset is None:
                move.bol()
            else:
                utils.repeat(move.right, times=offset)
            rb, cb = self.for_window.cursor
            return ra, ca, rb, cb

    def analyze(self, command, default_grabber=None):
        previous = []
        grabber = default_grabber
        x = 1
        part = PlaceModifier.whole
        while self._stack:
            i = self._stack.pop(0)
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
                    grabber = self.line_grabber
                elif i == Place.word:
                    grabber = self.word_grabber
                elif i == Place.whitespace:
                    grabber = self.whitespace_grabber
                elif i == Place.window:
                    grabber = self.window_grabber
                elif i == Place.content:
                    grabber = self.content_grabber
        command(partial(grabber, x, part) if grabber else None)

    def absolute_line(self):
        self.absolute_pm()
        self.line()
        self.analyze(self.move_me)

    def backspace(self):
        self.backward_pm()
        self.analyze(self.delete_me, self.character_grabber)

    def line(self):
        self._stack.append(Place.line)
    def window(self):
        self._stack.append(Place.window)
    def word(self):
        self._stack.append(Place.word)
    def whitespace(self):
        self._stack.append(Place.whitespace)
    def content(self):
        self._stack.append(Place.content)
    def beginning_pm(self):
        self._stack.append(PlaceModifier.beginning)
    def end_pm(self):
        self._stack.append(PlaceModifier.end)
    def backward_pm(self):
        self._stack.append(PlaceModifier.backward)
    def absolute_pm(self):
        self._stack.append(PlaceModifier.absolute)

    def clear(self):
        self._stack = []

    def times(self, i):
        if not self._stack:
            self._stack.append(Times(i))
        else:
            n = self._stack.pop().i
            n *= 10
            n += i
            self._stack.append(Times(n))

    def raise_stack(self):
        raise Exception(self._stack)

    def _open_search(self, forwards=True):
        start = ''
        if self._stack:
            s = self._stack.pop()
            start = s.s
        p = panes.focused.open_prompt(prompt.regex_prompt, forwards=forwards, start=start)
        p.keybinding_table.force_insert = True

    def _open_file(self):
        p = panes.focused.open_prompt(prompt.file_prompt)
        p.keybinding_table.force_insert = True

    def _open_exec(self):
        p = panes.focused.open_prompt(prompt.exec_prompt)
        p.keybinding_table.force_insert = True

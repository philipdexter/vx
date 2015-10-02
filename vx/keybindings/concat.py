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

class lines:
    def __init__(self, how_many=None, forward=True):
        self.how_many = how_many if how_many is not None else 1
        self.forward = forward

    def __str__(self):
        return '{} line{} {}'.format(self.how_many,
                                     's' if self.how_many > 1 else '',
                                     '' if self.forward else 'back')

    def __call__(self, item):
        if item == PlaceModifier.backward:
            self.forward = False
        else:
            raise Exception('lines cannot take new item {}'.format(item))

    def grab(self, buffer):
        with buffer.cursor_wander():
            la, ca = buffer.cursor
            for _ in range(self.how_many):
                move.down(buffer) if self.forward else move.up(buffer)
            lb, cb = buffer.cursor
            return la, ca, lb, cb

class beginning_lines(lines):
    def __init__(self, how_many=None, forward=True):
        how_many = how_many if how_many is not None else 0
        super(beginning_lines, self).__init__(how_many, forward)

    def grab(self, buffer):
        with buffer.cursor_wander():
            la, ca, lb, cb = super(beginning_lines, self).grab(buffer)
            buffer.cursor = (lb, cb)
            move.bol()
            lb, cb = buffer.cursor
            return la, ca, lb, cb

class end_lines(lines):
    def __init__(self, how_many=None, forward=True):
        how_many = how_many if how_many is not None else 0
        super(end_lines, self).__init__(how_many, forward)

    def grab(self, buffer):
        with buffer.cursor_wander():
            la, ca, lb, cb = super(end_lines, self).grab(buffer)
            buffer.cursor = (lb, cb)
            move.eol()
            lb, cb = buffer.cursor
            return la, ca, lb, cb

class whole_lines(lines):
    def __init__(self, how_many=None, forward=True):
        how_many = how_many if how_many is not None else 1
        super(whole_lines, self).__init__(how_many-1, forward)

    def grab(self, buffer):
        with buffer.cursor_wander():
            move.bol() if self.forward else move.eol()
            la, ca, lb, cb = super(whole_lines, self).grab(buffer)
            buffer.cursor = (lb, cb)
            move.eol() if self.forward else move.bol()
            lb, cb = buffer.cursor
            return la, ca, lb, cb

class absolute_line(lines):
    def __init__(self, line=None, *args):
        line = line if line is not None else 1
        self.line = line
        super(absolute_line, self).__init__(line, *args)

    def __str__(self):
        return 'line {}'.format(self.line)

    def grab(self, buffer):
        with buffer.cursor_wander():
            la, ca = buffer.cursor
            return la, ca, self.line, 1

class whitespace_lines(lines):
    def __init__(self, how_many=None, forward=True):
        self.how_many = how_many if how_many is not None else 1
        self.forward = forward

    def __str__(self):
        return '{} blank line{} {}'.format(self.how_many,
                                           's' if self.how_many > 1 else '',
                                           '' if self.forward else 'back')

    def __call__(self, item):
        if item == PlaceModifier.backward:
            self.forward = False
        else:
            raise Exception('lines cannot take new item {}'.format(item))

    def grab(self, buffer):
        with buffer.cursor_wander():
            la, ca = buffer.cursor
            for _ in range(self.how_many):
                offset = text.get_offset_regex(buffer, r'^$', forwards=self.forward)
                if offset is None:
                    move.end(buffer) if self.forward else move.end(buffer)
                else:
                    utils.repeat(move.right if self.forward else move.left, times=offset)
                lb, cb = buffer.cursor
            return la, ca, lb, cb

class words:
    def __init__(self, how_many=1, forward=True):
        self.how_many = how_many
        self.forward = forward

    def __str__(self):
        return '{} word{} {}'.format(self.how_many,
                                     's' if self.how_many > 1 else '',
                                     '' if self.forward else 'back')

    def __call__(self, item):
        if item == PlaceModifier.backward:
            self.forward = False
        else:
            raise Exception('words cannot take new item {}'.format(item))

    def grab(self, buffer):
        with buffer.cursor_wander():
            la, ca = buffer.cursor
            breaks = buffer.mode.breaks
            for _ in range(self.how_many):
                offset = text.get_offset_regex(buffer, '[{}]'.format(''.join(breaks)), forwards=self.forward)
                if offset is None:
                    move.eol(buffer) if self.forward else move.bol(buffer)
                else:
                    utils.repeat(move.right if self.forward else move.left, times=offset)
                lb, cb = buffer.cursor
            return la, ca, lb, cb

class whitespaces:
    def __init__(self, how_many=1, forward=True):
        self.how_many = how_many
        self.forward = forward

    def __str__(self):
        return '{} whitespace{} {}'.format(self.how_many,
                                           's' if self.how_many > 1 else '',
                                           '' if self.forward else 'back')

    def __call__(self, item):
        if item == PlaceModifier.backward:
            self.forward = False
        else:
            raise Exception('whitespaces cannot take new item {}'.format(item))

    def grab(self, buffer):
        with buffer.cursor_wander():
            la, ca = buffer.cursor
            breaks = (' ', '\n')
            for _ in range(self.how_many):
                offset = text.get_offset_regex(buffer, '[{}]'.format(''.join(breaks)), forwards=self.forward)
                if offset is None:
                    move.eol(buffer) if self.forward else move.bol(buffer)
                else:
                    utils.repeat(move.right if self.forward else move.left, times=offset)
                lb, cb = buffer.cursor
            return la, ca, lb, cb

class characters:
    def __init__(self, how_many=1, forward=True):
        self.how_many = how_many
        self.forward = forward

    def __str__(self):
        return '{} character{} {}'.format(self.how_many,
                                          's' if self.how_many > 1 else '',
                                          '' if self.forward else 'back')

    def __call__(self, item):
        if item == PlaceModifier.backward:
            self.forward = False
        else:
            raise Exception('characters cannot take new item {}'.format(item))

    def grab(self, buffer):
        with buffer.cursor_wander():
            la, ca = buffer.cursor
            utils.repeat(move.right if self.forward else move.left, times=self.how_many)
            lb, cb = buffer.cursor
            return la, ca, lb, cb

class String:
    def __init__(self, s):
        self.s = s
        self.final = False
    def finalize(self):
        self.final = True
    def is_final(self):
        return self.final
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

        self.cb(keys.L, self.line)
        self.cb(keys.r, self.window)
        self.cb(keys.w, self.word)
        self.cb(keys.W, self.whitespace)
        self.cb(keys.C, self.content)

        self.cb(keys.g, self.clear)

        self.cb(keys.period, self.execute)

        self.cb(keys.M, partial(self.push_command, self.move))

        self.cb(keys.x, partial(self.push_command, self.jail))
        self.cb(keys.h, self.move_left)
        self.cb(keys.j, self.next_line)
        self.cb(keys.k, self.previous_line)
        self.cb(keys.l, self.move_right)
        self.cb(keys.a, self.beginning)
        self.cb(keys.e, self.end)

        self.cb(keys.T, self.whole_pm)
        self.cb(keys.A, self.beginning_pm)
        self.cb(keys.E, self.end_pm)
        self.cb(keys.H, self.backward_pm)
        self.cb(keys.N, self.absolute_pm)

        self.cb(keys.q, vx.quit)

        self.cb(keys.s, lambda: self.for_window.save())

        self.cb(keys.u, self.times_default)

        self.cb(keys.o, self.raise_stack)

        self.cb(ctrl + keys.l, self.move_absolute_line)

        super(concat_keybindings, self).bind(keys.backspace, self.backspace)
        self.cb(keys.d, self.delete)
        self.cb(keys.y, self.pop_graveyard)

        self.cb(keys.forwardslash, self.for_window.undo)
        self.bind(ctrl + keys.underscore, self.for_window.undo)

        self.cb(keys.c, self.center_me)

        self.cb(keys.z, vx.suspend)

        self.cb(keys.f, self._open_search)
        self.cb(keys.F, partial(self._open_search, forwards=False))
        self.cb(keys.O, self._open_file)
        super(concat_keybindings, self).bind(alt + keys.x, self._open_exec)

        self.cb(ctrl + keys.t, test.run_tests)

        self.bind(ctrl + keys.x - keys['0'], lambda: organizer.remove_pane(panes.focused))
        self.bind(ctrl + keys.x - keys['2'], lambda: panes.focused.split())
        self.bind(ctrl + keys.x - keys.o, lambda: organizer.next_pane())

    def move_right(self):
        with self.for_window.column_save():
            self.move()

    def move_left(self):
        with self.for_window.column_save():
            if len(self._stack) > 0:
                if not callable(self._stack[-1]):
                    self.character()
                self._stack[-1](PlaceModifier.backward)
            else:
                self.backward_pm()
                self.character()
            self.move()

    def jail(self):
        if not self._stack:
            raise Exception('empty jail')
        else:
            i = self._stack.pop(-1)
            with self.for_window.cursor_wander():
                la, ca, lb, cb = i.grab(self.for_window)
            with self.for_window.cursor_jail(la, ca, lb, cb):
                self.execute()

    def delete(self):
        direction = 1
        if not self._stack:
            self._stack.insert(0, characters())
        i = self._stack.pop(0)
        if i == PlaceModifier.backward:
            i = characters(forward=False)
        elif isinstance(i, Times):
            i = characters(how_many=i.i)
        la, ca, lb, cb = i.grab(self.for_window)
        if (la == lb and ca > cb) or lb < la:
            lb, cb, la, ca = la, ca, lb, cb
            direction = 0
            self.for_window.cursor = (la, ca)
        removed = vx.get_str_linecol_to_linecol_window(self.for_window, la, ca, lb, cb)
        self._graveyard.append(removed)
        self.for_window.remove_text(la, ca, lb, cb)
        self.for_window.dirty = True
        self.for_window.undo_tree.add(undo.removal(removed, la, ca, hold=bool(direction), box=(la, ca, lb, cb)))

    def move(self):
        if not self._stack:
            move.right()
        else:
            i = self._stack.pop(0)
            if i == PlaceModifier.backward:
                move.left()
            elif isinstance(i, Times):
                utils.repeat(self.move, times=i.i)
            else:
                _, _, lb, cb = i.grab(self.for_window)
                self.for_window.cursor = lb, cb

    def push_command(self, command):
        class c:
            def __init__(self):
                self.command = command

            def __str__(self):
                return '[]'

            def __call__(self, *args):
                command(*args)
        self._stack.append(c())

    def execute(self):
        i = len(self._stack)-1
        while self._stack:
            if callable(self._stack[i]):
                c = self._stack.pop(i)
                self._stack = self._stack[:i]
                ret = c()
                if ret is not None:
                    self._stack.append(ret)
                i = len(self._stack)-1
            else:
                i -= 1

    def backward_pm(self):
        self._stack.append(PlaceModifier.backward)

    def cb(self, key, command):
        super(concat_keybindings, self).bind(key, self.concat_bind(command))

    def concat_bind(self, command):
        def h(key):
            if self._quoting and key != b'"':
                from . import utils
                if utils.is_printable(key):
                    if not self._stack or self._stack[-1].is_final():
                        self._stack.append(String(key.decode('utf8')))
                    else:
                        s = self._stack.pop()
                        s = s.s + key.decode('utf8')
                        self._stack.append(String(s))
            else:
                if self._quoting:
                    self._stack[-1].finalize()
                fi = self.force_insert
                if fi:
                    return keybinding_table.MATCH_STATE.reject
                else:
                    try:
                        command()
                    except:
                        p = panes.focused.open_prompt(prompt.time_prompt, message='clearing stack', seconds=.3)
                        self.clear()
            if not self._stack:
                if self.for_window.pane.status_bar:
                    self.for_window.pane.status_bar.reset_default_text()
            else:
                if self.for_window.pane.status_bar:
                    self.for_window.pane.status_bar.set_status_text(' '.join(list(map(str, self._stack))))
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
        with self.for_window.column_save():
            self.beginning_pm()
            self.line()
            self.move()

    def times_default(self):
        self._stack.append(Times(4))

    def end(self):
        with self.for_window.column_save():
            self.end_pm()
            self.line()
            self.move()

    def next_line(self):
        with self.for_window.column_restore():
            self.line()
            self.move()
    def previous_line(self):
        with self.for_window.column_restore():
            if len(self._stack) > 0:
                if not callable(self._stack[-1]):
                    self.line()
                self._stack[-1](PlaceModifier.backward)
            else:
                self.backward_pm()
                self.line()
            self.move()

    def pop_graveyard(self):
        if len(self._graveyard) > 0:
            g = self._graveyard.pop()
            self.for_window.add_string(g)

    def move_me(self, what=None):
        if what is None:
            move.right()
        else:
            _, _, rb, cb = what()
            self.for_window.cursor = (rb, cb)
            if self._set_column:
                self.for_window.last_seeked_column = cb
            self._set_column = True

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

    def line(self):
        how_many = None
        forward = True
        cls = lines
        while self._stack:
            i = self._stack.pop(0)
            if isinstance(i, Times):
                how_many = i.i
            elif isinstance(i, whitespaces):
                how_many = i.how_many
                forward = i.forward
                cls = whitespace_lines
            elif i == PlaceModifier.backward:
                forward = False
            elif i == PlaceModifier.whole:
                cls = whole_lines
            elif i == PlaceModifier.beginning:
                cls = beginning_lines
            elif i == PlaceModifier.end:
                cls = end_lines
            elif i == PlaceModifier.absolute:
                cls = absolute_line
            else:
                raise Exception('unsupported previous stack entry')
        self._stack.append(cls(how_many, forward))

    def whitespace(self):
        how_many = 1
        forward = True
        while self._stack:
            i = self._stack.pop(0)
            if isinstance(i, Times):
                how_many = i.i
            elif i == PlaceModifier.backward:
                forward = False
            else:
                raise Exception('unsupported previous stack entry')
        self._stack.append(whitespaces(how_many, forward))

    def word(self):
        how_many = 1
        forward = True
        while self._stack:
            i = self._stack.pop(0)
            if isinstance(i, Times):
                how_many = i.i
            elif i == PlaceModifier.backward:
                forward = False
            else:
                raise Exception('unsupported previous stack entry')
        self._stack.append(words(how_many, forward))

    def character(self):
        how_many = 1
        forward = True
        while self._stack:
            i = self._stack.pop(0)
            if isinstance(i, Times):
                how_many = i.i
            elif i == PlaceModifier.backward:
                forward = False
            else:
                raise Exception('unsupported previous stack entry')
        self._stack.append(characters(how_many, forward))

    def move_absolute_line(self):
        with self.for_window.column_restore():
            self.absolute_pm()
            self.line()
            self.move()

    def backspace(self):
        self.backward_pm()
        self.delete()

    def window(self):
        self._stack.append(Place.window)
    def content(self):
        self._stack.append(Place.content)
    def beginning_pm(self):
        self._stack.append(PlaceModifier.beginning)
    def whole_pm(self):
        self._stack.append(PlaceModifier.whole)
    def end_pm(self):
        self._stack.append(PlaceModifier.end)
    def absolute_pm(self):
        self._stack.append(PlaceModifier.absolute)

    def clear(self):
        self._stack = []

    def times(self, i):
        if not self._stack:
            self._stack.append(Times(i))
        else:
            if isinstance(self._stack[-1], Times):
                n = self._stack.pop().i
                n *= 10
                n += i
            else:
                n = i
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

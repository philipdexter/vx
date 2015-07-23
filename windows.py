import vx
import undo

import math
import contextlib
import traceback
import sys
from functools import partial, wraps
from io import StringIO
from os.path import isfile

def _seek_setting(f):
    @wraps(f)
    def g(*args, **kwargs):
        ret = f(*args, **kwargs)
        _, _focused_window.last_seeked_column = vx.get_linecol_window(_focused_window)
        return ret
    return g
def _seek_preserving(f):
    @wraps(f)
    def g(*args, **kwargs):
        ret = f(*args, **kwargs)
        _, c = vx.get_linecol_window(_focused_window)
        if c < _focused_window.last_seeked_column:
            vx.move_eol_window(_focused_window)
            _, c = vx.get_linecol_window(_focused_window)
            if _focused_window.last_seeked_column < c:
                vx.repeat(vx.move_left, c - _focused_window.last_seeked_column)
        return ret
    return g

_windows = []
_windows_traversable = []
_focused_window = None
vx.get_focused_window = lambda: _focused_window

class _graffiti:
    def __init__(self, y, x, text):
        self.y = y
        self.x = x
        self.text = text

    def render(self, window):
        vx.set_cursor(window, self.y, self.x)
        vx.print_string_window(window, self.text)

@vx.expose
class _window:
    def __init__(self, rows, columns, y, x, traversable=True, status_bar=True):
        self._c_window = vx.new_window(rows-1, columns, y, x)
        self.graffitis = []
        self.line = 1
        self.col = 1

        self.last_seeked_column = 0

        self.rows = rows
        self.columns = columns
        self.y = y
        self.x = x

        self.has_contents = False
        self.dirty = False

        self.keybinding_table = vx.keybinding_table()
        _windows.append(self)
        _windows.sort(key=lambda w: w.y)
        self.traversable = traversable
        if traversable:
            _windows_traversable.append(self)
            _windows_traversable.sort(key=lambda w: w.y)

        if status_bar:
            self.status_bar = vx.window(1, columns, y + rows - 1, x, traversable=False, status_bar=False)
            self.status_bar.blank()
            self.status_bar.set_color(5, -1)
        else:
            self.status_bar = None

    def add_string(self, s, track=True):
        vx.add_string_window(self, s)
        if track:
            self.dirty = True
            undo.register_change(s)

    def remove(self):
        _windows.remove(self)
        if self.traversable:
            _windows_traversable.remove(self)
        vx.delete_window(self)

    def resize(self, lines, columns):
        self.rows = lines
        self.columns = columns
        vx.resize_window(self, lines, columns)
        if self.status_bar:
            vx.resize_window(self, lines - 1, columns)
            self.status_bar.resize(1, columns)
            self.status_bar.move(self.y + self.rows - 1, self.x)

    def pad(self, top=0, bottom=0, left=0, right=0):
        if top > 0 or left > 0:
            self.resize(self.rows - top, self.columns - left)
            self.move(self.y + top, self.x + left)
        if bottom > 0 or right > 0:
            self.resize(self.rows - (bottom + top), self.columns - (right + left))
            if self.status_bar:
                self.status_bar.move(self.y + self.rows - 1, self.x)
        vx.redraw_all()

    def grow(self, top=0, bottom=0, left=0, right=0):
        if top > 0 or left > 0:
            self.move(self.y - top, self.x - left)
            self.resize(self.rows + top, self.columns + left)
        if bottom > 0 or right > 0:
            self.resize(self.rows + (bottom + top), self.columns + (right + left))
        vx.redraw_all()

    def move(self, y, x):
        self.y = y
        self.x = x
        vx.move_window(self, y, x)
        if self.status_bar:
            self.status_bar.move(y + self.rows - 1, x)

    def set_text(self, text):
        self.murals = []
        self.graffitis.append(_graffiti(0, 0, text))

    def blank(self):
        self.has_contents = True
        vx.attach_window_blank(self)

    def focus(self):
        global _focused_window
        if _focused_window:
            _focused_window.unfocus()
        _focused_window = self
        vx.keybinding_tables.insert(0, self.keybinding_table)
        vx.focus_window(self)

    def unfocus(self):
        vx.keybinding_tables.remove(self.keybinding_table)

    def prepare(self):
        vx.clear_window(self)
        vx.set_cursor(self, 0, 0)
        self.line, self.col = vx.get_linecol_window(self)
        if self.status_bar:
            self.status_bar.set_text('line: {} col: {} - {}{}\n'.format(self.line,
                                                                        self.col,
                                                                        self.filename if hasattr(self, 'filename') else '<none>',
                                                                        '(d)' if self.dirty else ''))

    def refresh(self):
        vx.refresh_window(self)

    def render(self):
        if self.has_contents:
            contents = vx.get_contents_window(self)
            r, c = vx.get_linecol_start_window(self)
            y, x = vx.get_window_size(self)

            lines = contents.split('\n')[r-1:r+y-1]

            for i, line in enumerate(lines):
                line = line.replace('\t', '        ')[c-1:c-1+x-2]
                if len(line) == x - 2:
                    line += '$'
                if c-1 > 0:
                    line = '$' + line[1:]
                vx.print_string_window(self, line)
                vx.print_string_window(self, '\n')
        for m in self.graffitis:
            m.render(self)

    def update(self):
        self.prepare()
        self.render()
        self.refresh()

    def set_cursor(self, y, x):
        vx.set_cursor(self, y, x)

    def set_color(self, fg, bg):
        vx.set_color_window(self, fg, bg)

    def attach_file(self, filename):
        self.filename = filename
        vx.attach_window(self, filename)
        self.has_contents = True

    def split_h(self):
        split_height = math.floor(self.rows / 2)
        split_width = self.columns
        self.resize(split_height, self.columns)
        new = _window(split_height, split_width, self.y + split_height, self.x)
        new.blank() #attach_file('README.md')
        new.focus()
        return new

    def split_v(self):
        split_height = self.rows
        split_width = math.floor(self.columns / 2)
        self.resize(split_height, split_width)
        new = _window(split_height, split_width, self.y, self.x + split_width)
        new.blank() #attach_file('README.md')
        new.focus()
        return new

@vx.expose
def _split_h():
    _focused_window.split_h()
@vx.expose
def _split_v():
    _focused_window.split_v()

def _focus_window(window):
    _windows_traversable[_windows_traversable.index(window)].focus()

@vx.expose
def _next_window():
    if _focused_window is None:
        return
    current = _windows_traversable.index(_focused_window)
    after = current + 1
    if after == len(_windows_traversable):
        after = 0
    _windows_traversable[after].focus()

def _tick():
    for w in _windows:
        w.update()
vx.register_tick_function(_tick)

@vx.expose
def _close_window():
    w = _focused_window
    _next_window()
    w.remove()

@vx.expose
class _prompt(_window):
    _history = []

    def __init__(self, attached_to=None):
        if attached_to is None:
            attached_to = vx.get_focused_window()
        super(_prompt, self).__init__(2, attached_to.columns,
                                      attached_to.y + attached_to.rows-1, attached_to.x,
                                      status_bar=False)
        attached_to.pad(bottom=1)
        self.blank()
        self.focus()

        def expand():
            attached_to.pad(bottom=1)
            self.grow(top=1)

        @contextlib.contextmanager
        def stdoutIO(stdout=None):
            old = sys.stdout
            if stdout is None:
                stdout = StringIO()
            sys.stdout = stdout
            yield stdout
            sys.stdout = old

        def getout():
            y, x = vx.get_window_size(self)
            attached_to.grow(bottom=y)
            _focus_window(attached_to)
            contents = vx.get_contents_window(self)
            _prompt._history.append(contents)
            with stdoutIO() as s:
                try:
                    exec(contents)
                except Exception as e:
                    tb = traceback.format_exc()
                else:
                    tb = None
            s = s.getvalue()
            if len(s) > 0 or tb:
                split = vx.get_focused_window().split_h()
                split.focus()
                if not tb:
                    vx.add_string(s)
                else:
                    vx.add_string(tb)
            self.remove()

        def cancel():
            y, x = vx.get_window_size(self)
            attached_to.grow(bottom=y)
            _focus_window(attached_to)
            self.remove()
        self.keybinding_table.bind(vx.ctrl + vx.keys.g, cancel)

        def _history_pullback(): # TODO create clear_contents_window
            if len(_prompt._history) > 0:
                vx.add_string(_prompt._history[-1])
        self.keybinding_table.bind(vx.alt + vx.keys.p, _history_pullback)

        self.keybinding_table.bind(vx.keys.enter, getout)
        def _enter_and_expand():
            expand()
            vx.add_string('\n')
        self.keybinding_table.bind(vx.ctrl + vx.keys.j, _enter_and_expand)

@vx.expose
class _file_prompt(_window):
    _history = []

    def __init__(self, attached_to=None):
        if attached_to is None:
            attached_to = vx.get_focused_window()
        super(_file_prompt, self).__init__(2, attached_to.columns,
                                      attached_to.y + attached_to.rows-1, attached_to.x,
                                      status_bar=False)
        attached_to.pad(bottom=1)
        self.blank()
        self.focus()

        @contextlib.contextmanager
        def stdoutIO(stdout=None):
            old = sys.stdout
            if stdout is None:
                stdout = StringIO()
            sys.stdout = stdout
            yield stdout
            sys.stdout = old

        def getout():
            y, x = vx.get_window_size(self)
            attached_to.grow(bottom=y)
            _focus_window(attached_to)
            contents = vx.get_contents_window(self)
            _file_prompt._history.append(contents)
            if isfile(contents):
                _focused_window.attach_file(contents)
            else:
                split = vx.get_focused_window().split_h()
                split.focus()
                vx.add_string('file "{}" does not exist'.format(contents))
            self.remove()

        def cancel():
            y, x = vx.get_window_size(self)
            attached_to.grow(bottom=y)
            _focus_window(attached_to)
            self.remove()
        self.keybinding_table.bind(vx.ctrl + vx.keys.g, cancel)

        def _history_pullback(): # TODO create clear_contents_window
            if len(_file_prompt._history) > 0:
                vx.add_string(_file_prompt._history[-1])
        self.keybinding_table.bind(vx.alt + vx.keys.p, _history_pullback)

        self.keybinding_table.bind(vx.keys.enter, getout)

# Exposed functions

@vx.expose
@_seek_preserving
def _move_up():
    vx.move_up_window(_focused_window)
@vx.expose
@_seek_preserving
def _move_down():
    vx.move_down_window(_focused_window)
@vx.expose
@_seek_setting
def _move_left():
    vx.move_left_window(_focused_window)
@vx.expose
@_seek_setting
def _move_right():
    vx.move_right_window(_focused_window)

@vx.expose
@_seek_setting
def _move_eol():
    vx.move_eol_window(_focused_window)
@vx.expose
@_seek_setting
def _move_bol():
    vx.move_bol_window(_focused_window)

@vx.expose
@_seek_setting
def _move_beg():
    vx.move_beg_window(_focused_window)
@vx.expose
@_seek_setting
def _move_end():
    vx.move_end_window(_focused_window)

@vx.expose
def _center():
    r, c = vx.get_window_size(_focused_window)
    y, x = vx.get_linecol_window(_focused_window)
    new_top = max(y - r // 2, 1)
    vx.set_linecol_start_window(_focused_window,  new_top, x)

@vx.expose
@_seek_setting
def _add_string(s, **kwargs):
    _focused_window.add_string(s, **kwargs)
@vx.expose
@_seek_setting
def _backspace(track=True):
    if track:
        _focused_window.dirty = True
        r, c = vx.get_linecol_window(_focused_window)
        if r > 1 or c > 1:
            c = c - 1
            if c == 0:
                r -= 1
                _move_up()
                _move_eol()
                _, c = vx.get_linecol_window(_focused_window)
                _move_down()
                _move_bol()
            ch = vx.get_ch_linecol_window(_focused_window, r, c)
            undo.register_removal(ch, r, c)
    vx.backspace_window(_focused_window)
@vx.expose
@_seek_setting
def _delete(track=True):
    if track:
        _focused_window.dirty = True
        r, c = vx.get_linecol_window(_focused_window)
        ch = vx.get_ch_linecol_window(_focused_window, r, c)
        undo.register_removal(ch, r, c, hold=True)
    vx.backspace_delete_window(_focused_window)

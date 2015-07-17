import vx
import math
import contextlib
import traceback
from functools import partial, wraps
from io import StringIO

import sys

_last_seeked_column = 0
def _seek_setting(f):
    @wraps(f)
    def g(*args, **kwargs):
        global _last_seeked_column
        ret = f(*args, **kwargs)
        _, _last_seeked_column = vx.get_linecol_window(_focused_window._c_window)
        return ret
    return g
def _seek_preserving(f):
    @wraps(f)
    def g(*args, **kwargs):
        ret = f(*args, **kwargs)
        _, c = vx.get_linecol_window(_focused_window._c_window)
        if c < _last_seeked_column:
            vx.move_eol_window(_focused_window._c_window)
            _, c = vx.get_linecol_window(_focused_window._c_window)
            if _last_seeked_column < c:
                vx.repeat(vx.move_left, c - _last_seeked_column)
        return ret
    return g

_windows = []
_windows_traversable = []
_focused_window = None

class _graffiti:
    def __init__(self, y, x, text):
        self.y = y
        self.x = x
        self.text = text

    def render(self, window):
        vx.set_cursor(window._c_window, self.y, self.x)
        vx.print_string_window(window._c_window, self.text)

class _window:
    def __init__(self, rows, columns, y, x, traversable=True, status_bar=True):
        self._c_window = vx.new_window(rows-1, columns, y, x)
        self.graffitis = []
        self.line = 1
        self.col = 1

        self.rows = rows
        self.columns = columns
        self.y = y
        self.x = x

        self.has_contents = False
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

    def add_string(self, s):
        vx.add_string_window(self._c_window, s)

    def remove(self):
        _windows.remove(self)
        if self.traversable:
            _windows_traversable.remove(self)
        vx.delete_window(self._c_window)

    def resize(self, lines, columns):
        self.rows = lines
        self.columns = columns
        vx.resize_window(self._c_window, lines, columns)
        if self.status_bar:
            vx.resize_window(self._c_window, lines - 1, columns)
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
        vx.move_window(self._c_window, y, x)
        if self.status_bar:
            self.status_bar.move(y + self.rows - 1, x)

    def set_text(self, text):
        self.murals = []
        self.graffitis.append(_graffiti(0, 0, text))

    def blank(self):
        self.has_contents = True
        vx.attach_window_blank(self._c_window)

    def focus(self):
        global _focused_window
        if _focused_window:
            _focused_window.unfocus()
        _focused_window = self
        vx.keybinding_tables.insert(0, self.keybinding_table)
        vx.focus_window(self._c_window)

    def unfocus(self):
        vx.keybinding_tables.remove(self.keybinding_table)

    def prepare(self):
        vx.clear_window(self._c_window)
        vx.set_cursor(self._c_window, 0, 0)
        self.line, self.col = vx.get_linecol_window(self._c_window)
        if hasattr(self, 'status_bar'):
            self.status_bar.set_text('line: {} col: {} - {}\n'.format(self.line,
                                                                      self.col,
                                                                      self.filename if hasattr(self, 'filename') else '<none>'))

    def refresh(self):
        vx.refresh_window(self._c_window)

    def render(self):
        if self.has_contents:
            contents = vx.get_contents_window(self._c_window)
            vx.print_string_window(self._c_window, contents)
        for m in self.graffitis:
            m.render(self)

    def update(self):
        self.prepare()
        self.render()
        self.refresh()

    def set_cursor(self, y, x):
        vx.set_cursor(self._c_window, y, x)

    def set_color(self, fg, bg):
        vx.set_color_window(self._c_window, fg, bg)

    def attach_file(self, filename):
        self.filename = filename
        vx.attach_window(self._c_window, filename)
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
        self.resize(split_height, self.columns)
        new = _window(split_height, split_width, self.y, self.x + split_width)
        new.blank() #attach_file('README.md')
        new.focus()
        return new

def _focus_window(window):
    _windows_traversable[_windows_traversable.index(window)].focus()

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

vx.window = _window
vx.graffiti = _graffiti
vx.next_window = _next_window
vx.get_focused_window = lambda: _focused_window

def _close_window():
    w = _focused_window
    _next_window()
    w.remove()
vx.close_window = _close_window

class _prompt(_window):
    def __init__(self, attached_to):
        super(_prompt, self).__init__(2, attached_to.columns,
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
            attached_to.grow(bottom=1)
            _focus_window(attached_to)
            contents = vx.get_contents_window(self._c_window)
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
        self.keybinding_table.bind(vx.keys.enter, getout)
        def _enter_and_expand():
            expand()
            vx.add_string('\n')
        self.keybinding_table.bind(vx.ctrl + vx.keys.j, _enter_and_expand)

vx.prompt = _prompt

@_seek_preserving
def _move_up():
    vx.move_up_window(_focused_window._c_window)
vx.move_up = _move_up
@_seek_preserving
def _move_down():
    vx.move_down_window(_focused_window._c_window)
vx.move_down = _move_down
@_seek_setting
def _move_left():
    vx.move_left_window(_focused_window._c_window)
vx.move_left = _move_left
@_seek_setting
def _move_right():
    vx.move_right_window(_focused_window._c_window)
vx.move_right = _move_right
@_seek_setting
def _move_eol():
    vx.move_eol_window(_focused_window._c_window)
vx.move_eol = _move_eol
@_seek_setting
def _move_bol():
    vx.move_bol_window(_focused_window._c_window)
vx.move_bol = _move_bol
@_seek_setting
def _move_beg():
    vx.move_beg_window(_focused_window._c_window)
vx.move_beg = _move_beg
@_seek_setting
def _move_end():
    vx.move_end_window(_focused_window._c_window)
vx.move_end = _move_end

def _add_string(s):
    _focused_window.add_string(s)
vx.add_string = _add_string
def _backspace():
    vx.backspace_window(_focused_window._c_window)
vx.backspace = _backspace
def _delete():
    vx.backspace_delete_window(_focused_window._c_window)
vx.delete = _delete

import vx
import undo

import math
from functools import partial, wraps

def _seek_setting(f):
    @wraps(f)
    def g(*args, **kwargs):
        ret = f(*args, **kwargs)
        _, _window.focused_window.last_seeked_column = vx.get_linecol_window(_window.focused_window)
        return ret
    return g
def _seek_preserving(f):
    @wraps(f)
    def g(*args, **kwargs):
        ret = f(*args, **kwargs)
        _, c = vx.get_linecol_window(_window.focused_window)
        if c < _window.focused_window.last_seeked_column:
            vx.move_eol_window(_window.focused_window)
            _, c = vx.get_linecol_window(_window.focused_window)
            if _window.focused_window.last_seeked_column < c:
                vx.repeat(vx.move_left, c - _window.focused_window.last_seeked_column)
        return ret
    return g

_windows = []
_windows_traversable = []

class _graffiti:
    def __init__(self, y, x, text):
        self.y = y
        self.x = x
        self.text = text

    def render(self, window):
        vx.set_cursor(window, self.y, self.x)
        vx.print_string_window(window, self.text)

class _window_meta(type):
    _focused_window = None

    def __get_focused_window(self):
        return _window_meta._focused_window

    def __set_focused_window(self, w):
        _window_meta._focused_window = w

    focused_window = property(__get_focused_window, __set_focused_window)

@vx.expose
class _window(metaclass=_window_meta):
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

        self.parent = None
        self.children = []

        self.traversable = traversable
        if traversable:
            _windows_traversable.append(self)
            _windows_traversable.sort(key=lambda w: w.y)

        if status_bar:
            self.status_bar = vx.window(1, columns, y + rows - 1, x, traversable=False, status_bar=False)
            self.status_bar.blank()
            self.status_bar.set_color(5, -1)
            self.status_bar_text = lambda window: 'line: {} col: {} - {}{}\n'.format(window.line,
                                                                                     window.col,
                                                                                     window.filename if hasattr(window, 'filename') else '<none>',
                                                                                     '(d)' if window.dirty else '')
        else:
            self.status_bar = None

    def save(self):
        vx.save_window(self)
        self.dirty = False

    @_seek_setting
    def set_linecol(self, row, col):
        vx.set_linecol_window(self, row, col)

    def set_start_linecol(self, row, col):
        vx.set_linecol_start_window(self,  row, col)

    def add_string(self, s, track=True):
        vx.add_string_window(self, s)
        if track:
            self.dirty = True
            undo.register_change(s)

    def remove(self, force=False):
        if not force and self.dirty:
            vx.yn_prompt('Window is dirty, really close?', partial(self.remove, force=True), None)
            return
        y, x = vx.get_window_size(self)
        if self.parent:
            if len(self.children) == 0:
                dy = self.y - self.parent.y
                dx = self.x - self.parent.x
                y += 1 if self.parent.status_bar is not None else 0
                if dy > 0:
                    self.parent.grow(bottom=y)
                if dx > 0:
                    self.parent.grow(right=x)
            else:
                for c in self.children:
                    c.parent = self.parent
                    self.parent.children.append(c)
                dy = self.children[0].y - self.y
                dx = self.children[0].x - self.x
                y += 1 if self.children[0].status_bar is not None else 0
                if dy > 0:
                    self.children[0].grow(top=y)
                if dx > 0:
                    self.children[0].grow(left=x)
            self.parent.children.remove(self)
            self.parent.focus()
        _windows.remove(self)
        if self.traversable:
            _windows_traversable.remove(self)
        vx.delete_window(self)
        if self.status_bar is not None:
            self.status_bar.remove()
        # quit editor if there are no more windows
        if len(_windows_traversable) == 0:
            # create new blank window so we don't crash
            # TODO fix c code so we don't need this
            new = _window(1, 1, 1, 1)
            new.blank()
            new.focus()
            vx.quit()

    def resize(self, lines, columns):
        self.rows = lines
        self.columns = columns
        vx.resize_window(self, lines, columns)
        if self.status_bar:
            vx.resize_window(self, lines - 1, columns)
            self.status_bar.move(self.y + self.rows - 1, self.x)
            self.status_bar.resize(1, columns)

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
        self.graffitis = []
        self.graffitis.append(_graffiti(0, 0, text))

    def set_status_bar_text(self, text):
        if callable(text):
            self.status_bar_text = text
        else:
            self.status_bar_text = lambda _: text

    def blank(self):
        self.has_contents = True
        vx.attach_window_blank(self)

    def focus(self):
        if _window.focused_window:
            _window.focused_window.unfocus()
        _window.focused_window = self
        vx.keybinding_tables.insert(0, self.keybinding_table)
        vx.focus_internal_window(self)

    def unfocus(self):
        vx.keybinding_tables.remove(self.keybinding_table)

    def prepare(self):
        vx.clear_window(self)
        vx.set_cursor(self, 0, 0)
        self.line, self.col = vx.get_linecol_window(self)
        if self.status_bar:
            self.status_bar.set_text(self.status_bar_text(self))

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
        self.resize(split_height, split_width)
        new = _window(split_height, split_width, self.y + split_height, self.x)
        new.parent = self
        self.children.append(new)
        new.blank()
        new.focus()
        return new

    def split_v(self):
        split_height = self.rows
        split_width = math.floor(self.columns / 2)
        self.resize(split_height, split_width)
        new = _window(split_height, split_width, self.y, self.x + split_width)
        new.parent = self
        self.children.append(new)
        new.blank()
        new.focus()
        return new

@vx.expose
def _split_h():
    _window.focused_window.split_h()
@vx.expose
def _split_v():
    _window.focused_window.split_v()

@vx.expose
def _focus_window(window):
    _windows_traversable[_windows_traversable.index(window)].focus()

@vx.expose
def _next_window():
    if _window.focused_window is None:
        return
    current = _windows_traversable.index(_window.focused_window)
    after = current + 1
    if after == len(_windows_traversable):
        after = 0
    _windows_traversable[after].focus()

def _tick():
    for w in _windows:
        w.update()
vx.register_tick_function(_tick, front=True)

@vx.expose
def _close_window():
    w = _window.focused_window
    _next_window()
    w.remove()

# Exposed functions

@vx.expose
@_seek_preserving
def _move_up():
    vx.move_up_window(_window.focused_window)
@vx.expose
@_seek_preserving
def _move_down():
    vx.move_down_window(_window.focused_window)
@vx.expose
@_seek_setting
def _move_left():
    vx.move_left_window(_window.focused_window)
@vx.expose
@_seek_setting
def _move_right():
    vx.move_right_window(_window.focused_window)

@vx.expose
@_seek_setting
def _move_eol():
    vx.move_eol_window(_window.focused_window)
@vx.expose
@_seek_setting
def _move_bol():
    vx.move_bol_window(_window.focused_window)

@vx.expose
@_seek_setting
def _move_beg():
    vx.move_beg_window(_window.focused_window)
@vx.expose
@_seek_setting
def _move_end():
    vx.move_end_window(_window.focused_window)

@vx.expose
def _center():
    r, c = vx.get_window_size(_window.focused_window)
    y, x = vx.get_linecol_window(_window.focused_window)
    new_top = max(y - r // 2, 1)
    _window.focused_window.set_start_linecol(new_top, x)

@vx.expose
@_seek_setting
def _add_string(s, **kwargs):
    _window.focused_window.add_string(s, **kwargs)
@vx.expose
@_seek_setting
def _backspace(track=True):
    if track:
        _window.focused_window.dirty = True
        r, c = vx.get_linecol_window(_window.focused_window)
        if r > 1 or c > 1:
            c = c - 1
            if c == 0:
                r -= 1
                _move_up()
                _move_eol()
                _, c = vx.get_linecol_window(_window.focused_window)
                _move_down()
                _move_bol()
            ch = vx.get_ch_linecol_window(_window.focused_window, r, c)
            undo.register_removal(ch, r, c)
    vx.backspace_window(_window.focused_window)
@vx.expose
@_seek_setting
def _delete(track=True):
    if track:
        _window.focused_window.dirty = True
        r, c = vx.get_linecol_window(_window.focused_window)
        ch = vx.get_ch_linecol_window(_window.focused_window, r, c)
        undo.register_removal(ch, r, c, hold=True)
    vx.backspace_delete_window(_window.focused_window)

@vx.expose
@_seek_setting
def _kill_to_end():
    (l, c, o) = vx.get_linecoloffset_of_str(_window.focused_window, '\n')
    y, x = vx.get_linecol_window(_window.focused_window)
    if o == 0:
        o += 1
    if o == -1:
        _move_eol()
        _, end = vx.get_linecol_window(_window.focused_window)
        vx.set_linecol_window(_window.focused_window, y, x)
        o = end - x
    removed_text = vx.get_str_linecol_window(_window.focused_window, y, x, o)
    vx.repeat(partial(vx.backspace_delete_window, _window.focused_window), times=o)
    undo.register_removal(removed_text, y, x, hold=True)
    _window.focused_window.dirty = True

@vx.expose
@_seek_setting
def _kill_to_forward():
    breaks = ('_', ' ', '\n')
    offsets = []
    for s in breaks:
        (l, c, o) = vx.get_linecoloffset_of_str(_window.focused_window, s)
        if o == -1:
            continue
        if o == 0 and s != '\n':
            vx.move_right()
            (l, c, o) = vx.get_linecoloffset_of_str(_window.focused_window, s)
            o += 1
            vx.move_left()
        offsets.append(o)
    if o == 0:
        _kill_to_end()
        return
    y, x = vx.get_linecol_window(_window.focused_window)
    if len(offsets) == 0:
        _kill_to_end()
        return
    o = min(offsets)
    removed_text = vx.get_str_linecol_window(_window.focused_window, y, x, o)
    vx.repeat(partial(vx.backspace_delete_window, _window.focused_window), times=o)
    undo.register_removal(removed_text, y, x, hold=True)
    _window.focused_window.dirty = True

@vx.expose
@_seek_setting
def _kill_to_backward():
    breaks = ('_', ' ', '\n')
    offsets = []
    for s in breaks:
        (l, c, o) = vx.get_linecoloffset_of_str(_window.focused_window, s, 0)
        if o == -1:
            continue
        if o == 0 and s != '\n':
            vx.move_left()
            (l, c, o) = vx.get_linecoloffset_of_str(_window.focused_window, s, 0)
            o += 1
            vx.move_right()
        offsets.append(o)
    if o == 0:
        vx.backspace()
        return
    y, x = vx.get_linecol_window(_window.focused_window)
    if len(offsets) == 0:
        o = x
    else:
        o = min(offsets)
    removed_text = vx.get_str_linecol_window(_window.focused_window, y, x, o, 0)
    vx.repeat(partial(vx.backspace_window, _window.focused_window), times=o)
    y, x = vx.get_linecol_window(_window.focused_window)
    undo.register_removal(removed_text, y, x, hold=False)
    _window.focused_window.dirty = True

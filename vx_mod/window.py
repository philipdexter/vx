import vx
import vx_mod.utils
import vx_mod.undo as undo
import vx_mod.mode as mode

import math
import traceback
from functools import partial, wraps

class _graffiti:
    def __init__(self, y, x, text):
        self.y = y
        self.x = x
        self.text = text

    def render(self, window):
        vx.set_cursor(window, self.y, self.x)
        vx.print_string_window(window, self.text)

class _window_meta(type):
    _focused = None
    _windows = []
    _traversable = []

    def __get_focused(self):
        return _window_meta._focused

    def __set_focused(self, w):
        _window_meta._focused = w

    def __get_windows(self):
        return _window_meta._windows

    def __get_traversable(self):
        return _window_meta._traversable

    def __iter__(self):
        return iter(self.windows)

    focused = property(__get_focused, __set_focused)
    windows = property(__get_windows)
    traversable = property(__get_traversable)

class windows(metaclass=_window_meta):
    @staticmethod
    def append(item):
        windows.windows.append(item)

    @staticmethod
    def sort(*args, **kwargs):
        windows.windows.sort(*args, **kwargs)

    @staticmethod
    def remove(*args, **kwargs):
        windows.windows.remove(*args, **kwargs)

class window:
    def __init__(self, rows, columns, y, x, starting_mode=None, traversable=True, status_bar=True):
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

        if vx.default_keybindings is not None:
            self.keybinding_table = vx.default_keybindings(self)
        else:
            self.keybinding_table = vx.keybinding_table()
        windows.append(self)
        windows.sort(key=lambda w: w.y)

        self.parent = None
        self.children = []

        self.traversable = traversable
        if traversable:
            windows.traversable.append(self)
            windows.traversable.sort(key=lambda w: w.y)

        if status_bar:
            self.status_bar = vx.status_bar(self)
        else:
            self.status_bar = None

        self.color_tags = []

        self.mode = starting_mode(self) if starting_mode else mode.mode(self)

    def __get_cursor(self):
        return vx.get_linecol_window(self)
    def __set_cursor(self, linecol):
        line, col = linecol
        return vx.set_linecol_window(self, line, col)
    cursor = property(__get_cursor, __set_cursor)

    def __get_window_start(self):
        return vx.get_linecol_start_window(self)
    def __set_window_start(self, linecol):
        line, col = linecol
        return vx.set_linecol_start_window(self, line, col)
    topleft = property(__get_window_start, __set_window_start)

    def __get_contents(self):
        return vx.get_contents_window(self)
    contents = property(__get_contents)

    def ensure_visible(self, line, col):
        r, c = vx.get_window_size(self)
        y, x = line, col
        sy, sx = vx.get_linecol_start_window(self)
        # Check line
        if y < sy:
            sy = y - 6
        elif y > sy + r:
            sy = y + 6 - r
        # Check col
        if x < sx:
            sx = max(1, x - 6)
        elif x > sx + c:
            sx = x + 6 - c

        self.topleft = (sy, sx)

    def save(self):
        vx.save_window(self)
        self.dirty = False
        vx.time_prompt('saved {}'.format(self.filename))

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
        windows.remove(self)
        if self.traversable:
            windows.traversable.remove(self)
        vx.delete_window(self)
        if self.status_bar is not None:
            self.status_bar.remove()
        # quit editor if there are no more windows
        if len(windows.traversable) == 0:
            # create new blank window so we don't crash
            # TODO fix c code so we don't need this
            new = window(1, 1, 1, 1)
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
        #vx.redraw_all()

    def grow(self, top=0, bottom=0, left=0, right=0):
        if top > 0 or left > 0:
            self.move(self.y - top, self.x - left)
            self.resize(self.rows + top, self.columns + left)
        if bottom > 0 or right > 0:
            self.resize(self.rows + (bottom + top), self.columns + (right + left))
        #vx.redraw_all()

    def move(self, y, x):
        self.y = y
        self.x = x
        vx.move_window(self, y, x)
        if self.status_bar:
            self.status_bar.move(y + self.rows - 1, x)

    def set_text(self, text):
        self.graffitis = []
        self.graffitis.append(_graffiti(0, 0, text))

    def blank(self):
        self.has_contents = True
        vx.attach_window_blank(self)

    def focus(self):
        if windows.focused:
            windows.focused.unfocus()
        windows.focused = self
        vx.keybinding_tables.insert(0, self.keybinding_table)
        vx.focus_internal_window(self)

    def unfocus(self):
        vx.keybinding_tables.remove(self.keybinding_table)

    def prepare(self):
        vx.clear_window(self)
        vx.set_cursor(self, 0, 0)
        self.line, self.col = self.cursor
        if self.status_bar:
            self.status_bar.set_text(self.status_bar.text(self))

    def refresh(self):
        vx.refresh_window(self)

    def render(self):
        if self.has_contents:
            contents = self.contents
            r, c = vx.get_linecol_start_window(self)
            y, x = vx.get_window_size(self)

            lines = contents.split('\n')[r-1:r+y-1]

            cline = r
            ccol = c
            for i, line in enumerate(lines):
                line = line.replace('\t', '        ')[c-1:c-1+x-2]
                if len(line) == x - 2:
                    line += '$'
                if c-1 > 0:
                    line = '$' + line[1:]

                colored = False
                for ctl, ctc, ctlen, ctfg, ctbg in self.color_tags:
                    if cline == ctl:
                        ctc -= ccol - 1
                        colored = True
                        vx.print_string_window(self, line[:ctc-1])
                        self.set_color(ctfg, ctbg)
                        vx.print_string_window(self, line[ctc-1:ctc-1+ctlen])
                        self.set_color(-1, -1)
                        vx.print_string_window(self, line[ctc-1+ctlen:])
                if not colored:
                    vx.print_string_window(self, line)
                vx.print_string_window(self, '\n')
                cline += 1
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

    def add_color_tag(self, l, c, length, fg, bg):
        self.color_tags.append((l, c, length, fg, bg))

    def attach_file(self, filename):
        self.filename = filename
        vx.attach_window(self, filename)
        self.has_contents = True
        m = mode.mode_from_filename(filename)
        if m:
            self.mode = m(self)

    def split_h(self):
        split_height = math.floor(self.rows / 2)
        split_width = self.columns
        self.resize(split_height, split_width)
        new = window(split_height, split_width, self.y + split_height, self.x)
        new.parent = self
        self.children.append(new)
        new.blank()
        new.focus()
        return new

    def split_v(self):
        split_height = self.rows
        split_width = math.floor(self.columns / 2)
        self.resize(split_height, split_width)
        new = window(split_height, split_width, self.y, self.x + split_width)
        new.parent = self
        self.children.append(new)
        new.blank()
        new.focus()
        return new

def _next_window():
    if windows.focused is None:
        return
    current = windows.traversable.index(windows.focused)
    after = current + 1
    if after == len(windows.traversable):
        after = 0
    windows.traversable[after].focus()

def _tick():
    for w in windows:
        w.update()
vx.register_tick_function(_tick)#, front=True)

def close_window():
    w = windows.focused
    _next_window()
    w.remove()

def center():
    r, c = vx.get_window_size(windows.focused)
    y, _ = windows.focused.cursor
    _, x = vx.get_linecol_start_window(windows.focused)
    new_top = max(y - r // 2, 1)
    windows.focused.topleft = (new_top, x)

def execute_window():
    contents = vx.windows.focused.contents
    with vx_mod.utils.stdoutIO() as s:
        try:
            exec(contents)
        except Exception as e:
            tb = traceback.format_exc()
        else:
            tb = None
    s = s.getvalue()
    if len(s) > 0 or tb:
        split = vx.windows.focused.split_h()
        split.focus()
        if not tb:
            vx.add_string(s)
        else:
            vx.add_string(tb)

def _resize_handler():
    for w in _windows:
        w.resize(w.rows, vx.cols)

vx.resize_handler = _resize_handler

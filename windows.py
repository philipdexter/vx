import vx
import math

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
        vx.add_string_window(window._c_window, self.text)

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
        if traversable:
            _windows_traversable.append(self)
            _windows_traversable.sort(key=lambda w: w.y)

        if status_bar:
            self.status_bar = vx.window(1, columns, y + rows - 1, x, traversable=False, status_bar=False)
            self.status_bar.blank()
            self.status_bar.set_color(5, -1)

    def remove(self):
        _windows.remove(self)
        vx.delete_window(self._c_window)

    def resize(self, lines, columns):
        self.rows = lines
        self.columns = columns
        vx.resize_window(self._c_window, lines, columns)
        if hasattr(self, 'status_bar'):
            vx.resize_window(self._c_window, lines - 1, columns)
            self.status_bar.resize(1, columns)
            self.status_bar.move(self.y + self.rows - 1, self.x)

    def move(self, y, x):
        self.y = y
        self.x = x
        vx.move_window(self._c_window, y, x)
        if hasattr(self, 'status_bar'):
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
            self.status_bar.set_text('line: {} col: {} / rows: {} cols: {}\n'.format(self.line,
                                                                                     self.col,
                                                                                     vx.rows,
                                                                                     vx.cols))

    def refresh(self):
        vx.refresh_window(self._c_window)

    def render(self):
        if self.has_contents:
            contents = vx.get_contents_window(self._c_window)
            vx.add_string_window(self._c_window, contents)
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

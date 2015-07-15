import vx

_windows = []
_windows_traversable = []

class _graffiti:
    def __init__(self, y, x, text):
        self.y = y
        self.x = x
        self.text = text

    def render(self, window):
        vx.set_cursor(window._c_window, self.y, self.x)
        vx.add_string_window(window._c_window, self.text)

class _window:
    def __init__(self, rows, columns, y, x, refresh=None, traversable=True, status_bar=True):
        self._c_window = vx.new_window(rows-1, columns, y, x)
        self.graffitis = []
        self.tick = None
        self.line = 1
        self.col = 1

        self.rows = rows
        self.y = y
        self.x = x

        self.has_file = False
        self.keybinding_table = vx.keybinding_table()
        if refresh is not None:
            self.tick = refresh
        _windows.append(self)
        if traversable:
            _windows_traversable.append(self)

        if status_bar:
            self.status_bar = vx.window(1, columns, y + rows - 1, x, traversable=False, status_bar=False)
            self.status_bar.blank()
            self.status_bar.set_color(5, -1)

    def remove(self):
        _windows.remove(self)
        vx.delete_window(self._c_window)

    def resize(self, lines, columns):
        self.rows = lines
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
        if self.has_file:
            contents = vx.get_contents_window(self._c_window)
            vx.add_string_window(self._c_window, contents)
        for m in self.graffitis:
            m.render(self)

    def update(self):
        self.prepare()
        if self.tick is not None:
            self.tick(self)
        self.render()
        self.refresh()

    def set_cursor(self, y, x):
        vx.set_cursor(self._c_window, y, x)

    def set_color(self, fg, bg):
        vx.set_color_window(self._c_window, fg, bg)

    def attach_file(self, filename):
        vx.attach_window(self._c_window, filename)
        self.has_file = True

_focused_window = None
_current_window = -1
def _next_window():
    global _current_window
    _current_window += 1
    if _current_window >= len(_windows_traversable):
        _current_window = 0
    _windows_traversable[_current_window].focus()

def _tick():
    for w in _windows:
        w.update()
vx.register_tick_function(_tick)

vx.window = _window
vx.graffiti = _graffiti
vx.next_window = _next_window

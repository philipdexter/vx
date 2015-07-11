import vx

class _window:
    def __init__(self, rows, columns, x, y):
        self._c_window = vx.new_window(rows, columns, x, y)

    def attach_file(self, filename):
        vx.attach_window(self._c_window, filename)

    def blank(self):
        vx.attach_window_blank(self._c_window)

    def focus(self):
        vx.focus_window(self._c_window)

    def update(self):
        vx.update_window(self._c_window)


_windows = []

_current_window = -1
def _next_window():
    global _current_window
    _current_window += 1
    if _current_window >= len(_windows):
        _current_window = 0
    _windows[_current_window].focus()

vx.windows = _windows
vx.window = _window
vx.next_window = _next_window

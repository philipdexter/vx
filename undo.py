import vx

_changes = []

def register_change(s):
    r, c = vx.get_linecol_window(vx.get_focused_window()._c_window)
    _changes.append({'string': s, 'row': r, 'col': c})

def _undo():
    if len(_changes) > 0:
        change = _changes.pop()
        vx.set_linecol_window(vx.get_focused_window()._c_window, change['row'], change['col'])
        vx.backspace()
vx.undo = _undo

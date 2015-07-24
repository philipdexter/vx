import vx

_changes = []

def register_change(s):
    r, c = vx.get_linecol_window(vx.get_focused_window()._c_window)
    _changes.append({'string': s, 'row': r, 'col': c, 'type': 'addition'})

def register_removal(s, r=None, c=None, hold=False):
    if r is None or c is None:
        r, c = vx.get_linecol_window(vx.get_focused_window()._c_window)
    _changes.append({'string': s, 'row': r, 'col': c, 'type': 'removal', 'hold': hold})

def _undo():
    if len(_changes) > 0:
        change = _changes.pop()
        if change['type'] == 'removal' and change['hold']:
            r, c = vx.get_linecol_window(vx.get_focused_window())
        vx.set_linecol_window(vx.get_focused_window()._c_window, change['row'], change['col'])
        if change['type'] == 'addition':
            vx.backspace(track=False)
        elif change['type'] == 'removal':
            vx.add_string(change['string'], track=False)
            if change['hold']:
                vx.set_linecol_window(vx.get_focused_window()._c_window, r, c)
        if len(_changes) == 0:
            vx.get_focused_window().dirty = False
vx.undo = _undo

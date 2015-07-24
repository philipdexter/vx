import vx

_changes = []

def register_change(s):
    r, c = vx.get_linecol_window(vx.window.focused_window)
    _changes.append({'string': s, 'row': r, 'col': c, 'type': 'addition'})

def register_removal(s, r=None, c=None, hold=False):
    if r is None or c is None:
        r, c = vx.get_linecol_window(vx.window.focused_window)
    _changes.append({'string': s, 'row': r, 'col': c, 'type': 'removal', 'hold': hold})

@vx.expose
def _undo():
    if len(_changes) > 0:
        change = _changes.pop()
        if change['type'] == 'removal' and change['hold']:
            r, c = vx.get_linecol_window(vx.window.focused_window)
        vx.window.focused_window.set_linecol(change['row'], change['col'])
        if change['type'] == 'addition':
            vx.backspace(track=False)
        elif change['type'] == 'removal':
            vx.add_string(change['string'], track=False)
            if change['hold']:
                vx.window.focused_window.set_linecol(r, c)
        if len(_changes) == 0:
            vx.window.focused_window.dirty = False

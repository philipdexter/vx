import vx
import vx_mod.text as text
import vx_mod.window

from collections import defaultdict

_changes = defaultdict(list)

def register_change(s):
    window = vx_mod.window.windows.focused
    r, c = window.cursor
    change_list = _changes[window]
    change_list.append({'string': s, 'row': r, 'col': c, 'type': 'addition'})

def register_removal(s, r=None, c=None, hold=False):
    window = vx_mod.window.windows.focused
    if r is None or c is None:
        r, c = window.cursor
    change_list = _changes[window]
    change_list.append({'string': s, 'row': r, 'col': c, 'type': 'removal', 'hold': hold})

def undo():
    window = vx_mod.window.windows.focused
    change_list = _changes[window]
    if len(change_list) > 0:
        change = change_list.pop()
        window.cursor = (change['row'], change['col'])
        if change['type'] == 'removal' and change['hold']:
            r, c = window.cursor
        if change['type'] == 'addition':
            for _ in range(len(change['string'])):
                text.backspace(track=False)
        elif change['type'] == 'removal':
            text.add_string(change['string'], track=False)
            if change['hold']:
                window.cursor = (r, c)
        if len(change_list) == 0:
            window.dirty = False

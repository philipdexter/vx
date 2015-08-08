import vx

from collections import defaultdict

_changes = defaultdict(list)

def register_change(s):
    r, c = vx.window.focused.cursor
    change_list = _changes[vx.window.focused]
    change_list.append({'string': s, 'row': r, 'col': c, 'type': 'addition'})

def register_removal(s, r=None, c=None, hold=False):
    if r is None or c is None:
        r, c = vx.window.focused.cursor
    change_list = _changes[vx.window.focused]
    change_list.append({'string': s, 'row': r, 'col': c, 'type': 'removal', 'hold': hold})

@vx.expose
def _undo():
    change_list = _changes[vx.window.focused]
    if len(change_list) > 0:
        change = change_list.pop()
        vx.window.focused.cursor = (change['row'], change['col'])
        if change['type'] == 'removal' and change['hold']:
            r, c = vx.window.focused.cursor
        if change['type'] == 'addition':
            for _ in range(len(change['string'])):
                vx.backspace(track=False)
        elif change['type'] == 'removal':
            vx.add_string(change['string'], track=False)
            if change['hold']:
                vx.window.focused.cursor = (r, c)
        if len(change_list) == 0:
            vx.window.focused.dirty = False

import vx
import vx_mod.window
import vx_mod.movement as move

def remove_text_linecol_to_linecol(rowa, cola, rowb, colb):
    # TODO inneficient, maybe implement this in C
    with vx.cursor_wander():
        window = vx_mod.window.windows.focused
        window.cursor = (rowb, colb)
        row, col = window.cursor
        while row != rowa or col != cola:
            backspace(track=False)
            row, col = window.cursor

def get_offsets_of(breaks, forward=True, ignore_pos=True, ignore_failed=True):
    if ignore_pos and forward:
        move.right()
    offsets = map(lambda s: (s, vx.get_linecoloffset_of_str(vx_mod.window.windows.focused, s, int(forward))[2]), breaks)
    offsets = list(map(lambda x: (x[0], x[1] + 1 if x[1] != -1 else x[1]), offsets)) if ignore_pos else offsets
    if ignore_pos and forward:
        move.left()
    return list(filter(lambda x: x[1] != -1, offsets) if ignore_failed else offsets)

def delete(track=True):
    window = vx_mod.window.windows.focused
    if track:
        window.dirty = True
        r, c = window.cursor
        ch = vx.get_ch_linecol_window(window, r, c)
        undo.register_removal(ch, r, c, hold=True)
    vx.backspace_delete_window(window)

def backspace(track=True):
    window = vx_mod.window.windows.focused
    if track:
        window.dirty = True
        r, c = window.cursor
        if r > 1 or c > 1:
            c = c - 1
            if c == 0:
                r -= 1
                move.up()
                move.eol()
                _, c = window.cursor
                move.down()
                move.bol()
            ch = vx.get_ch_linecol_window(window, r, c)
            if ch == '\t':
                c -= 7
            undo.register_removal(ch, r, c)
    vx.backspace_window(window)

def add_string(s, **kwargs):
    vx_mod.window.windows.focused.add_string(s, **kwargs)

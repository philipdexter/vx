import vx
import vx.window
import vx.movement as move
import vx.utils

import re
from functools import partial

def remove_text_linecol_to_linecol(rowa, cola, rowb, colb):
    """Removes all text between two points each specified as a row and column

    The removed text is not saved in the undo system.
    """
    # TODO inneficient, maybe implement this in C
    with vx.utils.cursor_wander():
        window = vx.window.windows.focused
        window.cursor = (rowb, colb)
        row, col = window.cursor
        while row != rowa or col != cola:
            backspace(track=False)
            row, col = window.cursor

def get_offsets_of(breaks, forward=True, ignore_pos=True, ignore_failed=True):
    """Returns a list of the offsets of each of the characters inside `breaks`

    :param forward: if False, search backwards
    :param ignore_pos: flag for ignoring the cursors current location
    :param ignore_failed: flag to prune characters that weren't found
    """
    if ignore_pos and forward:
        move.right()
    else:
        move.left()
    offsets = map(lambda s: (s, vx.get_linecoloffset_of_str(vx.window.windows.focused, s, int(forward))[2]), breaks)
    offsets = list(map(lambda x: (x[0], x[1] + 1 if x[1] != -1 else x[1]), offsets)) if ignore_pos else offsets
    if ignore_pos and forward:
        move.left()
    else:
        move.right()
    return list(filter(lambda x: x[1] != -1, offsets) if ignore_failed else offsets)

def delete(track=True):
    """Delete (the opposite direction of backspace) one character in the current window

    :param track: whether to track the action in the undo system
    """
    window = vx.window.windows.focused
    if track:
        window.dirty = True
        r, c = window.cursor
        ch = vx.get_ch_linecol_window(window, r, c)
        undo.register_removal(ch, r, c, hold=True)
    vx.backspace_delete_window(window)

def backspace(track=True):
    """Backspace one character in the current window

    :param track: whether to track the action in the undo system
    """
    window = vx.window.windows.focused
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
    """Add a string to the current window"""
    vx.window.windows.focused.add_string(s, **kwargs)

def find_regex(regex, window=None):
    if window is None:
        window = vx.window.windows.focused
    y, x = window.cursor
    contents = window.contents.split('\n')[y-1:]
    contents[0] = contents[0][x-1:]
    contents = '\n'.join(contents)
    try:
        rgx = re.compile(regex)
    except:
        return (0, 0, -1, 0)
    m = rgx.search(contents)
    if m:
        with vx.utils.cursor_wander():
            offset = m.start()
            vx.utils.repeat(partial(vx.move_right_window, window), times=offset)
            l, c = window.cursor
        return (l, c, offset, m.end() - m.start())
    else:
        return (0, 0, -1, 0)

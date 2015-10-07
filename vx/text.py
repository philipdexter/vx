import vx.movement as move
import vx.utils

from .pointer import windows

import re
from functools import partial

def regex_forward(window, regex):
    contents = window.get_contents_from_cursor()
    try:
        rgx = re.compile(regex, re.MULTILINE)
    except:
        return None
    return rgx.search(contents)

def regex_backward(window, regex):
    contents = window.get_contents_before_cursor()
    try:
        rgx = re.compile(regex, re.MULTILINE)
    except:
        return None
    results = list(rgx.finditer(contents))
    return results[-1] if results else None

def get_offset_regex(window, regex, forwards=True, ignore_pos=True):
    if ignore_pos:
        move.right(window) if forwards else move.left(window)
    m = regex_forward(window, regex) if forwards else regex_backward(window, regex)
    if m is None: return None
    if ignore_pos:
        move.left(window) if forwards else move.right(window)
    offset = m.start()
    if ignore_pos:
        offset += 1
    if not forwards:
        contents = window.get_contents_before_cursor()
        offset = len(contents) - offset
    return offset

def find_regex(regex, window=None, forwards=True):
    if window is None:
        window = windows.focused
    m = regex_forward(window, regex) if forwards else regex_backward(window, regex)
    if m:
        with window.cursor_wander():
            offset = m.start()
            if not forwards:
                contents = window.get_contents_before_cursor()
                offset = len(contents) - offset
            vx.utils.repeat(partial(move.right if forwards else move.left, window), times=offset)
            l, c = window.cursor
        return (l, c, offset, m.end() - m.start())
    else:
        return (0, 0, -1, 0)

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
    offsets = map(lambda s: (s, vx.get_linecoloffset_of_str(windows.focused, s, int(forward))[2]), breaks)
    offsets = list(map(lambda x: (x[0], x[1] + 1 if x[1] != -1 else x[1]), offsets)) if ignore_pos else offsets
    if ignore_pos and forward:
        move.left()
    else:
        move.right()
    return list(filter(lambda x: x[1] != -1, offsets) if ignore_failed else offsets)

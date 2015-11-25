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

def get_linecol_offset(text, forward=True):
    if forward:
        lines = text.count('\n')
        columns = text.rfind('\n')
        if columns == -1: columns = len(text)
        else: columns = len(text) - columns - 1
        return lines, columns
    else:
        lines = text.count('\n')
        columns = text.find('\n')
        if columns == -1: columns = len(text)
        return lines, columns

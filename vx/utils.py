import vx.window

from contextlib import contextmanager
from functools import partial

import sys
from io import StringIO

def repeat(c, times=4):
    res = []
    for _ in range(times):
        res.append(c())
    return res

@contextmanager
def cursor_wander(command=None, window=None):
    if window is None:
        window = vx.window.windows.focused
    y, x = window.cursor
    if command is not None:
        command()
    yp, xp = window.cursor
    yield (yp, xp)
    window.cursor = (y, x)

@contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

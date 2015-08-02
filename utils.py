import vx

from contextlib import contextmanager
from functools import partial

import sys
from io import StringIO

def _expose(f=None, name=None):
    if f is None:
        return partial(_expose, name=name)
    if name is None:
        name = f.__name__.lstrip('_')
    if getattr(vx, name, None) is not None:
        raise AttributeError("Cannot expose duplicate name: '{}'".format(name))
    setattr(vx, name, f)
    return f
vx.expose = _expose

@vx.expose
def _repeat(c, times=4):
    for _ in range(times):
        c()

@vx.expose
@contextmanager
def _cursor_wander(command=None, window=None):
    if window is None:
        window = vx.window.focused_window
    y, x = vx.get_linecol_window(window)
    if command is not None:
        command()
    yp, xp = vx.get_linecol_window(window)
    yield (yp, xp)
    vx.set_linecol_window(window, y, x)

@contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

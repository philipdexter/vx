import vx
import vx_mod.window

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
    res = []
    for _ in range(times):
        res.append(c())
    return res

@vx.expose
@contextmanager
def _cursor_wander(command=None, window=None):
    if window is None:
        window = vx_mod.window.windows.focused
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

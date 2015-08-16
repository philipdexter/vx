import vx.window

from .pointer import windows

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
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

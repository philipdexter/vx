import vx
from .pointer import windows

def up(window=None):
    vx.move_up_window(window if window else windows.focused)
def down(window=None):
    vx.move_down_window(window if window else windows.focused)
def left(window=None):
    vx.move_left_window(window if window else windows.focused)
def right(window=None):
    vx.move_right_window(window if window else windows.focused)

def eol(window=None):
    vx.move_eol_window(window if window else windows.focused)
def bol(window=None):
    vx.move_bol_window(window if window else windows.focused)

def beg(window=None):
    vx.move_beg_window(window if window else windows.focused)
def end(window=None):
    vx.move_end_window(window if window else windows.focused)

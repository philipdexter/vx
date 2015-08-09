import vx
import vx_mod.window

def up():
    vx.move_up_window(vx_mod.window.window.focused)
def down():
    vx.move_down_window(vx_mod.window.window.focused)
def left():
    vx.move_left_window(vx_mod.window.window.focused)
def right():
    vx.move_right_window(vx_mod.window.window.focused)

def eol():
    vx.move_eol_window(vx_mod.window.window.focused)
def bol():
    vx.move_bol_window(vx_mod.window.window.focused)

def beg():
    vx.move_beg_window(vx_mod.window.window.focused)
def end():
    vx.move_end_window(vx_mod.window.window.focused)

import vx
from vx.keybindings import bind, alt, ctrl, keys, keybinding_table
import vx.movement as move

def load(window):
    return barebones_keybindings(window)

class barebones_keybindings(keybinding_table):
    def __init__(self, for_window):
        super(barebones_keybindings, self).__init__()

        self.for_window = for_window

        self.bind(ctrl + keys.n, move.down)
        self.bind(ctrl + keys.p, move.up)
        self.bind(ctrl + keys.f, move.right)
        self.bind(ctrl + keys.b, move.left)

        self.bind(ctrl + keys.q, vx.quit)

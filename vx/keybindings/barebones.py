import vx
from vx.keybindings import bind, alt, ctrl, keys, KeybindingTable
import vx.movement as move

from functools import partial

def load(window):
    return Barebones(window)

class Barebones(KeybindingTable):
    def __init__(self, for_window):
        super().__init__()

        self.for_window = for_window

        self.bind(ctrl + keys.n, move.down)
        self.bind(ctrl + keys.p, move.up)
        self.bind(ctrl + keys.f, move.right)
        self.bind(ctrl + keys.b, move.left)

        self.bind(keys.backspace, self.for_window.backspace)
        self.bind(keys.enter, partial(self.for_window.add_string, '\n'))

        self.bind(ctrl + keys.x, vx.quit)

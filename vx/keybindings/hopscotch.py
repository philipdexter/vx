import vx
from vx.keybindings import bind, alt, ctrl, keys, keybinding_table
import vx.movement as move
import vx.utils as utils
import vx.window
import vx.test
import vx.prompt

from ..pointer import panes, organizer

from functools import partial

def load(window):
    return hopscotch_keybindings(window)

class hopscotch_keybindings(keybinding_table):
    def __init__(self, for_window):
        super(hopscotch_keybindings, self).__init__()

        self.for_window = for_window

        # simple movement

        self.bind(ctrl + keys.n, move.down)
        self.bind(ctrl + keys.p, move.up)
        self.bind(ctrl + keys.b, move.left)
        self.bind(ctrl + keys.f, move.right)

        self.bind(ctrl + keys.a, move.bol)
        self.bind(ctrl + keys.e, move.eol)

        self.bind(ctrl + keys.v, partial(utils.repeat, move.down))
        self.bind(alt + keys.v, partial(utils.repeat, move.up))

        self.bind(alt + keys.langle, move.beg)
        self.bind(alt + keys.rangle, move.end)

        self.bind(keys.backspace, self.for_window.backspace)

        # self.bind(alt + keys.b, vx.backward_word)
        # self.bind(alt + keys.f, vx.forward_word)

        self.bind(ctrl + keys.l, vx.window.center)

        # text manipulation

        # self.bind(ctrl + keys.d, vx.delete)

        # self.bind(ctrl + keys.k, vx.kill_to_end)

        # self.bind(alt + keys.d, vx.kill_to_forward)
        # self.bind(alt + keys.backspace, vx.kill_to_backward)

        # window management

        # self.bind(ctrl + keys.x - keys.o, vx.next_window)

        # self.bind(ctrl + keys.x - '2', vx.split_h)
        # self.bind(ctrl + keys.x - '3', vx.split_v)
        # self.bind(ctrl + keys.x - '0', vx.close_window)

        self.bind(ctrl + keys.x - keys['0'], lambda: organizer.remove_pane(panes.focused))
        self.bind(ctrl + keys.x - keys['2'], lambda: panes.focused.split())
        self.bind(ctrl + keys.x - keys.o, lambda: organizer.next_pane())

        # misc.

        self.bind(ctrl + keys.x - ctrl + keys.c, vx.quit)
        self.bind(alt + keys.x, lambda: panes.focused.open_prompt(vx.prompt.exec_prompt))

        self.bind(ctrl + keys.x - ctrl + keys.f, lambda: panes.focused.open_prompt(vx.prompt.file_prompt))

        self.bind(ctrl + keys.t, vx.test.run_tests)

        # undo/redo

        self.bind(ctrl + keys.underscore, self.for_window.undo)
        self.bind(alt + keys.forwardslash, self.for_window.redo)

        # save

        self.bind(ctrl + keys.x - ctrl + keys.s, lambda: self.for_window.save())

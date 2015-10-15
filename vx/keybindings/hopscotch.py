import vx
from vx.keybindings import bind, alt, ctrl, keys, KeybindingTable
import vx.movement as move
import vx.utils as utils
import vx.window
import vx.test
import vx.prompt

from ..pointer import panes, organizer

from functools import partial

def load(window):
    return Hopscotch(window)

class Hopscotch(KeybindingTable):
    def __init__(self, for_window):
        super().__init__()

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
        self.bind(ctrl + keys.d, self.for_window.delete)
        self.bind(keys.enter, partial(self.for_window.add_string, '\n'))

        self.bind(ctrl + keys.l, vx.window.center)

        self.bind(ctrl + keys.z, vx.suspend)


        self.bind(ctrl + keys.x - keys['0'], lambda: organizer.remove_pane(panes.focused))
        self.bind(ctrl + keys.x - keys['2'], lambda: panes.focused.split())
        self.bind(ctrl + keys.x - keys.o, lambda: organizer.next_pane())

        # misc.

        self.bind(ctrl + keys.x - ctrl + keys.c, vx.quit)
        self.bind(alt + keys.x, lambda: panes.focused.open_prompt(vx.prompt.exec_prompt))
        self.bind(ctrl + keys.s, lambda: panes.focused.open_prompt(vx.prompt.regex_prompt))

        self.bind(ctrl + keys.x - ctrl + keys.f, lambda: panes.focused.open_prompt(vx.prompt.file_prompt))

        self.bind(ctrl + keys.t, vx.test.run_tests)

        # undo/redo

        self.bind(ctrl + keys.underscore, self.for_window.undo)
        self.bind(alt + keys.forwardslash, self.for_window.redo)

        # save

        self.bind(ctrl + keys.x - ctrl + keys.s, lambda: self.for_window.save())

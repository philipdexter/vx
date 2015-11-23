import vx
from vx.keybindings import bind, alt, ctrl, keys, KeybindingTable
import vx.movement as move
import vx.utils as utils
import vx.window
import vx.test
import vx.prompt
import vx.undo as undo

from ..pointer import panes, organizer

from functools import partial

def load(window):
    return Hopscotch(window)

class Hopscotch(KeybindingTable):
    def __init__(self, for_window):
        super().__init__()

        self.for_window = for_window

        self.mark = (1,1)

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

        # mark

        self.bind(ctrl + keys.at, self.save_mark)

        # copy/paste

        self.bind(ctrl + keys.w, self.cut)
        self.bind(alt + keys.w, self.uncut)

    def save_mark(self):
        self.mark = self.for_window.cursor

    def uncut(self):
        if self.for_window.copystack.empty(): return

        (la, ca) = self.for_window.cursor
        to_insert = self.for_window.copystack.peek()
        self.for_window.add_string(to_insert)
        (lb, cb) = self.for_window.cursor
        self.for_window.dirty = True
        self.for_window.undo_tree.add(undo.addition(to_insert, la, ca, (la, ca, lb, cb)))

    def cut(self):
        (la, ca) = self.for_window.cursor
        (lb, cb) = self.mark
        forward = True
        if (la == lb and ca > cb) or lb < la:
            lb, cb, la, ca = la, ca, lb, cb
            forward = False
        text_between = vx.get_str_linecol_to_linecol_window(self.for_window, la, ca, lb, cb)
        self.for_window.copystack.push(text_between)
        self.for_window.remove_text(la, ca, lb, cb)
        self.for_window.dirty = True
        self.for_window.undo_tree.add(undo.removal(text_between, la, ca, (la, ca, lb, cb), forward))
        self.for_window.cursor = (la, ca)

import vx.text
import vx.window
from .pointer import windows

from itertools import zip_longest
from collections import defaultdict

class action:
    def __init__(self, string, line, col, box):
        self.string = string
        self.line, self.col = line, col
        self.box = box

    def stringify(self, string=''):
        return 'o'
        return 'o {} "{}" ({},{})'.format(string,
                                          self.string.split('\n')[0][:5] + '...',
                                          self.line,
                                          self.col)

class addition(action):
    def __init__(self, string, line, col, box):
        super().__init__(string, line, col, box)

    def undo(self, buffer):
        buffer.cursor = (self.line, self.col)
        for _ in range(len(self.string)):
            buffer.backspace(track=False)

    def redo(self, buffer):
        line, col, _, _ = self.box
        buffer.cursor = line, col
        buffer.add_string(self.string, track=False)

class removal(action):
    def __init__(self, string, line, col, box, hold):
        super().__init__(string, line, col, box)

        self.hold = hold

    def undo(self, buffer):
        buffer.cursor = (self.line, self.col)

        if self.hold:
            tmp_cursor = buffer.cursor

        buffer.add_string(self.string, track=False)

        if self.hold:
            buffer.cursor = tmp_cursor

    def redo(self, buffer):
        line, col, _, _ = self.box
        buffer.cursor = line, col
        buffer.remove_text(*self.box)

class tree:
    def __init__(self, item, parent):
        self.item = item
        self.children = []
        self.parent = parent

    def items(self):
        return (1 if self.item else 0) + sum(map(lambda x: x.items(), self.children))

    def stringify(self, flag, flag_next):
        this_item = self.item.stringify() if self.item else '+'
        if flag == self.item:
            this_item += '<===='
        if flag_next and flag_next == self.item:
            this_item += '<N'
        children = list(map(lambda x: x.stringify(flag, flag_next).split('\n'), self.children))
        output = ['|']

        max_columns = []
        for i in children:
            max_columns.append(len(max(i, key=len)))

        def ensure_width(line, width, char=' '):
            return line + (char * (width - len(line)))

        for lines in list(map(list, zip_longest(*children))):
            printed = 0
            for i,l in enumerate(lines):
                if l is None:
                    lines[i] = ensure_width('', max_columns[i])
            char = ' ' if len(self.children) <= 1 else '-'
            lines = list(map(lambda x: ensure_width(x[0], max(6, x[1]), (char if x[0].startswith('o') else ' ')), zip(lines, max_columns)))
            output += [''.join(reversed(lines))]
        return '\n'.join([this_item] + output)

class undo_tree:
    def __init__(self, buffer):
        self.tree = tree(None, None)
        self.current = self.tree
        self.next_child = -1
        self.buffer = buffer
        self.save_point = self.current

    def switch_child(self):
        if self.current.children:
            self.next_child = self.next_child - 1
            if self.next_child <= -1: self.next_child = len(self.current.children) + self.next_child

    def add(self, action):
        self.current.children.append(tree(action, self.current))
        self.current = self.current.children[self.next_child]

    def undo(self):
        if self.current.item is not None:
            self.current.item.undo(self.buffer)
            self.current = self.current.parent
            if self.current == self.save_point:
                self.buffer.dirty = False
            else:
                self.buffer.dirty = True
        self.next_child = -1

    def redo(self):
        if self.current.children and self.current.children[self.next_child] is not None:
            self.current.children[self.next_child].item.redo(self.buffer)
            self.current = self.current.children[self.next_child]
            if self.current == self.save_point:
                self.buffer.dirty = False
            else:
                self.buffer.dirty = True
        self.next_child = -1

    def mark_save_point(self):
        self.save_point = self.current

    def stringify(self):
        items = self.tree.items()
        next_child = self.current.children[self.next_child].item if self.current.children else None
        rep = self.tree.stringify(self.current.item, next_child)
        return '{}\n{}'.format(items, rep)

def load(buffer, attached_to):
    from .keybindings import keybinding_table, ctrl, keys
    from .pointer import organizer, panes
    class undo_tree_keybindings(keybinding_table):
        def __init__(self):
            super().__init__()

            self.buffer = buffer
            self.attached_to = attached_to
            self.undo_tree = attached_to.undo_tree

            self.bind(ctrl + keys.x - keys.o, lambda: organizer.next_pane())
            self.bind(ctrl + keys.x - keys['0'], lambda: organizer.remove_pane(panes.focused))

            def clear_and(do_this):
                self.buffer.blank()
                do_this()
                self.buffer.add_string(self.undo_tree.stringify())
            self.bind(keys.k, lambda: clear_and(self.attached_to.undo))
            self.bind(keys.j, lambda: clear_and(self.attached_to.redo))
            self.bind(keys.l, lambda: clear_and(self.undo_tree.switch_child))

    return undo_tree_keybindings()

import vx
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
        return 'o {} "{}" ({},{})'.format(string,
                                          self.string.split('\n')[0][:5] + '...',
                                          self.line,
                                          self.col)

class addition(action):
    def __init__(self, string, line, col, box):
        super(addition, self).__init__(string, line, col, box)

    def undo(self, buffer):
        buffer.cursor = (self.line, self.col)
        for _ in range(len(self.string)):
            buffer.backspace(track=False)

    def redo(self, buffer):
        line, col, _, _ = self.box
        buffer.cursor = line, col
        buffer.add_string(self.string, track=False)

    def stringify(self):
        s = 'addition'
        return super(addition, self).stringify(s)

class removal(action):
    def __init__(self, string, line, col, box, hold):
        super(removal, self).__init__(string, line, col, box)

        self.hold = hold

    def undo(self, buffer):
        if self.hold:
            tmp_cursor = buffer.cursor

        buffer.cursor = (self.line, self.col)
        buffer.add_string(self.string, track=False)

        if self.hold:
            buffer.cursor = tmp_cursor

    def redo(self, buffer):
        buffer.remove_text(*self.box)

    def stringify(self):
        s = 'removal {}'.format(self.hold)
        return super(removal, self).stringify(s)

class tree:
    def __init__(self, item, parent):
        self.item = item
        self.children = []
        self.parent = parent

    def items(self):
        return (1 if self.item else 0) + sum(map(lambda x: x.items(), self.children))

    def stringify(self, flag):
        this_item = self.item.stringify() if self.item else '+'
        if flag == self.item:
            this_item += '<===='
        children = list(map(lambda x: x.stringify(flag).split('\n'), self.children))
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
            lines = list(map(lambda x: ensure_width(x[0], x[1], (char if x[0].startswith('o') else ' ')), zip(lines, max_columns)))
            output += [''.join(reversed(lines))]
        return '\n'.join([this_item] + output)

class undo_tree:
    def __init__(self, buffer):
        self.tree = tree(None, None)
        self.current = self.tree
        self.buffer = buffer

    def add(self, action):
        self.current.children.append(tree(action, self.current))
        self.current = self.current.children[-1]

    def undo(self):
        if self.current.item is not None:
            self.current.item.undo(self.buffer)
            self.current = self.current.parent

    def redo(self):
        if self.current.children and self.current.children[-1] is not None:
            self.current.children[-1].item.redo(self.buffer)
            self.current = self.current.children[-1]

    def stringify(self):
        items = self.tree.items()
        rep = self.tree.stringify(self.current.item)
        return '{}\n{}'.format(items, rep)

import vx
from vx.window import window
from .undo import undo_tree, addition, removal
import vx.movement as move
import vx.text as text
from .keybindings import ctrl, keys

import re
from contextlib import contextmanager

class buffer(window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.undo_tree = undo_tree(self)

        def print_undo():
            from .pointer import panes
            p = panes.focused.split()
            p.buffer.blank()
            p.buffer.add_string(self.undo_tree.stringify())
            p.buffer.unfocus()
            p.buffer.keybinding_table = vx.undo.load(p.buffer, attached_to=self)
            p.buffer.focus()
        self.keybinding_table.bind(ctrl + keys.y, print_undo)

        self.last_seeked_column = 1

    def redo(self):
        self.undo_tree.redo()

    def undo(self):
        self.undo_tree.undo()

    def save(self):
        super().save()
        self.undo_tree.mark_save_point()

    @contextmanager
    def cursor_wander(self, command=None):
        y, x = self.cursor
        if command is not None:
            command()
        yp, xp = self.cursor
        yield (yp, xp)
        self.cursor = (y, x)

    @contextmanager
    def column_restore(self, column=None):
        if not column:
            column = self.last_seeked_column
        yield
        with self.cursor_wander():
            move.eol()
            _, end = self.cursor
        self.cursor = (self.cursor[0], min(end, column))

    @contextmanager
    def column_save(self):
        yield
        self.last_seeked_column = self.cursor[1]

    @contextmanager
    def cursor_jail(self, la, ca, lb, cb):
        old_cursor = getattr(buffer, 'cursor')
        def _set_cursor(inst, linecol):
            if self is inst:
                line, col = linecol
                if line < la: return
                if line > lb: return
                if line == la and col < ca: return
                if line == lb and col > cb: return
            return vx.set_linecol_window(self, line, col)
        def _get_cursor(self):
            return vx.get_linecol_window(self)
        setattr(buffer, 'cursor', property(_get_cursor, _set_cursor))
        yield
        setattr(buffer, 'cursor', old_cursor)

    def backspace(self, track=True):
        if track:
            self.dirty = True
            l, c = self.cursor
            lb, cb = l, c
            if l > 1 or c > 1:
                c = c - 1
                if c == 0:
                    l -= 1
                    move.up()
                    move.eol()
                    _, c = self.cursor
                    move.down()
                    move.bol()
                ch = vx.get_ch_linecol_window(self, l, c)
                if ch == '\t':
                    c -= 7
                self.undo_tree.add(removal(ch, l, c, hold=False, box=(l, c, lb, cb)))
        super().backspace()

    def delete(self, track=True):
        if track:
            self.dirty = True
            l, c = self.cursor
            move.right()
            lb, cb = self.cursor
            move.left()
            ch = vx.get_ch_linecol_window(self, l, c)
            self.undo_tree.add(removal(ch, l, c, hold=True, box=(l, c, lb, cb)))
        super().delete()

    def add_string(self, s, track=True):
        if track:
            la, ca = self.cursor
            self.dirty = True
        super().add_string(s)
        if track:
            lb, cb = self.cursor
            self.undo_tree.add(addition(s, lb, cb, (la, ca, lb, cb)))

    def remove_text(self, from_line, from_col, to_line, to_col):
        """Removes all the text between from_line/from_col to to_line/to_col"""
        with self.cursor_wander():
            self.cursor = (to_line, to_col)
            line, col = self.cursor
            while line != from_line or col != from_col:
                self.backspace(track=False)
                line, col = self.cursor

    def get_text_lines(self):
        return len(self.contents.split('\n'))

    def get_linecoloffset_of(self, to_find, contents=None, start=0, forward=True):
        if forward:
            contents = contents or self.get_contents_from_cursor()
            index = contents.find(to_find, start)
            lines, columns = text.get_linecol_offset(contents[:index])
            l, c = self.cursor
            columns = c + columns if lines == 0 else columns + 1
            lines = l + lines
            return lines, columns, index
        else:
            raise Exception('not implemented')

    def get_all_linecoloffsets_of(self, to_find, forward=True):
        if not forward:
            raise Exception('not implemented')
        contents = self.get_contents_from_cursor()
        start = 0
        while True:
            line, col, start = self.get_linecoloffset_of(to_find, contents, start, forward)
            if start == -1: break
            yield (line, col, start)
            start += 1

    def get_regex_linecoloffsetlength_of(self, regex, contents=None, start=0, forward=True):
        if forward:
            contents = contents or self.get_contents_from_cursor()
            try:
                rgx = re.compile(regex, re.MULTILINE)
            except:
                return (0, 0, -1, 0)
            match = rgx.search(contents, start)
            if match is None:
                return (0, 0, -1, 0)
            index = match.start()
            lines, columns = text.get_linecol_offset(contents[:index])
            l, c = self.cursor
            columns = c + columns if lines == 0 else columns + 1
            lines = l + lines
            length = match.end() - match.start()
            return lines, columns, index, length
        else:
            raise Exception('not implemented')

    def get_all_regex_linecoloffsetlengths_of(self, regex, forward=True):
        if not forward:
            raise Exception('not implemented')
        contents = self.get_contents_from_cursor()
        start = 0
        while True:
            line, col, start, length = self.get_regex_linecoloffsetlength_of(regex, contents, start, forward)
            if start == -1: break
            yield (line, col, start, length)
            start += 1

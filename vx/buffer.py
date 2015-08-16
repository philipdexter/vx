import vx
from vx.window import window
from .text import backspace

from contextlib import contextmanager

class buffer(window):
    def __init__(self, *args, **kwargs):
        super(buffer, self).__init__(*args, **kwargs)

    @contextmanager
    def cursor_wander(self, command=None):
        y, x = self.cursor
        if command is not None:
            command()
        yp, xp = self.cursor
        yield (yp, xp)
        self.cursor = (y, x)

    def backspace(self, track=True):
        if track:
            self.dirty = True
            l, c = self.cursor
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
                vx.undo.register_removal(ch, r, c)
        vx.backspace_window(self)

    def remove_text(self, from_line, from_col, to_line, to_col):
        """Removes all the text between from_line/from_col to to_line/to_col"""
        with self.cursor_wander():
            self.cursor = (to_line, to_col)
            line, col = self.cursor
            while line != from_line or col != from_col:
                backspace(track=False)
                line, col = self.cursor

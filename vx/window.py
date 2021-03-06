import vx
import vx.mode as mode
import vx.utils
import vx.keybindings
import vx.logger
from .pointer import windows, panes

import math
import traceback
from functools import partial, wraps

class _graffiti:
    def __init__(self, y, x, text):
        self.y = y
        self.x = x
        self.text = text

    def render(self, window):
        vx.set_cursor(window, self.y, self.x)
        vx.print_string_window(window, self.text)

class window:
    def __init__(self, rows, columns, y, x, starting_mode=None):
        self._c_window = vx.new_window(rows-1, columns, y, x)
        self.graffitis = []
        self.line = 1
        self.col = 1

        self.last_seeked_column = 0

        self.rows = rows
        self.columns = columns
        self.y = y
        self.x = x

        self.has_contents = False
        self.dirty = False

        if vx.default_keybindings is not None:
            self.keybinding_table = vx.default_keybindings(self)
        else:
            self.keybinding_table = vx.keybindings.keybinding_table()

        self.parent = None
        self.children = []

        self.color_tags = []

        self.mode = starting_mode(self) if starting_mode else mode.mode(self)

        self.__contents_cache = None

        self.id = 'blah'

    def __get_cursor(self):
        return vx.get_linecol_window(self)
    def __set_cursor(self, linecol):
        line, col = linecol
        return vx.set_linecol_window(self, line, col)
    cursor = property(__get_cursor, __set_cursor, doc="""A tuple (line, col) of the cursor position.
    This is a python property. You can set it and get it.""")

    def __get_window_start(self):
        return vx.get_linecol_start_window(self)
    def __set_window_start(self, linecol):
        line, col = linecol
        return vx.set_linecol_start_window(self, line, col)
    topleft = property(__get_window_start, __set_window_start)

    def __get_window_size(self):
        return vx.get_window_size(self)
    size = property(__get_window_size)

    def __get_contents(self):
        if self.__contents_cache is None:
            vx.logger.debug('cache fetch {}'.format(self.id))
            self.__contents_cache = vx.get_contents_window(self)
            self.syntax_highlight()
        return self.__contents_cache
    contents = property(__get_contents)

    def _invalidate_cache(self):
        vx.logger.debug('cache invalidation')
        self.__contents_cache = None

    def get_contents_from_cursor(self):
        y, x = self.cursor
        contents = self.contents.split('\n')[y-1:]
        i = 0
        tabs = 0
        end = x - 1
        while i < end and i < len(contents[0]):
            if contents[0][i] == '\t':
                end -= 7
                tabs += 1
            i += 1
        cutoff = x-1 - 7*tabs
        contents[0] = contents[0][cutoff:]
        contents = '\n'.join(contents)
        return contents

    def get_contents_before_cursor(self):
        y, x = self.cursor
        contents = self.contents.split('\n')[:y]
        try:
            i = 0
            tabs = 0
            end = x - 1
            while i < end and i < len(contents[-1]):
                if contents[-1][i] == '\t':
                    end -= 7
                    tabs += 1
                i += 1
            cutoff = x-1 - 7*tabs
            contents[-1] = contents[-1][:cutoff]
        except:
            return ''
        contents = '\n'.join(contents)
        return contents

    def ensure_visible(self, line, col):
        """Ensures that ``line`` and ``col`` are visible on the screen"""
        r, c = vx.get_window_size(self)
        y, x = line, col
        sy, sx = vx.get_linecol_start_window(self)
        # Check line
        if y < sy:
            sy = y - 6
        elif y > sy + r:
            sy = y + 6 - r
        # Check col
        if x < sx:
            sx = max(1, x - 6)
        elif x > sx + c:
            sx = x + 6 - c

        self.topleft = (sy, sx)

    def save(self):
        """Saves the contents of the window to ``self.filename``"""
        vx.save_window(self)
        self.dirty = False

    def add_string(self, s):
        self._invalidate_cache()
        vx.add_string_window(self, s)

    def remove(self, force=False):
        """Removes this window from the screen; prompting when the window is dirty."""
        vx.delete_window(self)

    def resize(self, rows, columns):
        self.rows = rows
        self.columns = columns
        vx.resize_window(self, rows, columns)

    def pad(self, top=0, bottom=0, left=0, right=0):
        if top > 0 or left > 0:
            self.resize(self.rows - top, self.columns - left)
            self.move(self.y + top, self.x + left)
        if bottom > 0 or right > 0:
            self.resize(self.rows - bottom, self.columns - right)

    def grow(self, top=0, bottom=0, left=0, right=0):
        if top > 0 or left > 0:
            self.move(self.y - top, self.x - left)
            self.resize(self.rows + top, self.columns + left)
        if bottom > 0 or right > 0:
            self.resize(self.rows + (bottom + top), self.columns + (right + left))

    def move(self, y, x):
        self.y = y
        self.x = x
        vx.move_window(self, y, x)

    def set_text(self, text):
        self.graffitis = []
        self.graffitis.append(_graffiti(0, 0, text))

    def blank(self):
        self.has_contents = True
        vx.attach_window_blank(self)

    def focus(self):
        vx.keybindings.keybinding_tables.insert(0, self.keybinding_table)
        vx.focus_internal_window(self)

    def unfocus(self):
        vx.keybindings.keybinding_tables.remove(self.keybinding_table)

    def prepare(self):
        vx.clear_window(self)
        vx.set_cursor(self, 0, 0)
        self.line, self.col = self.cursor

    def refresh(self):
        vx.refresh_window(self)

    def color_line(self, line_number, column_number, line):
        printed = 0
        start = 0
        this_line = list(filter(lambda x: x[1] == line_number, self.color_tags))
        to_add = []
        this_line.sort(key=lambda n: n[2])
        for (i, c) in enumerate(this_line):
            tag, ctl, ctc, ctlen, fg, bg = c
            for oc in this_line:
                if c == oc: continue
                _, _, octc, octlen, _, _ = oc
                if octc == ctc and octlen < ctlen:
                    this_line[i] = (tag, ctl, octc + octlen, ctc+ctlen-(octc+octlen), fg, bg)
                elif octc == ctc and octlen == ctlen:
                    this_line[i] = (tag, ctl, ctc, 0, fg, bg)
                elif octc > ctc and octc < ctc + ctlen:
                    this_line[i] = (tag, ctl, ctc, octc - ctc, fg, bg)
                    if ctc + ctlen > octc + octlen:
                        to_add.append((tag, ctl, octc+octlen, ctc+ctlen-(octc+octlen), fg, bg))
        this_line.extend(to_add)
        this_line.sort(key=lambda n: n[2])
        for tag, _, ctc, ctlen, ctfg, ctbg in this_line:
            ctc -= column_number - 1
            vx.print_string_window(self, line[start:ctc-1])
            printed += len(line[start:ctc-1])
            start += len(line[start:ctc-1])
            self.set_color(ctfg, ctbg)
            vx.print_string_window(self, line[ctc-1:ctc-1+ctlen])
            self.set_color(-1, -1)
            printed += ctlen
            start += ctlen
        vx.print_string_window(self, line[printed:])

    def render(self):
        if self.has_contents:
            contents = self.contents
            r, c = vx.get_linecol_start_window(self)
            y, x = vx.get_window_size(self)

            lines = contents.split('\n')[r-1:r+y-1]

            cline = r
            ccol = c
            for i, line in enumerate(lines):
                line = line.replace('\t', '        ')[c-1:c-1+x-2]
                if len(line) == x - 2:
                    line += '$'
                if c-1 > 0:
                    line = '$' + line[1:]

                self.color_line(cline, ccol, line)
                vx.print_string_window(self, '\n')
                cline += 1
        for m in self.graffitis:
            m.render(self)

    def update(self):
        self.prepare()
        self.render()
        self.refresh()

    def syntax_highlight(self):
        self.color_tags = list(filter(lambda x: x[0] != "syntax-highlight", self.color_tags))

        import re
        for cline, line in enumerate(self.contents.split('\n')):
            line = line.replace('\t', '        ')
            for keyword in self.mode.keywords:
                matches = [(m.start(), m.end() - m.start()) for m in re.finditer(keyword, line)]
                for col, length in matches:
                    a = ("syntax-highlight", cline+1, col+1, length, 4, -1)
                    self.color_tags = list(filter(lambda x: x != a, self.color_tags))
                    self.add_color_tag(*a)

    def set_cursor(self, y, x):
        vx.set_cursor(self, y, x)

    def set_color(self, fg, bg):
        vx.set_color_window(self, fg, bg)

    def add_color_tag(self, tag, l, c, length, fg, bg):
        self.color_tags.append((tag, l, c, length, fg, bg))

    def attach_file(self, filename):
        self.filename = filename
        vx.attach_window(self, filename)
        self.has_contents = True
        m = mode.mode_from_filename(filename)
        if m:
            self.mode = m(self)

    def split_h(self):
        split_height = math.floor(self.rows / 2)
        split_width = self.columns
        self.resize(split_height, split_width)
        new = window(split_height, split_width, self.y + split_height, self.x)
        new.parent = self
        self.children.append(new)
        new.blank()
        new.focus()
        return new

    def split_v(self):
        split_height = self.rows
        split_width = math.floor(self.columns / 2)
        self.resize(split_height, split_width)
        new = window(split_height, split_width, self.y, self.x + split_width)
        new.parent = self
        self.children.append(new)
        new.blank()
        new.focus()
        return new

    def backspace(self):
        self._invalidate_cache()
        vx.backspace_window(self)

    def delete(self):
        self._invalidate_cache()
        vx.backspace_delete_window(self)

    def undo(self):
        raise Exception('not implemented')
    def redo(self):
        raise Exception('not implemented')

def center():
    r, c = vx.get_window_size(windows.focused)
    y, _ = windows.focused.cursor
    _, x = vx.get_linecol_start_window(windows.focused)
    new_top = max(y - r // 2, 1)
    windows.focused.topleft = (new_top, x)

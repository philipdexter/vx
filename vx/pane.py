from .buffer import buffer
from .scratchbuffer import scratchbuffer
from .status_bar import status_bar
from .line_numbers import line_numbers

from .pointer import panes, windows, organizer

class pane:
    def __init__(self, buffer, rows, columns, y, x):
        self.rows = rows
        self.columns = columns
        self.y = y
        self.x = x

        self.windows = []

        self.buffer = buffer

        self.status_bar = status_bar(self.buffer)

        self.line_numbers = line_numbers(self.buffer)
        self.buffer.move(self.y, self.x)
        self.buffer.resize(self.rows, self.columns)
        self.buffer.pad(left=self.line_numbers.columns, bottom=1)

        self.attach_window(self.buffer)
        self.attach_window(self.status_bar)
        self.attach_window(self.line_numbers)

    def set_buffer(self, buffer):
        self.buffer = buffer
        self.line_numbers.attached_to = buffer
        self.status_bar.attached_to = buffer

    def attach_window(self, window):
        self.windows.append(window)
        windows.add(window)

    def detach_window(self, window):
        self.windows.remove(window)

    def unfocus(self):
        pass#self.buffer.unfocus()

    def focus(self):
        self.buffer.focus()

    def update(self):
        buffer_text_lines = len(str(self.buffer.get_text_lines()))
        line_number_lines = self.line_numbers.columns
        if buffer_text_lines > line_number_lines:
            diff = buffer_text_lines-line_number_lines
            self.line_numbers.grow(right=diff)
            self.buffer.pad(left=diff)
        elif buffer_text_lines < line_number_lines:
            diff = line_number_lines-buffer_text_lines
            self.line_numbers.pad(right=diff)
            self.buffer.grow(left=diff)
        for w in self.windows:
            w.prepare()
        for w in self.windows:
            w.render()
        for w in self.windows:
            w.refresh()

    def open_prompt(self, prompt, *args, **kwargs):
        def close_prompt(p):
            import vx
            self.windows.remove(p)
            self.grow(bottom=p.size[0])
            organizer.switch_to_pane(self)
        self.buffer.unfocus()
        p = prompt(*args, attached_to=self.buffer, remove_callback=close_prompt, **kwargs)
        p.focus()
        self.pad(bottom=1)
        self.attach_window(p)
        p.move(self.y + self.rows, 0)
        windows.focused = p
        return p

    def get_contents_from_cursor(self):
        return self.buffer.get_contents_from_cursor()

    def resize(self, rows, columns):
        self.rows = rows
        self.columns = columns

        self.line_numbers.resize(self.rows-1, self.line_numbers.columns)

        self.buffer.move(self.y, self.x)
        self.buffer.resize(self.rows, self.columns)
        self.buffer.pad(left=self.line_numbers.columns, bottom=1)

        self.status_bar.resize(1, self.columns)
        self.status_bar.move(self.y + self.rows - 1, self.x)

    def move(self, y, x):
        self.y = y
        self.x = x

        self.buffer.move(y, x)
        self.buffer.pad(left=self.line_numbers.columns)

        self.status_bar.move(self.y + self.rows - 1, self.x)

        self.line_numbers.move(self.y, self.x)

    def grow(self, top=0, bottom=0, left=0, right=0):
        if top > 0 or left > 0:
            self.move(self.y - top, self.x - left)
            self.resize(self.rows + top, self.columns + left)
        if bottom > 0 or right > 0:
            self.resize(self.rows + (bottom + top), self.columns + (right + left))

    def pad(self, top=0, bottom=0, left=0, right=0):
        if top > 0 or left > 0:
            self.resize(self.rows - top, self.columns - left)
            self.move(self.y + top, self.x + left)
        if bottom > 0 or right > 0:
            self.resize(self.rows - bottom, self.columns - right)

    def split(self):
        fb = scratchbuffer(self.rows, self.columns, self.y, self.x)
        p = pane(fb, self.rows, self.columns, self.y, self.x)
        organizer.add_pane(p, parent=self)
        organizer.switch_to_pane(p)
        return p

    def remove(self):
        for w in self.windows:
            w.remove()
            windows.remove(w)

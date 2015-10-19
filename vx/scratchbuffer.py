from vx.buffer import buffer
from .pointer import panes, windows, organizer
from .prompt import input_prompt
from .filebuffer import filebuffer

from functools import partial
from os.path import isfile

class scratchbuffer(buffer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.blank()

    def save(self):
        def callback(response):
            filename = response
            if isfile(filename):
                return
            else:
                panes.focused.detach_window(self)
                fb = filebuffer(filename, self.rows, self.columns, self.y, self.x)
                fb.add_string(self.contents)
                panes.focused.set_buffer(fb)
                panes.focused.attach_window(fb)
                organizer.switch_to_pane(panes.focused)
                windows.remove(self)
                self.remove(force=True)
        panes.focused.open_prompt(partial(input_prompt, "what file do you want to save to?", callback))

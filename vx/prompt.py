import vx
import vx.utils as utils
import vx.text as text
from .buffer import buffer
from vx.keybindings import ctrl, alt, keys, register_key_listener, unregister_key_listener

from .pointer import windows, panes, organizer
from .scheduler import schedule

import traceback
from os.path import isfile
from functools import partial

class _prompt(buffer):
    def __init__(self, attached_to=None, remove_callback=None):
        if attached_to is None:
            raise Exception('not implemented')
            attached_to = panes.focused
        super(_prompt, self).__init__(attached_to.pane,
                                      2, attached_to.columns,
                                      attached_to.y + attached_to.rows-1,
                                      attached_to.x)
        self.blank()
        self.attached_to = attached_to
        self.remove_callback = remove_callback

        self.keybinding_table.bind(ctrl + keys.g, self.cancel)

    def cancel(self):
        if self.remove_callback:
            self.remove_callback(self)
        self.attached_to.focus()
        self.remove(force=True)

class exec_prompt(_prompt):
    _history = []

    def __init__(self, *args, **kwargs):
        super(exec_prompt, self).__init__(*args, **kwargs)

        self.keybinding_table.bind(alt + keys.p, self._history_pullback)
        self.keybinding_table.bind(keys.enter, self.getout)
        self.keybinding_table.bind(ctrl + keys.j, self._enter_and_expand)

    def getout(self):
        contents = self.contents
        exec_prompt._history.append(contents)
        with utils.stdoutIO() as s:
            try:
                exec(contents)
            except Exception as e:
                tb = traceback.format_exc()
            else:
                tb = None
        s = s.getvalue()

        if self.remove_callback:
            self.remove_callback(self)

        if len(s) > 0 or tb:
            split = panes.focused.split()
            if not tb:
                split.buffer.add_string(s)
            else:
                split.buffer.add_string(tb)

        self.remove(force=True)

    def _enter_and_expand(self):
        self.expand()
        self.add_string('\n')

    def expand(self):
        self.attached_to.pad(bottom=1)
        self.grow(top=1)

    def _history_pullback(self):
        if len(_exec_prompt._history) > 0:
            vx.clear_contents_window(self)
            self.add_string(_exec_prompt._history[-1])

class file_prompt(_prompt):
    def __init__(self, *args, **kwargs):
        super(file_prompt, self).__init__(*args, **kwargs)

        self.completing = False

        self.keybinding_table.bind(keys.enter, self.getout)
        self.keybinding_table.bind(keys.tab, self.complete)

    def complete(self):
        import glob
        if not self.completing:
            self.completing = True
            contents = self.contents
            self.old_contents = contents
            vx.clear_contents_window(self)
            self.files = glob.glob('{}*'.format(contents))
            if len(self.files) == 0:
                self.completing = False
        if len(self.files) == 0:
            self.completing = False
            vx.clear_contents_window(self)
            self.add_string(self.old_contents)
        else:
            completion = self.files.pop()
            vx.clear_contents_window(self)
            self.add_string(completion)

    def getout(self, force=False, cancel_open=False):
        if not force and self.attached_to.dirty:
            self.attached_to.focus()
            yn_prompt('Window is dirty, really open another file?',
                       partial(self.getout, force=True),
                       partial(self.getout, force=True, cancel_open=True))
            return
        y, x = vx.get_window_size(self)
        self.attached_to.grow(bottom=y)
        self.attached_to.focus()
        if not cancel_open:
            contents = self.contents
            if isfile(contents):
                self.attached_to.attach_file(contents)
                self.attached_to.dirty = False
            else:
                split = self.attached_to.split_h()
                split.focus()
                split.add_string('file "{}" does not exist'.format(contents))
        self.remove(force=True)

class yn_prompt(_prompt):
    def __init__(self, message, yes, no, *args, **kwargs):
        super(yn_prompt, self).__init__(*args, **kwargs)

        self.yes = yes
        self.no = no

        self.keybinding_table.bind(keys.enter, self.getout)

        text.add_string('{} (y/n): '.format(message))

    def getout(self):
        contents = self.contents
        ret = False
        try:
            answer = contents.split(':')[1].strip()
            if answer.lower() in ('y', 'yes'):
                ret = True
        except:
            return
        y, x = vx.get_window_size(self)
        self.attached_to.grow(bottom=y)
        self.attached_to.focus()
        self.remove(force=True)
        if ret and self.yes:
            self.yes()
        elif self.no:
            self.no()

class time_prompt(_prompt):
    def __init__(self, message, seconds=2, *args, **kwargs):
        super(time_prompt, self).__init__(*args, **kwargs)

        self.message = message

        self.add_string(message)

        schedule(seconds, self.getout)

        self.attached_to.focus()

    def getout(self):
        if self.remove_callback:
            self.remove_callback(self)

        self.remove(force=True)

class search_prompt(_prompt):
    def __init__(self, start='', forwards=True, *args, **kwargs):
        super(search_prompt, self).__init__(*args, **kwargs)

        self.forwards = forwards

        self.keybinding_table.bind(keys.enter, self.getout)
        self.keybinding_table.bind(ctrl + keys.f, self.next)
        self.keybinding_table.bind(ctrl + keys.r, self.reverse)

        register_key_listener(self.isearch)

        self.original_cursor = self.attached_to.cursor
        self.original_start = self.attached_to.topleft

        self.matching = False
        self.match_length = 0

        self.add_string(start)

    def cancel(self):
        self.attached_to.cursor = (self.original_cursor[0], self.original_cursor[1])
        self.attached_to.topleft = (self.original_start[0], self.original_start[1])
        super(search_prompt, self).cancel()

    def reverse(self):
        self.forwards = not self.forwards
        self.next()

    def next(self):
        if self.matching:
            if self.forwards:
                utils.repeat(partial(vx.move_right_window, self.attached_to), times=self.match_length)
            else:
                utils.repeat(partial(vx.move_left_window, self.attached_to), times=self.match_length)
                vx.move_left_window(self.attached_to)

    def isearch(self):
        self.search()

    def dosearch(self, window, search_for, forwards):
        l, c, o = vx.get_linecoloffset_of_str(window, search_for, forwards)
        return l, c, o, len(search_for)

    def clear_color(self):
        self.attached_to.color_tags = list(filter(lambda x: x[0] != "search", self.attached_to.color_tags))

    def search(self):
        self.set_color(-1, -1)
        search_for = self.contents
        if not search_for: self.clear_color(); return
        l, c, o, length = self.dosearch(self.attached_to, search_for, int(self.forwards))
        if o == -1:
            self.attached_to.cursor = (self.original_cursor[0], self.original_cursor[1])
            self.clear_color()
            self.set_color(-1, 11)
            self.matching = False
            return
        self.attached_to.ensure_visible(l, c + length)
        self.matching = True
        self.match_length = length
        self.attached_to.cursor = (l, c)
        self.clear_color()
        self.attached_to.add_color_tag("search", l, c, length, 1, 10)
        if not self.forwards:
            utils.repeat(partial(vx.move_right_window, self.attached_to), times=length)

    def getout(self):
        if self.matching:
            if self.forwards:
                utils.repeat(partial(vx.move_right_window, self.attached_to), times=self.match_length)

        if self.remove_callback:
            self.remove_callback(self)

        self.remove(force=True)
        unregister_key_listener(self.isearch)
        self.clear_color()

class regex_prompt(search_prompt):
    def dosearch(self, window, search_for, forwards):
        if not forwards:
            vx.move_right_window(window)
        return text.find_regex(search_for, window, forwards)

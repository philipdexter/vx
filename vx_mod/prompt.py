import vx
import vx_mod.utils as utils
import vx_mod.text as text
import vx_mod.movement as move
from vx_mod.window import window, windows

import traceback
from os.path import isfile
from functools import partial

class _prompt(window):
    def __init__(self, attached_to=None):
        if attached_to is None:
            attached_to = windows.focused
        super(_prompt, self).__init__(2, attached_to.columns,
                                      attached_to.y + attached_to.rows-1,
                                      attached_to.x,
                                      status_bar=False)
        attached_to.pad(bottom=1)
        self.blank()
        self.focus()
        self.attached_to = attached_to

        self.keybinding_table.bind(vx.ctrl + vx.keys.g, self.cancel)

    def cancel(self):
        y, x = vx.get_window_size(self)
        self.attached_to.grow(bottom=y)
        self.attached_to.focus()
        self.remove(force=True)

@vx.expose
class _exec_prompt(_prompt):
    _history = []

    def __init__(self, *args, **kwargs):
        super(_exec_prompt, self).__init__(*args, **kwargs)

        self.keybinding_table.bind(vx.alt + vx.keys.p, self._history_pullback)
        self.keybinding_table.bind(vx.keys.enter, self.getout)
        self.keybinding_table.bind(vx.ctrl + vx.keys.j, self._enter_and_expand)

    def getout(self):
        y, x = vx.get_window_size(self)
        self.attached_to.grow(bottom=y)
        self.attached_to.focus()
        contents = self.contents
        _exec_prompt._history.append(contents)
        with utils.stdoutIO() as s:
            try:
                exec(contents)
            except Exception as e:
                tb = traceback.format_exc()
            else:
                tb = None
        s = s.getvalue()
        if len(s) > 0 or tb:
            split = self.attached_to.split_h()
            split.focus()
            if not tb:
                text.add_string(s)
            else:
                text.add_string(tb)
        self.remove(force=True)

    def _enter_and_expand(self):
        self.expand()
        text.add_string('\n')

    def expand(self):
        self.attached_to.pad(bottom=1)
        self.grow(top=1)

    def _history_pullback(self):
        if len(_exec_prompt._history) > 0:
            vx.clear_contents_window(self)
            text.add_string(_exec_prompt._history[-1])

@vx.expose
class _file_prompt(_prompt):
    def __init__(self, *args, **kwargs):
        super(_file_prompt, self).__init__(*args, **kwargs)

        self.completing = False

        self.keybinding_table.bind(vx.keys.enter, self.getout)
        self.keybinding_table.bind(vx.keys.tab, self.complete)

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
            text.add_string(self.old_contents)
        else:
            completion = self.files.pop()
            vx.clear_contents_window(self)
            text.add_string(completion)

    def getout(self, force=False, cancel_open=False):
        if not force and self.attached_to.dirty:
            self.attached_to.focus()
            _yn_prompt('Window is dirty, really open another file?',
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
                text.add_string('file "{}" does not exist'.format(contents))
        self.remove(force=True)

@vx.expose
class _yn_prompt(_prompt):
    def __init__(self, message, yes, no, *args, **kwargs):
        super(_yn_prompt, self).__init__(*args, **kwargs)

        self.yes = yes
        self.no = no

        self.keybinding_table.bind(vx.keys.enter, self.getout)

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

@vx.expose
class _time_prompt(_prompt):
    def __init__(self, message, seconds=2, *args, **kwargs):
        super(_time_prompt, self).__init__(*args, **kwargs)

        self.message = message

        text.add_string(message)

        vx.schedule(seconds, self.getout)

        self.attached_to.focus()

    def getout(self):
        y, x = vx.get_window_size(self)
        self.attached_to.grow(bottom=y)
        self.attached_to.focus()
        self.remove(force=True)

@vx.expose
class _search_prompt(_prompt):
    def __init__(self, start='', forwards=True, *args, **kwargs):
        super(_search_prompt, self).__init__(*args, **kwargs)

        self.forwards = forwards

        self.keybinding_table.bind(vx.keys.enter, self.getout)
        self.keybinding_table.bind(vx.ctrl + vx.keys.f, self.next)
        self.keybinding_table.bind(vx.ctrl + vx.keys.r, self.reverse)

        vx.register_key_listener(self.isearch)

        self.original_cursor = self.attached_to.cursor
        self.original_start = self.attached_to.topleft

        self.matching = False

        self.add_string(start)

    def cancel(self):
        self.attached_to.cursor = (self.original_cursor[0], self.original_cursor[1])
        self.attached_to.topleft = (self.original_start[0], self.original_start[1])
        super(_search_prompt, self).cancel()

    def reverse(self):
        self.forwards = not self.forwards
        self.next()

    def next(self):
        # TODO fix this when working with regex
        if self.matching:
            c = self.contents
            if self.forwards:
                vx.repeat(partial(vx.move_right_window, self.attached_to), times=len(c))
            else:
                vx.repeat(partial(vx.move_left_window, self.attached_to), times=len(c))
                vx.move_left_window(self.attached_to)

    def isearch(self):
        self.search()

    def dosearch(self, window, search_for, forwards):
        l, c, o = vx.get_linecoloffset_of_str(window, search_for, forwards)
        return l, c, o, len(search_for)

    def search(self):
        self.set_color(-1, -1)
        search_for = self.contents
        if not search_for: self.attached_to.color_tags.clear(); return
        l, c, o, length = self.dosearch(self.attached_to, search_for, int(self.forwards))
        if o == -1:
            self.attached_to.cursor = (self.original_cursor[0], self.original_cursor[1])
            self.attached_to.color_tags.clear()
            self.set_color(-1, 11)
            self.matching = False
            return
        self.attached_to.ensure_visible(l, c + length)
        self.matching = True
        self.attached_to.cursor = (l, c)
        self.attached_to.color_tags.clear()
        self.attached_to.add_color_tag(l, c, length, 1, 10)
        if not self.forwards:
            vx.repeat(partial(vx.move_right_window, self.attached_to), times=length)

    def getout(self):
        c = self.contents
        if self.matching:
            if self.forwards:
                vx.repeat(partial(vx.move_right_window, self.attached_to), times=len(c))
        y, x = vx.get_window_size(self)
        self.attached_to.grow(bottom=y)
        self.attached_to.focus()
        self.remove(force=True)
        vx.unregister_key_listener(self.isearch)
        self.attached_to.color_tags.clear()

@vx.expose
class _regex_prompt(_search_prompt):
    def dosearch(self, window, search_for, forwards):
        return text.find_regex(search_for, window)
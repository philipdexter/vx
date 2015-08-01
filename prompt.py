import vx

import contextlib
import traceback
import sys
from io import StringIO
from os.path import isfile
from functools import partial

class _prompt(vx.window):
    def __init__(self, attached_to=None):
        if attached_to is None:
            attached_to = vx.window.focused_window
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
        vx.focus_window(self.attached_to)
        self.remove(force=True)

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

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
        vx.focus_window(self.attached_to)
        contents = vx.get_contents_window(self)
        _exec_prompt._history.append(contents)
        with stdoutIO() as s:
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
                vx.add_string(s)
            else:
                vx.add_string(tb)
        self.remove(force=True)

    def _enter_and_expand(self):
        self.expand()
        vx.add_string('\n')

    def expand(self):
        self.attached_to.pad(bottom=1)
        self.grow(top=1)

    def _history_pullback(self):
        if len(_exec_prompt._history) > 0:
            vx.clear_contents_window(self)
            vx.add_string(_exec_prompt._history[-1])

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
            contents = vx.get_contents_window(self)
            self.old_contents = contents
            vx.clear_contents_window(self)
            self.files = glob.glob('{}*'.format(contents))
            if len(self.files) == 0:
                self.completing = False
        if len(self.files) == 0:
            self.completing = False
            vx.clear_contents_window(self)
            vx.add_string(self.old_contents)
        else:
            completion = self.files.pop()
            vx.clear_contents_window(self)
            vx.add_string(completion)

    def getout(self, force=False, cancel_open=False):
        if not force and self.attached_to.dirty:
            self.attached_to.focus()
            _yn_prompt('Window is dirty, really open another file?',
                       partial(self.getout, force=True),
                       partial(self.getout, force=True, cancel_open=True))
            return
        y, x = vx.get_window_size(self)
        self.attached_to.grow(bottom=y)
        vx.focus_window(self.attached_to)
        if not cancel_open:
            contents = vx.get_contents_window(self)
            if isfile(contents):
                self.attached_to.attach_file(contents)
                self.attached_to.dirty = False
            else:
                split = self.attached_to.split_h()
                split.focus()
                vx.add_string('file "{}" does not exist'.format(contents))
        self.remove(force=True)

@vx.expose
class _yn_prompt(_prompt):
    def __init__(self, message, yes, no, *args, **kwargs):
        super(_yn_prompt, self).__init__(*args, **kwargs)

        self.yes = yes
        self.no = no

        self.keybinding_table.bind(vx.keys.enter, self.getout)

        vx.add_string('{} (y/n): '.format(message))

    def getout(self):
        contents = vx.get_contents_window(self)
        ret = False
        try:
            answer = contents.split(':')[1].strip()
            if answer.lower() in ('y', 'yes'):
                ret = True
        except:
            return
        y, x = vx.get_window_size(self)
        self.attached_to.grow(bottom=y)
        vx.focus_window(self.attached_to)
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

        vx.add_string(message)

        vx.schedule(seconds, self.getout)

        self.attached_to.focus()

    def getout(self):
        y, x = vx.get_window_size(self)
        self.attached_to.grow(bottom=y)
        vx.focus_window(self.attached_to)
        self.remove(force=True)

import vx
from vx import bind, alt, ctrl, keys, window

import sys
from functools import partial

# which keybinding do we want
from keybindings import hopscotch

vx.default_start()

bind(ctrl + keys.x - '4', vx.prompt)

import vx

from sys import argv
from functools import partial

vx.my_vx = lambda: None
vx.status_line = lambda: 'status line'

vx.files = argv[1:]

import utils
import keybindings
import windows

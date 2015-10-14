import vx
from vx.window import window
from vx.keybindings import barebones, alt, ctrl, keys, keybinding_tables
from vx.scratchbuffer import scratchbuffer
from vx.pane import pane
from vx.pointer import organizer

def start():
    vx.default_keybindings = barebones.load
    keybindings = '''
Ctrl+q - quit
Ctrl+n - move down
Ctrl+p - move up
Ctrl+f - move right
Ctrl+b - move left
'''
    sb = scratchbuffer(vx.rows, vx.cols, 0, 0)
    p = pane(sb, vx.rows, vx.cols, 0, 0)
    organizer.add_pane(p)
    organizer.switch_to_pane(p)

    def _copy_rc_py():
        import os.path
        vx.movement.end()
        if os.path.isfile(os.path.expanduser('~/.vx/rc.py')):
            sb.add_string('you already have a ~/.vx/rc.py\n')
        else:
            contents = sb.contents
            rc_py = contents.split('\'\'\'')[1]
            os.makedirs(os.path.expanduser('~/.vx'), exist_ok=True)
            with open(os.path.expanduser('~/.vx/rc.py'), 'w') as f:
                      f.write(rc_py)
            sb.add_string('copied!')
    sb.keybinding_table.bind(ctrl + keys.o, _copy_rc_py)

    def _switch_to_concat():
        keybinding_tables.remove(sb.keybinding_table)
        from vx.keybindings import concat
        sb.keybinding_table = concat.load(sb)
        keybinding_tables.insert(0, sb.keybinding_table)
        sb.keybinding_table.bind(ctrl + keys.o, _copy_rc_py)
    sb.keybinding_table.bind(ctrl + keys.c, _switch_to_concat)

    def _switch_to_hopscotch():
        keybinding_tables.remove(sb.keybinding_table)
        from vx.keybindings import hopscotch
        sb.keybinding_table = hopscotch.load(sb)
        keybinding_tables.insert(0, sb.keybinding_table)
        sb.keybinding_table.bind(ctrl + keys.o, _copy_rc_py)
    sb.keybinding_table.bind(ctrl + keys.h, _switch_to_hopscotch)

    sb.add_string('''Hey!
It looks like this is your first time running vx, welcome!

This interactive process will guide you through customizing vx to your liking.

Your temporary keybindings are:
{keybindings}
If instead you would like to switch to the `concat' keybindings then press Ctrl+c at any point
If you would like to switch to the `hopscotch' keybindings then press Ctrl+h at any point

If you would like to copy a default rc.py (shown below) to your home directory under ~/.vx
then press Ctrl+o at any point

\'\'\'import vx

# which keybinding do we want?
from vx.keybindings import hopscotch
vx.default_keybindings = hopscotch.load

vx.default_start()
\'\'\'
'''.format(keybindings=keybindings))
    vx.movement.beg()

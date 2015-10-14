import vx
from vx.window import window
from vx.keybindings import barebones, alt, ctrl, keys, keybinding_tables

def start():
    vx.default_keybindings = barebones.load
    keybindings = '''
Ctrl+q - quit
Ctrl+n - move down
Ctrl+p - move up
Ctrl+f - move right
Ctrl+b - move left
'''
    w = window(vx.rows, vx.cols, 0, 0)
    w.blank()
    w.focus()

    def _copy_rc_py():
        import os.path
        vx.movement.end()
        if os.path.isfile(os.path.expanduser('~/.vx/rc.py')):
            w.add_string('you already have a ~/.vx/rc.py\n')
        else:
            contents = w.contents
            rc_py = contents.split('\'\'\'')[1]
            with open(os.path.expanduser('~/.vx/rc.py'), 'w') as f:
                      f.write(rc_py)
            w.add_string('copied!')
    w.keybinding_table.bind(ctrl + keys.o, _copy_rc_py)

    def _switch_to_concat():
        keybinding_tables.remove(w.keybinding_table)
        from vx.keybindings import concat
        w.keybinding_table = concat.load(w)
        keybinding_tables.insert(0, w.keybinding_table)
        w.keybinding_table.bind(ctrl + keys.o, _copy_rc_py)
    w.keybinding_table.bind(ctrl + keys.c, _switch_to_concat)

    w.add_string('''Hey!
It looks like this is your first time running vx, welcome!

This interactive process will guide you through customizing vx to your liking.

Your temporary keybindings are:
{keybindings}
If instead you would like to switch to the `concat' keybindings then press Ctrl+c at any point

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

import vx
import vx_mod.text as text
import vx_mod.movement as move
from vx_mod.window import windows

import traceback

_tests = []
def register_test(test):
    _tests.append(test)

def check(a, b):
    if a != b:
        raise AssertionError('{} is not {}\n'.format(a, b))

def check_items(a, b):
    for x, y in zip(a, b):
        check(x, y)

@vx.expose
def _run_tests():
    try:
        w = windows.focused
        w.blank()


        def check_at(s, a, forwards=True):
            check_items(vx.get_linecoloffset_of_str(w, s, int(forwards)), a)

        text.add_string(
'''
Tests are being run
''')
        move.beg()

        text.add_string('öäå')
        move.beg()

        check_at('ä', (1, 2, 1))
        check_at('ä', (1, 2, 1))
        check_at('öäå', (1, 1, 0))
        check_at('öäå\n', (1, 1, 0))

        move.down()

        check_at('ö', (1, 1, 4), False)

        move.eol()

        check_at('ö', (1, 1, 23), False)
        check_at('ä', (1, 2, 22), False)

        vx.set_linecol_window(w, 1, 2)

        check_at('ä', (1, 2, 0))
        check_at('å', (1, 3, 1))
        check_at('öäå', (1, 1, 1), False)
        check_at('öäå\n', (1, 1, 1), False)
        check_at('å\n', (1, 3, 1))

        for t in _tests:
            t()

        move.end()
        text.add_string('''
All tests have passed
''')
    except AssertionError as e:
        move.end()
        text.add_string('\n\n')
        text.add_string(traceback.format_exc())

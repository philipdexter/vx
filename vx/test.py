import vx
import vx.movement as move
from .pointer import windows

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

def profile():
    import cProfile
    from . import utils

    w = windows.focused

    with utils.stdoutIO() as s:
        cProfile.run('''import vx
import vx.pointer
w = vx.pointer.windows.focused
# for _ in range(10000):
#   vx.get_contents_window(w)
s = vx.get_contents_window(w)
for _ in range(10000):
  s = s[0:100] + 'a' + s[100:]
''')

    w.blank()

    w.add_string(s.getvalue())

def run_tests():
    try:
        w = windows.focused
        w.blank()


        def check_at(s, a, forwards=True):
            check_items(vx.get_linecoloffset_of_str(w, s, int(forwards)), a)

        w.add_string(
'''
Tests are being run
''')
        move.beg()

        w.add_string('öäå')
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
        w.add_string('''
All tests have passed
''')
    except AssertionError as e:
        move.end()
        w.add_string('\n\n')
        w.add_string(traceback.format_exc())

import vx

import traceback

def check(a, b):
    if a != b:
        raise AssertionError('{} is not {}\n'.format(a, b))

@vx.expose
def _run_tests():
    try:
        w = vx.window.focused_window
        w.blank()

        vx.add_string(
'''Hello
this is a test
''')
        vx.move_beg()

        vx.add_string('öäå')
        vx.move_beg()
        _, _, o = vx.get_linecoloffset_of_str(w, 'ä')
        check(o, 2)
    except AssertionError as e:
        vx.move_end()
        vx.add_string('\n\n')
        vx.add_string(traceback.format_exc())

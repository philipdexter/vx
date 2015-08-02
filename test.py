import vx

def check(a, b):
    if a != b:
        vx.move_end()
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

        vx.add_string('öäåä')
        vx.move_beg()
        _, _, o = vx.get_linecoloffset_of_str(w, 'ä')
        check(o, 2)
    except AssertionError as e:
        vx.add_string('FAILED: {}'.format(e))

import editor

editor.status_line = 'status line-------'

@editor.bind(editor.alt + 'd')
def down_more():
    editor.move_down()
    editor.move_down()
    editor.move_down()
    editor.move_down()

editor.bind(editor.ctrl + 'N', editor.move_down)
editor.bind(editor.ctrl + 'P', editor.move_up)
editor.bind(editor.ctrl + 'B', editor.move_left)
editor.bind(editor.ctrl + 'F', editor.move_right)

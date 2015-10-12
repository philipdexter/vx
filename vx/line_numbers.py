from .buffer import buffer

class line_numbers(buffer):
    def __init__(self, attached_to):
        width = len(str(attached_to.get_text_lines()))
        super(line_numbers, self).__init__(attached_to.rows, width,
                                           attached_to.y, attached_to.x)
        self.attached_to = attached_to

        self.blank()
        self.set_color(9, -1)

        self.id = 'line-numbers'

    def prepare(self):
        super(line_numbers, self).prepare()
        self.set_text('h')
        y, _ = self.attached_to.topleft
        r, _ = self.attached_to.size
        width = self.columns
        lines = self.attached_to.get_text_lines()+1
        self.set_text(''.join(
            list(map(lambda x: ' ' * (width - len(str(x))) + str(x), range(y, min(y+r,lines))))
            +
            list(map(lambda x: ' ' * (width - 1) + '~', range(min(y+r, lines), y+r)))
        ))

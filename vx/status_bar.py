from .buffer import buffer

class status_bar(buffer):
    def __init__(self, attached_to):
        super().__init__(1, attached_to.columns,
                                         attached_to.y + attached_to.rows - 1, attached_to.x)
        self.attached_to = attached_to
        self.text = lambda b: 'line: {} col: {} - {}{}'.format(b.line,
                                                               b.col,
                                                               b.filename if hasattr(b, 'filename') else '<none>',
                                                               '(d)' if b.dirty else '')
        self.default_text = self.text

        self.blank()
        self.set_color(5, -1)

        self.id = 'status_bar'

    def set_status_text(self, text):
        if callable(text):
            self.text = text
        else:
            self.text = lambda _: text

    def append_text(self, text):
        if not callable(text):
            texta = text
            text = lambda _: texta
        old_text = self.text
        self.text = lambda window: '{}{}'.format(old_text(window), text(window))

    def reset_default_text(self):
        self.text = self.default_text

    def prepare(self):
        super().prepare()
        self.set_text(self.text(self.attached_to))

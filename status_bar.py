import vx

def _status_bar_update(self):
    self.set_text('line: {} col: {} / rows: {} cols: {}\n'.format(vx.line,
                                                                  vx.col,
                                                                  vx.rows,
                                                                  vx.cols))

status_bar = vx.window(2, vx.cols, vx.rows - 1, 0, refresh=_status_bar_update, traversable=False)
status_bar.blank()
status_bar.set_color(5, -1)

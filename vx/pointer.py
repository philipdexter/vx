import vx

class _organizer:
    class pane_tree:
        def __init__(self):
            self.node = None

    def __init__(self):
        self.tree = _organizer.pane_tree()

    def fit_below(self, above, below):
        new_rows = above.rows // 2
        new_columns = above.columns
        above.resize(new_rows, new_columns)

        below.resize(new_rows, new_columns)
        below.move(above.y + above.rows, above.x)

    def remove_pane(self, p, tree=None):
        from .pane import pane

        if tree is None:
            panes.remove(p)

        if tree is None:
            tree = self.tree

        if tree is None:
            raise Exception('should not happen')

        if isinstance(tree.node[0], pane) and p == tree.node[0]:
            more_rows = tree.node[0].rows
            tree.node[1].grow(top=more_rows)
            tree.node[0].remove()
            self.switch_to_pane(tree.node[1])
            tree.node = tree.node[1]
            return True
        elif isinstance(tree.node[1], pane) and p == tree.node[1]:
            more_rows = tree.node[0].rows
            tree.node[0].grow(bottom=more_rows)
            tree.node[1].remove()
            self.switch_to_pane(tree.node[0])
            tree.node = tree.node[0]
            return True
        else:
            found = False
            if tree.node[0] and not isinstance(tree.node[0], pane):
                found = self.remove_pane(p, tree=tree.node[0])
                if isinstance(tree.node[0].node, pane):
                    tree.node[0] = tree.node[0].node
            if not found and tree.node[1] and not isinstance(tree.node[1], pane):
                found = self.remove_pane(p, tree=tree.node[1])
                if isinstance(tree.node[1].node, pane):
                    tree.node[1] = tree.node[1].node
            return found
        return False


    def add_pane(self, p, parent=None):
        from .pane import pane

        panes.add(p)

        if self.tree.node is None:
            self.tree.node = p
        elif parent is None:
            if isinstance(self.tree.node, pane):
                self.fit_below(self.tree.node, p)
                self.tree.node = [self.tree.node, p]
            else:
                node = self.tree.node
                while not isinstance(node[1], pane):
                    node = node[1].node
                self.fit_below(node[1], p)
                tmp_node = node[1]
                node[1] = _organizer.pane_tree()
                node[1].node = [tmp_node, p]

    def switch_to_pane(self, pane):
        if panes.focused is not None:
            panes.focused.unfocus()
        pane.focus()
        panes.focused = pane
        windows.focused = pane.buffer
organizer = _organizer()

class _windows:
    def __init__(self):
        self._windows = []
        self._focused = None

    def __get_focused(self):
        return self._focused
    def __set_focused(self, focused):
        self._focused = focused
    focused = property(__get_focused, __set_focused)

    def __get_all(self):
        return self._windows
    all = property(__get_all)

    def add(self, window):
        self._windows.append(window)
    def remove(self, window):
        self._windows.remove(window)

windows = _windows()

class _panes:
    def __init__(self):
        self._panes = []
        self._focused = None

    def __get_focused(self):
        return self._focused
    def __set_focused(self, focused):
        self._focused = focused
    focused = property(__get_focused, __set_focused)

    def __get_all(self):
        return self._panes
    all = property(__get_all)

    def add(self, pane):
        self._panes.append(pane)
    def remove(self, pane):
        self._panes.remove(pane)

panes = _panes()

def _tick():
    for p in panes.all:
        p.update()
vx.register_tick_function(_tick)

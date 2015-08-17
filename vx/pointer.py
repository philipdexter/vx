import vx
import operator

class _organizer:
    class pane_tree:
        def __init__(self):
            self.node = None

        def __get_rows(self):
            return self.get_f(lambda x: x.rows)
        rows = property(__get_rows)
        def __get_columns(self):
            return self.get_f(lambda x: x.columns)
        columns = property(__get_columns)
        def __get_y(self):
            return self.node[0].y
        y = property(__get_y)
        def __get_x(self):
            return self.node[0].x
        x = property(__get_x)

        def resize(self, rows, columns):
            pass

        def grow(self, top=0, bottom=0, left=0, right=0):
            if bottom > 0:
                self.node[0].grow(bottom=bottom+self.node[1].rows)
                organizer.fit_below(self.node[0], self.node[1])
            if top > 0:
                self.node[0].move(self.node[0].y - top, self.node[0].x)
                self.grow(bottom=top)

        def get_f(self, f, c=operator.add, z=0):
            from .pane import pane
            if self.node is None:
                return z
            if isinstance(self.node, pane):
                return f(pane)

            agg = z

            if isinstance(self.node[0], pane):
                agg = c(agg, f(self.node[0]))
            else:
                agg = c(agg, self.node[0].get_f(f, c, z))
            if isinstance(self.node[1], pane):
                agg = c(agg, f(self.node[1]))
            else:
                agg = c(agg, self.node[1].get_f(f, c, z))

            return agg

    def __init__(self):
        self.tree = _organizer.pane_tree()

    def fit_below(self, above, below):
        new_rows = above.rows // 2
        new_columns = above.columns
        above.resize(new_rows, new_columns)

        below.resize(new_rows, new_columns)
        below.move(above.y + above.rows, above.x)

    def next_pane(self):
        for i, p in enumerate(panes.all):
            if p == panes.focused:
                break
        self.switch_to_pane(panes.all[(i+1) % len(panes.all)])

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

            if isinstance(tree.node[1], pane):
                tree.node = tree.node[1]
                self.switch_to_pane(tree.node)
            else:
                tree = tree.node[1]
                self.switch_to_pane(tree.node[1])

            return True
        elif isinstance(tree.node[1], pane) and p == tree.node[1]:
            more_rows = tree.node[1].rows

            tree.node[0].grow(bottom=more_rows)

            tree.node[1].remove()

            if isinstance(tree.node[0], pane):
                tree.node = tree.node[0]
                self.switch_to_pane(tree.node)
            else:
                tree = tree.node[0]
                self.switch_to_pane(tree.node[0])

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

    def find_pane(self, p, tree=None):
        from .pane import pane

        if tree is None:
            tree = self.tree

        if isinstance(tree.node, pane):
            if p == tree.node: return (tree, -1)
            else: return None

        if isinstance(tree.node[0], pane) and p == tree.node[0]:
            return (tree, 0)
        if isinstance(tree.node[1], pane) and p == tree.node[1]:
            return (tree, 1)
        found = None
        if tree.node[0] and not isinstance(tree.node[0], pane):
            found = self.find_pane(p, tree.node[0])
        if not found and tree.node[1] and not isinstance(tree.node[1], pane):
            found = self.find_pane(p, tree.node[1])

        return found


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
        else:
            t, pos = self.find_pane(parent)
            if pos == -1:
                self.fit_below(t.node, p)
                t.node = [t.node, p]
            elif pos == 0 or pos == 1:
                self.fit_below(t.node[pos], p)
                tmp_node = t.node[pos]
                t.node[pos] = _organizer.pane_tree()
                t.node[pos].node = [tmp_node, p]

    def switch_to_pane(self, pane):
        if panes.focused is not None:
            panes.focused.unfocus()
        if windows.focused is not None:
            windows.focused.unfocus()
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

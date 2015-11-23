

class CopyStack:
    def __init__(self):
        self._stack = []

    def peek(self):
        return self._stack[-1]

    def peek_or_default(self, default=None):
        return self._stack[-1] if self._stack else default

    def pop(self):
        return self._stack.pop()

    def push(self, item):
        self._stack.append(item)

    def empty(self):
        return not bool(self._stack)

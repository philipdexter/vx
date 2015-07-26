import vx

def _expose(f=None, name=None):
    if name is None:
        name = f.__name__.lstrip('_')
    if getattr(vx, name, None) is not None:
        raise AttributeError("Cannot expose duplicate name: '{}'".format(name))
    if f is None:
        def g(f):
            setattr(vx, name, f)
            return f
        return g
    setattr(vx, name, f)
    return f
vx.expose = _expose

@vx.expose
def _repeat(c, times=4):
    for _ in range(times):
        c()

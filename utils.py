import vx

def _expose(f, name=None):
    if name is None:
        name = f.__name__.lstrip('_')
    setattr(vx, name, f)
    return f
vx.expose = _expose

@vx.expose
def _repeat(c, times=4):
    for _ in range(times):
        c()

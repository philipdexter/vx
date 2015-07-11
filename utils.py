import vx

def _repeat(c, times=4):
    for _ in range(times):
        c()

vx.repeat = _repeat

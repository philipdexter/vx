import vx

import sched

_sched = sched.scheduler()

@vx.expose
def _schedule(seconds, command, priority=1):
    _sched.enter(seconds, priority, command)

def _tick():
    _sched.run(blocking=False)
vx.register_tick_function(_tick)

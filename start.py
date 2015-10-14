try:
    import rc
except ImportError:
    import vx

    # which keybinding do we want
    from vx.keybindings import hopscotch
    vx.default_keybindings = hopscotch.load

    vx.default_start()

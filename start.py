try:
    import rc
except ImportError:
    import vx

    # which keybinding do we want
    from keybindings import hopscotch

    vx.default_start()

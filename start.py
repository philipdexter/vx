try:
    import rc
except ImportError:
    import vx

    # which keybinding do we want
    from vx_mod.keybindings import concat
    vx.default_keybindings = concat.load

    vx.default_start()

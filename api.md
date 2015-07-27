# vx API

## Core

*Enabled by default.*

`vx.windows` - an iterable of all open *windows* (including status bars, prompts, etc)
`vx.panes` - an iterable of all open *panes* (only primary windows)
`vx.buffers` - an iterable of all open *buffers* (files)

`vx.windows.focus` - points to the focused *window*
`vx.panes.focus` - points to the focused *pane*
`vx.buffers.focus` - points to the focused *buffer*

`vx.save()` - save the focused buffer
`vx.quit()` - completely exit vx

`vx.insert(string)` - insert the string at the cursor
`vx.delete()` - delete under the cursor

`vx.move` - contains all movement commands
`vx.move.up()`
`vx.move.down()`
`vx.move.left()`
`vx.move.right()`
`vx.move.bol()` - beginning of line
`vx.move.eol()` - end of line
`vx.move.bof()` - beginning of file
`vx.move.eof()` - end of file

## Built-in

*Included in standard package, but not enabled by default.*

`vx.status` - add status bars to a pane
`vx.status` should be assigned to a function that accepts one parameter - the
  pane that it's being displayed on

`vx.prompt` - add prompts
`vx.prompt.confirm` - prompts the user for y/n input
`vx.prompt.text` - prompts the user for text (can be passed to `exec()`, a
  custom handler, etc)
`vx.prompt.file` - prompts the user for a filename

`vx.keys` - bind key combinations to commands
`vx.keys.bind(key, cmd)` - bind `key` to perform `cmd`
`vx.keys.unbind(key)` - unbind `key` from all commands

`vx.keys.hopscotch` - default bindings, inspired by Emacs
`vx.keys.vigor` - default bindings, inspired by Vim

`vx.undo` - add undo history

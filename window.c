#include "window.h"

#include <stdlib.h>

Window *new_window(void)
{
	Window *window = calloc(1, sizeof(Window));
	if (!window) return NULL;
	window->line = 1;
	return window;
}

int build_window(Window *window, int nlines, int ncols, int begin_y, int begin_x)
{
	if (!window) return -1;

	if (window->curses_window)
		if (0 != delete_window(window))
			return -1;
	window->curses_window = newwin(nlines, ncols, begin_y, begin_x);
	window->lines = (size_t)nlines;
	window->columns = (size_t)ncols;

	return 0;
}

int delete_window(Window *window)
{
	if (OK != delwin(window->curses_window))
		return -1;
	free(window->buffer);
	window->buffer = NULL;
	return 0;
}

void attach_buffer(Window *window, Buffer *buffer)
{
	if (window->buffer) {
		free(window->buffer); // TODO create and use delete_buffer function
	}
	window->buffer = buffer;
}

int refresh_window(Window *window)
{
	if (OK != wrefresh(window->curses_window))
		return -1;
	return 0;
}

int print_string(Window *window, char *str)
{
	if (OK != waddstr(window->curses_window, str))
		return -1;
	return 0;
}

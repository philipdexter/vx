#include "window.h"

#include <stdlib.h>

Window *new_window(void)
{
	Window *window = calloc(1, sizeof(Window));
	if (!window) return NULL;
	window->line = 1;
	return window;
}

void delete_window(Window *window)
{
	delwin(window->curses_window);
	if (window->buffer)
		delete_buffer(window->buffer);
	free(window);
}

void resize_window(Window *window, int lines, int columns)
{
	wresize(window->curses_window, lines, columns);
	window->lines = lines;
	window->columns = columns;
}

void move_window(Window *window, int y, int x)
{
	mvwin(window->curses_window, y, x);
}

int build_window(Window *window, int nlines, int ncols, int begin_y, int begin_x)
{
	if (!window) return -1;

	if (window->curses_window)
		if (OK != delwin(window->curses_window))
			return -1;
	window->curses_window = newwin(nlines, ncols, begin_y, begin_x);
	window->lines = (size_t)nlines;
	window->columns = (size_t)ncols;

	return 0;
}

void attach_buffer(Window *window, Buffer *buffer)
{
	if (window->buffer) {
		free(window->buffer);
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

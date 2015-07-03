#include "window.h"

#include <stdlib.h>

Window *new_window(void)
{
	Window *window = calloc(1, sizeof(Window));
	window->line = 1;
	return window;
}

void build_window(Window *window, int nlines, int ncols, int begin_y, int begin_x)
{
	window->curses_window = newwin(nlines, ncols, begin_y, begin_x);
	window->lines = nlines;
	window->columns = ncols;
}

void delete_window(Window *window)
{
	delwin(window->curses_window);
}

void attach_buffer(Window *window, Buffer *buffer)
{
	window->buffer = buffer;
}

void refresh_window(Window *window)
{
	wrefresh(window->curses_window);
}

void print_string(Window *window, char *str)
{
	waddstr(window->curses_window, str);
}

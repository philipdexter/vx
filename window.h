#ifndef WINDOW_H
#define WINDOW_H

#include <curses.h>

#include "buffer.h"

typedef struct _WINDOW {
	size_t line;
	size_t lines;
	size_t columns;
	WINDOW *curses_window;
	Buffer *buffer;
} Window;

Window *new_window(void);
int build_window(Window*, int, int, int, int);
int delete_window(Window*);
void attach_buffer(Window*, Buffer*);
int refresh_window(Window*);
int print_string(Window*, char*);

#endif

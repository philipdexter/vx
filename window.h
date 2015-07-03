#ifndef WINDOW_H
#define WINDOW_H

#include <curses.h>

#include "buffer.h"

typedef struct _WINDOW {
	WINDOW *curses_window;
	Buffer *buffer;
} Window;

Window *new_window(void);
void build_window(Window*, int, int, int, int);
void delete_window(Window*);
void attach_buffer(Window*, Buffer*);
void refresh_window(Window*);
void print_string(Window*, char*);

#endif

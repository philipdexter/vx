#ifndef WINDOW_H
#define WINDOW_H

#include <curses.h>

#include "buffer.h"

typedef struct _WINDOW {
	size_t line;
	size_t lines;
	size_t column;
	size_t columns;
	WINDOW *curses_window;
	Buffer *buffer;
} Window;

Window *new_window(void);
void delete_window(Window*);
void resize_window(Window*, int, int);
void move_window(Window*, int, int);
void get_window_size(Window*, int*, int*);
int build_window(Window*, int, int, int, int);
void attach_buffer(Window*, Buffer*);
int refresh_window(Window*);
int print_string(Window*, char*);

#endif

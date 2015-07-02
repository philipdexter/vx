#ifndef TEXT_H
#define TEXT_H

#include <stddef.h>

typedef struct _TEXT {
	size_t size;
	size_t gap_start;
	size_t text_start;
	char *buf;
} Text;

Text *new_document(void);
void resize_gap(Text*, size_t);
void add_character(Text*, char);
void add_string(Text*, char*, size_t);
void move_cursor(size_t pos);
void move_cursor_to_beg(Text *text);
void move_cursor_bol(Text*);
void move_cursor_eol(Text*);
const char *get_str(Text*);
const char *get_str_from_line(Text*, size_t);
size_t get_cursor_pos(Text *text);
void get_cursor_rowcol(Text *text, int *row, int *col);
void backspace(Text *text);
void move_left(Text *text);
void move_right(Text *text);
void move_up(Text *text);
void move_down(Text *text);

#endif

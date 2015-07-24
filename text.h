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
void delete_text(Text*);
void clear_text(Text*);
int resize_gap(Text*, size_t);
int add_character(Text*, char);
int add_string(Text*, char*, size_t);
int move_cursor_to_beg(Text *text);
int move_cursor_to_end(Text *text);
int move_cursor_bol(Text*);
int move_cursor_eol(Text*);
char *get_str(Text*);
char *get_str_from_line(Text*, size_t);
char *get_str_from_line_to_line(Text*, size_t, size_t);
size_t get_cursor_pos(Text *text);
int get_rowcoloffset_of_char(Text*, char*, int*, int*, int*);
char *get_ch_rowcol(Text *text, int row, int col);
char *get_chars_rowcol(Text *text, int row, int col, int);
void get_cursor_rowcol(Text *text, int *row, int *col);
void set_cursor_rowcol(Text *text, int row, int col);
void backspace(Text *text, int);
void move_left(Text *text);
void move_right(Text *text);
void move_up(Text *text);
void move_down(Text *text);

extern const char more_bytes_utf8[];

#endif

#include "text.h"

#include <stdlib.h>
#include <string.h>

#define GAPSIZE(t) (t->text_start - t->gap_start)
#define NBYTES(t) ((t->size - t->text_start) + (t->gap_start))

#define RESIZE_BY 20

Text *new_document(void)
{
	Text *beg = calloc(1, sizeof(Text));
	return beg;
}

void resize_gap(Text *text, size_t new_gap)
{
	size_t gap = GAPSIZE(text);

	// resize_gap can't downsize
	if (new_gap <= gap)
		return;

	size_t expand_by = new_gap - gap;
	size_t old_size = text->size;
	size_t new_size = text->size + expand_by;
	text->size = new_size;
	size_t old_start = text->text_start;
	text->text_start += expand_by;
	char *old_buf = text->buf;
	text->buf = (char*)calloc(1, new_size);
	memcpy(text->buf, old_buf, text->gap_start);
	memcpy(text->buf + text->text_start, old_buf + old_start, old_size - old_start);
	free(old_buf);
}

void add_character(Text *text, char c)
{
	size_t freespace = GAPSIZE(text);
	if (freespace <= 1)
		resize_gap(text, RESIZE_BY);
	text->buf[text->gap_start++] = c;
}

void add_string(Text *text, char *buf, size_t len)
{
	size_t freespace = GAPSIZE(text);
	if (freespace < len + 1)
		resize_gap(text, RESIZE_BY + len);
	memcpy(text->buf + text->gap_start, buf, len);
	text->gap_start += len;
}

void move_cursor(size_t pos)
{
	;
}

void move_cursor_bol(Text *text)
{
	int i = text->gap_start-1;
	for (; i >= 0; i = text->gap_start-1) {
		if (text->buf[i] == '\n') break;
		move_left(text);
	}
}

void move_cursor_eol(Text *text)
{
	int i = text->text_start;
	for (; text->size - text->text_start > 0; i = text->text_start) {
		if (text->buf[i] == '\n') break;
		move_right(text);
	}
}

void move_cursor_to_beg(Text *text)
{
	size_t gap = GAPSIZE(text);

	char *old_buf = text->buf;
	text->buf = (char*)calloc(1, text->size + 1);
	memcpy(text->buf + gap, old_buf, text->gap_start);
	memcpy(text->buf + gap + text->gap_start, old_buf + text->text_start, text->size - text->text_start);
	text->gap_start = 0;
	text->text_start = gap;

	free(old_buf);
}

void move_cursor_to_end(Text *text)
{
	size_t gap = GAPSIZE(text);

	char *old_buf = text->buf;
	text->buf = (char*)calloc(1, text->size + 1);
	memcpy(text->buf, old_buf, text->gap_start);
	memcpy(text->buf + text->gap_start, old_buf + text->text_start, text->size - text->text_start);
	text->gap_start = text->size - gap;
	text->text_start = text->size;

	free(old_buf);
}

char *get_str(Text *text)
{
	char *buf = calloc(1, NBYTES(text) + 1);
	memcpy(buf, text->buf, text->gap_start);
	memcpy(buf + text->gap_start, text->buf + text->text_start, text->size - text->text_start);
	return buf;
}

char *get_str_from_line(Text *text, size_t line)
{
	size_t pos_line = 1;
	size_t i;
	for (i = 0; i < text->size; ++i) {
		if (pos_line == line) {
			break;
		}
		if (i == text->gap_start) {
			i += GAPSIZE(text) - 1;
			continue;
		}
		if (text->buf[i] == '\n') {
			++pos_line;
		}
	}

	char *buf = calloc(1, NBYTES(text) - i + 1);
	if (i <= text->gap_start) {
		memcpy(buf, text->buf + i, text->gap_start - i);
		memcpy(buf + text->gap_start - i, text->buf + text->text_start, text->size - text->text_start);
	} else {
		memcpy(buf, text->buf + i, text->size - text->text_start - i);
	}
	return buf;
}

size_t get_cursor_pos(Text *text)
{
	return text->gap_start;
}

void get_cursor_rowcol(Text *text, int *row, int *col)
{
	int r = 0, c = 0;
	for (int i = 0; i < text->gap_start; ++i) {
		if (text->buf[i] == '\n') {
			++r; c = 0;
		} else {
			++c;
		}
	}
	*row = r;
	*col = c;
}

void backspace(Text *text)
{
	if (text->gap_start > 0)
		--text->gap_start;
}

void move_left(Text *text)
{
	if (text->gap_start > 0) {
		text->buf[text->text_start-1] = text->buf[text->gap_start-1];
		--text->text_start;
		--text->gap_start;
	}
}

void move_right(Text *text)
{
	if (text->size - text->text_start > 0) {
		text->buf[text->gap_start] = text->buf[text->text_start];
		++text->text_start;
		++text->gap_start;
	}
}

void move_up(Text *text)
{
	int col = 0;
	int i = text->gap_start-1;
	for (; i > 0; i = text->gap_start-1, ++col) {
		if (text->buf[i] == '\n') break;
		move_left(text);
	}
	move_left(text);
	i = text->gap_start-1;
	for (; i >= 0; i = text->gap_start-1) {
		if (text->buf[i] == '\n') break;
		move_left(text);
	}
	for (int j = 0; j < col; i = text->gap_start-1, ++j) {
		if(text->buf[text->text_start] == '\n') break;
		move_right(text);
	}
}

void move_down(Text *text)
{
	int col = 0;
	int i = text->gap_start-1;
	for (; i >= 0; i = text->gap_start-1, ++col) {
		if (text->buf[i] == '\n') break;
		move_left(text);
	}
	i = text->text_start;
	for (; text->size - text->text_start > 0; i = text->text_start) {
		if (text->buf[i] == '\n') break;
		move_right(text);
	}
	move_right(text);
	i = text->text_start;
	for (int j = 0; j < col; i = text->text_start, ++j) {
		if(text->buf[i] == '\n') break;
		move_right(text);
	}
}

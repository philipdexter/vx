#include "text.h"

#include <unistd.h>
#include <stdlib.h>
#include <string.h>

#define GAPSIZE(t) (t->text_start - t->gap_start)
#define NBYTES(t) ((t->size - t->text_start) + (t->gap_start))
#define MIN(a, b) (a < b ? a : b)

#define RESIZE_BY 20

const char more_bytes_utf8[256] = {
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
	2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,4,4,4,4,5,5,5,5
};

Text *new_document(void)
{
	return calloc(1, sizeof(Text));
}

void delete_text(Text *text)
{
	free(text->buf);
	free(text);
}

int resize_gap(Text *text, size_t new_gap)
{
	size_t gap = GAPSIZE(text);
	size_t expand_by;
	size_t old_size, new_size;
	size_t old_start;
	char *old_buf;

	// resize_gap can't downsize
	if (new_gap <= gap)
		return 0;

	expand_by = new_gap - gap;
	old_size = text->size;
	new_size = text->size + expand_by;
	text->size = new_size;
	old_start = text->text_start;
	text->text_start += expand_by;
	old_buf = text->buf;
	text->buf = (char*)calloc(1, new_size);
	if (!text->buf) {
		text->buf = old_buf;
		return -1;
	}
	memcpy(text->buf, old_buf, text->gap_start);
	memcpy(text->buf + text->text_start, old_buf + old_start, old_size - old_start);
	free(old_buf);

	return 0;
}

int add_character(Text *text, char c)
{
	size_t freespace = GAPSIZE(text);
	if (freespace <= 1)
		if (0 != resize_gap(text, RESIZE_BY))
			return -1;
	text->buf[text->gap_start++] = c;

	return 0;
}

int add_string(Text *text, char *buf, size_t len)
{
	size_t freespace = GAPSIZE(text);

	if (freespace < len + 1)
		if (0 != resize_gap(text, RESIZE_BY + len))
			return -1;
	memcpy(text->buf + text->gap_start, buf, len);
	text->gap_start += len;

	return 0;
}

int move_cursor_bol(Text *text)
{
	ssize_t i = text->gap_start-1;
	for (; i >= 0; i = text->gap_start-1) {
		if (text->buf[i] == '\n') break;
		move_left(text);
	}

	return 0;
}

int move_cursor_eol(Text *text)
{
	size_t i = text->text_start;
	for (; text->size - text->text_start > 0; i = text->text_start) {
		if (text->buf[i] == '\n') break;
		move_right(text);
	}

	return 0;
}

int move_cursor_to_beg(Text *text)
{
	size_t gap = GAPSIZE(text);

	char *old_buf = text->buf;
	text->buf = (char*)calloc(1, text->size + 1);
	if (!text->buf) {
		text->buf = old_buf;
		return -1;
	}
	memcpy(text->buf + gap, old_buf, text->gap_start);
	memcpy(text->buf + gap + text->gap_start, old_buf + text->text_start, text->size - text->text_start);
	text->gap_start = 0;
	text->text_start = gap;

	free(old_buf);

	return 0;
}

int move_cursor_to_end(Text *text)
{
	size_t gap = GAPSIZE(text);

	char *old_buf = text->buf;
	text->buf = (char*)calloc(1, text->size + 1);
	if (!text->buf) {
		text->buf = old_buf;
		return -1;
	}
	memcpy(text->buf, old_buf, text->gap_start);
	memcpy(text->buf + text->gap_start, old_buf + text->text_start, text->size - text->text_start);
	text->gap_start = text->size - gap;
	text->text_start = text->size;

	free(old_buf);

	return 0;
}

char *get_str(Text *text)
{
	char *buf = calloc(1, NBYTES(text) + 1);
	if (!buf) return NULL;
	memcpy(buf, text->buf, text->gap_start);
	memcpy(buf + text->gap_start, text->buf + text->text_start, text->size - text->text_start);
	return buf;
}

char *get_str_from_line(Text *text, size_t line)
{
	size_t pos_line = 1;
	size_t i;
	char *buf;
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

	buf = calloc(1, NBYTES(text) - i + 1);
	if (!buf) return NULL;
	if (i <= text->gap_start) {
		memcpy(buf, text->buf + i, text->gap_start - i);
		memcpy(buf + text->gap_start - i, text->buf + text->text_start, text->size - text->text_start);
	} else {
		memcpy(buf, text->buf + i, text->size - text->text_start - i);
	}
	return buf;
}

char *get_str_from_line_to_line(Text *text, size_t from, size_t to)
{
	size_t pos_line = 1;
	size_t pos_end = 1;
	size_t i;
	size_t j;
	char *buf;

	for (i = 0; i < text->size; ++i) {
		if (pos_line == from) {
			break;
		}
		if (i == text->gap_start) {
			i += GAPSIZE(text) - 1;
			continue;
		}
		if (text->buf[i] == '\n') {
			++pos_line;
			++pos_end;
		}
	}
	for (j = i; j < text->size; ++j) {
		if (pos_end == to+1) {
			break;
		}
		if (j == text->gap_start) {
			j += GAPSIZE(text) - 1;
			continue;
		}
		if (text->buf[j] == '\n') {
			++pos_end;
		}
	}

	buf = calloc(1, j - i + 1);
	if (!buf)
		return NULL;
	if (i <= text->gap_start) {
		size_t end = MIN(text->gap_start, j);
		size_t len = end - i;
		size_t send = MIN(text->size, j);
		memcpy(buf, text->buf + i, len);
		if (send > text->text_start) {
			size_t slen = send - text->text_start;
			memcpy(buf + len, text->buf + text->text_start, slen);
		}
	} else {
		size_t end = MIN(text->size, j);
		size_t len = end - text->text_start - i;
		memcpy(buf, text->buf + i, len);
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
	size_t i, bytes;
	for (i = 0; i < text->gap_start; ++i) {
		if (text->buf[i] == '\n') {
			++r; c = 0;
		} else if (text->buf[i] == '\t') {
			c += 8;
		} else {
			// Handle unicode
			bytes = more_bytes_utf8[(unsigned int)(unsigned char)text->buf[i]];
			i += bytes;
			++c;
		}
	}
	*row = r;
	*col = c;
}

void set_cursor_rowcol(Text *text, int row, int col)
{
	int r, c;
	size_t i, bytes;
	int diff;

	--row, --col;

	get_cursor_rowcol(text, &r, &c);
	diff = abs(r - row);
	for (i = 0; i < diff; ++i)
		r > row ? move_up(text) : move_down(text);

	get_cursor_rowcol(text, &r, &c);

	diff = abs(c - col);
	for (i = 0; i < diff; ++i)
		if (text->buf[text->text_start] != '\n')
			c > col ? move_left(text) : move_right(text);
}

void backspace(Text *text, int delete)
{
	if (delete && text->text_start < text->size)
		++text->text_start;
	else if (!delete && text->gap_start > 0)
		--text->gap_start;
}

int is_utf8_start(unsigned char c)
{
	return c <= 0x7F || (c & 0xC0) != 0xC0;
}

void move_left(Text *text)
{
	if (text->gap_start > 0) {
		do {
			text->buf[text->text_start-1] = text->buf[text->gap_start-1];
			--text->text_start;
			--text->gap_start;
		} while (text->gap_start > 0 && !is_utf8_start(text->buf[text->gap_start - 1]));
	}
}

void move_right(Text *text)
{
	int bytes, i;
	if (text->size - text->text_start > 0) {
		// Handle unicode
		bytes = more_bytes_utf8[(unsigned int)(unsigned char)text->buf[text->text_start]] + 1;

		for (i = 0; i < bytes; ++i) {
			text->buf[text->gap_start] = text->buf[text->text_start];
			++text->text_start;
			++text->gap_start;
		}
	}
}

void move_up(Text *text)
{
	int col = 0;
	ssize_t j;
	ssize_t i = text->gap_start-1;
	for (; i > 0; i = text->gap_start-1, ++col) {
		if (text->buf[i] == '\n') break;
		move_left(text);
	}
	move_left(text);
	j = text->gap_start-1;
	for (; j >= 0; j = text->gap_start-1) {
		if (text->buf[j] == '\n') break;
		move_left(text);
	}
	for (j = 0; j < col; i = text->gap_start-1, ++j) {
		if(text->buf[text->text_start] == '\n') break;
		move_right(text);
	}
}

void move_down(Text *text)
{
	int col = 0;
	ssize_t i = text->gap_start-1;
	ssize_t j;
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
	for (j = 0; j < col; i = text->text_start, ++j) {
		if(text->buf[i] == '\n') break;
		move_right(text);
	}
}

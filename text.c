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

size_t text_offset(Text *text, size_t start, int offset)
{
	if (start >= text->text_start && (int)start + offset < text->text_start) {
		return start + offset - GAPSIZE(text);
	}
	return start + offset;
}

void text_memcpy_from_offsets(char *dest, size_t dest_start, Text *src, size_t src_start, size_t src_end)
{
	size_t copied;

	// Trying to copy across gap
	if (src_start <= src->gap_start && src_end >= src->text_start) {
		copied = src->gap_start - src_start;
		memcpy(dest + dest_start, src->buf + src_start, copied);
		memcpy(dest + dest_start + copied, src->buf + src->text_start, src_end - src->text_start);
	}
	else {
		memcpy(dest + dest_start, src->buf + src_start, src_end - src_start);
	}
}

void text_memcpy_from(char *dest, size_t dest_start, Text *src, size_t src_start, size_t n)
{
	size_t copied;

	// Trying to start a copy in the gap
	if (src_start >= src->gap_start && src_start < src->text_start) {
		copied = src->text_start - src_start;
		memcpy(dest + dest_start, src->buf + src->gap_start - copied, copied);
		memcpy(dest + dest_start + copied, src->buf + src->text_start, n - copied);
	}
	// Try to end a copy in the gap or trying to copy completely across the gap
	else if ((src_start + n > src->gap_start && src_start + n < src->text_start) ||
		(src_start < src->gap_start && src_start + n >= src->text_start)) {
		copied = src->gap_start - src_start;
		memcpy(dest + dest_start, src->buf + src_start, copied);
		memcpy(dest + dest_start + copied, src->buf + src->text_start, n - copied);
	}
	// No overlap, copy as normal
	else {
		memcpy(dest + dest_start, src->buf + src_start, n);
	}
}

Text *new_document(void)
{
	return calloc(1, sizeof(Text));
}

void delete_text(Text *text)
{
	free(text->buf);
	free(text);
}

void clear_text(Text *text)
{
	text->gap_start = 0;
	text->text_start = text->size;
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


int get_rowcoloffset_of_char(Text *text, char *ch, int *row, int *col, int *offset, int forwards)
{
	int r, c;
	int i, j, bytes, matched;

	get_cursor_rowcol(text, &r, &c);
	*offset = 0;

	// TODO can optimize this a little to only use these instead of r and c
	if (forwards) {
		for (i = text->text_start; i < text->size; ++i) {
			bytes = more_bytes_utf8[(unsigned int)(unsigned char)ch[0]];
			matched = 1;
			for (j = 0; j < bytes + 1; ++j) {
				if (text->buf[i + j] != ch[j]) {
					matched = 0;
					break;
				}
			}
			if (matched) {
				goto done;
			}
			if (text->buf[i] == '\n') {
				++r;
				c = 0;
			}
			else {
				++c;
			}
			++(*offset);
		}
	} else {
		for (i = ((int)text->gap_start)-1; i >= 0; --i) {
			bytes = more_bytes_utf8[(unsigned int)(unsigned char)ch[0]];
			matched = 1;
			for (j = 0; j < bytes + 1; ++j) {
				if (text->buf[i + j] != ch[j]) {
					matched = 0;
					break;
				}
			}
			if (matched) {
				goto done;
			}
			if (text->buf[i] == '\n') {
				--r;
				c = 0;
			} else {
				--c;
			}
			++(*offset);
		}
	}
	return -1;
done:
	*row = r;
	*col = c;
	return 0;
}

char *get_ch_rowcol(Text *text, int row, int col)
{
	int r = 0, c = 0;
	size_t i, bytes;
	char *ret;

	for (i = 0; i < text->size; ++i) {
		if (i == text->gap_start) {
			i += GAPSIZE(text) - 1;
			continue;
		}
		if (r >= row && c == col) break;
		if (text->buf[i] == '\n') {
			if (r == row && c == col - 1) break;
			++r; c = 0;
		} else if (text->buf[i] == '\t') {
			c += 8;// - (c % 8);
			if (r == row && c >= col) {
				if (c == col) ++i;
				break;
			}
		} else {
			// Handle unicode
			bytes = more_bytes_utf8[(unsigned int)(unsigned char)text->buf[i]];
			i += bytes;
			++c;
		}
	}

	bytes = more_bytes_utf8[(unsigned int)(unsigned char)text->buf[i]];
	ret = calloc(1, bytes + 2);
	memcpy(ret, text->buf + i, bytes+1);
	return ret;
}

char *get_chars_rowcol_to_rowcol(Text *text, int rowa, int cola, int rowb, int colb)
{
	int r = 0, c = 0;
	size_t i, bytes;
	char *ret;
	size_t start, end;

	for (i = 0; i < text->size; ++i) {
		if (i == text->gap_start) {
			i += GAPSIZE(text) - 1;
			continue;
		}
		if (r >= rowa && c == cola) break;
		if (text->buf[i] == '\n') {
			if (r == rowa && c == cola - 1) break;
			++r; c = 0;
		} else if (text->buf[i] == '\t') {
			c += 8;
		} else {
			bytes = more_bytes_utf8[(unsigned int)(unsigned char)text->buf[i]];
			i += bytes;
			++c;
		}
	}
	start = i;

	for (; i < text->size; ++i) {
		if (i == text->gap_start) {
			i += GAPSIZE(text) - 1;
			continue;
		}
		if (r >= rowb && c == colb) break;
		if (text->buf[i] == '\n') {
			if (r == rowb && c == colb - 1) break;
			++r; c = 0;
		} else if (text->buf[i] == '\t') {
			c += 8;
		} else {
			bytes = more_bytes_utf8[(unsigned int)(unsigned char)text->buf[i]];
			i += bytes;
			++c;
		}
	}
	end = i;

	ret = calloc(1, end - start + 1);
	text_memcpy_from_offsets(ret, 0, text, start, end);
	return ret;

	// TODO handle unicode
}

char *get_chars_rowcol(Text *text, int row, int col, int length, int forwards)
{
	int r = 0, c = 0;
	size_t i, bytes;
	char *ret;

	for (i = 0; i < text->size; ++i) {
		if (i == text->gap_start) {
			i += GAPSIZE(text) - 1;
			continue;
		}
		if (r >= row && c == col) break;
		if (text->buf[i] == '\n') {
			if (r == row && c == col - 1) break;
			++r; c = 0;
		} else if (text->buf[i] == '\t') {
			c += 8;// - (c % 8);
		} else {
			// Handle unicode
			bytes = more_bytes_utf8[(unsigned int)(unsigned char)text->buf[i]];
			i += bytes;
			++c;
		}
	}

	// TODO handle unicode
	ret = calloc(1, length + 1);
	if (forwards)
		text_memcpy_from(ret, 0, text, i, length);
	else
		text_memcpy_from(ret, 0, text, text_offset(text, i,  -length), length);
	return ret;
}

void get_cursor_rowcol(Text *text, int *row, int *col)
{
	int r = 0, c = 0;
	size_t i, bytes;
	for (i = 0; i < text->gap_start; ++i) {
		if (text->buf[i] == '\n') {
			++r; c = 0;
		} else if (text->buf[i] == '\t') {
			c += 8;// - c % 8;
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
	int i;
	int diff;

	get_cursor_rowcol(text, &r, &c);
	diff = abs(r - row);
	for (i = 0; i < diff; ++i)
		r > row ? move_up(text) : move_down(text);

	move_cursor_bol(text);

	get_cursor_rowcol(text, &r, &c);
	diff = abs(c - col);
	for (i = 0; i < diff; ++i) {
		if (text->buf[text->text_start] != '\n') {
			if (text->buf[text->text_start] == '\t')
				diff -= 7;
			c > col ? move_left(text) : move_right(text);
		}
	}
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

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
	/* for (int i = text->text_start; i < text->gap_start; ++i) */
	/* 	text->buf[i] = old_buf[i]; */
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

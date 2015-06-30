#include "text.h"

#include <stdlib.h>

#define RESIZE_BY 20

Text *new_document(void)
{
	Text *beg = calloc(1, sizeof(Text));
	return beg;
}

void resize_gap(Text *text, size_t new_gap)
{
	// resize_gap can't downsize
	if (new_gap <= text->size - text->gap_start)
		return;

	size_t expand_by = new_gap - (text->size - text->gap_start);
	size_t new_size = text->size + expand_by;
	text->size = new_size;
	char *old_buf = text->buf;
	text->buf = (char*)calloc(1, new_size);
	for (int i = 0; i < text->gap_start; ++i)
		text->buf[i] = old_buf[i];
	free(old_buf);
}

void add_character(Text *text, char c)
{
	size_t freespace = text->size - text->gap_start;
	if (freespace == 0)
		resize_gap(text, RESIZE_BY);
	text->buf[text->gap_start++] = c;
}

void add_string(Text *text, char *buf, size_t len)
{
	size_t freespace = text->size - text->gap_start;
	if (freespace < len)
		resize_gap(text, RESIZE_BY + len);
	for (int i = text->gap_start; i < text->gap_start+len; ++i)
		text->buf[i] = buf[i-text->gap_start];
	text->gap_start += len;
}

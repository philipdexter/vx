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
void add_string(Text *text, char *buf, size_t len);

#endif

#ifndef BUFFER_H
#define BUFFER_H

#include "text.h"

typedef struct _BUFFER {
	size_t line;
	char *filename;
	Text *text;
} Buffer;

Buffer *new_buffer(void);
void attach_file(Buffer*, char*);
void save_file(Buffer*);

#endif

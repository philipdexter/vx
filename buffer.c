#include "buffer.h"

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

Buffer *new_buffer(void)
{
	Buffer *buffer = calloc(1, sizeof(Buffer));
	buffer->text = new_document();
	return buffer;
}

void attach_file(Buffer *buffer, char *filename)
{
	FILE *fp = fopen(filename, "r");
	char buf[20];
	size_t nread;

	while ((nread = fread(buf, 1, sizeof buf, fp)) > 0)
		add_string(buffer->text, buf, nread);

	fclose(fp);
}

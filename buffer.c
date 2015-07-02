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
	buffer->filename = filename;
	FILE *fp = fopen(filename, "r");
	char buf[20];
	size_t nread;

	while ((nread = fread(buf, 1, sizeof buf, fp)) > 0)
		add_string(buffer->text, buf, nread);

	fclose(fp);
}

void save_file(Buffer *buffer)
{
	const char *str = get_str(buffer->text);
	char *name = calloc(1, strlen(buffer->filename) + 3);
	sprintf(name, ".%s.", buffer->filename);

	FILE *tmpfile = fopen(name, "w");
	fprintf(tmpfile, "%s", str);
	fclose(tmpfile);

	rename(name, buffer->filename);
}

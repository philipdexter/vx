#include "buffer.h"

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

Buffer *new_buffer(void)
{
	Buffer *buffer = calloc(1, sizeof(Buffer));
	if (!buffer) return NULL;
	buffer->text = new_document();
	if (!buffer->text) {
		free(buffer);
		return NULL;
	}
	return buffer;
}

void delete_buffer(Buffer *buffer)
{
	delete_text(buffer->text);
	free(buffer->filename);
	free(buffer);
}

int attach_file(Buffer *buffer, char *filename)
{
	FILE *fp;
	char buf[20];
	size_t nread;
	int ret;
	long file_size;
	char *old_filename = buffer->filename;
	buffer->filename = calloc(1, strlen(filename) + 1);
	if (!buffer->filename) {
		buffer->filename = old_filename;
		return -1;
	}
	strcpy(buffer->filename, filename);
	if (old_filename) {
		free(old_filename);
	}

	fp = fopen(filename, "r");
	if (!fp)
		return -1;

	fseek(fp, 0L, SEEK_END);
	file_size = ftell(fp);
	fseek(fp, 0L, SEEK_SET);
	resize_gap(buffer->text, file_size);

	while ((nread = fread(buf, 1, sizeof buf, fp)) > 0 && !ferror(fp))
		add_string(buffer->text, buf, nread);

	if (ferror(fp)) {
		fclose(fp);
		return -1;
	}

	ret = fclose(fp);
	if (ret) return -1;

	move_cursor_to_beg(buffer->text);

	return 0;
}

int save_file(Buffer *buffer)
{
	char *str;
	char *name;
	FILE *tmpfile;

	if (!buffer->filename) return -1;

	str = get_str(buffer->text);
	name = calloc(1, strlen(buffer->filename) + 3);
	if (!name) {
		free(str);
		return -1;
	}
	if (0 > snprintf(name, strlen(buffer->filename)+3, "%s##", buffer->filename)) {
		free(name);
		free(str);
		return -1;
	}

	tmpfile = fopen(name, "w");
	if (!tmpfile) {
		free(name);
		free(str);
		return -1;
	}
	fprintf(tmpfile, "%s", str);
	if (0 != fclose(tmpfile)) {
		free(name);
		free(str);
		return -1;
	}

	if (0 != rename(name, buffer->filename)) {
		free(name);
		free(str);
		return -1;
	}

	free(name);
	free(str);

	return 0;
}

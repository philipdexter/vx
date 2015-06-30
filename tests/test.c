#include <tap.h>

#include "../text.h"

#define NOTNULL(p) {isnt((const char*)p, NULL);}

int main(int argc, char *argv[])
{
	plan(NO_PLAN);

	Text *text = new_document();
	NOTNULL(text);

	done_testing();
}

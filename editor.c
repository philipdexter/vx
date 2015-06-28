#include <curses.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>

#include "buffer.h"
#include "text.h"

static void finish(int sig);

int
main(int argc, char *argv[])
{
	signal(SIGINT, finish);

	Text *text = new_document();

	initscr();
	nonl();
	cbreak();
	noecho();

	int row, col;
	getmaxyx(stdscr, row, col);

	addstr(text->buf);
	Buffer *buffer = new_buffer();
	attach_file(buffer, "README.md");
	addstr(buffer->text->buf);

	WINDOW *local_win = newwin(2, col, row-1, 0);
	refresh();
	wprintw(local_win, "rows: %d / cols: %d", row, col);
	wrefresh(local_win);
	move(0,0);

	for (;;)
	{
		int c = getch();
		if (c == 'q') break;
	}

	finish(0);
}

static void finish(int sig)
{
	endwin();
	exit(0);
}

#include <curses.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <locale.h>
#include <argp.h>

#include "vx_module.h"
#include "buffer.h"
#include "window.h"
#include "text.h"

static void finish(int sig);

int lets_edit = 1;

int row=0;
int col=0;

int screen_rows=0, screen_cols=0;

Window *focused_window = NULL;

const char *argp_program_version = "vx 0.1";
static char doc[] = "vx -- edit files";

static char args_doc[] = "[FILE...]";

#define OPT_NOPY 1

static  struct argp_option options[] = {
	{"verbose", 'v', 0, 0, "Produce verbose output" },
	{"nopy", OPT_NOPY, 0, 0, "Don't load any python : this flag doesn't work"},
	{ 0 }
};

struct arguments
{
	char **files;
	int verbose, nopy, num_files;
};

static error_t
parse_opt (int key, char *arg, struct argp_state *state)
{
	struct arguments *arguments = state->input;

	switch(key) {
		case 'v':
			arguments->verbose = 1;
			break;
		case OPT_NOPY:
			arguments->nopy = 1;
			break;
		case ARGP_KEY_ARG:
			arguments->files = &state->argv[state->next-1];
			arguments->num_files = state->argc - state->next + 1;
			state->next = state->argc;
			break;
		default:
			return ARGP_ERR_UNKNOWN;
	}
	return 0;
}

static struct argp argp = { options, parse_opt, args_doc, doc };

void init_curses(void)
{
	int i;

	initscr();
	start_color();
	use_default_colors();
	COLOR_PAIRS = 256;
	COLORS = 16;
	for (i = 0; i < COLOR_PAIRS; ++i) {
		unsigned short bg = i / COLORS - 1;
		init_pair(i, i % COLORS - 1, bg);
	}
	nonl();
	raw();
	noecho();
}

int main(int argc, char *argv[])
{
	struct arguments arguments;

	signal(SIGINT, finish);

	arguments.verbose = 0;
	arguments.nopy = 0;
	arguments.files = NULL;
	arguments.num_files = 0;
	argp_parse(&argp, argc, argv, 0, 0, &arguments);

	vx_py_init_python(arguments.num_files, argc, argv);

	init_curses();

	getmaxyx(stdscr, row, col);

	vx_py_load_start();

	clear();
	refresh();

	get_cursor_rowcol(focused_window->buffer->text, &screen_rows, &screen_cols);

	vx_py_update_vars();

	vx_py_pump();

	wmove(focused_window->curses_window, 0, 0);
	refresh_window(focused_window);

	while (lets_edit)
	{
		int c = getch();

		// Handle escape and alt
		if (c == '\033') {
			nodelay(stdscr, 1);
			c = getch();
			if (c == ERR) {
				// got an escape
				c = '\033';
			} else {
				// got an alt+key
				c |= 0x80;
			}
			nodelay(stdscr, 0);
		}

		vx_py_handle_key(c);

		get_cursor_rowcol(focused_window->buffer->text, &screen_rows, &screen_cols);
		while (screen_rows+1 < focused_window->line && focused_window->line > 1) --focused_window->line;
		while (screen_rows+1 > focused_window->line + focused_window->lines - 1) ++focused_window->line;

		vx_py_update_vars();
		vx_py_pump();

		wmove(focused_window->curses_window, screen_rows - (focused_window->line - 1), screen_cols);

		refresh_window(focused_window);

	}

	vx_py_deinit_python();

	finish(0);
}

static void finish(int sig)
{
	endwin();
	exit(0);
}

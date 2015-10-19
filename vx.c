#include <curses.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <locale.h>
#include <argp.h>
#include <time.h>

#include "vx_module.h"
#include "buffer.h"
#include "window.h"
#include "text.h"

static void finish(int sig);

int lets_edit = 1;
int lets_suspend = 0;

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
	arguments.num_files = argc-1;
	/*argp_parse(&argp, argc, argv, 0, 0, &arguments);*/

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

	clock_t last_tick = clock();
	float update_every = .25;
	while (lets_edit)
	{
		if (lets_suspend) {
			endwin();
			raise(SIGSTOP);
			lets_suspend = 0;
			refresh();
			clear();
			nonl();
			raw();
			noecho();
			getmaxyx(stdscr, row, col);
			vx_py_update_vars();
			vx_py_register_resize();
			continue;
		}
		float delay = update_every - ((float)(clock() - last_tick))/CLOCKS_PER_SEC;
		timeout(delay*1000);
		int c = getch();
		size_t bytes;
		int utf8q = 1;

		/* Handle resize */
		if (c == KEY_RESIZE) {
			endwin();
			refresh();
			clear();
			getmaxyx(stdscr, row, col);

			vx_py_update_vars();
			vx_py_register_resize();
			continue;
		}

		/* Handle escape and alt */
		if (c != ERR) {
			if (c == '\033') {
				nodelay(stdscr, 1);
				c = getch();
				if (c == ERR) {
					// got an escape
					c = '\033';
				} else {
					// got an alt+key
					c |= 0x80;
					utf8q = 0;
				}
				nodelay(stdscr, 0);
			}

			/* handle utf8 */
			bytes = more_bytes_utf8[c];
			if (utf8q && bytes > 0) {
				int i;
				char *c_utf8 = calloc(1, bytes + 2);
				c_utf8[0] = c;
				nodelay(stdscr, 1);
				for (i = 0; i < bytes; ++i) {
					c = getch();
					c_utf8[i+1] = c;
				}
				vx_py_handle_key_utf8(c_utf8);
				nodelay(stdscr, 0);
				free(c_utf8);
			} else {
				vx_py_handle_key(c);
			}
		}

		get_cursor_rowcol(focused_window->buffer->text, &screen_rows, &screen_cols);
		while (screen_rows+1 < focused_window->line && focused_window->line > 1) --focused_window->line;
		while (screen_rows+1 > focused_window->line + focused_window->lines - 1) ++focused_window->line;
		while (screen_cols < focused_window->column && focused_window->column > 1) --focused_window->column;
		while (screen_cols > focused_window->column + focused_window->columns - 4) ++focused_window->column;

		vx_py_update_vars();
		vx_py_pump();

		wmove(focused_window->curses_window, screen_rows - (focused_window->line - 1), screen_cols - (focused_window->column - 1));

		refresh_window(focused_window);

		last_tick = clock();
	}

	vx_py_deinit_python();

	endwin();
	exit(0);
}

static void finish(int sig)
{
	lets_edit = 0;
}

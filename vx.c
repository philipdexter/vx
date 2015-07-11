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

static char last_char;

int row=0;
int col=0;

int mr=0, mc=0;

Window *focused_window = NULL;

PyObject *vx_mod;

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

int main(int argc, char *argv[])
{
	struct arguments arguments;

	signal(SIGINT, finish);

	arguments.verbose = 0;
	arguments.nopy = 0;
	arguments.files = NULL;
	arguments.num_files = 0;
	argp_parse(&argp, argc, argv, 0, 0, &arguments);

	setlocale(LC_ALL, "en_US.UTF-8");

	wchar_t **wargv = calloc(arguments.num_files + 1, sizeof(wchar_t*));
	wargv[0] = calloc(1, sizeof(wchar_t) * (strlen(argv[0]) + 1) + 1);
	mbstowcs(wargv[0], argv[0], strlen(argv[0]));
	for (int i = argc - arguments.num_files, j = 1; i < argc; ++i, ++j) {
		wargv[j] = calloc(1, sizeof(wchar_t) * (strlen(argv[i]) + 1) + 1);
		mbstowcs(wargv[j], argv[i], strlen(argv[i]));
	}

	if (!arguments.nopy) {
		Py_SetProgramName(wargv[0]);
		PyImport_AppendInittab("vx", &PyInit_vx);
		Py_Initialize();
		PySys_SetArgv(arguments.num_files + 1, wargv);
	}

	initscr();
	can_change_color();
	has_colors();
	start_color();
	use_default_colors();
	for (int i = 0; i < COLORS; ++i)
		init_pair(i, i, -1);
	nonl();
	raw();
	noecho();

	getmaxyx(stdscr, row, col);

	if (!arguments.nopy) {
		PyObject *pName = PyUnicode_FromString("start");
		PyObject *imod = PyImport_Import(pName);
		if (!imod) {
			endwin();
			PyErr_Print();
			exit(0);
		}
		Py_DECREF(pName);
	}

	clear();
	refresh();

	get_cursor_rowcol(focused_window->buffer->text, &mr, &mc);
	update_vx_vars();

	PyObject *their_vx = PyObject_GetAttrString(vx_mod, "my_vx");
	PyObject *tmp_args = PyTuple_New(0);
	PyObject *tmp = PyObject_CallObject(their_vx, tmp_args);
	Py_DECREF(tmp_args);
	Py_XDECREF(tmp);

	Window *local_win = new_window();
	build_window(local_win, 2, col, row-1, 0);
	wmove(local_win->curses_window, 0, 0);
	PyObject *status_line = PyObject_GetAttrString(vx_mod, "status_line");
	PyObject *args = PyTuple_New(0);
	PyObject *ret = PyObject_CallObject(status_line, args);
	char *status_line_str = PyUnicode_AsUTF8(ret);
	wattron(local_win->curses_window, COLOR_PAIR(55));
	wprintw(local_win->curses_window, "%s", status_line_str);
	Py_DECREF(status_line);
	Py_DECREF(ret);
	Py_DECREF(args);
	refresh_window(local_win);

	last_char = '\0';

	wmove(focused_window->curses_window, 0, 0);
	refresh_window(focused_window);

	while (lets_edit)
	{
		int c = getch();
		last_char = c;

		if (c == '\033') {
			c = getch();
			c |= 0x80;
		}

		PyObject *ll = PyUnicode_FromOrdinal(c);

		PyObject *key_callback = PyObject_GetAttrString(vx_mod, "register_key");
		PyObject *args = Py_BuildValue("(O)", ll);
		PyObject *callret = PyObject_CallObject(key_callback, args);
		if (PyErr_Occurred()) {
			endwin();
			PyErr_Print();
			exit(0);
		}
		Py_DECREF(callret);
		Py_DECREF(args);
		Py_DECREF(key_callback);

		get_cursor_rowcol(focused_window->buffer->text, &mr, &mc);
		while (mr+1 < focused_window->line && focused_window->line > 1) --focused_window->line;
		while (mr+1 > focused_window->line + focused_window->lines - 1) ++focused_window->line;

		update_vx_vars();

		PyObject *their_vx = PyObject_GetAttrString(vx_mod, "my_vx");
		PyObject *tmp_args = PyTuple_New(0);
		PyObject *tmp = PyObject_CallObject(their_vx, tmp_args);
		Py_XDECREF(tmp);
		Py_DECREF(tmp_args);
		Py_DECREF(their_vx);

		wmove(local_win->curses_window, 0, 0);
		werase(local_win->curses_window);
		PyObject *status_line = PyObject_GetAttrString(vx_mod, "status_line");
		args = PyTuple_New(0);
		PyObject *ret = PyObject_CallObject(status_line, args);
		char *status_line_str = PyUnicode_AsUTF8(ret);
		wprintw(local_win->curses_window, "%s", status_line_str);
		Py_DECREF(status_line);
		Py_DECREF(ret);
		Py_DECREF(args);
		refresh_window(local_win);

		wmove(focused_window->curses_window, mr - (focused_window->line - 1), mc);

		refresh_window(focused_window);

	}

	if (!arguments.nopy)
		Py_Finalize();

	finish(0);
}

static void finish(int sig)
{
	endwin();
	exit(0);
}

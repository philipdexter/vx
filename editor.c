#include <curses.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <locale.h>
#include <argp.h>

#include <Python.h>

#include "buffer.h"
#include "text.h"

static void finish(int sig);

static int row=0;
static int col=0;

static PyObject*
editor_rows(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	return PyLong_FromLong(row);
}

static PyMethodDef EditorMethods[] = {
	{"rows", editor_rows, METH_VARARGS,
	 "Return the number of rows in the screen."},
	{NULL, NULL, 0, NULL}
};

static PyModuleDef EditorModule = {
	PyModuleDef_HEAD_INIT, "editor", NULL, -1, EditorMethods,
	NULL, NULL, NULL, NULL
};

static PyObject*
PyInit_editor(void)
{
	return PyModule_Create(&EditorModule);
}

const char *argp_program_version = "editor 0.1";
static char doc[] = "editor -- edit files";

static char args_doc[] = "FILE";

static  struct argp_option options[] = {
	{"verbose", 'v', 0, 0, "Produce verbose output" },
	{"nopy", 's', 0, 0, "Don't load any python"},
	{ 0 }
};

struct arguments
{
	char *args[1];
	int verbose, nopy;
};

static error_t
parse_opt (int key, char *arg, struct argp_state *state)
{
	struct arguments *arguments = state->input;

	switch(key) {
		case 'v':
			arguments->verbose = 1;
			break;
		case 's':
			arguments->nopy = 1;
			break;
		case ARGP_KEY_ARG:
			if (state->arg_num >= 1)
				argp_usage(state);
			arguments->args[state->arg_num] = arg;
			break;
		default:
			return ARGP_ERR_UNKNOWN;
	}
	return 0;
}

static struct argp argp = { options, parse_opt, args_doc, doc };

int main(int argc, char *argv[])
{
	signal(SIGINT, finish);

	struct arguments arguments;
	arguments.verbose = 0;
	arguments.nopy = 0;
	arguments.args[0] = NULL;
	argp_parse(&argp, argc, argv, 0, 0, &arguments);

	setlocale(LC_ALL, "en_US.UTF-8");

	wchar_t **wargv = calloc(argc, sizeof(wchar_t*));
	for(int i = 0; i < argc; ++i) {
		wargv[i] = calloc(1, sizeof(wchar_t) * (strlen(argv[i] + 1)));
		mbstowcs(wargv[i], argv[i], strlen(argv[i]));
	}

	if(!arguments.nopy) {
		Py_SetProgramName(wargv[0]);
		PyImport_AppendInittab("editor", &PyInit_editor);
		Py_Initialize();
		PySys_SetArgv(argc, wargv);
	}

	initscr();
	nonl();
	raw();
	noecho();

	getmaxyx(stdscr, row, col);

	if(!arguments.nopy) {
		PyObject *pName = PyUnicode_FromString("start");
		PyImport_Import(pName);
		Py_DECREF(pName);
	}

	Buffer *buffer = new_buffer();
	if (arguments.args[0])
		attach_file(buffer, arguments.args[0]);
	else
		attach_file(buffer, "README.md");
	move_cursor_to_beg(buffer->text);
	waddstr(stdscr, get_str(buffer->text));

	WINDOW *local_win = newwin(2, col, row-1, 0);
	refresh();
	wprintw(local_win, "rows: %d / cols: %d", row, col);
	wrefresh(local_win);
	wmove(stdscr, 0, 0);

	for (;;)
	{
		int c = getch();
		if (c == 'q') break;
		if (c == 13) {
			add_character(buffer->text, '\n');
		} else if (c == 8 || c == 127) {
			backspace(buffer->text);
		} else if (c == '\033') {
			getch();
			c = getch();
			if (c == 'A')
				move_up(buffer->text);
			else if (c == 'B')
				move_down(buffer->text);
			else if (c == 'C')
				move_right(buffer->text);
			else if (c == 'D')
				move_left(buffer->text);

		} else {
			add_character(buffer->text, c);
		}
		wmove(stdscr, 0, 0);
		waddstr(stdscr, get_str(buffer->text));
		wrefresh(stdscr);
		wmove(local_win, 0, 0);
		werase(local_win);
		wprintw(local_win, "rows: %d / cols: %d", row, col);
		wrefresh(local_win);
		int mr, mc;
		get_cursor_rowcol(buffer->text, &mr, &mc);
		wmove(stdscr, mr, mc);
	}

	if(!arguments.nopy)
		Py_Finalize();

	finish(0);
}

static void finish(int sig)
{
	endwin();
	exit(0);
}

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
	cbreak();
	noecho();

	getmaxyx(stdscr, row, col);

	if(!arguments.nopy) {
		PyObject *pName = PyUnicode_FromString("start");
		PyImport_Import(pName);
		Py_DECREF(pName);
	}

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

	if(!arguments.nopy)
		Py_Finalize();

	finish(0);
}

static void finish(int sig)
{
	endwin();
	exit(0);
}

#include <curses.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <locale.h>
#include <argp.h>

#include <Python.h>

#include "buffer.h"
#include "window.h"
#include "text.h"

static void finish(int sig);

static char last_char;

static int row=0;
static int col=0;

static PyObject *keymap;

static Buffer *buffer;

static PyObject*
editor_rows(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	return PyLong_FromLong(row);
}

static PyObject*
editor_move_up(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_up(buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_down(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_down(buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_left(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_left(buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_right(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_right(buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_bol(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_cursor_bol(buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_eol(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_cursor_eol(buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_beg(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_cursor_to_beg(buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_end(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_cursor_to_end(buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_save(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	save_file(buffer);
	Py_RETURN_NONE;
}

static PyMethodDef EditorMethods[] = {
	{"rows", editor_rows, METH_VARARGS,
	 "Return the number of rows in the screen."},
	{"move_up", editor_move_up, METH_VARARGS,
	 "Move the cursor up one row"},
	{"move_down", editor_move_down, METH_VARARGS,
	 "Move the cursor down one row"},
	{"move_left", editor_move_left, METH_VARARGS,
	 "Move the cursor left one row"},
	{"move_right", editor_move_right, METH_VARARGS,
	 "Move the cursor right one row"},
	{"move_bol", editor_move_bol, METH_VARARGS,
	 "Move the cursor to the beginning of the line"},
	{"move_eol", editor_move_eol, METH_VARARGS,
	 "Move the cursor to the end of the line"},
	{"move_beg", editor_move_beg, METH_VARARGS,
	 "Move the cursor to the beginning of the buffer"},
	{"move_end", editor_move_end, METH_VARARGS,
	 "Move the cursor to the end of the buffer"},
	{"save", editor_save, METH_VARARGS,
	 "Save the file"},
	{NULL, NULL, 0, NULL}
};

static PyModuleDef EditorModule = {
	PyModuleDef_HEAD_INIT, "editor", NULL, -1, EditorMethods,
	NULL, NULL, NULL, NULL
};

static PyObject *editor_mod;

static PyObject*
PyInit_editor(void)
{
	editor_mod = PyModule_Create(&EditorModule);
	PyObject *v = Py_BuildValue("s", "hello");
	PyObject_SetAttrString(editor_mod, "status_line", v);
	Py_DECREF(v);
	keymap = PyDict_New();
	PyObject_SetAttrString(editor_mod, "keymap", keymap);
	v = Py_BuildValue("s", "*");
	PyImport_ImportModuleEx("editor_intro", NULL, NULL, v);
	Py_DECREF(v);
	return editor_mod;
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

	size_t line = 1;

	Window *main_window = new_window();
	buffer = new_buffer();
	build_window(main_window, row-1, col, 0, 0);
	attach_buffer(main_window, buffer);
	if (arguments.args[0])
		attach_file(buffer, arguments.args[0]);
	else
		attach_file(buffer, "README.md");

	clear();
	refresh();

	move_cursor_to_beg(buffer->text);
	char *contents = get_str_from_line(buffer->text, line);
	print_string(main_window, contents);
	free(contents);

	if(!arguments.nopy) {
		PyObject *pName = PyUnicode_FromString("start");
		PyObject *imod = PyImport_Import(pName);
		if (!imod) {
			endwin();
			PyErr_Print();
			exit(0);
		}
		Py_DECREF(pName);
	}

	Window *local_win = new_window();
	build_window(local_win, 2, col, row-1, 0);
	wmove(local_win->curses_window, 0, 0);
	PyObject *status_line = PyObject_GetAttrString(editor_mod, "status_line");
	char *status_line_str = PyUnicode_AsUTF8(status_line);
	wprintw(local_win->curses_window, "%.*s", 20, status_line_str);
	last_char = '\0';
	Py_DECREF(status_line);
	refresh_window(local_win);

	wmove(main_window->curses_window, 0, 0);
	refresh_window(main_window);

	for (;;)
	{
		int c = getch();
		last_char = c;
		if (c == 'q') break;

		if (c == '\033') {
			c = getch();
			c |= 0x80;
		}

		PyObject *ll = PyUnicode_FromOrdinal(c);

		PyObject *key_callback = PyObject_GetAttrString(editor_mod, "register_key");
		PyObject *args = Py_BuildValue("(O)", ll);
		PyObject_CallObject(key_callback, args);
		Py_DECREF(args);
		Py_DECREF(key_callback);



		PyObject *callback = PyDict_GetItem(keymap, ll);
		Py_DECREF(ll);
		if (callback) {
			PyObject *args = PyTuple_New(0);
			PyObject *tmp = PyObject_CallObject(callback, args);
			Py_DECREF(args);
			Py_XDECREF(tmp);
		}
		else if (c == 13) {
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

		int mr, mc;
		get_cursor_rowcol(buffer->text, &mr, &mc);
		while (mr+1 < line && line > 1) --line;
		while (mr+1 > line + row - 2) ++line;

		wmove(main_window->curses_window, 0, 0);
		werase(main_window->curses_window);
		char *contents = get_str_from_line(buffer->text, line);
		print_string(main_window, contents);
		free(contents);
		refresh_window(main_window);

		wmove(local_win->curses_window, 0, 0);
		werase(local_win->curses_window);
		PyObject *status_line = PyObject_GetAttrString(editor_mod, "status_line");
		char *status_line_str = PyUnicode_AsUTF8(status_line);
		waddstr(local_win->curses_window, status_line_str);
		Py_DECREF(status_line);
		refresh_window(local_win);

		wmove(main_window->curses_window, mr - (line - 1), mc);

		refresh_window(main_window);

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

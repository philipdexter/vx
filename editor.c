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

static int mr=0, mc=0;

static PyObject *keymap;

static Window *focused_window = NULL;

static PyObject *editor_mod;

void update_editor_vars(void)
{
	PyObject *v = PyLong_FromLong(row);
	PyObject_SetAttrString(editor_mod, "rows", v);
	Py_DECREF(v);
	v = PyLong_FromLong(col);
	PyObject_SetAttrString(editor_mod, "cols", v);
	Py_DECREF(v);
	v = PyLong_FromLong(mr + 1);
	PyObject_SetAttrString(editor_mod, "line", v);
	Py_DECREF(v);
	v = PyLong_FromLong(mc + 1);
	PyObject_SetAttrString(editor_mod, "col", v);
	Py_DECREF(v);
}

static PyObject*
editor_move_up(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_up(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_down(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_down(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_left(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_left(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_right(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_right(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_bol(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_cursor_bol(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_eol(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_cursor_eol(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_beg(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_cursor_to_beg(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_move_end(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	move_cursor_to_end(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_add_string(PyObject *self, PyObject *args)
{
	char *str = NULL;
	if(!PyArg_ParseTuple(args, "s", &str))
		return NULL;
	add_string(focused_window->buffer->text, str, strlen(str));
	Py_RETURN_NONE;
}

static PyObject*
editor_backspace(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	backspace(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
editor_save(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ":rows"))
		return NULL;
	save_file(focused_window->buffer);
	Py_RETURN_NONE;
}

static PyObject*
editor_new_window(PyObject *self, PyObject *args)
{
	int nlines, ncols, begin_y, begin_x;
	if(!PyArg_ParseTuple(args, "iiii", &nlines, &ncols, &begin_y, &begin_x))
		return NULL;
	Window *w = new_window();
	build_window(w, nlines, ncols, begin_y, begin_x);
	PyObject *capsule = PyCapsule_New((void*)w, "editor.window", NULL);
	return capsule;
}

static PyObject*
editor_attach_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	char *file;
	if(!PyArg_ParseTuple(args, "Os", &capsule, &file))
		return NULL;
	Window *window = (Window*)PyCapsule_GetPointer(capsule, "editor.window");
	Buffer *buffer = new_buffer();
	attach_file(buffer, file);
	attach_buffer(window, buffer);
	Py_RETURN_NONE;
}

static PyObject*
editor_focus_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	if(!PyArg_ParseTuple(args, "O", &capsule))
		return NULL;
	Window *window = (Window*)PyCapsule_GetPointer(capsule, "editor.window");
	focused_window = window;
	Py_RETURN_NONE;
}

static PyObject*
editor_update_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	if(!PyArg_ParseTuple(args, "O", &capsule))
		return NULL;
	Window *window = (Window*)PyCapsule_GetPointer(capsule, "editor.window");
	wmove(window->curses_window, 0, 0);
	wclear(window->curses_window);
	char *contents = get_str_from_line_to_line(window->buffer->text, window->line, window->line + window->lines - 1);
	print_string(window, contents);
	refresh_window(window);
	free(contents);
	Py_RETURN_NONE;
}

static PyMethodDef EditorMethods[] = {
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
	{"add_string", editor_add_string, METH_VARARGS,
	 "Add a string to the buffer"},
	{"backspace", editor_backspace, METH_VARARGS,
	 "Delete a character to the left"},
	{"new_window", editor_new_window, METH_VARARGS,
	 "Create a new window"},
	{"attach_window", editor_attach_window, METH_VARARGS,
	 "Attach a window to a file"},
	{"focus_window", editor_focus_window, METH_VARARGS,
	 "Focus a window"},
	{"update_window", editor_update_window, METH_VARARGS,
	 "Update a window"},
	{NULL, NULL, 0, NULL}
};

static PyModuleDef EditorModule = {
	PyModuleDef_HEAD_INIT, "editor", NULL, -1, EditorMethods,
	NULL, NULL, NULL, NULL
};

static PyObject*
PyInit_editor(void)
{
	editor_mod = PyModule_Create(&EditorModule);
	keymap = PyDict_New();
	PyObject_SetAttrString(editor_mod, "keymap", keymap);
	update_editor_vars();
	PyObject *v = Py_BuildValue("s", "*");
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
		wargv[i] = calloc(1, sizeof(wchar_t) * (strlen(argv[i]) + 1) + 1);
		mbstowcs(wargv[i], argv[i], strlen(argv[i]));
	}

	if(!arguments.nopy) {
		Py_SetProgramName(wargv[0]);
		PyImport_AppendInittab("editor", &PyInit_editor);
		Py_Initialize();
		PySys_SetArgv(argc, wargv);
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

	clear();
	refresh();

	get_cursor_rowcol(focused_window->buffer->text, &mr, &mc);
	update_editor_vars();

	PyObject *their_editor = PyObject_GetAttrString(editor_mod, "my_editor");
	PyObject *tmp_args = PyTuple_New(0);
	PyObject *tmp = PyObject_CallObject(their_editor, tmp_args);
	Py_DECREF(tmp_args);
	Py_XDECREF(tmp);

	Window *local_win = new_window();
	build_window(local_win, 2, col, row-1, 0);
	wmove(local_win->curses_window, 0, 0);
	PyObject *status_line = PyObject_GetAttrString(editor_mod, "status_line");
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

		get_cursor_rowcol(focused_window->buffer->text, &mr, &mc);
		while (mr+1 < focused_window->line && focused_window->line > 1) --focused_window->line;
		while (mr+1 > focused_window->line + focused_window->lines - 1) ++focused_window->line;

		update_editor_vars();

		PyObject *their_editor = PyObject_GetAttrString(editor_mod, "my_editor");
		PyObject *tmp_args = PyTuple_New(0);
		PyObject *tmp = PyObject_CallObject(their_editor, tmp_args);
		Py_DECREF(tmp_args);
		Py_XDECREF(tmp);

		wmove(local_win->curses_window, 0, 0);
		werase(local_win->curses_window);
		PyObject *status_line = PyObject_GetAttrString(editor_mod, "status_line");
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

	if(!arguments.nopy)
		Py_Finalize();

	finish(0);
}

static void finish(int sig)
{
	endwin();
	exit(0);
}

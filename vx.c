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

static int lets_edit = 1;

static char last_char;

static int row=0;
static int col=0;

static int mr=0, mc=0;

static PyObject *keymap;

static Window *focused_window = NULL;

static PyObject *vx_mod;

void update_vx_vars(void)
{
	PyObject *v = PyLong_FromLong(row);
	PyObject_SetAttrString(vx_mod, "rows", v);
	Py_DECREF(v);
	v = PyLong_FromLong(col);
	PyObject_SetAttrString(vx_mod, "cols", v);
	Py_DECREF(v);
	v = PyLong_FromLong(mr + 1);
	PyObject_SetAttrString(vx_mod, "line", v);
	Py_DECREF(v);
	v = PyLong_FromLong(mc + 1);
	PyObject_SetAttrString(vx_mod, "col", v);
	Py_DECREF(v);
}

static PyObject*
vx_quit(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":quit"))
		return NULL;
	lets_edit = 0;
	Py_RETURN_NONE;
}

static PyObject*
vx_move_up(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_up"))
		return NULL;
	move_up(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
vx_move_down(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_down"))
		return NULL;
	move_down(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
vx_move_left(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_left"))
		return NULL;
	move_left(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
vx_move_right(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_right"))
		return NULL;
	move_right(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
vx_move_bol(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_bol"))
		return NULL;
	move_cursor_bol(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
vx_move_eol(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_eol"))
		return NULL;
	move_cursor_eol(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
vx_move_beg(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_beg"))
		return NULL;
	move_cursor_to_beg(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
vx_move_end(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_end"))
		return NULL;
	move_cursor_to_end(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
vx_add_string(PyObject *self, PyObject *args)
{
	char *str = NULL;
	if (!PyArg_ParseTuple(args, "s:add_string", &str))
		return NULL;
	add_string(focused_window->buffer->text, str, strlen(str));
	Py_RETURN_NONE;
}

static PyObject*
vx_backspace(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":backspace"))
		return NULL;
	backspace(focused_window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject*
vx_save(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":save"))
		return NULL;
	save_file(focused_window->buffer);
	Py_RETURN_NONE;
}

static PyObject*
vx_new_window(PyObject *self, PyObject *args)
{
	int nlines, ncols, begin_y, begin_x;
	if (!PyArg_ParseTuple(args, "iiii:new_window", &nlines, &ncols, &begin_y, &begin_x))
		return NULL;
	Window *w = new_window();
	build_window(w, nlines, ncols, begin_y, begin_x);
	PyObject *capsule = PyCapsule_New((void*)w, "vx.window", NULL);
	return capsule;
}

static PyObject*
vx_attach_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	char *file;
	if (!PyArg_ParseTuple(args, "Os:attach_window", &capsule, &file))
		return NULL;
	Window *window = (Window*)PyCapsule_GetPointer(capsule, "vx.window");
	Buffer *buffer = new_buffer();
	attach_file(buffer, file);
	attach_buffer(window, buffer);
	Py_RETURN_NONE;
}

static PyObject*
vx_attach_window_blank(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	if (!PyArg_ParseTuple(args, "O:attach_window_blank", &capsule))
		return NULL;
	Window *window = (Window*)PyCapsule_GetPointer(capsule, "vx.window");
	Buffer *buffer = new_buffer();
	attach_buffer(window , buffer);
	Py_RETURN_NONE;
}

static PyObject*
vx_focus_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	if (!PyArg_ParseTuple(args, "O:focus_window", &capsule))
		return NULL;
	Window *window = (Window*)PyCapsule_GetPointer(capsule, "vx.window");
	focused_window = window;
	Py_RETURN_NONE;
}

static PyObject*
vx_update_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	if (!PyArg_ParseTuple(args, "O:update_window", &capsule))
		return NULL;
	Window *window = (Window*)PyCapsule_GetPointer(capsule, "vx.window");
	wmove(window->curses_window, 0, 0);
	wclear(window->curses_window);
	char *contents = get_str_from_line_to_line(window->buffer->text, window->line, window->line + window->lines - 1);
	print_string(window, contents);
	refresh_window(window);
	free(contents);
	Py_RETURN_NONE;
}

static PyMethodDef VxMethods[] = {
	{"quit", vx_quit, METH_VARARGS,
	 "Quit"},
	{"move_up", vx_move_up, METH_VARARGS,
	 "Move the cursor up one row"},
	{"move_down", vx_move_down, METH_VARARGS,
	 "Move the cursor down one row"},
	{"move_left", vx_move_left, METH_VARARGS,
	 "Move the cursor left one row"},
	{"move_right", vx_move_right, METH_VARARGS,
	 "Move the cursor right one row"},
	{"move_bol", vx_move_bol, METH_VARARGS,
	 "Move the cursor to the beginning of the line"},
	{"move_eol", vx_move_eol, METH_VARARGS,
	 "Move the cursor to the end of the line"},
	{"move_beg", vx_move_beg, METH_VARARGS,
	 "Move the cursor to the beginning of the buffer"},
	{"move_end", vx_move_end, METH_VARARGS,
	 "Move the cursor to the end of the buffer"},
	{"save", vx_save, METH_VARARGS,
	 "Save the file"},
	{"add_string", vx_add_string, METH_VARARGS,
	 "Add a string to the buffer"},
	{"backspace", vx_backspace, METH_VARARGS,
	 "Delete a character to the left"},
	{"new_window", vx_new_window, METH_VARARGS,
	 "Create a new window"},
	{"attach_window", vx_attach_window, METH_VARARGS,
	 "Attach a window to a file"},
	{"attach_window_blank", vx_attach_window_blank, METH_VARARGS,
	 "Attach a window to a blank buffer"},
	{"focus_window", vx_focus_window, METH_VARARGS,
	 "Focus a window"},
	{"update_window", vx_update_window, METH_VARARGS,
	 "Update a window"},
	{NULL, NULL, 0, NULL}
};

static PyModuleDef VxModule = {
	PyModuleDef_HEAD_INIT, "vx", NULL, -1, VxMethods,
	NULL, NULL, NULL, NULL
};

static PyObject*
PyInit_vx(void)
{
	vx_mod = PyModule_Create(&VxModule);
	keymap = PyDict_New();
	PyObject_SetAttrString(vx_mod, "keymap", keymap);
	update_vx_vars();
	PyObject *v = Py_BuildValue("s", "*");
	PyObject *mod = PyImport_ImportModuleEx("vx_intro", NULL, NULL, v);
	Py_DECREF(mod);
	Py_DECREF(v);
	return vx_mod;
}

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
	signal(SIGINT, finish);

	struct arguments arguments;
	arguments.verbose = 0;
	arguments.nopy = 0;
	arguments.files = NULL;
	arguments.num_files = 0;
	argp_parse(&argp, argc, argv, 0, 0, &arguments);

	setlocale(LC_ALL, "en_US.UTF-8");

	wchar_t **wargv = calloc(arguments.num_files + 1, sizeof(wchar_t*));
	wargv[0] = calloc(1, sizeof(wchar_t) * (strlen(argv[0]) + 1) + 1);
	mbstowcs(wargv[0], argv[0], strlen(argv[0]));
	for(int i = argc - arguments.num_files, j = 1; i < argc; ++i, ++j) {
		wargv[j] = calloc(1, sizeof(wchar_t) * (strlen(argv[i]) + 1) + 1);
		mbstowcs(wargv[j], argv[i], strlen(argv[i]));
	}

	if(!arguments.nopy) {
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

	if(!arguments.nopy)
		Py_Finalize();

	finish(0);
}

static void finish(int sig)
{
	endwin();
	exit(0);
}

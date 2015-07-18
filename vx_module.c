#include "vx_module.h"

#include <locale.h>
#include <wchar.h>

static PyObject *vx_mod;
static PyObject *vx_intro_mod;
static PyObject *start_mod;

static PyObject *PyInit_vx(void);

#define WINDOW_FROM_CAPSULE \
	if (PyObject_HasAttrString(capsule, "_c_window"))		\
		capsule = PyObject_GetAttrString(capsule, "_c_window"); \
	window = (Window*)PyCapsule_GetPointer(capsule, "vx.window");

int vx_py_init_python(int num_files, int argc, char **argv)
{
	int i, j, ret;
	wchar_t **wargv;

	if (!setlocale(LC_ALL, "en_US.UTF-8"))
		return -1;

	wargv = calloc(num_files + 1, sizeof(wchar_t*));
	if (!wargv) {
		ret = -1;
		goto cleanup;
	}
	wargv[0] = calloc(1, sizeof(wchar_t) * (strlen(argv[0]) + 1) + 1);
	if (!wargv[0]) {
		ret = -1;
		goto cleanup;
	}
	if ((size_t)-1 == mbstowcs(wargv[0], argv[0], strlen(argv[0]))) {
		ret = -1;
		goto cleanup;
	}
	for (i = argc - num_files, j = 1; i < argc; ++i, ++j) {
		wargv[j] = calloc(1, sizeof(wchar_t) * (strlen(argv[i]) + 1) + 1);
		if ((size_t)-1 == mbstowcs(wargv[j], argv[i], strlen(argv[i]))) {
			ret = -1;
			goto cleanup;
		}
	}

	Py_SetProgramName(wargv[0]);
	if (-1 == PyImport_AppendInittab("vx", &PyInit_vx)) {
		goto cleanup;
	}
	Py_Initialize();
	PySys_SetArgv(num_files + 1, wargv);

	ret = 0;

cleanup:
	for (i = argc - num_files, j = 1; i < argc; ++i, ++j)
		free(wargv[i]);
	free(wargv);
	return ret;
}

void vx_py_deinit_python(void)
{
	Py_DECREF(start_mod);
	Py_DECREF(vx_mod);
	Py_DECREF(vx_intro_mod);
	Py_Finalize();
}

void vx_py_load_start(void)
{
	PyObject *pName = PyUnicode_FromString("start");
	start_mod = PyImport_Import(pName);
	if (!start_mod) {
		endwin();
		PyErr_Print();
		exit(0);
	}
	Py_DECREF(pName);
}

int vx_py_update_vars(void)
{
	PyObject *v = PyLong_FromLong(row);
	if (-1 == PyObject_SetAttrString(vx_mod, "rows", v))
		goto err;
	Py_DECREF(v);
	v = PyLong_FromLong(col);
	if (-1 == PyObject_SetAttrString(vx_mod, "cols", v))
		goto err;
	Py_DECREF(v);
	v = PyLong_FromLong(screen_rows + 1);
	if (-1 == PyObject_SetAttrString(vx_mod, "line", v))
		goto err;
	Py_DECREF(v);
	v = PyLong_FromLong(screen_cols + 1);
	if (-1 == PyObject_SetAttrString(vx_mod, "col", v))
		goto err;
	Py_DECREF(v);

	return 0;

err:
	Py_DECREF(v);
	return -1;
}

void vx_py_pump(void)
{
	PyObject *their_vx = PyObject_GetAttrString(vx_mod, "my_vx");
	PyObject *tmp_args = PyTuple_New(0);
	PyObject *tmp = PyObject_CallObject(their_vx, tmp_args);
	Py_DECREF(their_vx);
	Py_DECREF(tmp_args);
	Py_XDECREF(tmp);
}

static PyObject *vx_quit(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":quit"))
		return NULL;
	lets_edit = 0;
	Py_RETURN_NONE;
}

static PyObject *vx_move_up_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:move_up", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	move_up(window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject *vx_move_down_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:move_down", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	move_down(window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject *vx_move_left_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:move_left", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	move_left(window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject *vx_move_right_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:move_right", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	move_right(window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject *vx_move_bol_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:move_bol", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	move_cursor_bol(window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject *vx_move_eol_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:move_eol", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	move_cursor_eol(window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject *vx_move_beg_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:move_beg", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	move_cursor_to_beg(window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject *vx_move_end_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:move_end", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	move_cursor_to_end(window->buffer->text);
	Py_RETURN_NONE;
}

static PyObject *vx_add_string_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	char *str = NULL;
	if (!PyArg_ParseTuple(args, "Os:add_string_window", &capsule, &str))
		return NULL;
	if (!str) return NULL;
	WINDOW_FROM_CAPSULE;
	add_string(window->buffer->text, str, strlen(str));
	Py_RETURN_NONE;
}

static PyObject *vx_backspace_delete_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:backspace", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	backspace(window->buffer->text, 1);
	Py_RETURN_NONE;
}

static PyObject *vx_backspace_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:backspace", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	backspace(window->buffer->text, 0);
	Py_RETURN_NONE;
}

static PyObject *vx_save_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	if (!PyArg_ParseTuple(args, "O:save", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	save_file(window->buffer);
	Py_RETURN_NONE;
}

static PyObject *vx_new_window(PyObject *self, PyObject *args)
{
	int nlines, ncols, begin_y, begin_x;
	Window *window;
	PyObject *capsule;

	if (!PyArg_ParseTuple(args, "iiii:new_window", &nlines, &ncols, &begin_y, &begin_x))
		return NULL;
	window = new_window();
	build_window(window, nlines, ncols, begin_y, begin_x);
	capsule = PyCapsule_New((void*)window, "vx.window", NULL);
	return capsule;
}

static PyObject *vx_delete_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;

	if (!PyArg_ParseTuple(args, "O:delete_window", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	delete_window(window);
	Py_RETURN_NONE;
}

static PyObject *vx_attach_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	char *file;
	Window *window;
	Buffer *buffer;


	if (!PyArg_ParseTuple(args, "Os:attach_window", &capsule, &file))
		return NULL;
	WINDOW_FROM_CAPSULE;
	buffer = new_buffer();
	attach_file(buffer, file);
	attach_buffer(window, buffer);
	Py_RETURN_NONE;
}

static PyObject *vx_attach_window_blank(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	Buffer *buffer;

	if (!PyArg_ParseTuple(args, "O:attach_window_blank", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	buffer = new_buffer();
	attach_buffer(window , buffer);
	Py_RETURN_NONE;
}

static PyObject *vx_focus_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;

	if (!PyArg_ParseTuple(args, "O:focus_window", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	focused_window = window;
	Py_RETURN_NONE;
}

static PyObject *vx_redraw_all(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":redraw_all"))
		return NULL;
	clear();
	refresh();
	Py_RETURN_NONE;
}

static PyObject *vx_clear_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;

	if (!PyArg_ParseTuple(args, "O:clear_window", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	wclear(window->curses_window);
	Py_RETURN_NONE;
}

static PyObject *vx_get_window_size(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	PyObject *ret;
	int y, x;

	if (!PyArg_ParseTuple(args, "O:get_window_size", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	get_window_size(window, &y, &x);
	ret = Py_BuildValue("(ii)", y, x);
	return ret;
}

static PyObject *vx_get_ch_linecol_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	PyObject *ret;
	int row, col;
	char *ch;

	if (!PyArg_ParseTuple(args, "Oii:get_ch_linecol_window", &capsule, &row, &col))
		return NULL;
	WINDOW_FROM_CAPSULE;
	--row, --col;
	ch = get_ch_rowcol(window->buffer->text, row, col);
	ret = Py_BuildValue("s", ch);
	return ret;
}

static PyObject *vx_get_linecol_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	PyObject *ret;
	int r, c;

	if (!PyArg_ParseTuple(args, "O:get_linecol_window", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	get_cursor_rowcol(window->buffer->text, &r, &c);
	ret = Py_BuildValue("(ii)", ++r, ++c);

	return ret;
}

static PyObject *vx_set_linecol_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	int r, c;

	if (!PyArg_ParseTuple(args, "Oii:set_linecol_window", &capsule, &r, &c))
		return NULL;
	WINDOW_FROM_CAPSULE;
	--r, --c;
	set_cursor_rowcol(window->buffer->text, r, c);
	Py_RETURN_NONE;
}

static PyObject *vx_print_string_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	char *string;

	if (!PyArg_ParseTuple(args, "Os:print_string_window", &capsule, &string))
		return NULL;
	WINDOW_FROM_CAPSULE;
	print_string(window, string);
	Py_RETURN_NONE;
}

static PyObject *vx_refresh_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;

	if (!PyArg_ParseTuple(args, "O:refresh_window", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	refresh_window(window);
	Py_RETURN_NONE;
}

static PyObject *vx_resize_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	int lines, columns;

	if (!PyArg_ParseTuple(args, "Oii:resize_window", &capsule, &lines, &columns))
		return NULL;
	WINDOW_FROM_CAPSULE;
	resize_window(window, lines, columns);
	Py_RETURN_NONE;
}

static PyObject *vx_move_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	int y, x;

	if (!PyArg_ParseTuple(args, "Oii:move_window", &capsule, &y, &x))
		return NULL;
	WINDOW_FROM_CAPSULE;
	move_window(window, y, x);
	Py_RETURN_NONE;
}

static PyObject *vx_get_contents_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	char *contents;
	PyObject *str;

	if (!PyArg_ParseTuple(args, "O:refresh_window", &capsule))
		return NULL;
	WINDOW_FROM_CAPSULE;
	contents = get_str_from_line_to_line(window->buffer->text, window->line, window->line + window->lines - 1);
	str = Py_BuildValue("s", contents);
	free(contents);
	return str;
}

static PyObject *vx_set_color_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	int fg, bg;
	unsigned short color;

	if (!PyArg_ParseTuple(args, "Oii:update_window", &capsule, &fg, &bg))
		return NULL;
	WINDOW_FROM_CAPSULE;
	color = (bg + 1) * COLORS + ((fg + 1) % COLORS);
	wcolor_set(window->curses_window, color, NULL);
	Py_RETURN_NONE;
}

static PyObject *vx_set_cursor_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	int y, x;

	if (!PyArg_ParseTuple(args, "Oii:set_cursor_window", &capsule, &y, &x))
		return NULL;
	WINDOW_FROM_CAPSULE;
	wmove(window->curses_window, y, x);

	Py_RETURN_NONE;
}

static PyMethodDef VxMethods[] = {
	{"quit", vx_quit, METH_VARARGS,
	 "Quit"},
	{"move_up_window", vx_move_up_window, METH_VARARGS,
	 "Move the cursor up one row"},
	{"move_down_window", vx_move_down_window, METH_VARARGS,
	 "Move the cursor down one row"},
	{"move_left_window", vx_move_left_window, METH_VARARGS,
	 "Move the cursor left one row"},
	{"move_right_window", vx_move_right_window, METH_VARARGS,
	 "Move the cursor right one row"},
	{"move_bol_window", vx_move_bol_window, METH_VARARGS,
	 "Move the cursor to the beginning of the line"},
	{"move_eol_window", vx_move_eol_window, METH_VARARGS,
	 "Move the cursor to the end of the line"},
	{"move_beg_window", vx_move_beg_window, METH_VARARGS,
	 "Move the cursor to the beginning of the buffer"},
	{"move_end_window", vx_move_end_window, METH_VARARGS,
	 "Move the cursor to the end of the buffer"},
	{"save_window", vx_save_window, METH_VARARGS,
	 "Save the file"},
	{"add_string_window", vx_add_string_window, METH_VARARGS,
	 "Add a string to a window"},
	{"backspace_delete_window", vx_backspace_delete_window, METH_VARARGS,
	 "Delete a character to the right"},
	{"backspace_window", vx_backspace_window, METH_VARARGS,
	 "Delete a character to the left"},
	{"new_window", vx_new_window, METH_VARARGS,
	 "Create a new window"},
	{"delete_window", vx_delete_window, METH_VARARGS,
	 "Delete window"},
	{"attach_window", vx_attach_window, METH_VARARGS,
	 "Attach a window to a file"},
	{"attach_window_blank", vx_attach_window_blank, METH_VARARGS,
	 "Attach a window to a blank buffer"},
	{"focus_window", vx_focus_window, METH_VARARGS,
	 "Focus a window"},
	{"redraw_all", vx_redraw_all, METH_VARARGS,
	 "Redraw the entire window"},
	{"clear_window", vx_clear_window, METH_VARARGS,
	 "Clear a window"},
	{"get_window_size", vx_get_window_size, METH_VARARGS,
	 "Get the size of a window"},
	{"get_ch_linecol_window", vx_get_ch_linecol_window, METH_VARARGS,
	 "Get the character at a linecol"},
	{"get_linecol_window", vx_get_linecol_window, METH_VARARGS,
	 "Get the line and column the cursor is on of a window"},
	{"set_linecol_window", vx_set_linecol_window, METH_VARARGS,
	 "Set the line and column the cursor is on of a window"},
	{"print_string_window", vx_print_string_window, METH_VARARGS,
	 "Add a string to a window"},
	{"refresh_window", vx_refresh_window, METH_VARARGS,
	 "Refresh a window"},
	{"resize_window", vx_resize_window, METH_VARARGS,
	 "Resize a window"},
	{"move_window", vx_move_window, METH_VARARGS,
	 "Move a window"},
	{"get_contents_window", vx_get_contents_window, METH_VARARGS,
	 "Get the contents of a window"},
	{"set_color_window", vx_set_color_window, METH_VARARGS,
	 "Set the color"},
	{"set_cursor", vx_set_cursor_window, METH_VARARGS,
	 "Set the cursor in a window"},
	{NULL, NULL, 0, NULL}
};

static PyModuleDef VxModule = {
	PyModuleDef_HEAD_INIT, "vx", NULL, -1, VxMethods,
	NULL, NULL, NULL, NULL
};

static PyObject *PyInit_vx(void)
{
	PyObject *v;

	vx_mod = PyModule_Create(&VxModule);
	vx_py_update_vars();
	v = Py_BuildValue("s", "*");
	vx_intro_mod = PyImport_ImportModuleEx("vx_intro", NULL, NULL, v);
	Py_DECREF(v);
	return vx_mod;
}

void vx_py_handle_key(int c)
{
	char *str = calloc(1, 2);
	str[0] = c;
	vx_py_handle_key_utf8(str);
	free(str);
	return;
}

void vx_py_handle_key_utf8(char *str)
{
	PyObject *key_callback = PyObject_GetAttrString(vx_mod, "register_key");
	PyObject *args = Py_BuildValue("(y)", str);
	PyObject *callret = PyObject_CallObject(key_callback, args);
	if (PyErr_Occurred()) {
		endwin();
		PyErr_Print();
		exit(0);
	}
	Py_DECREF(callret);
	Py_DECREF(args);
	Py_DECREF(key_callback);
}

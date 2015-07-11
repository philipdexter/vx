#include "vx_module.h"

#include <locale.h>
#include <wchar.h>

PyObject *vx_mod;

void vx_py_init_python(int num_files, int argc, char **argv)
{
	setlocale(LC_ALL, "en_US.UTF-8");

	wchar_t **wargv = calloc(num_files + 1, sizeof(wchar_t*));
	wargv[0] = calloc(1, sizeof(wchar_t) * (strlen(argv[0]) + 1) + 1);
	mbstowcs(wargv[0], argv[0], strlen(argv[0]));
	for (int i = argc - num_files, j = 1; i < argc; ++i, ++j) {
		wargv[j] = calloc(1, sizeof(wchar_t) * (strlen(argv[i]) + 1) + 1);
		mbstowcs(wargv[j], argv[i], strlen(argv[i]));
	}

	Py_SetProgramName(wargv[0]);
	PyImport_AppendInittab("vx", &PyInit_vx);
	Py_Initialize();
	PySys_SetArgv(num_files + 1, wargv);
}

void vx_py_deinit_python(void)
{
	Py_Finalize();
}

void vx_py_load_start(void)
{
	PyObject *pName = PyUnicode_FromString("start");
	PyObject *imod = PyImport_Import(pName);
	if (!imod) {
		endwin();
		PyErr_Print();
		exit(0);
	}
	Py_DECREF(pName);
}

void vx_py_update_vars(void)
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

void vx_py_pump(void)
{
	PyObject *their_vx = PyObject_GetAttrString(vx_mod, "my_vx");
	PyObject *tmp_args = PyTuple_New(0);
	PyObject *tmp = PyObject_CallObject(their_vx, tmp_args);
	Py_DECREF(tmp_args);
	Py_XDECREF(tmp);
}

PyObject *vx_quit(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":quit"))
		return NULL;
	lets_edit = 0;
	Py_RETURN_NONE;
}

PyObject *vx_move_up(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_up"))
		return NULL;
	move_up(focused_window->buffer->text);
	Py_RETURN_NONE;
}

PyObject *vx_move_down(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_down"))
		return NULL;
	move_down(focused_window->buffer->text);
	Py_RETURN_NONE;
}

PyObject *vx_move_left(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_left"))
		return NULL;
	move_left(focused_window->buffer->text);
	Py_RETURN_NONE;
}

PyObject *vx_move_right(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_right"))
		return NULL;
	move_right(focused_window->buffer->text);
	Py_RETURN_NONE;
}

PyObject *vx_move_bol(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_bol"))
		return NULL;
	move_cursor_bol(focused_window->buffer->text);
	Py_RETURN_NONE;
}

PyObject *vx_move_eol(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_eol"))
		return NULL;
	move_cursor_eol(focused_window->buffer->text);
	Py_RETURN_NONE;
}

PyObject *vx_move_beg(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_beg"))
		return NULL;
	move_cursor_to_beg(focused_window->buffer->text);
	Py_RETURN_NONE;
}

PyObject *vx_move_end(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":move_end"))
		return NULL;
	move_cursor_to_end(focused_window->buffer->text);
	Py_RETURN_NONE;
}

PyObject *vx_add_string(PyObject *self, PyObject *args)
{
	char *str = NULL;
	if (!PyArg_ParseTuple(args, "s:add_string", &str))
		return NULL;
	if (!str) return NULL;
	add_string(focused_window->buffer->text, str, strlen(str));
	Py_RETURN_NONE;
}

PyObject *vx_backspace(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":backspace"))
		return NULL;
	backspace(focused_window->buffer->text);
	Py_RETURN_NONE;
}

PyObject *vx_save(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":save"))
		return NULL;
	save_file(focused_window->buffer);
	Py_RETURN_NONE;
}

PyObject *vx_new_window(PyObject *self, PyObject *args)
{
	int nlines, ncols, begin_y, begin_x;
	Window *w;
	PyObject *capsule;

	if (!PyArg_ParseTuple(args, "iiii:new_window", &nlines, &ncols, &begin_y, &begin_x))
		return NULL;
	w = new_window();
	build_window(w, nlines, ncols, begin_y, begin_x);
	capsule = PyCapsule_New((void*)w, "vx.window", NULL);
	return capsule;
}

PyObject *vx_attach_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	char *file;
	Window *window;
	Buffer *buffer;


	if (!PyArg_ParseTuple(args, "Os:attach_window", &capsule, &file))
		return NULL;
	window = (Window*)PyCapsule_GetPointer(capsule, "vx.window");
	buffer = new_buffer();
	attach_file(buffer, file);
	attach_buffer(window, buffer);
	Py_RETURN_NONE;
}

PyObject *vx_attach_window_blank(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	Buffer *buffer;

	if (!PyArg_ParseTuple(args, "O:attach_window_blank", &capsule))
		return NULL;
	window = (Window*)PyCapsule_GetPointer(capsule, "vx.window");
	buffer = new_buffer();
	attach_buffer(window , buffer);
	Py_RETURN_NONE;
}

PyObject *vx_focus_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;

	if (!PyArg_ParseTuple(args, "O:focus_window", &capsule))
		return NULL;
	window = (Window*)PyCapsule_GetPointer(capsule, "vx.window");
	focused_window = window;
	Py_RETURN_NONE;
}

PyObject *vx_update_window(PyObject *self, PyObject *args)
{
	PyObject *capsule;
	Window *window;
	char *contents;

	if (!PyArg_ParseTuple(args, "O:update_window", &capsule))
		return NULL;
	window = (Window*)PyCapsule_GetPointer(capsule, "vx.window");
	wmove(window->curses_window, 0, 0);
	wclear(window->curses_window);
	contents = get_str_from_line_to_line(window->buffer->text, window->line, window->line + window->lines - 1);
	print_string(window, contents);
	refresh_window(window);
	free(contents);
	Py_RETURN_NONE;
}

PyMethodDef VxMethods[] = {
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

PyModuleDef VxModule = {
	PyModuleDef_HEAD_INIT, "vx", NULL, -1, VxMethods,
	NULL, NULL, NULL, NULL
};

PyObject *PyInit_vx(void)
{
	PyObject *v;
	PyObject *mod;

	vx_mod = PyModule_Create(&VxModule);
	vx_py_update_vars();
	v = Py_BuildValue("s", "*");
	mod = PyImport_ImportModuleEx("vx_intro", NULL, NULL, v);
	Py_DECREF(mod);
	Py_DECREF(v);
	return vx_mod;
}

void vx_py_handle_key(int c)
{
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
}

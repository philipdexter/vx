#include <curses.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <locale.h>

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

int main(int argc, char *argv[])
{
	signal(SIGINT, finish);

	PyObject *pName;
	int i;

	setlocale(LC_ALL, "en_US.UTF-8");

	wchar_t **wargv = calloc(argc, sizeof(wchar_t*));
	for(i = 0; i < argc; ++i) {
		wargv[i] = calloc(1, sizeof(wchar_t) * (strlen(argv[i] + 1)));
		mbstowcs(wargv[i], argv[i], strlen(argv[i]));
	}

	Py_SetProgramName(wargv[0]);
	PyImport_AppendInittab("editor", &PyInit_editor);
	Py_Initialize();
	PySys_SetArgv(argc, wargv);

	initscr();
	nonl();
	cbreak();
	noecho();

	getmaxyx(stdscr, row, col);

	pName = PyUnicode_FromString("start");
	PyImport_Import(pName);
	Py_DECREF(pName);

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

	Py_Finalize();
	finish(0);
}

static void finish(int sig)
{
	endwin();
	exit(0);
}

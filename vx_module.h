#ifndef VX_MODULE_H
#define VX_MODULE_H

#include <Python.h>

#include "window.h"

void vx_py_init_python(int num_files, int argc, char **argv);
void vx_py_deinit_python(void);
void vx_py_load_start(void);
void vx_py_update_vars(void);
void vx_py_pump(void);

PyObject *vx_quit(PyObject *self, PyObject *args);
PyObject *vx_move_up(PyObject *self, PyObject *args);
PyObject *vx_move_down(PyObject *self, PyObject *args);
PyObject *vx_move_left(PyObject *self, PyObject *args);
PyObject *vx_move_right(PyObject *self, PyObject *args);
PyObject *vx_move_bol(PyObject *self, PyObject *args);
PyObject *vx_move_eol(PyObject *self, PyObject *args);
PyObject *vx_move_beg(PyObject *self, PyObject *args);
PyObject *vx_move_end(PyObject *self, PyObject *args);
PyObject *vx_add_string(PyObject *self, PyObject *args);
PyObject *vx_backspace(PyObject *self, PyObject *args);
PyObject *vx_save(PyObject *self, PyObject *args);
PyObject *vx_new_window(PyObject *self, PyObject *args);
PyObject *vx_attach_window(PyObject *self, PyObject *args);
PyObject *vx_attach_window_blank(PyObject *self, PyObject *args);
PyObject *vx_focus_window(PyObject *self, PyObject *args);
PyObject *vx_update_window(PyObject *self, PyObject *args);
PyObject *vx_set_cursor_window(PyObject *self, PyObject *args);

PyObject *PyInit_vx(void);

void vx_py_handle_key(int c);

/* Defined elsewhere */
extern Window *focused_window;
extern int row, col;
extern int mr, mc;
extern int lets_edit;

#endif

#ifndef VX_MODULE_H
#define VX_MODULE_H

#include <Python.h>

#include "window.h"

int vx_py_init_python(int num_files, int argc, char **argv);
void vx_py_deinit_python(void);
void vx_py_load_start(void);
int vx_py_update_vars(void);
void vx_py_register_resize(void);
void vx_py_pump(void);

void vx_py_handle_key(int);
void vx_py_handle_key_utf8(char*);

/* Defined elsewhere */
extern Window *focused_window;
extern int row, col;
extern int screen_rows, screen_cols;
extern int lets_edit;
extern int lets_suspend;

#endif

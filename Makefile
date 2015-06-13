all:
	gcc -c editor.c -o editor.o
	gcc -lcurses editor.o -o editor

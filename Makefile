all:
	gcc -c editor.c -o editor.o -g
	gcc -c text.c -o text.o -g
	gcc -c buffer.c -o buffer.o -g
	gcc -lcurses editor.o text.o buffer.o -o editor -g

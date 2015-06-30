SOURCES=test.c

OBJS = $(SOURCES:.c=.o)

HDS = $(SOURCES:.c=.m)

TOTEST = ../text.o

CFLAGS = -g -Wall -pedantic -std=c99 -O0 -Ilibtap
LDFLAGS = -Llibtap -ltap

PYCFLAGS = $(shell /usr/bin/python3.4-config --cflags)
PYLDFLAGS = $(shell /usr/bin/python3.4-config --ldflags)

.PHONY: all
all: test


test: $(OBJS)
	gcc -lpython3.4m -lncurses $(OBJS) $(TOTEST) -otest $(PYLDFLAGS) $(LDFLAGS)

.c.o:
	gcc -c $< -o $@ -I/usr/include/python3.4m -MMD -MF $(<:.c=.m) $(PYCFLAGS) $(CFLAGS)

-include $(HDS)

.PHONY: clean
clean:
	rm -f test $(OBJS)

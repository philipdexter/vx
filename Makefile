TARGET=vx

SOURCES=vx.c \
	text.c \
	buffer.c \
	window.c

OBJS = $(SOURCES:.c=.o)

HDS = $(SOURCES:.c=.m)

CFLAGS = -g -Wall -pedantic -std=c99 -O0

PYCFLAGS = $(shell /usr/bin/python3.4-config --cflags)
PYLDFLAGS = $(shell /usr/bin/python3.4-config --ldflags)

.PHONY: all
all: $(TARGET)


$(TARGET): $(OBJS)
	gcc -lpython3.4m -lncurses $(OBJS) -o$(TARGET) $(PYLDFLAGS)

.c.o:
	gcc -c $< -o $@ -I/usr/include/python3.4m -MMD -MF $(<:.c=.m) $(PYCFLAGS) $(CFLAGS)

-include $(HDS)

.PHONY: clean
clean:
	rm -f $(TARGET) $(OBJS)

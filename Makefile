TARGET=bin/vx

SOURCES=vx.c \
	text.c \
	buffer.c \
	window.c \
	vx_module.c

OUT_DIR = bin

OBJS = $(SOURCES:%.c=$(OUT_DIR)/%.o)

HDS = $(SOURCES:%.c=$(OUT_DIR)/%.m)

CFLAGS = -g -Wall -pedantic -std=c99 -O0

PYCFLAGS = $(shell /usr/bin/python3.4-config --cflags)
PYLDFLAGS = $(shell /usr/bin/python3.4-config --ldflags)

.PHONY: all
all: dirs $(TARGET)

.PHONY: dirs
dirs:
	mkdir -p $(OUT_DIR)

$(TARGET): $(OBJS)
	gcc -lpython3.4m -lncurses $(OBJS) -o$(TARGET) $(PYLDFLAGS)

$(OUT_DIR)/%.o: %.c
	gcc -c $< -o $@ -I/usr/include/python3.4m -MMD -MF $(<:%.c=$(OUT_DIR)/%.m) $(PYCFLAGS) $(CFLAGS)

-include $(HDS)

.PHONY: clean
clean:
	rm -rf $(OUT_DIR)


.PHONY: install
install: all
	mkdir -p ~/.vx
	cp ./start.py ~/.vx
	cp ./vx_intro.py ~/.vx
	cp -r ./vx_mod ~/.vx/vx_mod
	install -D -m0755 $(OUT_DIR)/vx /usr/bin/vx

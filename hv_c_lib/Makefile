# Makefile for the 'hv_c' library on linux

# Compiler
CC = gcc

# Compiler flags
CFLAGS = -Wall -Wextra -Werror -std=c99 -pedantic -g

# Source files
SRC = $(wildcard *.c)

# Object files
OBJ = $(SRC:.c=.o)

# Library name
LIB = libhv_c.so

# Default target
all: $(LIB)

# Compile source files into object files
%.o: %.c
	$(CC) $(CFLAGS) -fPIC -c $< -o $@

# Link object files into a shared library
$(LIB): $(OBJ)
	$(CC) -shared -o $@ $^

# Clean up
clean:
	rm -f $(OBJ) $(LIB)
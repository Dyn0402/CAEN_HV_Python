# Makefile for the 'hv_c' shared library on Linux

GLOBALDIR=      ./

LIBRARY=	libhv_c.so

CC=		gcc

FLAGS=		-DUNIX -DLINUX -fPIC -std=c99

LFLAGS=		-shared -Wl,-soname,$(LIBRARY)

LIBS=		-lcaenhvwrapper -lncurses -lpthread -ldl -lm

INCLUDEDIR=	-I./$(GLOBALDIR) -I./include/

SOURCES=	$(GLOBALDIR)hv_functions.c

OBJECTS=	$(SOURCES:.c=.o)

INCLUDES=	hv_functions.h CAENHVWrapper.h

########################################################################

CFLAGS=			$(FLAGS)

all:			$(LIBRARY)

$(LIBRARY):		$(OBJECTS)
			$(CC) $(CFLAGS) $(LFLAGS) -o $(LIBRARY) $(OBJECTS) $(LIBS)

$(GLOBALDIR)%.o:	$(GLOBALDIR)%.c
			$(CC) $(CFLAGS) $(INCLUDEDIR) -o $@ -c $<

install:		$(LIBRARY)
			cp $(LIBRARY) /usr/local/lib
			ldconfig

clean:
			rm -f $(OBJECTS) $(LIBRARY)

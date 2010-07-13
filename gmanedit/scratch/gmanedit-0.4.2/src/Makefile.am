## Process this file with automake to produce Makefile.in

INCLUDES = \
	@GTK_CFLAGS@ \
	-DDATADIR=\""$(datadir)"\" \
	-DLOCALEDIR=\""$(datadir)/locale"\" \
	-DG_DISABLE_DEPRECATED \
	-DGDK_DISABLE_DEPRECATED \
	-DGDK_PIXBUF_DISABLE_DEPRECATED \
	-DGTK_DISABLE_DEPRECATED

bin_PROGRAMS = gmanedit

gmanedit_SOURCES = \
	main.c \
	support.c support.h \
	interface.c interface.h \
	callbacks.c callbacks.h

gmanedit_LDADD = \
	@GTK_LIBS@


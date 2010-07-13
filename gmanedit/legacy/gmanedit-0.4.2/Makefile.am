## Process this file with automake to produce Makefile.in

SUBDIRS = po src
pixmapdir = $(datadir)/pixmaps

dist_pixmap_DATA = \
	pixmaps/gmanedit_icon.png \
	pixmaps/gmanedit.png

man_MANS = gmanedit.1

DESKTOP_FILES = gmanedit.desktop

desktopdir = $(datadir)/applications
desktop_DATA = $(DESKTOP_FILES)

ACLOCAL_AMFLAGS = -I m4

EXTRA_DIST = config.rpath $(DESKTOP_FILES) gmanedit.1

uninstall-local:
	rm -rf $(pkgdatadir)/*
	rmdir $(pkgdatadir)

/*
 *  Copyright 2000-2001 Sergio Rua
 *  Copyright 2008 Joop Stakenborg <pg4i@amsat.org>
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Library General Public License for more details.
 *
 *  You should have received a copy of the GNU Library General Public License
 *  along with this program; if not, write to the Free Software Foundation,
 *  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02111-1307, USA.
 */

#include <libintl.h>
#include <gtk/gtk.h>

#include "interface.h"
#include "support.h"

#define cuantos (sizeof(tabla)/sizeof(GtkTargetEntry))

enum {
          TARGET_STRING,
          TARGET_URL,
          TARGET_MAN
};

GtkWidget *wprincipal;

static GtkTargetEntry tabla[]={
        { "STRING", 0, TARGET_STRING },
        { "text/plain", 0, TARGET_STRING },
        { "text/uri-list", 0, TARGET_URL },
        { "application/x-troff-man", 0, TARGET_MAN }
};


int
main (int argc, char *argv[])
{
  GtkWidget *text;

#ifdef ENABLE_NLS
  bindtextdomain (PACKAGE, LOCALEDIR);
  textdomain (PACKAGE);
#endif

  add_pixmap_directory (DATADIR G_DIR_SEPARATOR_S "pixmaps");

  gtk_set_locale ();
  gtk_init (&argc, &argv);

  /*
   * The following code was added by Glade to create one of each component
   * (except popup menus), just so that you see something after building
   * the project. Delete any components that you don't want shown initially.
   */
  wprincipal = create_wprincipal ();
  gtk_widget_show (wprincipal);
  
  text=lookup_widget(GTK_WIDGET(wprincipal),"text");

  gtk_drag_dest_set(text, GTK_DEST_DEFAULT_ALL, tabla, cuantos-1, 
		  GDK_ACTION_COPY|GDK_ACTION_MOVE);

  gtk_main ();  
  return 0;
}


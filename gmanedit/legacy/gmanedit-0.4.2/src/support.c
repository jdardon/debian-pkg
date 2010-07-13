/*
 *  Copyright 2000-2001: Sergio Rua <srua@debian.org>
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

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string.h>

#include <gtk/gtk.h>

#include "support.h"

GtkWidget*
lookup_widget                          (GtkWidget       *widget,
                                        const gchar     *widget_name)
{
  GtkWidget *parent, *found_widget;

  for (;;)
    {
      if (GTK_IS_MENU (widget))
        parent = gtk_menu_get_attach_widget (GTK_MENU (widget));
      else
        parent = widget->parent;
      if (parent == NULL)
        break;
      widget = parent;
    }

  found_widget = (GtkWidget*) g_object_get_data (G_OBJECT (widget),
                                                   widget_name);
  if (!found_widget)
    g_warning ("Widget not found: %s", widget_name);
  return found_widget;
}

static GList *pixmaps_directories = NULL;
/* Use this function to set the directory containing installed pixmaps. */
void
add_pixmap_directory(const gchar        *directory)
{
        pixmaps_directories = g_list_prepend (pixmaps_directories, g_strdup (directory));
}

/* This is an internally used function to find pixmap files. */
static gchar*
find_pixmap_file(const gchar    *filename)
{
        GList *elem;

        /* We step through each of the pixmaps directory to find it. */
        elem = pixmaps_directories;
        while (elem)
        {
                gchar *pathname = g_strdup_printf ("%s%s%s", (gchar*)elem->data, G_DIR_SEPARATOR_S, filename);
                if (g_file_test (pathname, G_FILE_TEST_EXISTS))
                        return pathname;
                g_free (pathname);
                elem = elem->next;
        }
        return NULL;
}

GdkPixbuf*
create_image(const gchar *filename)
{
        gchar *pathname = NULL;
        GdkPixbuf *pixbuf;
        GError *error = NULL;

        if (!filename || !filename[0]) return NULL;

        pathname = find_pixmap_file (filename);

        if (!pathname)
        {
                g_warning (_("Couldn't find pixmap file: %s"), filename);
                return NULL;
        }

        pixbuf = gdk_pixbuf_new_from_file (pathname, &error);
        if (!pixbuf)
        {
                fprintf (stderr, _("Failed to load pixbuf file: %s: %s\n"),
                        pathname, error->message);
                g_error_free (error);
        }
        g_free (pathname);
        return pixbuf;
}


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

#ifdef ENABLE_NLS
  #include <libintl.h>
  #undef _
  #define _(String) dgettext (PACKAGE, String)
  #ifdef gettext_noop
	#define N_(String) gettext_noop (String)
  #else
	#define N_(String) (String)
  #endif
#else
  #define textdomain(String) (String)
  #define gettext(String) (String)
  #define dgettext(Domain,Message) (Message)
  #define dcgettext(Domain,Message,Type) (Message)
  #define bindtextdomain(Domain,Directory) (Domain)
  #define _(String) (String)
  #define N_(String) (String)
#endif

#define HOOKUP_OBJECT(component,widget,name) \
 g_object_set_data_full (G_OBJECT (component), name, \
 g_object_ref (widget), (GDestroyNotify) g_object_unref)

GtkWidget*  lookup_widget              (GtkWidget       *widget,
                                        const gchar     *widget_name);

GdkPixbuf* create_image            (const gchar     *filename);
void add_pixmap_directory(const gchar *directory);

/*
 *  Copyright 2000-2001: Sergio Rua
 *  Copyright 2008 Joop Stakenborg <pg4i@amsat.org>
 *  Copyright 2008 Anibal Avelar <aavelar@cofradia.org>
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

#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>
#include <zlib.h>
#include <sys/types.h>
#include <signal.h>
#include <unistd.h>
#include <argz.h>
#include <sys/wait.h>

#include <gtk/gtk.h>

#include "callbacks.h"
#include "interface.h"
#include "support.h"

#define BUFFER_SIZE 131072

extern GtkWidget *wprincipal;
GtkWidget *open_file=NULL;
GtkWidget *save_file=NULL;
GtkWidget *buscar=NULL;
GtkWidget *about=NULL;
GtkWidget *exit_dialog=NULL;
GtkWidget *prefs=NULL;
GtkWidget *wizard=NULL;

gchar *filename=NULL;
gint in_gzip=0;

/* Funciones */
static void save_as(gchar *name);
static void mensaje (gchar *msg,gint tipo);
static gchar *ReadConfFromFile(gchar *variable);
static void insert_label(const gchar *base,const gchar *text_info);
static void help_without_gnome(GtkWidget *wid);
static void open_man_file(gchar *manfile);


/* Eventos */
void
on_wprincipal_delete                  (GtkObject       *object,
                                        gpointer         user_data)
{
	if (exit_dialog==NULL)
		exit_dialog=create_exit_dialog();

	gtk_widget_show(exit_dialog);
}

void
on_cortar1_activate                    (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	GtkWidget *text,*statusbar;
	
	text = lookup_widget (GTK_WIDGET (wprincipal), "text");
	GtkTextBuffer *b = gtk_text_view_get_buffer (GTK_TEXT_VIEW(text));
	gtk_text_buffer_cut_clipboard (b, gtk_clipboard_get(GDK_SELECTION_CLIPBOARD), TRUE);
	statusbar = lookup_widget (GTK_WIDGET (wprincipal), "statusbar1");
	gtk_statusbar_pop (GTK_STATUSBAR (statusbar), 1);
	gtk_statusbar_push (GTK_STATUSBAR (statusbar), 1, _("Text cut."));
}


void
on_copiar1_activate                    (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	GtkWidget *text,*statusbar;
	
	text = lookup_widget (GTK_WIDGET (wprincipal), "text");
	GtkTextBuffer *b = gtk_text_view_get_buffer (GTK_TEXT_VIEW(text));
	gtk_text_buffer_copy_clipboard (b,  gtk_clipboard_get(GDK_SELECTION_CLIPBOARD));
	statusbar = lookup_widget (GTK_WIDGET (wprincipal), "statusbar1");
	gtk_statusbar_pop (GTK_STATUSBAR (statusbar), 1);
	gtk_statusbar_push (GTK_STATUSBAR (statusbar), 1, _("Text copied."));
	          
}


void
on_pegar1_activate                     (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	GtkWidget *text,*statusbar;
	
	text = lookup_widget (GTK_WIDGET (wprincipal), "text");
	GtkTextBuffer *b = gtk_text_view_get_buffer (GTK_TEXT_VIEW(text));
	gtk_text_buffer_paste_clipboard (b, gtk_clipboard_get(GDK_SELECTION_CLIPBOARD), NULL, TRUE);
	    
	statusbar = lookup_widget (GTK_WIDGET (wprincipal), "statusbar1");
	gtk_statusbar_pop (GTK_STATUSBAR (statusbar), 1);
	gtk_statusbar_push (GTK_STATUSBAR (statusbar), 1, _("Text pasted."));
}


void
on_pagina_base1_activate               (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
    const gchar *base=_(
    ".\\\"Created with GNOME Manpages Editor\n"
	".\\\"http://sourceforge.net/projects/gmanedit2\n\n"
	".\\\"Replace <program> with the program name, x with the Section Number\n"
	".TH <program> x \"<date>\" \"\" \"Linux User\'s Manual\"\n\n"
	".SH NAME\n<program> \\- program for...\n\n."
	".SH SYNOPSIS\n.B <program>\n.RI [ options ]\n.br\n\n"
	".SH DESCRIPTION\nThis manual page explains the \\fB<program>\\fP program."
	" The \\fB<program>\\fP program is for...\n\n"
	".SH OPTIONS\n.IP \\fB\\-OPTION\\fP\nThis option...\n\n"
	".SH NOTES\n\n"
	".SH \"SEE ALSO\"\n");

	insert_label(base,"Page created.");
}


void
on_novo1_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	GtkWidget *text,*statusbar;

	text=lookup_widget(GTK_WIDGET(wprincipal),"text");
	GtkTextBuffer *b = gtk_text_view_get_buffer (GTK_TEXT_VIEW(text));
	gtk_text_buffer_set_text (b, "", -1);
	statusbar = lookup_widget(GTK_WIDGET(wprincipal),"statusbar1");
	gtk_statusbar_pop (GTK_STATUSBAR (statusbar), 1);
	gtk_statusbar_push (GTK_STATUSBAR (statusbar), 1, _("New file."));
	in_gzip=0;
}


void
on_abrir1_activate                     (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *temp;

	open_file = create_fileselection (GTK_WIDGET(wprincipal));
	gtk_widget_show (open_file);
	if (gtk_dialog_run (GTK_DIALOG (open_file)) == GTK_RESPONSE_ACCEPT)
	{
		temp = gtk_file_chooser_get_filename (GTK_FILE_CHOOSER (open_file));
		filename = g_strdup(temp);
		gtk_widget_hide(open_file);
		open_man_file(filename);
	}
	else
		gtk_widget_destroy (open_file);
}


void
on_gardar1_activate                    (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
        const gchar *temp;
	if (filename!=NULL)
		save_as(filename);
	else
	{
		save_file=create_save_file(GTK_WIDGET(wprincipal));
		gtk_widget_show(save_file);
                if (gtk_dialog_run (GTK_DIALOG (save_file)) == GTK_RESPONSE_ACCEPT)
                {
                 temp = gtk_file_chooser_get_filename (GTK_FILE_CHOOSER (save_file));
                 filename = g_strdup(temp);
                 gtk_widget_hide(save_file);
                 save_as(filename);
                }else{
                 gtk_widget_destroy (save_file);
                }
	}
}


void
on_gardar_como1_activate               (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
        const gchar *temp;
	save_file=create_save_file(GTK_WIDGET(wprincipal));
        gtk_widget_show(save_file);
        if (gtk_dialog_run (GTK_DIALOG (save_file)) == GTK_RESPONSE_ACCEPT)
                {
                 temp = gtk_file_chooser_get_filename (GTK_FILE_CHOOSER (save_file));
                 filename = g_strdup(temp);
                 gtk_widget_hide(save_file);
                 save_as(filename);
        }else{
                 gtk_widget_destroy (save_file);
        }		
}


void
on_sair4_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	if (exit_dialog==NULL)
		exit_dialog=create_exit_dialog();

	gtk_widget_show(exit_dialog);
}

static void save_as(gchar *name)
{
	GtkWidget *text,*statusbar;
	FILE *f;
	gchar *datos;
	gint bytes_written;
	char extension[5];
	int n;

/* Esta comprabación se hace para permitir guardar un fichero comprimido */
/* sin comprimir */
	n = strlen(name)-3;
        strncpy(extension,name+n,3);
        if (!strncmp(extension,".gz",3))
            in_gzip=1;
        else
            in_gzip=0;

	text=lookup_widget(GTK_WIDGET(wprincipal),"text");
	
/* Barra de estado */
	statusbar=lookup_widget(GTK_WIDGET(wprincipal),"statusbar1");
	gtk_statusbar_pop(GTK_STATUSBAR(statusbar),1);

	GtkTextBuffer *b = gtk_text_view_get_buffer (GTK_TEXT_VIEW(text));
	GtkTextIter startiter, enditer;
	gtk_text_buffer_get_start_iter (b, &startiter);
	gtk_text_buffer_get_end_iter (b, &enditer);
	datos=gtk_text_buffer_get_text (b, &startiter, &enditer, FALSE);

	if (in_gzip)
		f=gzopen(name,"wb");
	else
		f=fopen(name,"w");
	
	if ((f!=NULL) && (f!=Z_NULL))
	{
	  if (!in_gzip)
		bytes_written=fwrite(datos,sizeof(gchar),strlen(datos),f);
	  else
	  	bytes_written=gzwrite(f,datos,strlen(datos));
  	  gtk_statusbar_push(GTK_STATUSBAR(statusbar),1,_("File saved."));		
	}
	else
	{
  	  gtk_statusbar_push(GTK_STATUSBAR(statusbar),1,_("File NOT saved."));		
  	  mensaje(strerror(errno),GTK_MESSAGE_ERROR);
	}
	if (in_gzip)
	    gzclose(f);
        else
	    fclose(f);
}

void
on_titulo_activate                     (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".TH <program> <section number> \"<date>\" \"\" \"Linux User\'s Manual\"\n\n");

	insert_label(base,"Title written.");
}


void
on_nome1_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH NAME\n<program> \\- program for... \n");

        insert_label(base,"Section name written.");
}


void
on_sinopsis1_activate                  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH SYNOPSIS\n");

 	insert_label(base,"Section synopsis written.");
}


void
on_configuration_activate                  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH CONFIGURATION\n");

 	insert_label(base,"Section configuration written.");
}

void
on_descripcion1_activate               (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH DESCRIPTION\n");

	insert_label(base,"Section description written.");
}


void
on_opcions1_activate                   (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH OPTIONS\n");

 	insert_label(base,"Section options written.");
}


void
on_valores_retornados1_activate        (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH \"RETURN VALUE\"\n");

 	insert_label(base,"Section return value written.");
}


void
on_estados_de_saida1_activate          (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH \"EXIT STATUS\"\n");
 	insert_label(base,"Section exit status written.");
}


void
on_errors_activate                       (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH ERRORS\n");

 	insert_label(base,"Section errors written.");
}


void
on_ficheiro1_activate                  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH FILES\n");
 	insert_label(base,"Section files written.");
}


void
on_entorno1_activate                   (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH ENVIRONMENT\n");
 	insert_label(base,"Section environment written.");
}


void
on_versions_activate               (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH VERSIONS\n");
 	insert_label(base,"Section versions written.");
}


void
on_notas1_activate                     (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH NOTES\n");
 	insert_label(base,"Section notes written.");
}


void
on_bugs1_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH BUGS\n");
 	insert_label(base,"Section bugs written.");
}


void
on_exemplos1_activate                  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH EXAMPLE\n");

 	insert_label(base,"Section examples written.");
}


void
on_ver_tamen1_activate                 (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH \"SEE ALSO\"\n");
 	insert_label(base,"Section see also written.");
}


void
on_conforme_a1_activate                (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH \"CONFORMING TO\"\n");
 	insert_label(base,"Section conforming to written.");
}


void
on__1_activate                         (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{

}


void
on_otro1_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SH \"<SECTION NAME>\"\n");
 	insert_label(base,"Section other written.");
}


void
on_ambas1_activate                     (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".AD B\n";
 	insert_label(base,"Right and left justify.");
}


void
on_activar1_activate                   (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".FI\n";
 	insert_label(base,"Filling enabled.");
}


void
on_desactivar1_activate                (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".NF\n";
 	insert_label(base,"Filling disabled.");    
}


void
on_bold1_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".B\n";
 	insert_label(base,"Font Bold selected.");    
}


void
on_bold_roman1_activate                (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".BR\n";
 	insert_label(base,"Font Bold-Roman selected."); 
}


void
on_italica1_activate                   (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".I\n";
 	insert_label(base,"Font Italic selected."); 
}


void
on_italica_bold1_activate              (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".IB\n";
 	insert_label(base,"Font Italic-Bold selected."); 
}


void
on_italica_roman1_activate             (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".IR\n";
 	insert_label(base,"Font Italic-Roman selected."); 
}


void
on_roman_bold1_activate                (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".RB\n";
 	insert_label(base,"Font Roman-Bold selected."); 
}


void
on_roman_italic1_activate              (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".RI\n";
 	insert_label(base,"Font Roman-Italic selected."); 
}


void
on_small_bold1_activate                (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".SB\n";
 	insert_label(base,"Font Small-Bold selected."); 
}


void
on_small1_activate                     (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".SM\n";
 	insert_label(base,"Font Small selected."); 
}


void
on_novo_parrafo1_activate              (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".LP\n";
 	insert_label(base,"New paragraph."); 
}


void
on_comezo_parrafo1_activate            (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".PP\n";
 	insert_label(base,"Paragraph start."); 
}


void
on_comezo_marxen1_activate             (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".RS <margin position>\n");
 	insert_label(base,"Margin position."); 
}


void
on_finaliza_marxen1_activate           (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".RE\n";
 	insert_label(base,"Relative margin end."); 
}


void
on_tabulador_por_defecto1_activate     (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".DT\n";
 	insert_label(base,"Default tab.");
 }


void
on_subcabeceira1_activate              (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=_(".SS \"<NAME>\"\n");
 	insert_label(base,"Subheader inserted.");
}

void
on_xustificacion_a_esquerda1_activate  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *base=".AD L\n";
 	insert_label(base,"Left justifier.");
 	
}

void
on_paxina_creada1_activate             (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	GtkWidget *text,*statusbar;
	FILE *f;
	gint bytes_written=0;
	gchar temp[30];
	gchar command[50],*datos;
	gint exitstatus;

/* I read conf file ~/.gmaneditrc */
	
	strcpy(temp, "/tmp/gmanedit.XXXXXX");
	mkstemp (temp);
	datos=ReadConfFromFile("COMMAND");

	if (datos==NULL)
		snprintf(command, sizeof command, "xterm -e man -l %s", temp);
	else
		snprintf(command, sizeof command, "%s -l %s", datos, temp);

	text=lookup_widget(wprincipal,"text");
	
/* Barra de estado */
	statusbar=lookup_widget(wprincipal,"statusbar1");
	gtk_statusbar_pop(GTK_STATUSBAR(statusbar),1);
	gtk_statusbar_push(GTK_STATUSBAR(statusbar),1,_("Page preview."));	

	GtkTextBuffer *b = gtk_text_view_get_buffer (GTK_TEXT_VIEW(text));
	GtkTextIter startiter, enditer;
	gtk_text_buffer_get_start_iter (b, &startiter);
	gtk_text_buffer_get_end_iter (b, &enditer);
	datos=gtk_text_buffer_get_text (b, &startiter, &enditer, FALSE);
	if ((f=fopen(temp,"w"))!=NULL)
	{
 	     bytes_written=fwrite(datos,sizeof(gchar),strlen(datos),f);
	     fclose(f);
	}
	else
	     mensaje(strerror(errno),GTK_MESSAGE_ERROR);


	if (bytes_written>0)
		g_spawn_command_line_sync(command, NULL, NULL, &exitstatus, NULL);
	unlink(temp);
}

void
on_buscar_e_reemprazar1_activate        (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
     if (buscar == NULL)
            buscar = create_wbuscar();
             
     gtk_widget_show(buscar);
}

void
on_opcions_programa1_activate        (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	gchar *aux;
	GtkWidget *obj;
	gchar datos[255];
	
	prefs=create_wpreferences();
	aux=ReadConfFromFile("COMMAND");
	if (aux != NULL)
	{
		strncpy(datos,aux, sizeof datos - 1);
		datos[sizeof(datos) - 1] = 0;
		obj=lookup_widget(GTK_WIDGET(prefs),"entry_command");
		gtk_entry_set_text(GTK_ENTRY(obj),datos);
	}
	aux=ReadConfFromFile("INTERNET_BROWSER");
	if (aux != NULL)
	{
		strncpy(datos,aux, sizeof(datos) - 1);
		datos[sizeof(datos) - 1] = 0;
		obj=lookup_widget(GTK_WIDGET(prefs),"combo2");
		if (!strcmp(datos, "mozilla"))
			 gtk_combo_box_set_active (GTK_COMBO_BOX(obj), 0);
		else if (!strcmp(datos, "firefox"))
			 gtk_combo_box_set_active (GTK_COMBO_BOX(obj), 1);
		else if (!strcmp(datos, "galeon"))
			 gtk_combo_box_set_active (GTK_COMBO_BOX(obj), 2);
		else if (!strcmp(datos, "epiphany"))
			 gtk_combo_box_set_active (GTK_COMBO_BOX(obj), 3);
		else if (!strcmp(datos, "konqueror"))
			 gtk_combo_box_set_active (GTK_COMBO_BOX(obj), 4);
	}
	gtk_widget_show(prefs);
}


void
on_bbuscar_clicked                     (GtkButton       *button,
                                        gpointer         user_data)
{

}


void
on_breemprazar_clicked                 (GtkButton       *button,
                                        gpointer         user_data)
{

}


void
on_bpechar_clicked                     (GtkButton       *button,
                                        gpointer         user_data)
{
	gtk_widget_hide(buscar);
}


void
on_data1_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
     GtkWidget *text,*statusbar;
     GtkTextBuffer*  buffer;
     time_t fech;
     struct tm *fecha;
     gchar cad[30];
     gchar *meses[]={_("January"),_("February"),_("March"),_("April"),
        		_("May"),_("June"),_("July"),_("August"),
        		_("September"),_("October"),_("November"),_("December")};

	
     time(&fech);
     fecha=localtime(&fech);
	
	if (fecha!=NULL)
	{
		sprintf(cad,"%d %s %d",fecha->tm_mday,meses[fecha->tm_mon],fecha->tm_year+1900);
		text=lookup_widget(wprincipal,"text");	
		if (GTK_IS_TEXT_VIEW (text)){
                  buffer = gtk_text_view_get_buffer (GTK_TEXT_VIEW (text));
                  gtk_text_buffer_insert_at_cursor( buffer, cad ,strlen(cad));
	        }
		statusbar = lookup_widget(wprincipal,"statusbar1");
		gtk_statusbar_pop (GTK_STATUSBAR (statusbar), 1);
		gtk_statusbar_push (GTK_STATUSBAR (statusbar), 1, _("Date inserted."));    
	}
	else
		mensaje(_("Cannot get system date!"),GTK_MESSAGE_ERROR);		
}

void
on_about2_activate                     (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
     create_about();
}

static void
mensaje (gchar *msg,gint tipo)
{
	GtkWidget *msgbox;
	
	msgbox=gtk_message_dialog_new(GTK_WINDOW(wprincipal),GTK_DIALOG_MODAL,tipo, GTK_BUTTONS_OK, msg,NULL);
	gtk_dialog_run (GTK_DIALOG (msgbox));
    gtk_widget_destroy (msgbox);
}

void
on_bdialog_yes_clicked                 (GtkButton       *button,
                                        gpointer         user_data)
{
	gtk_main_quit();
}


void
on_bdialog_no_clicked                  (GtkButton       *button,
                                        gpointer         user_data)
{
	gtk_widget_hide(exit_dialog);
}

void
on_bpok_clicked                        (GtkButton       *button,
                                        gpointer         user_data)
{
	FILE *p;
	GtkWidget *entry,*ch;
	const gchar *entry_text=NULL;
	gchar buf[1024];
	gchar *rcname, *browser;

	rcname = g_build_filename (g_get_home_dir(), G_DIR_SEPARATOR_S, ".gmaneditrc", NULL );

	entry=lookup_widget(prefs,"entry_command");
	entry_text=gtk_entry_get_text(GTK_ENTRY(entry));
	ch = lookup_widget(prefs, "combo2");
	browser = gtk_combo_box_get_active_text (GTK_COMBO_BOX (ch));
	snprintf(buf, sizeof buf, "# File created by gmanedit preferences option\n\nCOMMAND=%s\nINTERNET_BROWSER=%s", entry_text, browser);
	g_free(browser);
	
	if ((p=fopen(rcname,"w"))!=NULL)
	{
		fprintf(p,"%s\n",buf);
		fclose(p);	
	}
	else
		mensaje(strerror(errno),GTK_MESSAGE_ERROR);
	g_free (rcname);
	gtk_widget_destroy(prefs);
}


void
on_bpcancel_clicked                    (GtkButton       *button,
                                        gpointer         user_data)
{
	gtk_widget_destroy(prefs);
}

static gchar *ReadConfFromFile(gchar *variable)
{
  FILE *f;
  gchar *rcname;
  gchar *tok;
  gchar buf[1024];
  
  rcname = g_build_filename (g_get_home_dir(), G_DIR_SEPARATOR_S, ".gmaneditrc", NULL );
  f = fopen(rcname,"r");
  g_free (rcname);

  if (f == NULL) return((gchar *)NULL);
    
  while (fgets(buf,80,f) != NULL)
  {
     if (buf[strlen(buf)-1] == '\n')
     	buf[strlen(buf)-1] = '\0';
       
     if ((buf[0] != '#') && (!strncmp(variable,buf,strlen(variable))))
     {
        tok = strtok(buf,"=");
        tok = strtok(NULL,"=");
        fclose(f);
        return(tok);
     }    
  }
  fclose(f);
  return((gchar *)NULL);
}

void
on_help1_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	help_without_gnome(wprincipal);
}


void
on_select_all1_activate                (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
    GtkWidget *text,*statusbar;
    gchar *datos;
	
	text = lookup_widget (GTK_WIDGET (wprincipal), "text");

	GtkTextBuffer *b = gtk_text_view_get_buffer (GTK_TEXT_VIEW(text));
	GtkTextIter startiter, enditer;
	gtk_text_buffer_get_start_iter (b, &startiter);
	gtk_text_buffer_get_end_iter (b, &enditer);
	datos=gtk_text_buffer_get_text (b, &startiter, &enditer, FALSE);

	if (strlen(datos)>0)
	{
	gtk_text_buffer_select_range (b, &startiter, &enditer);
	statusbar = lookup_widget (GTK_WIDGET (wprincipal), "statusbar1");
	gtk_statusbar_pop (GTK_STATUSBAR (statusbar), 1);
	gtk_statusbar_push (GTK_STATUSBAR (statusbar), 1, _("Text selected."));
	}
}


void
on_new_wizard_page1_activate           (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	if (wizard == NULL)
		wizard=create_wizard();
	gtk_widget_show(wizard);
}

void
on_assistant_cancel                    (GtkAssistant *assistant,
                                        gpointer         user_data)
{
	gtk_widget_destroy (GTK_WIDGET(assistant));
	wizard = NULL;
}


void
on_dthe_end_finish                     (GtkAssistant *assistant,
                                        gpointer         user_data)
{
   GtkWidget *ch,*text,*druid;
   gchar *nombre,*snumber,*date,*title;
   gchar cadena[500];
   gint number;

/* Init for main_window */
   druid = gtk_widget_get_toplevel (GTK_WIDGET (assistant));

/* First, I get man page name from step 1 */
   text = lookup_widget(GTK_WIDGET(assistant), "mname");
   nombre = gtk_editable_get_chars(GTK_EDITABLE(text),0,-1);

/* Date from step 1 */
   text = lookup_widget(GTK_WIDGET(assistant), "mdate");
   date = gtk_editable_get_chars(GTK_EDITABLE(text),0,-1);

/* Title from step 1 */
   text = lookup_widget(GTK_WIDGET(assistant), "mtitle");
   title = gtk_editable_get_chars(GTK_EDITABLE(text),0,-1);

/* Section number from combo */
   ch = lookup_widget(GTK_WIDGET(assistant), "combo1");
   number = gtk_combo_box_get_active (GTK_COMBO_BOX(ch));
   snumber = g_strdup_printf ("%d", number+1);

/* Page Start */
   strcpy(cadena,
   ".\\\"Created with GNOME Manpages Editor Wizard\n"
   ".\\\"http://sourceforge.net/projects/gmanedit2\n");
   strcat(cadena,".TH ");
   strcat(cadena,nombre);
   strcat(cadena," ");
   strcat(cadena,snumber);
   strcat(cadena," \"");
   strcat(cadena,date);   
   strcat(cadena,"\" ");
   strcat(cadena,"\"\" ");
   strcat(cadena,"\"");
   strcat(cadena,title);   
   strcat(cadena,"\"\n\n");
   
/* Section NAME */
   ch = lookup_widget (GTK_WIDGET (assistant), "chname");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
   {
	strcat(cadena,_(".SH NAME\n"));   
	strcat(cadena,nombre);
	strcat(cadena,_(" \\- program for...\n\n"));
   }
/* Section SYNOPSIS */
   ch = lookup_widget (GTK_WIDGET (assistant), "chsynopsis");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
   {
	strcat(cadena,_(".SH SYNOPSIS\n.B "));   
	strcat(cadena,nombre);
	strcat(cadena,_("\n.RI [ options ]\n.br\n\n"));
   }
/* Section CONFIGURATION */
   ch = lookup_widget (GTK_WIDGET (assistant), "chconfiguration");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH CONFIGURATION\n\n"));   
/* Section DESCRIPTION */
   ch = lookup_widget (GTK_WIDGET (assistant), "chdescription");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
   {
	strcat(cadena,_(".SH DESCRIPTION\nThis manual page explains the\n.B "));   
	strcat(cadena,nombre);
	strcat(cadena,_("\nprogram. This program...\n.PP\n\\fB"));
	strcat(cadena,nombre);
	strcat(cadena,_("\\fP is for...\n\n"));
   }
/* Section OPTIONS */
   ch = lookup_widget (GTK_WIDGET (assistant), "choptions");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH OPTIONS\n.B\n.IP -OPTION\nThis option...\n\n"));   
/* Section EXIT STATUS */
   ch = lookup_widget (GTK_WIDGET (assistant), "chexitstatus");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH \"EXIT STATUS\"\n\n"));   


/* Section RETURN VALUE */
   ch = lookup_widget (GTK_WIDGET (assistant), "chreturnvalues");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,".SH \"RETURN VALUE\"\n\n");   
/* Section ERRORS */
   ch = lookup_widget (GTK_WIDGET (assistant), "cherrors");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH ERRORS\n\n"));   
/* Section ENVIRONMENT */
   ch = lookup_widget (GTK_WIDGET (assistant), "chenvironment");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH ENVIRONMENT\n\n"));   
/* Section FILES */
   ch = lookup_widget (GTK_WIDGET (assistant), "chfiles");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH FILES\n\n"));   
/* Section VERSIONS */
   ch = lookup_widget (GTK_WIDGET (assistant), "chversions");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH VERSIONS\n\n"));   

/* Section CONFORMING TO */
   ch = lookup_widget (GTK_WIDGET (assistant), "chconformingto");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH \"CONFORMING TO\"\n\n"));   
/* Section NOTES */
   ch = lookup_widget (GTK_WIDGET (assistant), "chnotes");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH NOTES\n\n"));   
/* Section BUGS */
   ch = lookup_widget (GTK_WIDGET (assistant), "chbugs");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH BUGS\n\n"));   
/* Section EXAMPLE */
   ch = lookup_widget (GTK_WIDGET (assistant), "chexample");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH EXAMPLE\n\n"));   
/* Section SEE ALSO */
   ch = lookup_widget (GTK_WIDGET (assistant), "chseealso");
   if (gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(ch))==TRUE)
	strcat(cadena,_(".SH \"SEE ALSO\"\n\n"));   
	
/* Hide wizard */
   gtk_widget_hide(wizard);
   
/* Insert all into gmanedit */
   insert_label(cadena,_("Wizard page created."));

/* Wizard closed */
   gtk_widget_destroy(wizard);
   wizard=NULL;
}

static
void insert_label(const gchar *base,const gchar *text_info)
{
	GtkWidget *text,*statusbar;
        GtkTextBuffer *buffer;

	text=lookup_widget(GTK_WIDGET(wprincipal),"text");
        buffer = gtk_text_view_get_buffer (GTK_TEXT_VIEW (text));
        gtk_text_buffer_insert_at_cursor(buffer, base, -1);
	
	statusbar = lookup_widget(GTK_WIDGET(wprincipal),"statusbar1");
	gtk_statusbar_pop (GTK_STATUSBAR (statusbar), 1);
	gtk_statusbar_push (GTK_STATUSBAR (statusbar), 1, text_info);
}

void
on_home_page1_activate                 (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	gchar *browser;
	gchar buf[1024];
	gint exitstatus;
	
	browser=ReadConfFromFile("INTERNET_BROWSER");
	if (browser==NULL)
		browser="mozilla";
	snprintf(buf, sizeof buf, "%s http://sourceforge.net/projects/gmanedit2", browser);

	g_spawn_command_line_sync(buf, NULL, NULL, &exitstatus, NULL);
}

static void help_without_gnome(GtkWidget *wid)
{
	GtkWidget *statusbar;
	gchar *datos;
	gchar temp[10],command[1024];
	gint exitstatus;

	strcpy(temp," 7 man");
	datos=ReadConfFromFile("COMMAND");

	if (datos==NULL)
		snprintf(command, sizeof command, "xterm -e man %s", temp);
	else
		snprintf(command, sizeof command, "%s %s", datos, temp);

	g_spawn_command_line_sync(command, NULL, NULL, &exitstatus, NULL);

/* Barra de estado */
	statusbar=lookup_widget(GTK_WIDGET(wprincipal),"statusbar1");
	gtk_statusbar_pop(GTK_STATUSBAR(statusbar),1);
	gtk_statusbar_push(GTK_STATUSBAR(statusbar),1,_("Man help."));	
}

static void open_man_file(gchar *manfile)
{
	GtkWidget *statusbar,*text;
	GtkTextBuffer *tb;
	gzFile *f;
	gint bytes_read;
	int n;
	char extension[10];
	gchar *utf8;
	gchar * buffer = (gchar*)malloc(BUFFER_SIZE);


	text=lookup_widget(GTK_WIDGET(wprincipal),"text");
	tb = gtk_text_view_get_buffer (GTK_TEXT_VIEW (text));
	gtk_text_buffer_set_text (tb, "", 0);
	
/* Barra de estado */
	statusbar=lookup_widget(GTK_WIDGET(wprincipal),"statusbar1");
	gtk_statusbar_pop(GTK_STATUSBAR(statusbar),1);
	gtk_statusbar_push(GTK_STATUSBAR(statusbar),1,_("File opened."));	

/* Ahora abro el fichero */

	n = strlen(manfile)-3;
	strncpy(extension,manfile+n,3);
	if (!strncmp(extension,".gz",3))
	    in_gzip=1;
	else
	    in_gzip=0;


	if ((f=gzopen((gchar *)manfile,"rb"))!=NULL)
	{
	  while(!gzeof(f))
	  {
		bytes_read=gzread(f,buffer,BUFFER_SIZE);
		if (bytes_read>0)
		{
			utf8 = NULL;
			if (g_utf8_validate(buffer, -1, NULL) == FALSE)
			{
				utf8 = g_locale_to_utf8(buffer, -1, NULL, NULL, NULL);
			}
			if (utf8 != NULL){
				strncpy(buffer,utf8, BUFFER_SIZE - 1);
				buffer[BUFFER_SIZE - 1] = 0;
			}
			gtk_text_buffer_insert_at_cursor(tb, buffer ,bytes_read);
		} 
	  }
  	  gzclose(f);
	}
	else
		mensaje(strerror(errno),GTK_MESSAGE_ERROR);
	if (open_file) gtk_widget_destroy (open_file);
}

void
on_text_drag_data_received             (GtkWidget       *widget,
                                        GdkDragContext  *drag_context,
                                        gint             x,
                                        gint             y,
                                        GtkSelectionData *data,
                                        guint            info,
                                        guint            time,
                                        gpointer         user_data)
{
	if (data->length >= 0)
	{
	    if (!strncmp((gchar *)data->data,"file:",4))
	    {
		filename=(gchar *)data->data+5;
		filename[strlen(filename)-2]='\0';
		open_man_file(filename);
	    }

	}
	gtk_drag_finish(drag_context, TRUE, FALSE, time);
}


void
on_comments1_activate                  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
	const gchar *comm=".\\\" ";

	insert_label(comm,"Label Comments Inserted.");
}

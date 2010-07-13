# -*- coding: utf-8 -*-

# field_gtk.py
# Copyright (C) 2007-2008 Jean-Baptiste LAMY -- jiba@tuxfamily.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import editobj2
from editobj2.field import *
from editobj2.field import _RangeField, _ShortEnumField, _LongEnumField
import gobject, gtk, gtk.gdk as gdk

class GtkField(MultiGUIField):
  y_flags = gtk.FILL

class GtkEntryField(GtkField, EntryField, gtk.Entry):
  def __init__(self, gui, master, o, attr, undo_stack):
    gtk.Entry.__init__(self)
    super(GtkEntryField, self).__init__(gui, master, o, attr, undo_stack)
    
    self.update()
    self.connect("focus_out_event", self.validate)
    self.connect("key_press_event", self.validate)
    
  def validate(self, widget, event):
    if (event.type is gdk.KEY_PRESS) and ((not event.string) or (not event.string in "\r\n")): return
    s = self.get_text().decode("utf-8")
    if s != self.old_str:
      self.old_str = s
      self.set_value(s)
      
  def update(self):
    self.updating = 1
    try:
      self.old_str = self.get_value()
      self.set_text(self.old_str)
    finally:
      self.updating = 0
    
    
class GtkIntField   (GtkEntryField, IntField): pass # XXX no "spin-button" since they don't allow entering e.g. "1 + 2" as an integer !
class GtkFloatField (GtkEntryField, FloatField): pass
class GtkStringField(GtkEntryField, StringField): pass

class GtkPasswordField(GtkStringField, PasswordField):
  def __init__(self, gui, master, o, attr, undo_stack):
    GtkStringField.__init__(self, gui, master, o, attr, undo_stack)
    self.set_visibility(0)
  

class GtkBoolField(GtkField, BoolField, gtk.CheckButton):
  def __init__(self, gui, master, o, attr, undo_stack):
    gtk.CheckButton.__init__(self)
    super(GtkBoolField, self).__init__(gui, master, o, attr, undo_stack)
    
    self.update()
    self.connect("toggled", self.validate)
    self.connect("clicked", self.clicked)
    
  def validate(self, *event):
    v = self.descr.get(self.o, self.attr)
    if isinstance(v, int):
      self.set_value(int(self.get_active()))
    else:
      self.set_value(bool(self.get_active()))
  
  def clicked(self, *event):
    if self.get_inconsistent(): self.set_inconsistent(0)
    
  def update(self):
    self.updating = 1
    try:
      v = self.descr.get(self.o, self.attr)
      if v is introsp.NonConsistent: self.set_inconsistent(1)
      else: self.set_active(v)
    finally:
      self.updating = 0


class GtkProgressBarField(GtkField, ProgressBarField, gtk.ProgressBar):
  def __init__(self, gui, master, o, attr, undo_stack):
    gtk.ProgressBar.__init__(self)
    super(ProgressBarField, self).__init__(gui, master, o, attr, undo_stack)
    self.update()
    
  def update(self):
    v = self.get_value()
    if v is introsp.NonConsistent:
      self.pulse()
    else: self.set_fraction(v)
    

class GtkEditButtonField(GtkField, EditButtonField, gtk.Button):
  def __init__(self, gui, master, o, attr, undo_stack):
    gtk.Button.__init__(self, editobj2.TRANSLATOR(u"Edit..."))
    super(GtkEditButtonField, self).__init__(gui, master, o, attr, undo_stack)
    self.connect("clicked", self.on_click)
    self.update()
    
  def update(self):
    self.set_property("sensitive", not self.get_value() is None)
    
    
class GtkWithButtonStringField(GtkField, WithButtonStringField, gtk.HBox):
  def __init__(self, gui, master, o, attr, undo_stack):
    gtk.HBox.__init__(self)
    super(GtkWithButtonStringField, self).__init__(gui, master, o, attr, undo_stack)
    self.pack_start(self.string_field)
    button = gtk.Button(editobj2.TRANSLATOR(self.button_text))
    button.connect("clicked", self.on_button)
    self.pack_end(button, 0, 1)
    
class GtkFilenameField(GtkWithButtonStringField, FilenameField):
  def on_button(self, *args):
    dialog = gtk.FileChooserDialog(action = gtk.FILE_CHOOSER_ACTION_SAVE, buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
    dialog.set_resizable(1)
    dialog.set_current_name(self.get_value())
    if dialog.run() == gtk.RESPONSE_OK:
      filename = dialog.get_filename()
      if filename:
        self.string_field.set_value(filename)
        self.string_field.update()
    dialog.destroy()
    
class GtkDirnameField(GtkWithButtonStringField, DirnameField):
  def on_button(self, *args):
    dialog = gtk.FileChooserDialog(action = gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER, buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
    dialog.set_resizable(1)
    dialog.set_current_folder(self.get_value())
    if dialog.run() == gtk.RESPONSE_OK:
      folder = dialog.get_current_folder()
      if folder:
        self.string_field.set_value(folder)
        self.string_field.update()
    dialog.destroy()
    
    
class GtkURLField(GtkWithButtonStringField, URLField):
  def on_button(self, *args):
    import webbrowser
    webbrowser.open_new(self.get_value())
    

class GtkTextField(GtkField, TextField, gtk.ScrolledWindow):
  y_flags = gtk.FILL | gtk.EXPAND
  def __init__(self, gui, master, o, attr, undo_stack):
    gtk.ScrolledWindow.__init__(self)
    super(GtkTextField, self).__init__(gui, master, o, attr, undo_stack)
    self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.set_shadow_type(gtk.SHADOW_IN)
    self.set_size_request(-1, 125)
    
    self.text = gtk.TextView()
    self.text.set_wrap_mode(gtk.WRAP_WORD)
    self.text.set_size_request(200, -1)
    self.text.connect("focus_out_event", self.validate)
    self.add(self.text)
    self.update()
    
  def validate(self, *args):
    s = self.text.get_buffer().get_text(*self.text.get_buffer().get_bounds()).decode("utf-8")
    self.set_value(s)
    
  def update(self):
    self.updating = 1
    try:
      self.old_str = self.get_value()
      self.text.get_buffer().set_text(self.old_str)
    finally:
      self.updating = 0

class GtkObjectAttributeField(GtkField, ObjectAttributeField, gtk.Frame):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(GtkObjectAttributeField, self).__init__(gui, master, o, attr, undo_stack)
    gtk.Frame.__init__(self)
    self.set_shadow_type(gtk.SHADOW_IN)
    self.add(self.attribute_pane)

class GtkObjectHEditorField(GtkField, ObjectHEditorField, gtk.Frame):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(GtkObjectHEditorField, self).__init__(gui, master, o, attr, undo_stack)
    gtk.Frame.__init__(self)
    self.set_shadow_type(gtk.SHADOW_IN)
    self.add(self.editor_pane)

class GtkObjectVEditorField(GtkField, ObjectVEditorField, gtk.Frame):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(GtkObjectVEditorField, self).__init__(gui, master, o, attr, undo_stack)
    gtk.Frame.__init__(self)
    self.set_shadow_type(gtk.SHADOW_IN)
    self.add(self.editor_pane)

class Gtk_RangeField(GtkField, _RangeField, gtk.HScale):
  def __init__(self, gui, master, o, attr, undo_stack, min, max, incr = 1):
    self.adjustment = gtk.Adjustment(0, min, max, incr)
    gtk.HScale.__init__(self, self.adjustment)
    self.set_digits(0)
    super(Gtk_RangeField, self).__init__(gui, master, o, attr, undo_stack, min, max, incr)
    self.connect("value_changed", self.validate)
    
  def validate(self, *args):
    if self.updating: return
    self.set_value(int(round(self.adjustment.get_value())))
    
  def update(self):
    self.updating = 1
    try:
      self.adjustment.set_value(self.get_value())
    finally:
      self.updating = 0
    
class Gtk_ShortEnumField(GtkField, _ShortEnumField, gtk.ComboBox):
  def __init__(self, gui, master, o, attr, undo_stack, choices, value_2_enum = None, enum_2_value = None):
    self.liststore = gtk.ListStore(gobject.TYPE_STRING)
    gtk.ComboBox.__init__(self, self.liststore)
    cell = gtk.CellRendererText()
    self.pack_start(cell, True)
    self.add_attribute(cell, 'text', 0)
    super(Gtk_ShortEnumField, self).__init__(gui, master, o, attr, undo_stack, choices, value_2_enum, enum_2_value)
    
    for choice in self.choice_keys: self.liststore.append((choice,))
    self.update()
    self.connect("changed", self.validate)
    
  def validate(self, *args):
    i = self.get_active()
    if i != -1: self.set_value(self.choices[self.choice_keys[i]])
    
  def update(self):
    self.updating = 1
    try:
      i = self.choice_2_index.get(self.get_value())
      if not i is None: self.set_active(i)
      else: self.set_active(-1)
    finally:
      self.updating = 0
      
class Gtk_LongEnumField(GtkField, _LongEnumField, gtk.ScrolledWindow):
  y_flags = gtk.FILL | gtk.EXPAND
  def __init__(self, gui, master, o, attr, undo_stack, choices, value_2_enum = None, enum_2_value = None):
    gtk.ScrolledWindow.__init__(self)
    self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.set_shadow_type(gtk.SHADOW_IN)
    self.set_size_request(-1, 125)
    
    super(Gtk_LongEnumField, self).__init__(gui, master, o, attr, undo_stack, choices, value_2_enum, enum_2_value)
    
    self.liststore = gtk.ListStore(gobject.TYPE_STRING)
    for choice in self.choice_keys: self.liststore.append((choice,))
    renderer = gtk.CellRendererText()
    self.treeview = gtk.TreeView(self.liststore)
    self.treeview.set_headers_visible(0)
    self.treeview.append_column(gtk.TreeViewColumn(None, renderer, text = 0))
    self.add(self.treeview)
    
    self.update()
    self.treeview.get_selection().connect("changed", self.validate)
    
  def validate(self, *args):
    liststore, iter = self.treeview.get_selection().get_selected()
    if iter:
      i = int(liststore.get_path(iter)[0])
      if i != self.i:  # XXX validate is called twice by GTK, why ?
        self.i = i
        enum = self.choices[self.choice_keys[i]]
        self.set_value(enum)
        
  def update(self):
    self.updating = 1
    try:
      selection = self.treeview.get_selection()
      selection.unselect_all()
      self.i = self.choice_2_index.get(self.get_value())
      if not self.i is None:
        selection.select_iter(self.liststore.get_iter(self.i))
        self.treeview.scroll_to_cell(self.i)
    finally:
      self.updating = 0

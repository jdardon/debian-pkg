# -*- coding: utf-8 -*-

# field_tk.py
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

from editobj2.field import *
from editobj2.field import _RangeField, _ShortEnumField, _LongEnumField
import Tkinter

class TkField(MultiGUIField):
  pass

class TkEntryField(TkField, EntryField, Tkinter.Entry):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(TkEntryField, self).__init__(gui, master, o, attr, undo_stack)
    self.str = Tkinter.StringVar()
    
    self.old_str = self.get_value()
    
    self.str.set(self.old_str)
    
    Tkinter.Entry.__init__(self, master, width = 25, textvariable = self.str, background = "white")
    self.bind("<FocusOut>"       , self.validate)
    self.bind("<KeyPress-Return>", self.validate)
    
  def validate(self, event = None):
    s = self.str.get()
    if s != self.old_str:
      self.old_str = s
      self.set_value(s)
      
  def update(self):
    self.updating = 1
    try:
      self.old_str = self.get_value()
      self.str.set(self.old_str)
    finally: self.updating = 0
    
    
class TkFloatField (TkEntryField, FloatField ): pass
class TkIntField   (TkEntryField, IntField   ): pass
class TkStringField(TkEntryField, StringField): pass

class TkPasswordField(TkStringField, PasswordField):
  def __init__(self, gui, master, o, attr, undo_stack):
    TkStringField.__init__(self, gui, master, o, attr, undo_stack)
    self["show"] = "*"
  

class TkEditButtonField(TkField, EditButtonField, Tkinter.Button):
  def __init__(self, gui, master, o, attr, undo_stack):
    Tkinter.Button.__init__(self, master, text = editobj2.TRANSLATOR(u"Edit..."), command = self.on_click)
    super(TkEditButtonField, self).__init__(gui, master, o, attr, undo_stack)
    self.update()
    
  def update(self):
    self.updating = 1
    try:
      if self.get_value() is None: self.configure(state = "disabled")
      else:                        self.configure(state = "normal")
    finally: self.updating = 0
    
    
class TkWithButtonStringField(TkField, WithButtonStringField, Tkinter.Frame):
  def __init__(self, gui, master, o, attr, undo_stack):
    Tkinter.Frame.__init__(self, master)
    super(TkWithButtonStringField, self).__init__(gui, master, o, attr, undo_stack)
    self.string_field.pack(expand = 1, fill = Tkinter.BOTH, side = Tkinter.LEFT)
    button = Tkinter.Button(self, text = editobj2.TRANSLATOR(self.button_text))
    button.bind("<ButtonRelease>", self.on_button)
    button.pack(expand = 0, fill = Tkinter.BOTH, side = Tkinter.RIGHT)
    
import tkFileDialog
class TkFilenameField(TkWithButtonStringField, FilenameField):
  def on_button(self, *args):
    filename = tkFileDialog.askopenfilename()
    if filename:
      self.string_field.set_value(filename)
      self.string_field.update()
    
class TkDirnameField(TkWithButtonStringField, DirnameField):
  def on_button(self, *args):
    folder = tkFileDialog.askdirectory()
    if folder:
      self.string_field.set_value(folder)
      self.string_field.update()
    
class TkURLField(TkWithButtonStringField, URLField):
  def on_button(self, *args):
    import webbrowser
    webbrowser.open_new(self.get_value())


class TkBoolField(BoolField, Tkinter.Checkbutton):
  def __init__(self, gui, master, o, attr, undo_stack):
    self.bool = Tkinter.BooleanVar()
    Tkinter.Checkbutton.__init__(self, master, variable = self.bool, command = self.validate)
    super(TkBoolField, self).__init__(gui, master, o, attr, undo_stack)
    self.update()
    
  def validate(self, *event):
    v = self.descr.get(self.o, self.attr)
    if isinstance(v, int):
      self.set_value(int(self.bool.get()))
    else:
      self.set_value(bool(self.bool.get()))
    
  def update(self):
    self.updating = 1
    try:
      v = self.descr.get(self.o, self.attr)
      if v is introsp.NonConsistent: v = 0
      self.bool.set(v)
    finally: self.updating = 0


class TkProgressBarField(TkField, ProgressBarField, Tkinter.Label):
  def __init__(self, gui, master, o, attr, undo_stack):
    Tkinter.Label.__init__(self, master)
    super(TkProgressBarField, self).__init__(gui, master, o, attr, undo_stack)
    self.update()
    
  def update(self):
    self.updating = 1
    try:
      v = self.get_value()
      if v is introsp.NonConsistent: self["text"] = "???"
      else:                          self["text"] = "%s%%" % int(100 * v)
    finally: self.updating = 0
    

class TkTextField(TkField, TextField, Tkinter.Frame):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(TkTextField, self).__init__(gui, master, o, attr, undo_stack)
    Tkinter.Frame.__init__(self, master)
    
    self.columnconfigure(0, weight = 1)

    v = self.get_value()
    height = min(15, max(5, v.count("\n") + 1, len(v) // 75))
    self.text = Tkinter.Text(self, width = 25, height = height, wrap = "word", font = "Helvetica -12", background = "white")
    self.text.bind("<FocusOut>", self.validate)
    self.text.grid(sticky = "nsew")
    self.update()
    
    bar = Tkinter.Scrollbar(self, orient = Tkinter.VERTICAL)
    bar.grid(row = 0, column = 1, sticky = "nsew")
    bar['command'] = self.text.yview
    self.text['yscrollcommand'] = bar.set
    
  def validate(self, event = None):
    s = self.text.get("0.0", "end")
    if s[-1] == "\n": s = s[0:-1]
    self.set_value(s)
    
  def update(self):
    self.updating = 1
    try:
      self.old_str = self.get_value()
      self.text.delete("0.0", "end")
      self.text.insert("end", self.old_str)
    finally: self.updating = 0

class TkObjectAttributeField(TkField, ObjectAttributeField, Tkinter.Frame):
  def __init__(self, gui, master, o, attr, undo_stack):
    Tkinter.Frame.__init__(self, master)
    super(TkObjectAttributeField, self).__init__(gui, master, o, attr, undo_stack)
    self.attribute_pane.pack(expand = 1, fill = Tkinter.BOTH)
    self.attribute_pane["relief"] = "sunken"
    self.attribute_pane["borderwidth"] = 1
    
class Tk_RangeField(TkField, _RangeField, Tkinter.Scale):
  def __init__(self, gui, master, o, attr, undo_stack, min, max, incr = 1):
    Tkinter.Scale.__init__(self, master, orient = Tkinter.HORIZONTAL, from_ = min, to = max)
    super(Tk_RangeField, self).__init__(gui, master, o, attr, undo_stack, min, max, incr)
    self.bind("<ButtonRelease>", self.validate)
    
  def validate(self, *args): self.set_value(self.get())
    
  def update(self):
    self.updating = 1
    try:
      self.set(self.get_value())
    finally: self.updating = 0
    
class Tk_ShortEnumField(TkField, _ShortEnumField, Tkinter.OptionMenu):
  def __init__(self, gui, master, o, attr, undo_stack, choices, value_2_enum = None, enum_2_value = None):
    super(Tk_ShortEnumField, self).__init__(gui, master, o, attr, undo_stack, choices, value_2_enum, enum_2_value)
    self.choice = Tkinter.StringVar()
    Tkinter.OptionMenu.__init__(self, master, self.choice, command = self.validate, *self.choice_keys)
    self.update()
    
  def validate(self, choice): self.set_value(self.choices[choice])
    
  def update(self):
    self.updating = 1
    try:
      i = self.choice_2_index.get(self.get_value())
      if not i is None: self.choice.set(self.choice_keys[i])
      else:             self.choice.set("")
    finally: self.updating = 0
    
class Tk_LongEnumField(TkField, _LongEnumField, Tkinter.Frame):
  def __init__(self, gui, master, o, attr, undo_stack, choices, value_2_enum = None, enum_2_value = None):
    Tkinter.Frame.__init__(self, master)
    super(Tk_LongEnumField, self).__init__(gui, master, o, attr, undo_stack, choices, value_2_enum, enum_2_value)
    self.columnconfigure(0, weight = 1)
    self.listbox = Tkinter.Listbox(self, exportselection = 0, background = "white")
    i = 0
    for choice in self.choice_keys:
      self.listbox.insert(i, choice)
      i = i + 1
    self.listbox.grid(sticky = "nsew")
    
    bar = Tkinter.Scrollbar(self, orient = Tkinter.VERTICAL)
    bar.grid(row = 0, column = 1, sticky = "nsew")
    bar["command"] = self.listbox.yview
    self.listbox["yscrollcommand"] = bar.set
    self.listbox.bind("<ButtonRelease>", self.validate)
    self.listbox["selectmode"] = "singledzd"
    self.update()
    
  def validate(self, choice):
    i = int(self.listbox.curselection()[0])
    self.set_value(self.choices[self.choice_keys[i]])
    
  def update(self):
    self.updating = 1
    try:
      self.listbox.selection_clear(0, 1000000)
      i = self.choice_2_index.get(self.get_value())
      if not i is None:
        self.listbox.activate(i)
        self.listbox.selection_set(i)
        self.listbox.see(i)
    finally: self.updating = 0

# EditObj
# Copyright (C) 2001-2002 Jean-Baptiste LAMY -- jiba@tuxfamily
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

import sys, types, copy, bisect, Tkinter, editobj, editobj.custom as custom
from custom import encode, unicodify

from Tkinter import *
from UserList import UserList
from UserDict import UserDict
import string, os, os.path
import cPickle as pickle

class Editor:
  require_right_menu = 1
  expand_right       = 0
  
  def __init__(self, master, obj, attr):
    self.obj  = obj
    self.attr = attr
    
  def get_value(self): return getattr(self.obj, self.attr)
  
  def set_value(self, value):
    old_value = getattr(self.obj, self.attr, None)
    
    def do_it():
      if hasattr(self.obj, "set_" + self.attr): # implicit setter
        getattr(self.obj, "set_" + self.attr)(value)
      else: setattr(self.obj, self.attr, value)
      
      if self.master.cancel: self.master.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      if hasattr(self.obj, "set_" + self.attr): # implicit setter
        getattr(self.obj, "set_" + self.attr)(old_value)
      else: setattr(self.obj, self.attr, old_value)
      
      if self.master.cancel: self.master.cancel.add_redo(do_it)
      
    do_it()
    
  def update(self): pass
  

class BoolEditor(Editor, Tkinter.Checkbutton):
  require_right_menu = 0
  expand_right       = 0
  
  def __init__(self, master, obj, attr):
    Editor.__init__(self, master, obj, attr)
    
    self.value     = Tkinter.BooleanVar()
    self.old_val   = self.get_value()
    self.value.set(self.old_val)
    
    Tkinter.Checkbutton.__init__(self, master, variable = self.value, command = self.validate)
    
  def validate(self, event = None):
    self.old_val = value = self.value.get()
    self.set_value(value)
    
  def get_value(self):
    if getattr(self.obj, self.attr, 0): return 1
    return 0
  
  def set_value(self, value):
    if value: Editor.set_value(self, 1)
    else:     Editor.set_value(self, 0)
    
  def update(self):
    self.old_val = self.get_value()
    self.value.set(self.old_val)
    
    
class EntryEditor(Editor, Tkinter.Entry):
  def __init__(self, master, obj, attr):
    Editor.__init__(self, master, obj, attr)
    
    self.unicode   = 0 # Will be overriden by subclasses' get_value()
    self.value     = Tkinter.StringVar()
    self.old_value = self.get_value()
    
    if self.unicode: self.value.set(self.old_value.encode("latin")) # Entry doesn't support Unicode ???
    else:            self.value.set(self.old_value)
    
    Tkinter.Entry.__init__(self, master, width = 25, textvariable = self.value, selectbackground = "#CCCCFF")
    self.bind("<FocusOut>"       , self.focus_out)
    self.bind("<KeyPress-Return>", self.validate)
    
  def focus_out(self, event = None):
    value = self.value.get()
    
    if self.unicode: value = unicodify(value)
    else:            value = encode   (value)
    
    if value != self.old_value: self.validate()
    
  def validate(self, event = None):
    value = self.value.get()
    if self.unicode: value = unicodify(value)
    else:            value = encode   (value)
    self.old_value = value
    self.set_value(value)
    
  def get_value(self):
    if hasattr(self.obj, self.attr): return repr(getattr(self.obj, self.attr, ""))
    else: return ""
    
  def set_value(self, value):
    if value and (value[0] != "<"):
      try: value = editobj.eval(value)
      except: sys.excepthook(*sys.exc_info())
      
      Editor.set_value(self, value)
      
  def update(self):
    self.old_value = self.get_value()
    if self.unicode: self.value.set(self.old_value.encode("latin")) # Entry doesn't support Unicode ???
    else:            self.value.set(self.old_value)
    
class StringEditor(EntryEditor):
  def get_value(self):
    value = getattr(self.obj, self.attr, "")
    self.unicode = isinstance(value, unicode)
    return value
  
  def set_value(self, value): Editor.set_value(self, value)
  
class IntEditor(EntryEditor):
  require_right_menu = 0
  
  def get_value(self): return str(getattr(self.obj, self.attr, ""))
  
  def set_value(self, value): Editor.set_value(self, int(editobj.eval(value)))
  
class FloatEditor(EntryEditor):
  require_right_menu = 0
  
  def get_value(self): return str(getattr(self.obj, self.attr, ""))
  
  def set_value(self, value): Editor.set_value(self, float(editobj.eval(value)))
  
  
class TextEditor(Editor, Tkinter.Frame):
  """A muti-line text editor."""
  def __init__(self, master, obj, attr):
    Editor.__init__(self, master, obj, attr)
    Tkinter.Frame.__init__(self, master)
    
    self.columnconfigure(0, weight = 1)
    
    value = self.old_value = getattr(obj, attr, "")
    self.unicode = value.__class__ is unicode
    
    self.text = Tkinter.Text(self, width = 25, height = 5, wrap = "word", font = "Helvetica -12", selectbackground = "#CCCCFF")
    self.text.insert("end", value)
    self.text.bind("<FocusOut>", self.validate)
    self.text.grid(sticky = "nsew")
    
    bar = Tkinter.Scrollbar(self, orient = VERTICAL)
    bar.grid(row = 0, column = 1, sticky = "nsew")
    bar['command'] = self.text.yview
    self.text['yscrollcommand'] = bar.set
    
    self.text.focus_out = self.validate
    
  def validate(self, event = None):
    value = self.text.get("0.0", "end")
    if value[-1] == "\n": value = value[0:-1]
    if self.unicode: value = unicodify(value)
    else:            value = encode   (value)
    self.set_value(value)
  
  def get_value(self): return getattr(self.obj, self.attr, "")
  
  def update(self):
    try: self.old_value = self.get_value()
    except AttributeError: return 1 # Not readable => do not update !
    self.text.delete("0.0", "end")
    self.text.insert("end", self.old_value)
    
def RangeEditor(min, max):
  """A slider-based editor."""
  class _RangeEditor(Editor, Tkinter.Scale):
    def __init__(self, master, obj, attr):
      Editor.__init__(self, master, obj, attr)
      Tkinter.Scale.__init__(self, master, orient = Tkinter.HORIZONTAL, from_ = min, to = max)
      self.bind("<ButtonRelease>", self.validate)
      self.update()
      
    def validate(self, event): self.set_value(self.get())
      
    def get_value(self): return int(getattr(self.obj, self.attr, 0))
    
    def update(self):
      try: self.set(getattr(self.obj, self.attr))
      except AttributeError: pass # Not readable => do not update !
      
  return _RangeEditor

class _ListEditor(Editor, Tkinter.OptionMenu):
  require_right_menu = 0
  expand_right       = 1
  _LIST = "(...)"
  def __init__(self, master, obj, attr, choices):
    Editor.__init__(self, master, obj, attr)
    
    self.choices = choices
    
    self.value = Tkinter.StringVar()
    self.value.set(self.get_value())
    
    Tkinter.OptionMenu.__init__(self, master, self.value, command = self.validate, *choices)
    
  def validate(self, value): self.set_value(value)
    
  def update(self): self.value.set(self.get_value())
  
class _LongListEditor(Editor, Tkinter.Frame):
  require_right_menu = 0
  expand_right       = 1
  
  def __init__(self, master, obj, attr, choices):
    Editor.__init__(self, master, obj, attr)
    Tkinter.Frame.__init__(self, master)
    
    self.choices = choices
    
    self.columnconfigure(0, weight = 1)
    self.listbox = Tkinter.Listbox(self, exportselection = 0, selectbackground = "#CCCCFF")
    i = 0
    for choice in choices:
      self.listbox.insert(i, choice)
      i = i + 1
    self.listbox.grid(sticky = "nsew")
    
    bar = Tkinter.Scrollbar(self, orient = VERTICAL)
    bar.grid(row = 0, column = 1, sticky = "nsew")
    bar['command'] = self.listbox.yview
    self.listbox['yscrollcommand'] = bar.set
    self.listbox.bind("<ButtonRelease>", self.validate)
    
    self.update()
    
  def validate(self, event = None):
    self.set_value(self.choices[int(self.listbox.curselection()[0])])
    
  def update(self):
    i     = 0
    value = self.get_value()
    while i < len(self.choices):
      if self.choices[i] == value:
        self.listbox.activate(i)
        self.listbox.selection_set(i)
        self.listbox.see(i)
        break
      i = i + 1
  
def ListEditor(values):
  """Create and return a new option-menu like Editor class. The values available are given by VALUES."""
  str2values = {}
  for value in values:
    try:    val = unicode(value)
    except: val = str(value)
    str2values[val] = value
  
  if len(values) < 30: super = _ListEditor
  else:                super = _LongListEditor
  
  class ListEditor(super):
    def __init__(self, master, obj, attr):
      values_str = str2values.keys()
      values_str.sort()
      super.__init__(self, master, obj, attr, values_str)
      
    def get_value(self):
      try:    return unicode(getattr(self.obj, self.attr))
      except: return str    (getattr(self.obj, self.attr))
      
    def set_value(self, value):
      try: value = str2values[value]
      except KeyError:
        for val in values:
          text = str(val)
          if text == value:
            str2values[text] = val
            value = val
            break
            
      Editor.set_value(self, value)
      
  return ListEditor

def EnumEditor(values):
  """Create and return a new option-menu like Editor class. The values available are given by VALUES, which is intented to be a dictionary mapping values to their string representations (e.g. { 0 : "disabled", 1 : "enabled" })."""
  items = values.items()
  items.sort()
  values_str = zip(*items)[1]
  
  if len(values) < 30: super = _ListEditor
  else:                super = _LongListEditor
  
  class ListEditor(super):
    def __init__(self, master, obj, attr):
      super.__init__(self, master, obj, attr, values_str)
      
    def get_value(self): return values.get(getattr(self.obj, self.attr), "")
    
    def set_value(self, value):
      for key, val in values.items():
        if val == value:
          Editor.set_value(self, key)
          break
        
  return ListEditor

def LambdaListEditor(lambd, value_tansformer = None):
  """Create and return a new option-menu like Editor class. The values available are the return values of LAMBD (which must be callable with one arg, the object edited), eventually transformed by VALUE_TRANSFORMER (which should be a callable with one arg)."""
  class ListEditor(_ListEditor):
    _LIST = "(...)"
    def __init__(self, master, obj, attr):
      _ListEditor.__init__(self, master, obj, attr, (getattr(obj, attr, ""),))

      self.values = None
      self.bind("<ButtonPress>", self.on_list)

    def on_list(self, event = None):
      if self.values: return

      self.values = lambd(self.obj)
      self.str2value = {}

      menu     = self["menu"]
      variable = self.value
      callback = self.validate
      
      menu.delete(0)
      if len(self.values) > 16: menu.add_command(label = self._LIST, command = self.on_listall)
      for value in self.values:
        text = str(value)
        self.str2value[text] = value
        menu.add_command(label = text, command = Tkinter._setit(variable, text, callback))
        
    def on_listall(self, *args): # Usefull if there is too many element in the list.
      t = Toplevel()
      l = Listbox(t)
      l.pack(expand = 1, fill = "both", side = "left")
      for value in self.values:
        text = str(value)
        self.str2value[text] = value
        l.insert("end", text)
        
      b = Scrollbar(t, orient = Tkinter.VERTICAL, command = l.yview)
      b.pack(side = "right", fill = "y")
      l["yscrollcommand"] = b.set
      l.bind("<ButtonRelease-1>", lambda event: self.set_value(l.get(l.curselection()[0])))
      
    def get_value(self): return str(getattr(self.obj, self.attr))
    
    def set_value(self, value):
      value = self.str2value[value]
      if value_tansformer: value = value_tansformer(value)
      Editor.set_value(self, value)
      
  return ListEditor


class EditButtonEditor(Editor, Tkinter.Button, object):
  """Edits an object as a button; when the button is clicked, the object is edited in a new window."""
  require_right_menu = 0
  expand_right       = 0
  
  def __init__(self, master, obj, attr):
    Editor.__init__(self, master, obj, attr)
    text = self.get_value()
    if not isinstance(text, basestring):
      text = unicode(text)
    Tkinter.Button.__init__(self, master, text = text, command = self.button_click)
    
  def button_click(self): editobj.edit(self.get_value(), dialog = 1)
    
  def update(self): self["text"] = str(self.get_value())
  
  
class WithButtonEditor(Editor, Tkinter.Frame, object):
  require_right_menu = 0
  expand_right       = 1
  
  def __init__(self, master, obj, attr, internal_editor_class, button_text):
    Editor.__init__(self, master, obj, attr)
    Tkinter.Frame.__init__(self, master)
    self.columnconfigure(0, weight = 1)
    
    self.internal_editor = internal_editor_class(self, obj, attr)
    self.internal_editor.grid(row = 0, column = 0, sticky = "NSEW")
    
    self.button = Tkinter.Button(self, text = button_text, command = self.button_click)
    self.button.grid(row = 0, column = 1)
    
  def button_click(self): pass
  
  def get_value(self): return self.internal_editor.get_value()
  def set_value(self, value): self.internal_editor.set_value(value)
  def update(self): self.internal_editor.update()
  
  def get_cancel(self): return self.master.cancel
  cancel = property(get_cancel)
  
class FilenameEditor(WithButtonEditor):
  def __init__(self, master, obj, attr):
    WithButtonEditor.__init__(self, master, obj, attr, StringEditor, "...")
    
  def button_click(self):
    import tkFileDialog
    s = tkFileDialog.askopenfilename()
    if s: self.set_value(s)
    
class DirnameEditor(WithButtonEditor):
  def __init__(self, master, obj, attr):
    WithButtonEditor.__init__(self, master, obj, attr, StringEditor, "...")
    
  def button_click(self):
    import tkFileDialog
    s = tkFileDialog.askdirectory()
    if s: self.set_value(s)
    
class MethodEditor(Editor, Tkinter.Frame):
  require_right_menu = 0
  expand_right       = 1
  
  def __init__(self, master, obj, attr, args_editor_class):
    Editor.__init__(self, master, obj, attr)
    Tkinter.Frame.__init__(self, master)
    
    self.args_editor_class = args_editor_class
    i = 0
    for arg_editor_class in args_editor_class:
      self.columnconfigure(i, weight = 1)

      if   arg_editor_class is FloatEditor:  setattr(self, "_arg_%s" % i, 0.0)
      elif arg_editor_class is IntEditor:    setattr(self, "_arg_%s" % i, 0)
      elif arg_editor_class is BoolEditor:   setattr(self, "_arg_%s" % i, 0)
      elif arg_editor_class is StringEditor: setattr(self, "_arg_%s" % i, "")
      elif arg_editor_class is TextEditor:   setattr(self, "_arg_%s" % i, "")
      else:                                  setattr(self, "_arg_%s" % i, None)
      
      arg_editor = arg_editor_class(self, self, "_arg_%s" % i)
      arg_editor.grid(row = 0, column = i, sticky = "NSEW")
      
      i += 1
      
    if args_editor_class:
      self.button = Tkinter.Button(self, text = custom.TRANSLATOR("Do"), command = self.button_click)
      self.button.grid(row = 0, column = i)
    else:
      self.columnconfigure(i, weight = 1)
      self.button = Tkinter.Button(self, text = custom.TRANSLATOR((callable(attr) and attr.__name__) or attr), command = self.button_click)
      self.button.grid(row = 0, column = i, sticky = "NSEW")
    
  def button_click(self):
    focused = self.focus_lastfor()
    if hasattr(focused, "focus_out"): focused.focus_out()
    if callable(self.attr): method = self.attr
    else:                   method = getattr(self.obj.__class__, self.attr)
    method(self.obj, *map(lambda i: getattr(self, "_arg_%s" % i), range(len(self.args_editor_class))))
    
  def get_value(self): return None
  def set_value(self, value): pass
  def update(self): pass
  
  def get_cancel(self): return self.master.cancel
  cancel = property(get_cancel)
  
  
class SubEditor(Editor, Tkinter.Frame, object):
  """An editor that edits its values in an inner property frame."""
  def __init__(self, master, obj, attr):
    Editor.__init__(self, master, obj, attr)
    
    Tkinter.Frame.__init__(self, master)
    self.columnconfigure(0, weight = 1)
    
    import main
    self.propframe = main.EditPropertyFrame(self)
    self.propframe.edit(self.get_value())
    self.propframe.pack()
    
  def get_cancel(self): return self.master.cancel
  cancel = property(get_cancel)


class TypeEditor(Tkinter.OptionMenu):
  def __init__(self, master, obj, attr):
    self.obj           = obj
    self.attr          = attr
    self.value         = Tkinter.StringVar()
    
    choices = custom._find_values(attr)
    apply(Tkinter.OptionMenu.__init__, [self, master, self.value, ""] + choices + ["(edit...)", "(set in clipboard)", "(paste clipboard)", "(deepcopy clipboard)"], {"command" : self.validate})
    
  def validate(self, event = None):
    import editobj
    
    value = self.value.get()
    self.value.set("")
    
    if   value == "(edit...)":            editobj.edit(getattr(self.obj, self.attr))
    elif value == "(set in clipboard)":   editobj.clipboard = getattr(self.obj, self.attr)
    elif value == "(paste clipboard)":    setattr(self.obj, self.attr, editobj.clipboard); self.master.fields[self.attr].update()
    elif value == "(deepcopy clipboard)": setattr(self.obj, self.attr, copy.deepcopy(editobj.clipboard)); self.master.fields[self.attr].update()
    else:                                 self.master.fields[self.attr].set_value(value)


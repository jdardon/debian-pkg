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

from Tkinter import *
from editobj import *
from editobj.observe import *

import os, sys, types, editobj, editobj.editor as editor, editobj.custom as custom, editobj.treewidget as treewidget

class EditWindow(Toplevel):
  def __init__(self, o = None, show_right_menu = 1, dialog = 0, command = None, preamble = None, cancel = None, grab = 0):
    # Get, or create if needed, the root Tk.
    try:
      from Tkinter import _default_root
      tkroot = _default_root
    except ImportError: pass
    if not tkroot:
      tkroot = Tk(className = 'EditObj')
      tkroot.withdraw()
      
    import editobj.observe
    if not editobj.observe.SCANNING: start_observing_tk()
    
    self.history = []
    self.dialog  = dialog
    
    if not cancel:
      from cancel import Context
      cancel = Context()
      
    if grab and cancel: cancel.push()
    self.cancel = cancel
    
    if not dialog:
      menubar = Menu(tkroot)
      self.picklemenu = picklemenu = Menu(menubar)
      picklemenu.add_command(label = 'Load...'   , command = self.pickle_load)
      picklemenu.add_command(label = 'Save'      , command = self.pickle_save)
      picklemenu.add_command(label = 'Save as...', command = self.pickle_save_as)
      menubar.add_cascade(label='Pickle', menu = picklemenu)
      
      self.copymenu = copymenu = Menu(menubar)
      copymenu.add_command(label = 'Copy...'     , command = self.copy_copy)
      copymenu.add_command(label = 'Deep copy...', command = self.copy_deepcopy)
      menubar.add_cascade(label='Copy', menu = copymenu)
      
      self.editmenu = editmenu = Menu(menubar)
      if self.cancel:
        editmenu.add_command(label = 'Undo'                 , command = self.edit_undo)
        editmenu.add_command(label = 'Redo'                 , command = self.edit_redo)
        editmenu.add_separator()
      editmenu.add_command(label = 'New hierarchy view...', command = self.edit_newview)
      editmenu.add_command(label = 'New property view...' , command = self.edit_newpropview)
      editmenu.add_command(label = 'Back'                 , command = self.edit_back)
      editmenu.add_command(label = 'Console...'           , command = self.display_console)
      menubar.add_cascade(label='Edit', menu = editmenu)
    else:
      menubar = None
      
    self.filename = None
    
    Toplevel.__init__(self, tkroot, menu = menubar)
    self.bind("<Destroy>", self.__del)
    
    self.withdraw()
    
    if preamble:
      t = Text(self, width = 0, height = 10, wrap = "word", highlightthickness = 0, font = "Helvetica -12", selectbackground = "#CCCCFF")
      t.pack(fill = BOTH, side = TOP)
      t.insert("end", preamble)
      
    if dialog:
      def _command(event = None):
        # Focus the OK button so as the currently active editor will be unfocused (as some editors validate themselves when they are unfocused).
        ok.focus_set()
        self.update() # Ensure the Tk unfocus event will be sent
        self.destroy()
        if command:
          def do_it():
            command()
            if cancel: cancel.add_post_cancel(cancel_it) # Do it AFTER the other cancellable operation !!!
            
          def cancel_it():
            command()
            if cancel: cancel.add_post_redo(do_it)
            
          do_it()
          
        if grab and cancel: cancel.pop()
        
      ok = Button(self, text = "OK", command = _command)
      ok.pack(expand = 0, fill = X, side = BOTTOM)
      self.wm_protocol("WM_DELETE_WINDOW", _command)
      
    self.scrollpane = treewidget.ScrollPane(self, 0, 1)
    self.scrollpane.pack(expand = 1, fill = BOTH, side = BOTTOM)
    self.propframe = EditPropertyFrame(self, show_right_menu, self.cancel, bd = 0)
    self.propframe.edit = self.edit
    self.scrollpane.setContent(self.propframe)
    
    self.edited          = None
    self.hierarchy       = None
    self.hierarchyedited = None
    self.buttonsframe    = None
    self.console         = None
    self.edit(o)
    
    if dialog: ok.tkraise()
    
    self.deiconify()
    if grab: self.grab_set()
    
  def createButtonsFrame(self):
    self.buttonsframe = Frame(self, borderwidth = 2, relief = "raised")
    self.buttonsframe.pack(expand = 0, fill = BOTH, side = TOP)
    self.buttonsframe.columnconfigure(5, weight = 1)
    self.addbutton = Button(self.buttonsframe, padx = 5, text = custom.TRANSLATOR("Add..."), command = self.button_add, relief = "flat")
    self.addbutton.grid(row = 0, column = 0, sticky = E + W)
    self.removebutton = Button(self.buttonsframe, padx = 5, text = custom.TRANSLATOR("Remove"), command = self.button_remove, relief = "flat")
    self.removebutton.grid(row = 0, column = 1, sticky = E + W)
    self.upbutton = Button(self.buttonsframe, padx = 5, text = custom.TRANSLATOR("Up"), command = self.button_up, relief = "flat")
    self.upbutton.grid(row = 0, column = 2, sticky = E + W)
    self.downbutton = Button(self.buttonsframe, padx = 5, text = custom.TRANSLATOR("Down"), command = self.button_down, relief = "flat")
    self.downbutton.grid(row = 0, column = 3, sticky = E + W)
    if self.propframe.show_right_menu:
      self.clipbutton = Button(self.buttonsframe, padx = 5, text = custom.TRANSLATOR("Copy"), command = self.button_clip, relief = "flat")
      self.clipbutton.grid(row = 0, column = 4, sticky = E + W)
      
  #def __del__(self):
  #  print "__del__ de", self
    
  def __del(self, event):
    if (type(event.widget) is StringType and event.widget[1:] == self.winfo_name()) or event.widget == self:
      if not self.dialog:
        self.picklemenu.destroy()
        self.copymenu  .destroy()
        self.editmenu  .destroy()
        
      self.unsetevent()
      
  def setevent  (self): pass
  def unsetevent(self): pass
  
  def edit(self, o, newview = 0, reedition = 0):
    if newview: edit(o)
    else:
      locked = self.winfo_ismapped()
      if locked: self.pack_propagate(0)
      
      o = editobj.editable(o)
      
      self.history.append(o)
      self.edited = o
      if hasattr(o, "filename"): self.filename = o.filename
      EditPropertyFrame.edit(self.propframe, o, reedition)
      self.scrollpane.updateContentSize()
      
      if self.console: self.console.dict["obj"] = o
      
      # If the new edited object is in the same hierarchy than the former, keep the same hierarchy. Else, create one.
      if (self.hierarchyedited is None) or not ((self.hierarchyedited is o) or editobj.in_hierarchy(o, self.hierarchyedited)):
        children = custom._find_children(o)
        if not children is None:
          self.unsetevent()
          self.hierarchyedited = self.edited
          self.setevent()
          if self.hierarchy is None:
            self.createButtonsFrame()
            self.hierarchy = treewidget.Tree(self)
            self.hierarchy.pack(expand = 1, fill = BOTH)
          ItemNode(self.hierarchy, o, editor = self.edit)
        else:
          if not self.hierarchyedited is None:
            self.hierarchy.destroy()
            self.unsetevent()
            self.hierarchy = None
            self.hierarchyedited = None
            self.buttonsframe.destroy()
            self.buttonsframe = None
          
      if locked: self.pack_propagate(1)
      
  def button_add(self):
    if self.hierarchy.selection: o = self.hierarchy.selection[0]
    else:                        o = self.hierarchy.node
    
    items, insert, del_ = custom._find_children_insert_remove(o.item)
    while items is None:
      o = o.parent
      items, insert, del_ = custom._find_children_insert_remove(o.item)
      
    def add_this(key, item):
      def do_it():
        try:              insert(key, item)
        except TypeError: insert(item)
        if self.cancel: self.cancel.add_cancel(cancel_it)
        
      def cancel_it():
        del_(key)
        if self.cancel: self.cancel.add_redo(do_it)
        
      do_it()
      
    choices = custom._find_available_children(o.item)
    if isinstance(choices, list):
      if isinstance(items, list): AddDialog(o.item, choices, len(items), add_this)
      else:                       AddDialog(o.item, choices, ""        , add_this)
    elif choices:
      try: choice = editobj.eval(choices, locals = {"parent" : o.item})
      except NotImplementedError: return
      add_this(len(items), choice)
      
  def button_remove(self):
    if not self.hierarchy.selection: return
    o = self.hierarchy.selection[0]
    items, insert, del_ = custom._find_children_insert_remove(o.itemparent)
    key = o.key
    item = o.item
    
    def do_it():
      del_(key)
      if self.cancel: self.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      try:              insert(key, item)
      except TypeError: insert(item)
      if self.cancel: self.cancel.add_redo(do_it)
      
    do_it()
    
  def button_up(self):
    if not self.hierarchy.selection: return
    o = self.hierarchy.selection[0]
    items = custom._find_children(o.itemparent)
    if not isinstance(items, list): return
    i = o.key
    
    def do_it():
      items[i - 1], items[i] = items[i], items[i - 1]
      if self.cancel: self.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      items[i - 1], items[i] = items[i], items[i - 1]
      if self.cancel: self.cancel.add_redo(do_it)
      
    do_it()
    
  def button_down(self):
    if not self.hierarchy.selection: return
    o = self.hierarchy.selection[0]
    items = custom._find_children(o.itemparent)
    if not isinstance(items, list): return
    i = o.key
    
    def do_it():
      if i + 1 == len(items): items[0    ], items[i] = items[i], items[0]
      else:                   items[i + 1], items[i] = items[i], items[i + 1]
      if self.cancel: self.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      if i + 1 == len(items): items[0    ], items[i] = items[i], items[0]
      else:                   items[i + 1], items[i] = items[i], items[i + 1]
      if self.cancel: self.cancel.add_redo(do_it)
      
    do_it()
    
  def button_clip(self): editobj.clipboard = self.hierarchy.selection[0].item
    
  def pickle_save(self):
    obj = self.hierarchyedited or self.edited
    if hasattr(obj, "save"):
      try:
        obj.save()
        return
      except TypeError: sys.excepthook(*sys.exc_info())
    if self.filename:
      import cPickle as pickle
      pickle.dump(obj, open(self.filename, "w"))
    else: self.pickle_save_as()
  def pickle_save_as(self):
    obj = self.hierarchyedited or self.edited
    import cPickle as pickle, tkFileDialog
    self.filename = tkFileDialog.asksaveasfilename()
    if hasattr(obj, "save"):
      try:
        obj.save(self.filename)
        return
      except TypeError: pass
    pickle.dump(obj, open(self.filename, "w"))
  def pickle_load(self):
    import cPickle as pickle, tkFileDialog
    self.filename = tkFileDialog.askopenfilename()
    self.edit(pickle.load(open(self.filename, "r")))
    
  def copy_copy(self):
    import copy
    edit(copy.copy(self.edited))
  def copy_deepcopy(self):
    import copy
    edit(copy.deepcopy(self.edited))
    
  def edit_undo(self): self.cancel.cancel()
  def edit_redo(self): self.cancel.redo()
  def edit_newview(self):
    if self.hierarchyedited is None: self.edit_newpropview()
    else: edit(self.hierarchyedited)
  def edit_newpropview(self): edit(self.edited)
  def edit_back(self):
    if len(self.history) >= 2:
      self.history.pop()
      self.edit(self.history.pop())
  def display_console(self):
    if not self.console:
      import editobj.console
      dict = { "root" : self.hierarchyedited or self.edited, "obj" : self.edited }
      self.console = editobj.console.Console(self, dict = dict, globals = editobj.EVAL_ENV)
      
      self.console.text.insert("end", """\nYou can access the currently edited obj as "obj", and the root of the hierarchy as "root".\n""")
      self.console.text.insert("end", sys.ps1)
      self.console.text.configure(width = 10, height = 10)
      self.console.pack(fill = BOTH, expand = 1, side = BOTTOM)
    else:
      self.console.destroy()
      self.console = None
      
      
class EditPropertyFrame(Frame):
  def __init__(self, master, show_right_menu = 1, cancel = None, **opts):
    self.edited          = None
    self.show_right_menu = show_right_menu
    self.cancel          = cancel
    
    Frame.__init__(self, master, opts)
    self.columnconfigure(0, weight = 0)
    self.columnconfigure(1, weight = 1)
    self.columnconfigure(2, weight = 0)
    self.bind("<Destroy>", self.__del)
    
  def __del(self, event = None): self.unsetevent()
  
  def setevent  (self): observe  (self.edited, self.edited_changed)
  def unsetevent(self): unobserve(self.edited, self.edited_changed)
  
  def edit(self, o, reedition = 0):
    self.unsetevent()
    
    if not reedition: custom._call_on_edit(o, self.master)
    
    self.fields = {}
    
    # Unfocus the current widget -- avoid change in this widget to be lost !
    focused = self.focus_lastfor()
    if hasattr(focused, "focus_out"): focused.focus_out() # Hack !!! The "else" case should work with ANY editor widget, but it doesn't...?? In particular, it works with TextEditor, but not with StringEditor !
    else:
      try:
        focused.tk_focusNext().focus_set()
        focused.update() # Ensure the Tk unfocus event will be sent
      except: pass
      
    for widget in self.children.values(): widget.destroy()
    
    self.edited = o
    if not o is None:
      self.edited_attrs = editobj.attrs_of(o)
      attrs = map(lambda attr: (custom.TRANSLATOR(attr), attr), self.edited_attrs)
      attrs.sort()
      
      line = 1
      for (translation, attr) in attrs:
        fieldclass = custom._find_editor(o, attr)
        if fieldclass:
          label = Label(self, text = translation)
          label.grid(row = line, column = 0, sticky = "WNS")
          
          field = self.fields[attr] = fieldclass(self, o, attr)
          
          if self.show_right_menu and field.require_right_menu:
            field.grid(row = line, column = 1, sticky = "EWNS")
            
            change = editor.TypeEditor(self, o, attr)
            change.grid(row = line, column = 2, sticky = "EWNS")
          else:
            field.grid(row = line, column = 1, columnspan = 1 + field.expand_right, sticky = "EWNS")
            
          line += 1
          
      methods = custom._find_methods(o)
      methods = map(lambda (method, args_editor): (custom.TRANSLATOR((callable(method) and method.__name__) or method), method, args_editor), methods)
      methods.sort()
      for translation, method, args_editor in methods:
        label = Label(self, text = translation)
        label.grid(row = line, column = 0, sticky = "WNS")
        
        field = self.fields[method] = editor.MethodEditor(self, o, method, args_editor)
        field.grid(row = line, column = 1, columnspan = 1 + field.expand_right, sticky = "EWNS")
        
        line += 1
        
      self.setevent()
      
  def edited_changed(self, o, type, new_dict, old_dict):
    if type is object:
      for attr, new, old in diffdict(new_dict, old_dict):
        if ((old is None) and (not attr in self.edited_attrs)) or (not hasattr(o, attr)):
          self.edit(self.edited, reedition = 1) # A new attribute
          return
        
        field = self.fields.get(attr)
        if field: field.update()
        
  def update(self):
    for field in self.fields.values(): field.update()
    
    
class ItemNode(treewidget.Node):
  def __init__(self, parent, item, itemparent = None, editor = edit, key = None, show_key = 0):
    self.item          = item
    self.itemparent    = itemparent
    self.edit          = editor
    self.key           = key
    self.show_key      = show_key
    treewidget.Node.__init__(self, parent)
    self.setevent()
    
  def setevent  (self):
    items = custom._find_children(self.item)
    observe(self.item, self.content_changed)
    if (not items is None) and (not items is self.item): observe(items, self.content_changed)
    
  def unsetevent(self):
    items = custom._find_children(self.item)
    unobserve(self.item, self.content_changed)
    if (not items is None) and (not items is self.item): unobserve(items, self.content_changed)
    
  def destroy(self):
    treewidget.Node.destroy(self)
    self.unsetevent()
    
  def unseteventtree(self):
    self.unsetevent()
    for child in self.children: child.unseteventtree()
    
  def __unicode__(self):
    if (not self.show_key) or (self.key is None): return unicode(self.item)
    return unicode(self.key) + ": " + unicode(self.item)
  
  def createchildren(self, oldchildren = ()):
    children = []
    
    items = custom._find_children(self.item)
      
    if isinstance(items, list):
      i = 0
      for item in items:
        for oldchild in oldchildren: # Re-use the child if possible.
          if oldchild.item is item:
            oldchild.key = i # Index may have changed...
            oldchild.update() # ... so we need to update.
            children.append(oldchild)
            oldchildren.remove(oldchild) # Do not re-use it twice !
            break
        else: children.append(ItemNode(self, item, self.item, self.edit, i, 0))
        i += 1
      for child in oldchildren:
        child._undrawtree()
        child.unseteventtree()
        
    elif isinstance(items, dict):
      items = items.items()
      for child in oldchildren:
        for key, item in items:
          if item is child.item and key == child.key:
            children.append(child) # Re-use this one.
            items.remove((key, item)) # Do not re-use it twice !
            break
        else: # Delete this one.
          child._undrawtree()
          child.unseteventtree()
      for key, item in items: # The new ones are left.
        children.append(ItemNode(self, item, self.item, self.edit, key, 1))
        
    return children
  
  def iseditable(self): return 0
  def isexpandable(self): return custom._find_children(self.item) # Avoid calling it too often...
  def settext(self, text): pass

  def select(self, event = None):
    treewidget.Node.select(self)
    if type(self.item) in _WRAPPED_TYPE: # self.item is not an editable object ! => Wrap it !
      self.edit(StringOrNumberWrapper(self.key, self.item, self.itemparent, self))
    else: self.edit(self.item)
    
  def expand(self, event = None):
    treewidget.Node.expand(self, event)
    custom._call_on_children_visible(self.item, 1)
    
  def collapse(self, event = None):
    treewidget.Node.collapse(self, event)
    custom._call_on_children_visible(self.item, 0)
    
  def content_changed(self, o, type, new, old):
    self.update()
    self.updatechildren()
    

_WRAPPED_TYPE = (int, long, float, complex, str, unicode)

class StringOrNumberWrapper:
  def __init__(self, key, value, parent, itemnode):
    self._key      = key
    self.value     = value
    self._parent   = parent
    self._itemnode = itemnode
    
  def __setattr__(self, name, value):
    if name == "value" and hasattr(self, "_parent"):
      self._itemnode.item = value
      self._itemnode.update()
      items, insert, del_ = custom._find_children_insert_remove(self._parent)
      
      del_(self._key)
      try: insert(self._key, value)
      except TypeError: insert(value)
      
    self.__dict__[name] = value
    
  def __cmp__(self, other): return cmp(self.value, other)
  def __eq__ (self, other): return self.value == other
  def __hash__ (self): return object.__hash__(self)

class AddDialog(Toplevel):
  def __init__(self, add_into, choices, default_key, callback):
    self.add_into = add_into
    self.callback = callback
    
    choices = choices + [u"(paste clipboard)", u"(deepcopy clipboard)"]
    
    Toplevel.__init__(self)
    self.columnconfigure(0, weight = 1)
    self.columnconfigure(1, weight = 0)
    
    self.entryk = Entry(self)
    self.entryk.insert(0, repr(default_key))
    self.entryk.grid(row = 0, columnspan = 2, sticky = "EW")
    
    self.var = StringVar()
    self.entry = Entry(self, textvariable = self.var)
    self.entry.grid(row = 1, columnspan = 2, sticky = "EW")
    self.entry.focus_set()
    self.entry.bind("<KeyPress-Return>", self.validate)
    
    self.list = Listbox(self)
    if choices: apply(self.list.insert, [0] + choices)
    self.list.bind("<ButtonRelease-1>", self.list_selected)
    self.list.bind("<Double-1>", self.validate)
    self.list.grid(row = 2, column = 0, sticky = "NSEW")
    self.rowconfigure(2, weight = 1)
    
    self.bar = Scrollbar(self, orient = VERTICAL)
    self.bar.grid(row = 2, column = 1, sticky = "NSEW")
    
    self.list['yscrollcommand'] = self.bar.set
    self.bar['command'] = self.list.yview
    
    self.ok = Button(self, text = "OK", command = self.validate)
    self.ok.grid(row = 3, columnspan = 2, sticky = "EW")
    
  def list_selected(self, event = None): self.var.set(self.list.selection_get())
  
  def validate(self, event = None):
    self.choosen(self.var.get())
    self.destroy()
    
  def choosen(self, text):
    if   text == u"(paste clipboard)"   : added = editobj.clipboard
    elif text == u"(deepcopy clipboard)": added = copy.deepcopy(editobj.clipboard)
    else:                                 added = editobj.eval(text, locals = {"parent" : self.add_into})
    self.callback(editobj.eval(self.entryk.get(), locals = {"parent" : self.add_into}), added)


def list_or_dict_class_of(clazz):
  "Figure out what is the class that extends UserList or UserDict in the class inheritance tree..."
  
  # Guess that the the type of the item is associated with the class that inherit UserList/UserDict
  if (list in clazz.__bases__) or (dict in clazz.__bases__) or (UserList in clazz.__bases__) or (UserDict in clazz.__bases__):
    return clazz
  # Recursive
  for base in clazz.__bases__:
    answer = list_or_dict_class_of(base)
    if answer: return answer
    



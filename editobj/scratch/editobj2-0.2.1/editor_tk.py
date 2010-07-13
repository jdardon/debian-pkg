# -*- coding: utf-8 -*-

# editor_tk.py
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
from editobj2.editor import *
from editobj2 import treewidget
import Tkinter



class TkEditorDialog(EditorDialog, Tkinter.Toplevel):
  def __init__(self, gui, direction = "h", on_validate = None, edit_child_in_self = 1, undo_stack = None, on_close = None):
    try:
      from Tkinter import _default_root
      tkroot = _default_root
    except ImportError: pass
    if not tkroot:
      tkroot = Tkinter.Tk(className = 'EditObj2')
      tkroot.withdraw()
    
    Tkinter.Toplevel.__init__(self, tkroot)
    super(TkEditorDialog, self).__init__(gui, direction, on_validate, edit_child_in_self, undo_stack, on_close)
    self.rowconfigure(0, weight = 1)
    self.rowconfigure(1, weight = 0)
    self.columnconfigure(0, weight = 1)
    self.columnconfigure(1, weight = 1)
    self.editor_pane.grid(column = 0, columnspan = 3, row = 0, padx = 10, pady = 10, sticky = "EWNS")
    
    if on_validate:
      cancel = Tkinter.Button(self, text = editobj2.TRANSLATOR("Cancel"), command = self.on_cancel)
      ok     = Tkinter.Button(self, text = editobj2.TRANSLATOR("Ok"    ), command = self.on_ok)
      cancel.grid(column = 0, row = 1, sticky = "EWNS")
      ok    .grid(column = 1, row = 1, sticky = "EWNS")
    else:
      close = Tkinter.Button(self, text = editobj2.TRANSLATOR("Close"), command = self.on_close_dialog)
      close.grid(column = 1, row = 1, sticky = "EWNS")
    self.on_close = on_close
    
  def edit(self, o):
    EditorDialog.edit(self, o)
    label = self.editor_pane.hierarchy_pane.descr.label_for(o)
    self.wm_title(label.replace(u"\n", u" ").replace(u"\t", u" "))
    return self

  def wait_for_validation(self): return self
  
  def on_close_dialog(self):
    if self.on_close: self.on_close()
    self.destroy()
    
  def on_cancel(self):
    self.on_validate(None)
    self.destroy()
    
  def on_ok(self):
    self.on_validate(self.editor_pane.attribute_pane.o)
    self.destroy()
    
  def main(self):
    #import tkFileDialog; filename = tkFileDialog.asksaveasfilename()
    Tkinter.mainloop()

  def set_default_size(self, width, height):
    self.geometry("%sx%s" % (width, height))
    

class TkHEditorPane(HEditorPane, Tkinter.Frame):
  def __init__(self, gui, master, edit_child_in_self = 1, undo_stack = None):
    Tkinter.Frame.__init__(self, master)
    self.scroll_pane = treewidget.ScrollPane(self, 0, 1, max_height = 800)
    self.scroll_pane.grid(column = 2, row = 0, sticky = "EWNS", padx = 0, pady = 0)
    
    self.frame = Tkinter.Frame(self.scroll_pane)
    self.frame.columnconfigure(0, weight = 1)
    self.frame.rowconfigure   (0, weight = 0)
    self.frame.rowconfigure   (1, weight = 0)
    self.frame.rowconfigure   (2, weight = 1)
    
    self.scroll_pane.setContent(self.frame)
    
    self.columnconfigure(0, weight = 0)
    self.columnconfigure(1, weight = 1)
    self.columnconfigure(2, weight = 2)
    self.rowconfigure   (0, weight = 1)
    
    super(TkHEditorPane, self).__init__(gui, master, edit_child_in_self, undo_stack)
    self.icon_pane     .grid(column = 0, row = 0, sticky = "EWNS", padx = 10)
    f = Tkinter.Frame(self.frame)
    f["bg"] = "gray"
    f.grid(column = 0, row = 1, sticky = "EWNS", padx = 10, pady = 10)
    self.attribute_pane.grid(column = 0, row = 2, sticky = "EWNS", padx = 10)
    
    self.hierarchy_pane.grid(column = 0, row = 0, sticky = "EWNS", padx = 0, pady = 0)
    self.hierarchy_pane.hbar.grid_forget()
    self.hierarchy_pane["borderwidth"] = 1
    self.hierarchy_pane["relief"] = "sunken"
    
    self.childhood_pane.grid(column = 0, row = 0, sticky = "EWNS", padx = 0, pady = 0)
    
  def edit(self, o):
    HEditorPane.edit(self, o)
    self.scroll_pane.updateContentSize()
    
  def edit_child(self, o):
    HEditorPane.edit_child(self, o)
    self.scroll_pane.updateContentSize()
    
  def _set_hierarchy_visible(self, visible):
    if visible:
      self.hierarchy_pane.frame.grid(column = 1, row = 0, sticky = "EWNS", padx = 0, pady = 0)
      self.childhood_pane      .grid(column = 0, row = 0, sticky = "EWNS", padx = 0, pady = 0)
      self.columnconfigure(1, weight = 1)
    else:
      self.hierarchy_pane.frame.grid_forget()
      self.childhood_pane      .grid_forget()
      self.columnconfigure(1, weight = 0)
      

class TkVEditorPane(VEditorPane, Tkinter.Frame):
  def __init__(self, gui, master, edit_child_in_self = 1, undo_stack = None):
    Tkinter.Frame.__init__(self, master)
    self.scroll_pane = treewidget.ScrollPane(self, 0, 1, max_height = 800)
    self.scroll_pane.grid(column = 0, row = 1, sticky = "EWNS", padx = 0, pady = 0, columnspan = 2)
    
    self.frame = Tkinter.Frame(self.scroll_pane)
    self.frame.columnconfigure(0, weight = 1)
    self.frame.rowconfigure   (0, weight = 0)
    self.frame.rowconfigure   (1, weight = 0)
    self.frame.rowconfigure   (2, weight = 1)
    
    self.scroll_pane.setContent(self.frame)
    
    self.columnconfigure(0, weight = 0)
    self.columnconfigure(1, weight = 1)
    self.rowconfigure   (0, weight = 1)
    self.rowconfigure   (1, weight = 2)
    
    super(TkVEditorPane, self).__init__(gui, master, edit_child_in_self, undo_stack)
    self.icon_pane     .grid(column = 0, row = 0, sticky = "EWNS", padx = 10)
    f = Tkinter.Frame(self.frame)
    f["bg"] = "gray"
    f.grid(column = 0, row = 1, sticky = "EWNS", padx = 10, pady = 10)
    self.attribute_pane.grid(column = 0, row = 2, sticky = "EWNS", padx = 10)
    
    self.hierarchy_pane.frame.grid(column = 1, row = 0, sticky = "EWNS", padx = 0, pady = 0)
    self.hierarchy_pane.hbar.grid_forget()
    self.hierarchy_pane["borderwidth"] = 1
    self.hierarchy_pane["relief"] = "sunken"
    
    self.childhood_pane.grid(column = 0, row = 0, sticky = "EWNS", padx = 0, pady = 0)
    
  def edit(self, o):
    VEditorPane.edit(self, o)
    self.scroll_pane.updateContentSize()
    
  def edit_child(self, o):
    VEditorPane.edit_child(self, o)
    self.scroll_pane.updateContentSize()
    
  def _set_hierarchy_visible(self, visible):
    if visible:
      self.hierarchy_pane.frame.grid(column = 1, row = 0, sticky = "EWNS", padx = 0, pady = 0)
      self.childhood_pane      .grid(column = 0, row = 0, sticky = "EWNS", padx = 0, pady = 0)
    else:
      self.hierarchy_pane.frame.grid_forget()
      self.childhood_pane      .grid_forget()
      

class TkIconPane(IconPane, Tkinter.Frame):
  def __init__(self, gui, master, use_small_icon = 0, compact = 0, bold_label = 1):
    if isinstance(master, EditorPane):
      Tkinter.Frame.__init__(self, master.frame)
    else:
      Tkinter.Frame.__init__(self, master)
    super(TkIconPane, self).__init__(gui, master, use_small_icon, compact, bold_label)
    self.columnconfigure(0, weight = 0)
    self.columnconfigure(1, weight = 1)
    
    self.image = Tkinter.Label(self)
    self.image.grid(row = 0, column = 0, sticky = "N", padx  = 15, pady = 10, rowspan = 2)
    
    self.label = Tkinter.Label(self)
    self.label.grid(row = 0, column = 1, sticky = "WNS")
    self.label["font"] = "-size 16"
    
    self.text = Tkinter.Label(self, justify = "left", wraplength = 400)
    self.text.grid(row = 1, column = 1, sticky = "WNS")
    
  def _set_icon_filename_label_details(self, icon_filename, label, details):
    if icon_filename and isinstance(icon_filename, basestring):
      self._image = load_big_icon(icon_filename)
    else:
      self._image = None
    self.image["image"] = self._image
    self.label["text"] = label
    self.text ["text"] = details
    
    
class TkAttributePane(AttributePane, Tkinter.Frame):
  def __init__(self, gui, master, edit_child = None, undo_stack = None, **gui_opts):
    super(TkAttributePane, self).__init__(gui, master, edit_child, undo_stack, **gui_opts)
    
    if isinstance(master, EditorPane):
      Tkinter.Frame.__init__(self, master.frame, **gui_opts)
    else:
      Tkinter.Frame.__init__(self, master, **gui_opts)
    self.columnconfigure(0, weight = 0)
    self.columnconfigure(1, weight = 1)
    self.columnconfigure(2, weight = 0)
    self.bind("<Destroy>", self._destroyed)
    
  def __str__(self): return Tkinter.Frame.__str__(self)
  
  def _delete_all_fields(self):
    for widget in self.children.values(): widget.destroy()
    
  def _new_field(self, name, field, unit, i):
    self.rowconfigure(i, weight = 1)
    label = Tkinter.Label(self, text = name)
    label.grid(row = i, column = 0, sticky = "WNS")
    field.grid(row = i, column = 1, sticky = "EWNS")
    if unit:
      unit_label = Tkinter.Label(self, text = unit)
      unit_label.grid(row = i, column = 2, sticky = "WNS")

    
    

class TkChildhoodPane(ChildhoodPane, Tkinter.Frame):
  def __init__(self, gui, master, undo_stack = None):
    Tkinter.Frame.__init__(self, master)
    super(TkChildhoodPane, self).__init__(gui, master, undo_stack)
    
    self.columnconfigure(0, weight = 1)
    self.rowconfigure(0, weight = 1)
    self.rowconfigure(1, weight = 1)
    self.rowconfigure(2, weight = 1)
    self.rowconfigure(3, weight = 1)
    
    self.button_move_up   = Tkinter.Button(self, text = "^", relief = "flat", overrelief = "raised", command = self.on_move_up)
    self.button_add       = Tkinter.Button(self, text = "+", relief = "flat", overrelief = "raised", command = self.on_add)
    self.button_remove    = Tkinter.Button(self, text = "-", relief = "flat", overrelief = "raised", command = self.on_remove)
    self.button_move_down = Tkinter.Button(self, text = "v", relief = "flat", overrelief = "raised", command = self.on_move_down)
    
    self.button_move_up  .grid(column = 0, row = 0, sticky = "EWNS")
    self.button_add      .grid(column = 0, row = 1, sticky = "EWNS")
    self.button_remove   .grid(column = 0, row = 2, sticky = "EWNS")
    self.button_move_down.grid(column = 0, row = 3, sticky = "EWNS")
    
  def set_button_visibilities(self, visible1, visible2, visible3, visible4):
    self.button_move_up  .configure(state = ["disabled", "normal"][int(bool(visible1))])
    self.button_add      .configure(state = ["disabled", "normal"][int(bool(visible2))])
    self.button_remove   .configure(state = ["disabled", "normal"][int(bool(visible3))])
    self.button_move_down.configure(state = ["disabled", "normal"][int(bool(visible4))])
    

class Tk_HierarchyNode(HierarchyNode, treewidget.Node):
  icon_width = 26
  def geticon(self):
    icon_filename = self.descr.icon_filename_for(self.o)
    if icon_filename and isinstance(icon_filename, basestring): return load_small_icon(icon_filename)
    
  def __unicode__(self):
    s = self.descr.label_for(self.o)
    if not isinstance(s, unicode): s = s.decode("latin")
    return s.replace(u"\n", u" ")
  
  def createchildren(self, old_children = ()): return self.create_children(old_children)
  def update_children(self): self.updatechildren()
  
  def iseditable(self): return 0
  def isexpandable(self): return self.o_has_children
  def settext(self, text): pass
  
  def select(self, event = None):
    treewidget.Node.select(self)
    self.tree.edit_child(self.o)
    if self.tree.childhood_pane:
      if self.parent: parent = self.parent.o
      else:           parent = None
      self.tree.childhood_pane.edit(parent, self.o)
      
  def _drawtext(self, x, y):
    treewidget.Node._drawtext(self, x, y)
    self.label.bind("<3>"       , self.on_mouse_right_button)
    self.label.bind("<Control-1>"       , self.on_mouse_right_button)
    self.label.bind("<Double-1>", self.on_double_click)
    
  def on_mouse_right_button(self, event):
    self.select(event)
    
    if self.parent: parent = self.parent.o
    else:           parent = None
    actions = self.tree._get_actions(self.o, parent)
    
    menu = Tkinter.Menu(tearoff = 0)

    for action in actions:
      menu.add_command(label = action.label, command = lambda action = action: self.tree._action_activated(None, self.o, action, parent))
    menu.tk_popup(event.x_root, event.y_root)
    
  def on_double_click(self, event):
    if self.parent: parent = self.parent.o
    else:           parent = None
    actions = self.tree._get_actions(self.o, parent)
    for action in actions:
      if action.default:
        self.tree._action_activated(None, self.o, action, parent)
        
    
class TkHierarchyPane(HierarchyPane, treewidget.Tree):
  Node = Tk_HierarchyNode
  def __init__(self, gui, master, edit_child, undo_stack = None):
    super(TkHierarchyPane, self).__init__(gui, master, edit_child, undo_stack)
    
    treewidget.Tree.__init__(self, master)
    self.nodeheight  = 26
    self.tree = self

    


  
SMALL_ICON_SIZE = 26

_small_icons = {}
_big_icons   = {}

def load_big_icon(filename):
  image = _big_icons.get(filename)
  if not image:
    try: import PIL, PIL.Image, PIL.ImageTk
    except:
      image = _big_icons[filename] = Tkinter.PhotoImage(file = filename)
      return image
      return None
    pil_image = PIL.Image.open(filename)
    image = _big_icons[filename] = PIL.ImageTk.PhotoImage(image = pil_image)
    image.pil_image = pil_image
  return image

def load_small_icon(filename):
  image = _small_icons.get(filename)
  if not image:
    try: import PIL, PIL.Image, PIL.ImageTk
    except: return None
    image = load_big_icon(filename)
    w, h = image.pil_image.size
    if (w > SMALL_ICON_SIZE) or (h > SMALL_ICON_SIZE):
      if image.pil_image.mode == "RGBA":
        pil_image = PIL.Image.new("RGB", image.pil_image.size, (255, 255, 255))
        pil_image.paste(image.pil_image, image.pil_image.split()[3])
      else:
        pil_image = image.pil_image
      if w > h: pil_image = pil_image.resize((SMALL_ICON_SIZE, int(float(SMALL_ICON_SIZE) * h / w)), 1)
      else:     pil_image = pil_image.resize((int(float(SMALL_ICON_SIZE) * w / h), SMALL_ICON_SIZE), 1)
      image = _small_icons[filename] = PIL.ImageTk.PhotoImage(image = pil_image)
      image.pil_image = pil_image
  return image

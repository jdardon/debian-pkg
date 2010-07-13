# -*- coding: utf-8 -*-

# editor.py
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
import editobj2.introsp  as introsp
import editobj2.observe  as observe
import editobj2.undoredo as undoredo
import editobj2.field


class MultiGUIEditor(editobj2.field.MultiGUIWidget):
  _Tk_MODULE     = "editobj2.editor_tk"
  _Gtk_MODULE    = "editobj2.editor_gtk"
  _Qt_MODULE     = "editobj2.editor_qt"
  _Qtopia_MODULE = "editobj2.editor_qtopia"


class EditorDialog(MultiGUIEditor):
  def __init__(self, gui, direction = "h", on_validate = None, edit_child_in_self = 1, undo_stack = None, on_close = None):
    self.gui         = gui
    self.on_validate = on_validate
    if direction == "h": self.editor_pane = HEditorPane(gui, self, edit_child_in_self, undo_stack or undoredo.stack)
    else:                self.editor_pane = VEditorPane(gui, self, edit_child_in_self, undo_stack or undoredo.stack)
    
  def edit      (self, o): return self.editor_pane.edit      (o)
  def edit_child(self, o):        self.editor_pane.edit_child(o)

class EditorPane(MultiGUIEditor):
  def __init__(self, gui, master, edit_child_in_self = 1, undo_stack = None):
    undo_stack = undo_stack or undoredo.stack
    self.gui                = gui
    self.master             = master
    self.edit_child_in_self = edit_child_in_self
    self.childhood_pane     = ChildhoodPane(gui, self, undo_stack)
    self.hierarchy_pane     = HierarchyPane(gui, self, self.edit_child, undo_stack)
    self.attribute_pane     = AttributePane(gui, self, self.edit_child, undo_stack)
    self.icon_pane          = IconPane     (gui, self)
    self.hierarchy_pane.set_childhood_pane(self.childhood_pane)
    
  def edit(self, o):
    self.hierarchy_pane.edit(o)
    if self.hierarchy_pane.descr.children_of(o) is None: self._set_hierarchy_visible(0)
    else:                                                self._set_hierarchy_visible(1)
    self.icon_pane     .edit(o)
    self.attribute_pane.edit(o)
    
  def edit_child(self, o):
    if self.edit_child_in_self:
      self.icon_pane     .edit(o)
      self.attribute_pane.edit(o)
      
  def _set_hierarchy_visible(self, visible):
    pass
  
class VEditorPane(EditorPane): pass
class HEditorPane(EditorPane): pass


_inexistent = object()

class AttributePane(MultiGUIEditor):
  def __init__(self, gui, master, edit_child = None, undo_stack = None):
    self.gui        = gui
    self.master     = master
    self.o          = None
    self.undo_stack = undo_stack or undoredo.stack
    self.attrs      = []
    if edit_child: self.edit_child = edit_child
    
  def _listener(self, o, type, new, old):
    if   type == "__class__":
      self.edit(None)
      self.edit(o)
      
    elif type is object:
      diffs = observe.diffdict(new, old, _inexistent)
      for attr, new_val, old_val in diffs:
        if (old_val is _inexistent) or (new_val is _inexistent):
          self.edit(None)
          self.edit(o)
          return
        
      already = set()
      for attr, new_val, old_val in diffs:
        field = self.fields.get(attr)
        if field:
          field.update()
          already.add(attr)
        else:
          for field in self.fields.values(): field.update()
          return
        
      # Update ALL fields corresponding to a property / getset
      for attr in self.property_attrs - already:
        field = self.fields.get(attr)
        if field: field.update()
      
  def _destroyed(self, *args):
    observe.unobserve(self.o, self._listener)
    
#   def edit(self, o):
#     if o is self.o: return
    
#     if not self.o is None:
#       observe.unobserve(self.o, self._listener)
#       self._delete_all_fields()
      
#     self.o              = o
#     self.descr          = introsp.description(o.__class__)
#     self.property_attrs = self.descr.property_attrs_of(o)
    
#     if not o is None:
#       attrs = [(self.descr.priority_for_attr(o, attr), editobj2.TRANSLATOR(attr), attr, self.descr.field_for_attr(o, attr)) for attr in self.descr.attrs_of(o)]
#       attrs = [priority_name_attr_Field for priority_name_attr_Field in attrs if priority_name_attr_Field[-1]]
#       attrs.sort()
#       self._set_nb_fields(len(attrs))
#       i = 0
#       self.fields = {}
#       for priority, name, attr, Field in attrs:
#         if (Field is editobj2.field.ObjectAttributeField) and isinstance(self.master, editobj2.field.ObjectAttributeField):
#           Field = editobj2.field.EntryField
#         field = self.fields[attr] = Field(self.gui, self, o, attr, self.undo_stack)
#         self._new_field(name, field, self.descr.unit_for_attr(o, attr), i)
#         i += 1
        
#       observe.observe(self.o, self._listener)
      
  def edit(self, o):
    if o is self.o: return
    
    self.descr = introsp.description(o.__class__)
    
    if not o is None:
      attrs = [(self.descr.priority_for_attr(o, attr), editobj2.TRANSLATOR(attr), attr, self.descr.field_for_attr(o, attr)) for attr in self.descr.attrs_of(o)]
      attrs = [priority_name_attr_Field for priority_name_attr_Field in attrs if priority_name_attr_Field[-1]]
      attrs.sort()
    else:
      attrs = []
      
    if o and self.o and (self.attrs == attrs):
      if not self.o is None: observe.unobserve(self.o, self._listener)
      
      self.o              = o
      self.property_attrs = self.descr.property_attrs_of(o)
      self.attrs          = attrs
      
      if not o is None:
        for field in self.fields.itervalues(): field.edit(o)
        observe.observe(self.o, self._listener)
        
    else:
      if not self.o is None:
        observe.unobserve(self.o, self._listener)
        self._delete_all_fields()
        
      self.o              = o
      self.property_attrs = self.descr.property_attrs_of(o)
      self.attrs          = attrs
      
      if not o is None:
        self._set_nb_fields(len(attrs))
        i = 0
        self.fields = {}
        for priority, name, attr, Field in attrs:
          if (Field is editobj2.field.ObjectAttributeField) and isinstance(self.master, editobj2.field.ObjectAttributeField):
            Field = editobj2.field.EntryField
          field = self.fields[attr] = Field(self.gui, self, o, attr, self.undo_stack)
          self._new_field(name, field, self.descr.unit_for_attr(o, attr), i)
          i += 1

        observe.observe(self.o, self._listener)
  edit_child = edit
  
  def _delete_all_fields(self): pass
  def _set_nb_fields(self, nb): pass
  def _new_field(self, name, field, unit, i): pass


class IconPane(MultiGUIEditor):
  def __init__(self, gui, master, use_small_icon = 0, compact = 0, bold_label = 1):
    self.master         = master
    self.o              = None
    self.use_small_icon = use_small_icon
    self.compact        = compact
    self.bold_label     = bold_label
    self.descr          = None
    
  def config(self, use_small_icon = 0, compact = 1, bold_label = 1):
    self.use_small_icon = use_small_icon
    self.compact        = compact
    self.bold_label     = bold_label
    if self.descr: self._update()
    
  def edit(self, o):
    if o is self.o: return
    
    if not self.o is None: observe.unobserve(self.o, self._listener)
    
    self.o     = o
    self.descr = introsp.description(o.__class__)
    
    if not o is None:
      self._update()
      observe.observe(self.o, self._listener)
    else:
      self._set_icon_filename_label_details("", "", "")
      
  def _listener(self, o, type, new, old): self._update()
  
  def _update(self):
    if self.compact: details = ""
    else:            details = self.descr.details_for(self.o)
    self._set_icon_filename_label_details(self.descr.icon_filename_for(self.o), self.descr.label_for(self.o), details)
    
  def _set_icon_filename_label_details(self, icon_filename, label, details): pass
  
  def _destroyed(self, *args):
    observe.unobserve(self.o, self._listener)
  

class ChildhoodPane(MultiGUIEditor):
  def __init__(self, gui, master, undo_stack = None):
    self.undo_stack = undo_stack or undoredo.stack
    self.p          = None
    self.o          = None
    
  def edit(self, parent, object):
    self.p = parent
    self.o = object
    
    self.set_button_visibilities(
      self.p and self.o and introsp.ACTION_MOVE_UP  .filter(self.p, self.o),
     (self.o and            introsp.ACTION_ADD       in introsp.description(self.o.__class__).actions_for(self.o)) or
     (self.p and            introsp.ACTION_ADD       in introsp.description(self.p.__class__).actions_for(self.p)),
      self.p and self.o and introsp.ACTION_REMOVE    in introsp.description(self.o.__class__).actions_for(self.o, self.p),
      self.p and self.o and introsp.ACTION_MOVE_DOWN.filter(self.p, self.o),
      )
    
  def on_add(self, *args):
    if self.o and introsp.ACTION_ADD in introsp.description(self.o.__class__).actions_for(self.o):
      o     = self.o
      index = None
    else:
      o     = self.p
      try:
        index = introsp.description(o.__class__).children_of(o).index(self.o) + 1
      except:
        index = None
        
    introsp.description(o.__class__).do_action(introsp.ACTION_ADD, self.undo_stack, o, index)
    
  def on_remove(self, *args):
    introsp.description(self.p.__class__).do_action(introsp.ACTION_REMOVE, self.undo_stack, self.p, self.o)
      
  def on_move_up(self, *args):
    introsp.description(self.p.__class__).do_action(introsp.ACTION_MOVE_UP, self.undo_stack, self.p, self.o)
      
  def on_move_down(self, *args):
    introsp.description(self.p.__class__).do_action(introsp.ACTION_MOVE_DOWN, self.undo_stack, self.p, self.o)
    

class HierarchyPane(MultiGUIEditor):
  Node = None
  def __init__(self, gui, master, edit_child, undo_stack = None):
    self.gui            = gui
    self.master         = master
    self.edit_child     = edit_child
    self.o              = None
    self.root_node      = None
    self.undo_stack     = undo_stack or undoredo.stack
    self.childhood_pane = None

  def set_childhood_pane(self, childhood_pane):
    self.childhood_pane = childhood_pane
    
  def _destroyed(self, *args):
    if self.root_node: self.root_node.destroy()
    
  def edit(self, o):
    if o is self.o: return
    
    if self.root_node: self.root_node.destroy()
    
    self.o = o
    
    if not o is None:
      self.descr     = introsp.description(o.__class__)
      self.root_node = self.Node(self.tree, o)
      
    if self.childhood_pane: self.childhood_pane.edit(None, o)
    
  def _get_actions(self, o, parent):
    actions = list(introsp.description(o.__class__).actions_for(o, parent))
    for action in actions: action.label = editobj2.TRANSLATOR(action.name)
    actions.sort(lambda a, b: cmp(a.label, b.label))
    return actions

  def _action_activated(self, drop_it, o, action, parent):
    if action.pass_editor_in_args:
      if isinstance(self.master, EditorPane):
        if isinstance(self.master.master, EditorDialog): editor = self.master.master
        else:                                            editor = self.master
      else:                                              editor = self
      
      if isinstance(action, introsp.ActionOnAChild):
        descr = introsp.description(parent.__class__)
        descr.do_action(action, self.undo_stack, parent, o, editor)
      else:
        descr = introsp.description(o.__class__)
        descr.do_action(action, self.undo_stack, o, editor)
    else:
      if isinstance(action, introsp.ActionOnAChild):
        descr = introsp.description(parent.__class__)
        descr.do_action(action, self.undo_stack, parent, o)
      else:
        descr = introsp.description(o.__class__)
        descr.do_action(action, self.undo_stack, o)
 

class HierarchyNode(object):
  def __init__(self, parent_node, o):
    self.descr             = introsp.description(o.__class__)
    self.o                 = o
    self.o_children_getter = self.descr.children_getter_of(self.o)
    self.o_children        = None
    self.o_has_children    = self.descr.has_children(self.o)
    super(HierarchyNode, self).__init__(parent_node)
    
    observe.observe(self.o, self._listener)

    if isinstance(self.o_has_children, list) or isinstance(self.o_has_children, set) or isinstance(self.o_has_children, dict):
      observe.observe(self.o_has_children, self._listener)
      
  def has_children(self): return self.o_has_children
  
  def create_children(self, old_children = ()):
    if not self.o_has_children: return []
    if self.o_children is None:
      if isinstance(self.o_has_children, list) or isinstance(self.o_has_children, set) or isinstance(self.o_has_children, dict):
        observe.unobserve(self.o_has_children, self._listener)
      self.o_children = self.descr.children_of(self.o)
      observe.observe(self.o_children, self._listener)
      
    # Order them
    if   isinstance(self.o_children, set      ): self.o_children = list (self.o_children)
    elif isinstance(self.o_children, frozenset): self.o_children = tuple(self.o_children)
    elif isinstance(self.o_children, dict     ): self.o_children = self.o_children.values()
    
    old = dict([(child.o, child) for child in old_children])
    return [old.get(o) or self.__class__(self, o) for o in self.o_children]
  
  def _listener(self, o, type, new, old):
    self.update()
    if   (type is list) or (type is set) or (type is dict):
      if self.o_children is not None:
        observe.unobserve(self.o_children, self._listener)
        self.o_children = self.descr.children_of(self.o)
        observe.observe(self.o_children, self._listener)
      self.update_children()
        
    elif type is object:
      if self.o_children is not None:
        if (self.o_children_getter in new.keys()) or (self.o_children_getter in old.keys()): # XXX Optimizable : verify if self.o_children_getter is a string AND new[self.o_children_getter] == old[self.o_children_getter]
          observe.unobserve(self.o_children, self._listener)
          self.o_children = self.descr.children_of(self.o)
          observe.observe(self.o_children, self._listener)
          self.update_children()
          
    elif type == "__class__":
      self.descr = introsp.description(self.o.__class__)
      self.update_children()
      
  def destroy(self):
    super(HierarchyNode, self).destroy()
    observe.unobserve(self.o, self._listener)
    if   self.o_children is not None:
      observe.unobserve(self.o_children, self._listener)
    elif isinstance(self.o_has_children, list) or isinstance(self.o_has_children, set) or isinstance(self.o_has_children, dict):
      observe.unobserve(self.o_has_children, self._listener)
      
  def __repr__(self): return "<Node for %s>" % self.o



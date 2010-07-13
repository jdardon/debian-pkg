# -*- coding: utf-8 -*-

# introsp.py
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

import os, os.path, types, inspect
import editobj2, editobj2.undoredo as undoredo

PROPERTY_TYPE_NAMES = set(["property", "getset_descriptor"])
IGNORED_ATTRS       = set(["__weakref__"])
BOOL_ATTRS          = set(["visible", "hidden", "active"])
CHILDREN_ATTRS      =     ["children", "elements", "items"]
REMOVE_ATTRS        =     ["remove", "remove_item", "discard", "drop", "delete"]

def _mro(klass):
  mro = [klass]
  for c in klass.__bases__: mro.extend(_mro(c))
  return mro

def _method_has_nb_args(method, nb):
  try: return method.im_func.func_code.co_argcount == nb
  except: return 0

_NEXT_PRIORITY = 0

class ClassDescr(object):
  def __init__(self, klass):
    self.klass            = klass
    self.attributes       = {}
    self.attr_fields      = {}
    self.attr_units       = {}
    self.attr_priority    = {}
    self.actions          = {}
    self.cactions         = {}
    self.children_getter  = None
    self.icon_filename    = None
    self.label            = None
    self.details          = None
    self.new_child_method = None
    self.add_method       = None
    self.remove_method    = None
    self.reorderable      = None
    
    self.klass_mro = getattr(klass, "__mro__", None) or _mro(klass)
    if not object is self.klass_mro[-1]: self.klass_mro = self.klass_mro + [object]
    
    attrs = dir(klass)
    for attr in attrs:
      if attr in IGNORED_ATTRS: continue
      kval = getattr(klass, attr)
      if   type(kval).__name__ in PROPERTY_TYPE_NAMES:
        attribute = self.attributes[attr] = Attribute(attr)
        if isinstance(kval, property):
          if not kval.fset: attribute.setter = None
          if not kval.fget: attribute.getter = None
        else:
          if not kval.__set__: attribute.setter = None
          if not kval.__get__: attribute.getter = None
          
      elif attr.startswith("set") and (len(attr) > 3) and _method_has_nb_args(kval, 2):
        if attr[3] == "_": attr2 = attr[4:]
        else:              attr2 = attr[3].lower() + attr[4:]
        attribute = self.attributes.get(attr2)
        if not attribute: attribute = self.attributes[attr2] = Attribute(attr2, "__dict__", attr)
        else:             attribute.setter = attr
      elif attr.startswith("get") and (len(attr) > 3) and _method_has_nb_args(kval, 1):
        if attr[3] == "_": attr2 = attr[4:]
        else:              attr2 = attr[3].lower() + attr[4:]
        attribute = self.attributes.get(attr2)
        if not attribute: attribute = self.attributes[attr2] = Attribute(attr2, attr, "__dict__")
        else:             attribute.getter = attr
        
    _CLASS_DESCRS[klass] = self
    
  def __repr__(self):
    return ("<ClassDescr for %s, attributes:\n  " % self.klass) + "\n  ".join([repr(attribute) for attribute in self.attributes.values()]) + "\n>"
  
  def set_icon_filename(self, icon_filename): self.icon_filename = icon_filename
  
  def icon_filename_for(self, o):
    for klass in self.klass_mro:
      descr = description(klass)
      if descr.icon_filename:
        if callable(descr.icon_filename): return descr.icon_filename(o)
        else:                             return descr.icon_filename
    if hasattr(o, "icon_filename") or self.attributes.has_key("icon_filename"): return self.get(o, "icon_filename")
    return os.path.join(editobj2._ICON_DIR, "python.png")
  
  def set_label(self, label): self.label = label
  
  def label_for(self, o):
    for klass in self.klass_mro:
      descr = description(klass)
      if descr.label:
        if callable(descr.label): return descr.label(o)
        else:                     return descr.label
    return unicode(o)
  
  def set_details(self, details): self.details = details
  
  def details_for(self, o):
    for klass in self.klass_mro:
      descr = description(klass)
      if descr.details:
        if callable(descr.details): return descr.details(o)
        else:                       return descr.details
    if hasattr(o, "details") or self.attributes.has_key("details"): return self.get(o, "details")
    return ""
  
  def set_children_getter(self, children_getter, has_children_method = None, new_child_method = None, add_method = None, remove_method = None, reorderable = None):
    self.children_getter       = children_getter
    self.has_children_method   = has_children_method
    self.new_child_method      = new_child_method
    self.add_method            = add_method
    self.remove_method         = remove_method
    self.reorderable           = reorderable
    
  def children_getter_of(self, o):
    for klass in self.klass_mro:
      descr = description(klass)
      if descr.children_getter: return descr.children_getter
    for attr in CHILDREN_ATTRS:
      if isinstance(o, dict) and (attr == "items"): continue
      if hasattr(o, attr) or self.attributes.has_key(attr): return attr
    return None
  
  def children_of(self, o):
    attr = self.children_getter_of(o)
    if attr:
      if callable(attr): return attr(o)
      else:              return self.get(o, attr)
    if isinstance(o, list) or isinstance(o, set) or isinstance(o, dict): return o
    
  def has_children_method_of(self, o):
    for klass in self.klass_mro:
      descr = description(klass)
      if descr.children_getter and descr.has_children_method: return descr.has_children_method
    for attr in CHILDREN_ATTRS:
      attr = "has_%s" % attr
      if hasattr(o, attr) or self.attributes.has_key(attr): return attr
    return None
  
  def has_children(self, o):
    attr = self.has_children_method_of(o)
    if attr:
      if callable(attr): return attr(o)
      else:              return getattr(o, attr)()
    #return bool(self.children_of(o))
    return self.children_of(o)
  
  def _add_to(self, parent, o, index = None):
    if not self.add_method: raise ValueError("Register a add_method first!")
    #if callable(self.add_method): add_method = self.add_method
    #else:                         add_method = getattr(parent, self.add_method)
    
    if callable(self.add_method):
      nb_args = len(inspect.getargspec(self.add_method)[0])
      if isinstance(self.add_method, types.MethodType) and (not self.add_method.im_self is None):
        nb_args -= 1
      if nb_args <= 2:
        self.add_method(parent, o)
      else:
        if index is None: index = len(self.children_of(parent))
        self.add_method(parent, index, o)
        
    else:
      add_method = getattr(parent, self.add_method)
      nb_args = len(inspect.getargspec(add_method)[0])
      if isinstance(add_method, types.MethodType) and (not add_method.im_self is None):
        nb_args -= 1
      if nb_args <= 1:
        add_method(o)
      else:
        if index is None: index = len(self.children_of(parent))
        add_method(index, o)
        
  def _remove_from(self, parent, o):
    if not self.remove_method: raise ValueError("Register a remove_method first!")
    if callable(self.remove_method): self.remove_method(parent, o)
    else:                            getattr(parent, self.remove_method)(o)

  def is_reorderable(self, o): return self.reorderable
  
  def add_attribute(self, attribute):
    self.attributes[attribute.name] = attribute
    
  def attrs_of(self, o):
    dict = getattr(o, "__dict__", None)
    if dict: return set(self.attributes.keys() + dict.keys())
    else:    return set(self.attributes.keys())
    
  def property_attrs_of(self, o):
    return set(self.attributes.keys())
  
  def get(self, o, attr):
    attribute = self.attributes.get(attr)
    if attribute: return attribute.get(o)
    else:         return getattr(o, attr)
    
  def set(self, o, attr, val):
    attribute = self.attributes.get(attr)
    if attribute: attribute.set(o, val)
    else:         setattr(o, attr, val)
    
  def set_field_for_attr(self, attr, Field, unit = None, priority = None):
    if priority is None:
      global _NEXT_PRIORITY
      _NEXT_PRIORITY += 1
      priority = _NEXT_PRIORITY
      
    self.attr_fields  [attr] = Field
    self.attr_units   [attr] = unit
    self.attr_priority[attr] = priority
    
  def field_for_attr(self, o, attr):
    for klass in self.klass_mro:
      descr = description(klass)
      if descr.attr_fields.has_key(attr): return descr.attr_fields[attr]
      
    # Default heuristic rules
    import editobj2.field as field
    if attr.startswith("_"): return None
    
    val = self.get(o, attr)
    if   isinstance(val, bool ): return field.BoolField
    elif isinstance(val, float): return field.FloatField
    elif isinstance(val, int):
      if ((val == 1) or (val == 0)) and (attr.startswith("is") or attr.startswith("has") or attr.endswith("enabled") or attr.endswith("Enabled") or (attr in BOOL_ATTRS)):
        return field.BoolField
      return field.IntField
    elif isinstance(val, long): return field.IntField
    elif isinstance(val, basestring):
      if attr == "password": return field.PasswordField
      if attr.endswith("filename") or attr.endswith("Filename"): return field.FilenameField
      if attr.endswith("url") or attr.endswith("Url") or attr.endswith("URL"): return field.URLField
      if (len(val) > 100) or ("\n" in val): return field.TextField
      else:                                 return field.StringField
    elif isinstance(val, object) and hasattr(val, "__dict__"):
      descr = description(val.__class__)
      if (len(descr.attrs_of(val)) < 7) and (attr != "parent") and (attr != "master") and (attr != "root"):
        return field.ObjectAttributeField
      
  def unit_for_attr(self, o, attr):
    for klass in self.klass_mro:
      descr = description(klass)
      return descr.attr_units.get(attr, "")
      
  def priority_for_attr(self, o, attr):
    for klass in self.klass_mro:
      descr = description(klass)
      return descr.attr_priority.get(attr, 0)
      
  def add_action(self, action):
    if isinstance(action, ActionOnAChild): self.cactions[action.name] = action
    else:                                  self.actions [action.name] = action
    
  def actions_for(self, o, parent = None):
    actions = {}
    for klass in self.klass_mro[::-1]:
      actions.update(description(klass).actions)
    actions = set([action for action in actions.values() if action.filter(o)])
    
    cactions = {}
    if parent:
      for klass in description(parent.__class__).klass_mro[::-1]:
        cactions.update(description(klass).cactions)
    cactions = set([action for action in cactions.values() if action.filter(parent, o)])

    return actions | cactions
  
#   def get_action(self, action_name):
#     for klass in self.klass_mro[::-1]:
#       descr = description(klass)
#       if descr. actions.has_key(action_name): return descr. actions[action_name]
#       if descr.cactions.has_key(action_name): return descr.cactions[action_name]
      
  def do_action(self, action, undo_stack, *args):
    return action.do(undo_stack, *args)


class Attribute(object):
  def __init__(self, name, getter = "__dict__", setter = "__dict__"):
    self.name   = name
    self.getter = getter
    self.setter = setter
    
  def get(self, o):
    if   self.getter == "__dict__": return getattr(o, self.name)
    elif callable(self.getter):     return self.getter(o)
    elif self.getter:               return getattr(o, self.getter)()
    else:                           raise AttributeError("unreadable attribute %s!" % self.name)
    
  def set(self, o, value):
    if   self.setter == "__dict__": return setattr(o, self.name, value)
    elif callable(self.getter):     return self.setter(o, value)
    elif self.setter:               getattr(o, self.setter)(value)
    else:                           raise AttributeError("unwritable attribute %s!" % self.name)
    
  def __repr__(self):
    if   self.getter == "__dict__": get = ""
    elif self.getter:               get = ", get with '%s'" % self.getter
    else:                                get = ", write-only"
    if   self.setter == "__dict__": set = ""
    elif self.setter:               set = ", set with '%s'" % self.setter
    else:                           set = ", read-only"
    return "<Attribute '%s'%s%s" % (self.name, get, set) + ">"


class Action(object):
  def __init__(self, name, func, filter = None, accept_object_pack = 0, default = 0, Field = None, pass_editor_in_args = 0):
    self.name                = name
    self.func                = func
    self.Field               = Field
    self.accept_object_pack  = accept_object_pack
    self.default             = default
    self.pass_editor_in_args = pass_editor_in_args
    if filter: self.filter   = filter
    
  def filter(self, o): return 1
  
  def do(self, undo_stack, *args):
    if callable(self.func):      self.func(undo_stack, *args)
    else:                        getattr(args[0], self.func)(undo_stack, *args[1:])
    
    
class ActionOnAChild(Action):
  def filter(self, o, children): return 1



_CLASS_DESCRS = {}
def description(klass):
  return _CLASS_DESCRS.get(klass) or ClassDescr(klass)
  


def _edit_in_new_window_action(undo_stack, o):
  import editobj2.editor
  editobj2.edit(o)

def _move_child_action(undo_stack, parent, o, move):
  if isinstance(parent, ObjectPack):
    parents = parent.objects
    objects = o.objects
  else:
    parents = [parent]
    objects = [o]
    
  def build():
    parent_indexes_objects = {}
    for parent in parents: parent_indexes_objects[parent] = []
    for i in range(len(parents)):
      children = description(parents[i].__class__).children_of(parents[i])
      parent_indexes_objects[parents[i]].append((children.index(objects[i]), objects[i]))
    for parent in parents: parent_indexes_objects[parent].sort()
    return parent_indexes_objects

  parent_indexes_objects = build()
  for parent, indexes_objects in parent_indexes_objects.items():
    children = description(parent.__class__).children_of(parent)
    if (move == -1) and (indexes_objects[ 0][0] <=                 0): return # Cannot move up
    if (move ==  1) and (indexes_objects[-1][0] >= len(children) - 1): return # Cannot move down

  def move_up():
    parent_indexes_objects = build()

    for parent, indexes_objects in parent_indexes_objects.items():
      children = description(parent.__class__).children_of(parent)
      for i, o in indexes_objects:
        children[i - 1], children[i] = children[i], children[i - 1]

  def move_down():
    parent_indexes_objects = build()

    for parent, indexes_objects in parent_indexes_objects.items():
      indexes_objects.reverse()
      children = description(parent.__class__).children_of(parent)
      for i, o in indexes_objects:
        children[i + 1], children[i] = children[i], children[i + 1]

  labels = u"', '".join([description(o.__class__).label_for(o) for o in objects])
  if move == -1: undoredo.UndoableOperation(move_up  , move_down, editobj2.TRANSLATOR("move up '%s'"  ) % labels, undo_stack)
  else:          undoredo.UndoableOperation(move_down, move_up  , editobj2.TRANSLATOR("move down '%s'") % labels, undo_stack)

def _reorder_filter(parent, o):
  return description(parent.__class__).is_reorderable(parent)


# def _remove_action(undo_stack, parent, o):
#   if isinstance(parent, ObjectPack):
#     parents = parent.objects
#     objects = o.objects
#   else:
#     parents = [parent]
#     objects = [o]
    
#   old_children = {}
#   for parent in parents:
#     if not old_children.has_key(parent):
#       old_children[parent] = list(description(parent.__class__).children_of(parent))
      
#   def do_it():
#     for i in range(len(parents)):
#       description(parents[i].__class__)._remove_from(parents[i], objects[i])
      
#   def undo_it():
#     for i in range(len(parents)):
#       descr = description(parents[i].__class__)
#       current_children = descr.children_of(parents[i])
#       descr._add_to(parents[i], objects[i])
#       current_children.__init__(old_children[parents[i]]) # Needed to restore the indexes
      
#   labels = u"', '".join([description(o.__class__).label_for(o) for o in objects])
#   undoredo.UndoableOperation(do_it, undo_it, editobj2.TRANSLATOR(u"remove '%s'") % labels, undo_stack)

def _remove_action(undo_stack, parent, o):
  if isinstance(parent, ObjectPack):
    parents = parent.objects
    objects = o.objects
  else:
    parents = [parent]
    objects = [o]
    
  indexes = [None] * len(parents)
  for i in range(len(indexes)):
    try: indexes[i] = description(parents[i].__class__).children_of(parents[i]).index(objects[i])
    except: pass
    
  def do_it():
    for i in range(len(parents)):
      description(parents[i].__class__)._remove_from(parents[i], objects[i])
      
  def undo_it():
    for i in range(len(parents)):
      description(parents[i].__class__)._add_to(parents[i], objects[i], indexes[i])
      
  labels = u"', '".join([description(o.__class__).label_for(o) for o in objects])
  undoredo.UndoableOperation(do_it, undo_it, editobj2.TRANSLATOR(u"remove '%s'") % labels, undo_stack)

def _remove_filter(parent, o):
  descr = description(parent.__class__)
  return descr.add_method and descr.remove_method


def _add_action(undo_stack, parent, index = None):
  descr = description(parent.__class__)
  if callable(descr.new_child_method): new_child = descr.new_child_method(parent)
  else:                                new_child = getattr(parent, descr.new_child_method)()
  
  if new_child:
    def do_it():
      children = description(parent.__class__).children_of(parent)
      if not new_child in children: # Else, it might already have been added by new_child_method(parent) ?
        descr._add_to(parent, new_child, index)
        
    def undo_it():
      descr._remove_from(parent, new_child)
      
    undoredo.UndoableOperation(do_it, undo_it, editobj2.TRANSLATOR(u"add '%s'") % description(new_child.__class__).label_for(new_child), undo_stack)

def _add_filter(parent):
  descr = description(parent.__class__)
  return descr.new_child_method and descr.add_method and descr.remove_method

object_descr = description(object)

add_action         = object_descr.add_action
add_attribute      = object_descr.add_attribute
set_field_for_attr = object_descr.set_field_for_attr
del object_descr

ACTION_ADD       = Action        (u"Add"                  , _add_action   , filter = _add_filter   , accept_object_pack = 0)
ACTION_REMOVE    = ActionOnAChild(u"Remove"               , _remove_action, filter = _remove_filter, accept_object_pack = 1)
ACTION_MOVE_UP   = ActionOnAChild(u"Move up"              , lambda undo_stack, parent, o: _move_child_action(undo_stack, parent, o, -1), filter = _reorder_filter, accept_object_pack = 1)
ACTION_MOVE_DOWN = ActionOnAChild(u"Move down"            , lambda undo_stack, parent, o: _move_child_action(undo_stack, parent, o,  1), filter = _reorder_filter, accept_object_pack = 1)
ACTION_EDIT      = Action(u"Edit in new window...", _edit_in_new_window_action)

add_action(ACTION_EDIT)
add_action(ACTION_ADD)
add_action(ACTION_REMOVE)
add_action(ACTION_MOVE_UP)
add_action(ACTION_MOVE_DOWN)

class ObjectPack(object):
  def __init__(self, objects):
    self.objects        = objects
    self.attrs          = [description(o.__class__).attrs_of         (o) for o in objects]
    self.property_attrs = [description(o.__class__).property_attrs_of(o) for o in objects]
    
class NonConsistent(object):
  def __repr__(self): return "NonConsistent"
  def __nonzero__(self): return 0
NonConsistent = NonConsistent()

class ObjectPackDescription(object):
  def icon_filename_for(self, pack):
    icon_filenames = set()
    for o in pack.objects:
      icon_filenames.add(description(o.__class__).icon_filename_for(o))
    icon_filenames = list(icon_filenames)
    icon_filenames.sort()
    if len(icon_filenames) == 1: icon_filenames = icon_filenames * 2
    return icon_filenames
    
  def label_for(self, pack):
    return "(pack of %s objects)" % len(pack.objects)
  
  def details_for (self, pack): return ""
  def children_of (self, pack): return None
  def has_children(self, pack): return 0
  def children_getter_of(self, o): return None
  
  def is_reorderable(self, pack):
    for o in pack.objects:
      if description(o.__class__).is_reorderable(o): return 1
      
  def attrs_of(self, pack):
    attrs = set()
    for o_attrs in pack.attrs: attrs.update(o_attrs)
    return attrs
  
  def property_attrs_of(self, pack):
    attrs = set()
    for o_attrs in pack.property_attrs: attrs.update(o_attrs)
    return attrs
  
  def get(self, pack, attr):
    val = NonConsistent
    for i in range(len(pack.objects)):
      if attr in pack.attrs[i]:
        v = description(pack.objects[i].__class__).get(pack.objects[i], attr)
        if val is NonConsistent: val = v
        elif val != v: return NonConsistent
    return val
  
  def set(self, pack, attr, val):
    for i in range(len(pack.objects)):
      if attr in pack.attrs[i]:
        description(pack.objects[i].__class__).set(pack.objects[i], attr, val)
        
  def field_for_attr(self, pack, attr):
    Field = None
    for i in range(len(pack.objects)):
      descr = description(pack.objects[i].__class__)
      if attr in pack.attrs[i]:
        NewField = descr.field_for_attr(pack.objects[i], attr)
        if Field and NewField and (not Field is NewField): return None
        Field = NewField
    return Field
  
  def unit_for_attr(self, pack, attr):
    unit = None
    for i in range(len(pack.objects)):
      descr = description(pack.objects[i].__class__)
      if attr in pack.attrs[i]:
        new_unit = descr.unit_for_attr(pack.objects[i], attr)
        if unit and new_unit and (unit != new_unit): return None
        unit = new_unit
    return unit
      
  def priority_for_attr(self, pack, attr):
    for i in range(len(pack.objects)):
      descr = description(pack.objects[i].__class__)
      if attr in pack.attrs[i]:
        priority = descr.priority_for_attr(pack.objects[i], attr)
        if priority: return priority
      
  def actions_for(self, pack, parents = None):
    if parents: parents = parents.objects
    else:       parents = [None] * len(pack.objects)
    actions = set()
    i = 0
    for o in pack.objects:
      descr = description(o.__class__)
      actions.update(descr.actions_for(o, parents[i]))
      i += 1
    return actions
  
  def do_action(self, action, undo_stack, pack, *args):
    if action.accept_object_pack:
      if isinstance(action, ActionOnAChild):
        parents = pack   .objects
        objects = args[0].objects
        new_parents = []
        new_objects = []
        for i in range(len(parents)):
          if action in description(objects[i].__class__).actions_for(objects[i], parents[i]):
            new_parents.append(parents[i])
            new_objects.append(objects[i])
        return action.do(undo_stack, ObjectPack(new_parents), ObjectPack(new_objects), *args[1:])
      
      else:
        objects = ObjectPack([o for o in pack   .objects if action in description(o.__class__).actions_for(o)])
        return action.do(undo_stack, objects, *args)
      
    else:
      if isinstance(action, ActionOnAChild):
        parents = pack.objects
        children = args[0].objects
        args = args[1:]
        i = 0
        for i, parent in enumerate(parents):
          o = children[i]
          parent_descr = description(parent.__class__)
          o_descr      = description(o     .__class__)
          if action in o_descr.actions_for(o, parent):
            parent_descr.do_action(action, undo_stack, parent, o, *args)
      else:
        for o in pack.objects:
          descr = description(o.__class__)
          if action in descr.actions_for(o):
            descr.do_action(action, undo_stack, o, *args)
  
  
_CLASS_DESCRS[ObjectPack] = ObjectPackDescription()

# -*- coding: utf-8 -*-

# field.py
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

import sys

import editobj2
import editobj2.introsp  as introsp
import editobj2.undoredo as undoredo
import editobj2.observe  as observe


class MultiGUIWidget(object):
  _Tk_MODULE  = ""
  _Qt_MODULE  = ""
  _Gtk_MODULE = ""
  def __new__(klass, gui, *args):
    #print klass, gui, args
    if not klass.__name__.startswith(gui):
      klass = getattr(__import__(getattr(klass, "_%s_MODULE" % gui), fromlist = [""]), gui + klass.__name__)
    #print klass, gui, args
    #print "  ", klass.__base__
    #print
    return super(MultiGUIWidget, klass).__new__(klass)
    

class Field(object):
  def __init__(self, gui, master, o, attr, undo_stack):
    self.o          = o
    self.attr       = attr
    self.descr      = introsp.description(o.__class__)
    self.master     = master
    self.undo_stack = undo_stack
    self.updating   = 0
    
    #if isinstance(self, CoalescedChange): self.last_undoable = None

  def edit(self, o):
    self.o          = o
    self.descr      = introsp.description(o.__class__)
    self.update()
    
  def update(self): pass
  def get_value(self): return self.descr.get(self.o, self.attr)
  def set_value(self, value):
    if self.updating: return
    self.updating = 1
    try:
      if isinstance(self.o, introsp.ObjectPack):
        objects    = [o for (i, o) in enumerate(self.o.objects) if self.attr in self.o.attrs[i]]
        old_values = [introsp.description(o.__class__).get(o, self.attr) for o in objects]
        def do_it  ():
          for o in objects: introsp.description(o.__class__).set(o, self.attr, value)
        def undo_it():
          for i, o in enumerate(objects): introsp.description(o.__class__).set(o, self.attr, old_values[i])
        a = undoredo.UndoableOperation(do_it, undo_it, editobj2.TRANSLATOR("change of %s") % editobj2.TRANSLATOR(self.attr), self.undo_stack)
        
      else:
        old_value = introsp.description(self.o.__class__).get(self.o, self.attr)
        def do_it  (): self.descr.set(self.o, self.attr, value)
        def undo_it(): self.descr.set(self.o, self.attr, old_value)
        a = undoredo.UndoableOperation(do_it, undo_it, editobj2.TRANSLATOR("change of %s") % editobj2.TRANSLATOR(self.attr), self.undo_stack)
    finally:
      self.updating = 0
      
class CoalescedChangeField(Field):
  def __init__(self, gui, master, o, attr, undo_stack):
    Field.__init__(self, gui, master, o, attr, undo_stack)
    self.last_undoable = None
    
  def set_value(self, value):
    if self.updating: return
    Field.set_value(self, value)
    
    if (len(self.undo_stack.undoables) >= 2) and (self.undo_stack.undoables[-2] is self.last_undoable):
      self.undo_stack.undoables[-1].coalesce_with(self.last_undoable)
    if self.undo_stack.undoables: # Can be empty when undoing / redoing
      self.last_undoable = self.undo_stack.undoables[-1]

      
    
class MultiGUIField(Field, MultiGUIWidget):
  _Tk_MODULE     = "editobj2.field_tk"
  _Gtk_MODULE    = "editobj2.field_gtk"
  _Qt_MODULE     = "editobj2.field_qt"
  _Qtopia_MODULE = "editobj2.field_qtopia"

  
class EntryField(MultiGUIField):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(EntryField, self).__init__(gui, master, o, attr, undo_stack)
    
  def get_value(self):
    v = Field.get_value(self)
    if v is introsp.NonConsistent: return ""
    return repr(v)
  
  def set_value(self, s):
    if s and (s[0] != "<"):
      try: s = editobj2.eval(s)
      except: pass #sys.excepthook(*sys.exc_info())
    Field.set_value(self, s)
    
class FloatField(EntryField):
  def get_value(self):
    v = Field.get_value(self)
    if v is introsp.NonConsistent: return ""
    return str(v)
  def set_value(self, s):
    try: s = float(editobj2.eval(s))
    except: return
    Field.set_value(self, s)
    
class IntField(EntryField):
  def get_value(self):
    v = Field.get_value(self)
    if v is introsp.NonConsistent: return ""
    return str(v)
  def set_value(self, s):
    try: s = int(editobj2.eval(s))
    except: return
    Field.set_value(self, s)
  
class StringField(EntryField):
  def get_value(self):
    v = Field.get_value(self)
    if v is introsp.NonConsistent: return ""
    return v
  def set_value(self, s): Field.set_value(self,s)
  
class PasswordField(StringField  ): pass
class TextField    (StringField  ): pass

class BoolField    (MultiGUIField):
  def set_value(self, value):
    if isinstance(self.o, introsp.ObjectPack):
      o = self.o.objects[0]
      old = introsp.description(o.__class__).get(o, self.attr)
    else:
      old = self.get_value()
    if (old is True) or (old is False):
      if value: MultiGUIField.set_value(self, True)
      else:     MultiGUIField.set_value(self, False)
    else:
      if value: MultiGUIField.set_value(self, 1)
      else:     MultiGUIField.set_value(self, 0)
      
class ProgressBarField(MultiGUIField):
  def get_value(self):
    v = Field.get_value(self)
    if v is introsp.NonConsistent: return v
    return float(v)
  

class EditButtonField(MultiGUIField):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(EditButtonField, self).__init__(gui, master, o, attr, undo_stack)
    
  def on_click(self, *args):
    editobj2.edit(self.get_value(), undo_stack = self.undo_stack)
    
    
class WithButtonStringField(MultiGUIField):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(WithButtonStringField, self).__init__(gui, master, o, attr, undo_stack)
    self.string_field = StringField(gui, self, o, attr, undo_stack)
    
  def update(self): self.string_field.update()
  
  def edit(self, o): self.string_field.edit(o)
  
class FilenameField(WithButtonStringField): button_text = "..."
class DirnameField (WithButtonStringField): button_text = "..."
class URLField     (WithButtonStringField): button_text = "Goto..."

class ObjectAttributeField(MultiGUIField):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(ObjectAttributeField, self).__init__(gui, master, o, attr, undo_stack)
    import editobj2.editor as editor
    self.attribute_pane = editor.AttributePane(gui, self)
    self.update()
    
  def update(self):
    self.updating = 1
    try:
      v = self.descr.get(self.o, self.attr)
      if (v is introsp.NonConsistent) and isinstance(self.o, introsp.ObjectPack):
        v = introsp.ObjectPack([introsp.description(o.__class__).get(o, self.attr) for o in self.o.objects if self.attr in introsp.description(o.__class__).attrs_of(o)])

      self.attribute_pane.edit(v)
    finally:
      self.updating = 0
      
class ObjectHEditorField(MultiGUIField):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(ObjectHEditorField, self).__init__(gui, master, o, attr, undo_stack)
    import editobj2.editor as editor
    self.editor_pane = editor.HEditorPane(gui, self)
    self.update()
    
  def update(self):
    v = self.descr.get(self.o, self.attr)
    self.editor_pane.edit(v)

class ObjectVEditorField(MultiGUIField):
  def __init__(self, gui, master, o, attr, undo_stack):
    super(ObjectVEditorField, self).__init__(gui, master, o, attr, undo_stack)
    import editobj2.editor as editor
    self.editor_pane = editor.VEditorPane(gui, self)
    self.update()
    
  def update(self):
    v = self.descr.get(self.o, self.attr)
    self.editor_pane.edit(v)

def RangeField(min, max, incr = 1):
  """A slider-based field."""
  return lambda gui, master, o, attr, undo_stack: _RangeField(gui, master, o, attr, undo_stack, min, max, incr)

class _RangeField(MultiGUIField, CoalescedChangeField):
  def __init__(self, gui, master, o, attr, undo_stack, min, max, incr = 1):
    super(_RangeField, self).__init__(gui, master, o, attr, undo_stack)
    self.min = min
    self.max = max
    self.update()
    
  def get_value(self):
    v = Field.get_value(self)
    if v is introsp.NonConsistent: return self.min
    return v
  
def EnumField(choices, value_2_enum = None, enum_2_value = None, long_list = None, translate = 1):
  if isinstance(choices, list):
    if translate: choices = dict([(editobj2.TRANSLATOR(x), x) for x in choices])
    else:         choices = dict([(x                     , x) for x in choices])
  def _Field(gui, master, o, attr, undo_stack):
    if callable(choices):
      my_choices = choices()
      if isinstance(my_choices, list): my_choices = dict([(x, x) for x in my_choices])
    else: my_choices = choices
    if long_list or ((long_list is None) and (len(my_choices) > 30)):
      return _LongEnumField(gui, master, o, attr, undo_stack, my_choices, value_2_enum, enum_2_value)
    else:
      return _ShortEnumField(gui, master, o, attr, undo_stack, my_choices, value_2_enum, enum_2_value)
  return _Field

class _EnumField(MultiGUIField):
  def __init__(self, gui, master, o, attr, undo_stack, choices, value_2_enum = None, enum_2_value = None):
    super(_EnumField, self).__init__(gui, master, o, attr, undo_stack)
    self.choices        = choices
    self.choice_keys    = choices.keys()
    self.choice_keys.sort()
    self.choice_2_index = dict([(choice, self.choice_keys.index(key)) for (key, choice) in self.choices.items()])
    self.value_2_enum   = value_2_enum
    self.enum_2_value   = enum_2_value
    
  def get_value(self):
    value = Field.get_value(self)
    if self.value_2_enum: value = self.value_2_enum(self.o, value)
    return value
  def set_value(self, enum):
    if self.enum_2_value: enum = self.enum_2_value(self.o, enum)
    Field.set_value(self, enum)
    
class _ShortEnumField(_EnumField): pass
class _LongEnumField (_EnumField): pass


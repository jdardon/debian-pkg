# -*- coding: utf-8 -*-

# undoredo.py
# Copyright (C) 2007 Jean-Baptiste LAMY -- jiba@tuxfamily.org
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


#from __future__ import with_statement

"""editobj2.undoredo -- A framework for automatic multiple undo/redo.

"""

__all__ = ["Stack", "UndoableOperation"] #, "AutomaticUndoableOperation"]

import editobj2.observe as observe

class Stack(object):
  def __init__(self, limit = 20):
    self.limit     = limit
    self.undoables = []
    self.redoables = []
    self._active_operation = None
    
#   def observe       (self, o): observe.observe       (o, self.listener)
#   def unobserve     (self, o): observe.unobserve     (o, self.listener)
#   def observe_tree  (self, o): observe.observe_tree  (o, self.listener)
#   def unobserve_tree(self, o): observe.unobserve_tree(o, self.listener)
  
  def listener(self, obj, type, new, old):
    if self._active_operation:
      self._active_operation.changes.append((obj, type, new, old))
      
  def can_undo(self):
    if self.undoables: return self.undoables[-1]
    return 0
  
  def can_redo(self):
    if self.redoables: return self.redoables[-1]
    return 0
  
  def undo(self):
    if not self.undoables: raise ValueError("No operation to undo!")
    undo = self.undoables.pop()
    opposite = undo.opposite()
    
  def redo(self):
    if not self.redoables: raise ValueError("No operation to redo!")
    redo = self.redoables.pop()
    opposite = redo.opposite()
    
  def clear(self):
    self.undoables = []
    self.redoables = []
    
  def __repr__(self):
    return "<%s, undoables:\n%s\n  redoables:\n%s\n>" % (
      self.__class__.__name__,
      "\n".join(["    %s" % repr(i) for i in self.undoables]),
      "\n".join(["    %s" % repr(i) for i in self.redoables]),
      )
    
stack = Stack()


class _Operation(object):
  def __init__(self, do_func, undo_func, name = "", stack = stack):
    self.do_func   = do_func
    self.undo_func = undo_func
    self.name      = name
    self.stack     = stack
    do_func()

  def __repr__(self):
    return "<%s '%s' do_func='%s' undo_func='%s'>" % (self.__class__.__name__, self.name, self.do_func, self.undo_func)
    
class UndoableOperation(_Operation):
  def __init__(self, do_func, undo_func, name = "", stack = stack):
    _Operation.__init__(self, do_func, undo_func, name, stack)
    stack.undoables.append(self)
    if len(self.stack.undoables) > self.stack.limit: del self.stack.undoables[0]
    observe.scan()
    
  def opposite(self):
    return _RedoableOperation(self.undo_func, self.do_func, self.name, self.stack)

  def coalesce_with(self, previous_undoable_operation):
    self.undo_func = previous_undoable_operation.undo_func
    previous_undoable_operation.stack.undoables.remove(previous_undoable_operation)
    
class _RedoableOperation(_Operation):
  def __init__(self, do_func, undo_func, name = "", stack = stack):
    _Operation.__init__(self, do_func, undo_func, name, stack)
    stack.redoables.append(self)
    observe.scan()
    
  def opposite(self):
    return UndoableOperation(self.undo_func, self.do_func, self.name, self.stack)


# class _AutomaticOperation(object):
#   def __init__(self, name = "", stack = stack):
#     self.name    = name
#     self.stack   = stack
#     self.changes = []
    
#   def start(self):
#     self.stack._active_operation = self
#     observe.scan()
#   __enter__ = start
  
#   def end(self):
#     observe.scan()
#     self.stack._active_operation = None
    
#   def __exit__(self, exc_type, exc_value, traceback): self.end()
    
#   def _do(self):
#     for obj, type, new, old in self.changes[::-1]:
#       if   type is object:
#         for attr, val in old.iteritems(): setattr(obj, attr, val)
#       elif type is list: list.__init__(obj, old)
#       elif type is set : set .__init__(obj, old)
#       elif type is dict: obj.clear(); dict.__init__(obj, old)
#       elif type == "__class__": obj.__class__ = old
#     observe.scan()
    
# class AutomaticUndoableOperation(_AutomaticOperation):
#   def end(self):
#     _AutomaticOperation.end(self)
#     if len(self.stack.undoables) > self.stack.limit: del self.stack.undoables[0]
#     self.stack.undoables.append(self)

#   def opposite(self):
#     redo = _AutomaticRedoableOperation(self.name)
#     redo.changes = [(obj, type, _copy(old), _copy(new)) for (obj, type, new, old) in self.changes[::-1]]
#     return redo
  
# class _AutomaticRedoableOperation(_AutomaticOperation):
#   def end(self):
#     _AutomaticOperation.end(self)
#     self.stack.redoables.append(self)
    
#   def opposite(self):
#     undo = AutomaticUndoableOperation(self.name)
#     undo.changes = [(obj, type, _copy(old), _copy(new)) for (obj, type, new, old) in self.changes[::-1]]
#     return undo
  
# def _copy(o):
#   if isinstance(o, dict): return o.copy()
#   if isinstance(o, list): return o[:]
#   if isinstance(o, set ): return set(o)
#   return o
  

# if __name__ == "__main__":
  
#   class Person(object):
#     def __init__(self, name): self.name = name

#   jiba = Person("Jiba")

#   stack.observe(jiba)

#   op = AutomaticUndoableOperation(stack)
#   op.start()
#   jiba.name = "Blam"
#   op.end()
  
#   print jiba.name
  
#   stack.undo()
  
#   print jiba.name
  
#   stack.redo()
  
#   print jiba.name
  
#   print stack.undoables, stack.redoables
  
#   op = AutomaticUndoableOperation(stack)
#   op.start()
#   jiba.name = "Marmoute"
#   op.end()
  
#   print jiba.name
#   stack.undo(); print jiba.name
#   stack.undo(); print jiba.name
  
#   stack.redo(); print jiba.name
#   stack.redo(); print jiba.name

#   print
#   jiba.name = "Jiba"
#   print jiba.name
#   def do_it():
#     jiba.name = "Kerdekel"
#   def undo_it():
#     jiba.name = "Jiba"
#   UndoableOperation(do_it, undo_it)
#   print jiba.name
#   stack.undo(); print jiba.name
#   stack.redo(); print jiba.name
  

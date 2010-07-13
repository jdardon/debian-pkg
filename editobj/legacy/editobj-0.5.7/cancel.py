# Songwrite
# Copyright (C) 2001-2002 Jean-Baptiste LAMY
#
# This program is free software. See README or LICENSE for the license terms.

"""Cancel -- A framework for multiple undo/redo.

"""

NUMBER_OF_CANCEL = 20

class CancelmentStack:
  def __init__(self, previous = None):
    self.closures = []
    self.previous = previous
    
  def append(self, closure):
    self.closures.append(closure)
  add_cancel = add_redo = append
  
  def prepend(self, closure):
    self.closures.insert(0, closure)
    
  def is_noop(self): return not self.closures
  
  def __call__(self):
    self.closures.reverse() # Operation must be undoed in the reverse order !!!
    for closure in self.closures: closure()
    
class RootCancelmentStack(CancelmentStack):
  def __init__(self):
    self.closures = []
    
  def append(self, closure):
    self.closures.append(closure)
    if len(self.closures) > NUMBER_OF_CANCEL: del self.closures[0]
    
  def prepend(self, closure):
    self.closures.insert(0, closure)
    
  def pop_and_call(self):
    if not self.closures: return 0
    closure = self.closures.pop()
    if isinstance(closure, CancelmentStack) and closure.is_noop(): return self.pop_and_call()
    else:
      closure()
      return 1
    
class Context:
  def __init__(self):
    self.cancels = self.cur_cancels = RootCancelmentStack()
    self.redos   = self.cur_redos   = RootCancelmentStack()
    self.redoing = 0
    
  def add_cancel(self, closure):
    self.cur_cancels.append(closure)
    #if (not self.redoing) and self.redos.closures:
    #  self.redos.closures *= 0
      
  def add_post_cancel(self, closure):
    self.cur_cancels.prepend(closure)
    
  def add_redo(self, closure):
    self.cur_redos.append(closure)
    
  def add_post_redo(self, closure):
    self.cur_redos.prepend(closure)
    
  def get_last_cancelable(self):
    if self.cancels.closures: return self.cancels.closures[-1]
    return None
  
  def cancel(self):
    self.push_redo()
    try: return self.cancels.pop_and_call()
    finally: self.pop_redo()
    
  def redo(self):
    self.redoing = 1
    self.push()
    try: return self.redos.pop_and_call()
    finally:
      self.pop()
      self.redoing = 0
      
  def push(self):
    new_stack = CancelmentStack(self.cur_cancels)
    self.add_cancel(new_stack)
    self.cur_cancels = new_stack
    
  def pop(self):
    if self.cur_cancels.is_noop():
      try: self.cancels.closures.remove(self.cur_cancels)
      except ValueError: pass
    self.cur_cancels = self.cur_cancels.previous
    
  def push_redo(self):
    new_stack = CancelmentStack(self.cur_redos)
    self.add_redo(new_stack)
    self.cur_redos = new_stack
    
  def pop_redo(self):
    if self.cur_redos.is_noop():
      try: self.redos.closures.remove(self.cur_redos)
      except ValueError: pass
    self.cur_redos = self.cur_redos.previous
    


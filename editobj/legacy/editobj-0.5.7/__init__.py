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

"""EditObj -- Display a Tkinter-based dialog box to edit any Python instance, list or dict.

This is what Java calls a "Bean Editor", but for Python :-)

In terms of MVC (Model View Controler), EditObj is a generic View coupled with a
universal Controler.

The module only provide the function edit(obj), that returns the Tk top-level window.
EditObj will edit all attributes and, for list or dict, all items.
The upper part of the window display the list/dict items in a hierarchical tree view, and the lower part lists all the edited instance's attributes.

An object can provide an __edit__(window) method, that will be called on edition, with the EditObj's window as argument. If it returns true, it is assumed that the edition is entirely done by the object itself.
If an object is edited as a child / item / component of another, __subedit__ will be called, with the EditObj's window as argument.
When the children of an object are made visible or invisible in the tree view, the object __editchildren__ method is called (if it has one) with the visibility (1 or 0).
An object can also provide a __wrapedit__() method, that returns a wrapper for the object. The wrapper will be edited instead of the object.

editobj.TRANSLATOR can be set to a translator function (such as the ones from the gettext module), if you want to translate the names of the properties.

Quick example :
>>> import editobj
>>> class C(list):
...   def __init__(self):
...     list.__init__(self)
...     self.x = 1
...     self.append("A string.")
...     self.append([1, 2, 3])
>>> toplevel = editobj.edit(C())
>>> toplevel.mainloop()"""

__all__ = ["edit"]

import sys, Tkinter
from UserList import UserList
from UserDict import UserDict

def edit(o, **kargs):
  from editobj.main import EditWindow
  return EditWindow(o, **kargs)


clipboard = None

EVAL_ENV = {}

_eval = eval
def eval(text, globals = EVAL_ENV, locals = EVAL_ENV):
  try:
    return _eval(text, globals, locals)
  except NotImplementedError: raise
  except:
    sys.excepthook(*sys.exc_info())
    print "Error ?", "-- consider input as a string."
    return text
  
def is_getset(o): return isinstance(o, property) or (type(o).__name__ == "getset_descriptor")
def attrs_of(obj):
  if hasattr(obj, "__dict__"): attrs = obj.__dict__.keys()
  else:                        attrs = []
  
  if hasattr(obj, "__members__"): attrs.extend(obj.__members__)
  
  klass = obj.__class__
  attrs.extend(filter(lambda attr: is_getset(getattr(klass, attr)), dir(klass)))
  return attrs
  

def editable(o):
  """Wrap o if needed (try to call o.__wrapedit__()). Return o itself if no wrapper is provided."""
  if hasattr(o, "__wrapedit__"): return o.__wrapedit__()
  return o

def in_hierarchy(item, hierarchy):
  """A recursive __contains__, for working with hierarchical tree.
The caller must assume that, if needed, item and hierarchy are wrapped (by _getEditedObject)."""
  items = custom._find_children(hierarchy)
  if items:
    for i in items:
      # Wrap i, if needed (already done for item and hierarchy).
      i = editable(i)
      if item == i: return 1
      if in_hierarchy(item, i): return 1
      


class MultiEdit(object):
  def __init__(self, objs):
    self.__dict__["_objs"] = objs
    
  def __observe__(self, func):
    from editobj.observe import observe
    for obj in self._objs: observe(obj, func)
    
  def __unobserve__(self, func):
    from editobj.observe import unobserve
    for obj in self._objs: unobserve(obj, func)
    
  def _get_members(self):
    attrs = []
    for obj in self._objs:
      for attr in attrs_of(obj):
        if not attr in attrs: attrs.append(attr)
    return attrs
  __members__ = property(_get_members)
  
  def __getattr__(self, attr):
    for obj in self._objs:
      if hasattr(obj, attr): return getattr(obj, attr)
    raise AttributeError, attr
  
  def __setattr__(self, attr, value):
    for obj in self._objs:
      if hasattr(obj, "set_" + attr): getattr(obj, "set_" + attr)(value)
      else:                           setattr(obj, attr, value)
      
import custom

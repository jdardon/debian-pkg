# EventObj
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

# This module is certainly my best hack ;-)
# It is nothing else than a sequence of hacks, from the beginning to the end !!!!!

"""EventObj -- Allow to add attribute-change, content-change or hierarchy-change event to any Python instance.

Provides the following functions (view their doc for more info):
  dumper_event(obj, attr, oldvalue, newvalue)
  addevent(obj, event)
  hasevent(obj[, event])
  removeevent(obj, event)
  addevent_rec(obj, event)
  removeevent_rec(obj, event)
And the following constant for addition/removal events:
  ADDITION
  REMOVAL

Events : An event is any callable object that take 4 parameters (= the listened instance, the changed attribute name, the new value, the old value).
After registration with addevent, it will be called just after any attribute is change on the instance.
You can add many events on the same instance, and use the same event many times.
An instance can implement __addevent__(event, copiable = 0), __hasevent__(event = None) and __removeevent__(event) to allow a custom event system.

Notice that the event is weakref'ed, so if it is no longer accessible, the event is silently removed.

Caution : As event management is performed by changing the class of the instance, you use eventobj with critical objects at your own risk... !

Quick example :
>>> from editobj.eventobj import *
>>> class C: pass
>>> c = C()
>>> def event(obj, attr, value, oldvalue):
...   print "c." + attr, "was", `oldvalue` + ", is now", `value`
>>> addevent(c, event)
>>> c.x = 1
c.x was None, is now 1

Addition/Removal events : if you add them to a list / UserList or a dict / UserDict, or a subclass, events are also called for addition or removal in the list/dict.
Addition or removal can be performed by any of the methods of UserList/UserDict (e.g. append, extend, remove, __setitem__,...)
In this case, name will be the ADDITION or REMOVAL constant, value the added object for a list and the key-value pair for a dict, and oldvalue None.

Quick example :
>>> from editobj.eventobj import *
>>> c = []
>>> def event(obj, attr, value, oldvalue):
...   if attr is ADDITION: # Only for list / dict
...     print `value`, "added to c"
...   elif attr is REMOVAL: # Only for list / dict
...     print `value`, "removed from c"
...   else:
...     print "c." + attr, "was", `oldvalue` + ", is now", `value`
>>> addevent(c, event)
>>> c.append(0)
0 added to c

Hierachy events : such events are used with UserList or UserDict, and are usefull to listen an entire hierarchy (e.g. a list that contains other lists that can contain other lists...).
The event apply to the registred instance, and any other item it contains, and so on if the list/dict is a deeper hierarchy.
If you want to automatically add or remove the event when the hierarchy change (addition or removal at any level), use a HierarchyEvent (see example below).

Quick example :
>>> from editobj.eventobj import *
>>> c = []
>>> def event(obj, attr, value, oldvalue):
...   if   attr is ADDITION:
...     print `value`, "added to", `obj`
...   elif attr is REMOVAL:
...     print `value`, "removed from", `obj`
>>> addevent_rec(c, event)
>>> c.append([])             # This sub-list was not in c when we add the event...
[] added to [[]] # [[]] is c
>>> c[0].append(12)          # ...but the hierarchical event has been automatically added !
12 added to [12] # [12] is c[0]
"""

import warnings
warnings.warn("editobj.eventobj is deprecated. Use the new editobj.observe module instead.", DeprecationWarning, stacklevel = 2)

__all__ = [
  "addevent",
  "hasevent",
  "removeevent",
  "addevent_rec",
  "removeevent_rec",
  "dumper_event",
  "ADDITION",
  "REMOVAL",
  ]

import sys, new, weakref, types
from UserList import UserList
from UserDict import UserDict


def to_list(obj):
  if isinstance(obj, list) or isinstance(obj, UserList): return obj
  if hasattr(obj, "children"):
    items = obj.children
    if callable(items): return items()
    return items
  if hasattr(obj, "items"):
    items = obj.items
    if callable(items): return items()
    return items
  if hasattr(obj, "__getitem__"): return obj
  return None

def to_dict(obj):
  if isinstance(obj, dict) or isinstance(obj, UserDict): return obj
  return None

def to_dict_or_list(obj):
  content = to_dict(obj) # Try dict...
  if content is None:
    content = to_list(obj) # Try list...
    if content is None: return None, None
    return list, content
  else:
    return dict, content
  
def to_content(obj):
  content = to_dict(obj) # Try dict...
  if content is None: return to_list(obj) or () # Try list...
  return content.values()


def dumper_event(obj, attr, value, old):
  """dumper_event -- an event that dump a stacktrace when called. Usefull for debugging !

dumper_event is the default value for add_event.
"""
  import traceback
  traceback.print_stack()
  
  if   attr is ADDITION: print "%s now contains %s." % (obj, value)
  elif attr is REMOVAL : print "%s no longer contains %s." % (obj, value)
  else:                  print "%s.%s was %s, is now %s." % (obj, attr, old, value)
  

def addevent(obj, event = dumper_event):
  """addevent(obj, event = dumper_event)
Add the given attribute-change event to OBJ. OBJ must be a class instance (old or new style) or a list / dict, and EVENT a function that takes 4 args: (obj, attr, value, old).
EVENT will be called when any attribute of obj will be changed; OBJ is the object, ATTR the name of the attribute, VALUE the new value of the attribute and OLD the old one.

EVENT defaults to the "dumper" event, which print each object modification.

Raise eventobj.NonEventableError if OBJ cannot support event.
"""

  event = _wrap_event(obj, event)
  
  try:
    obj.__addevent__(event)
  except:
    if hasattr(obj, "__dict__"):
      # Store the event and the old class of obj in an instance of _EventObj_stuff (a class we use to contain that).
      # Do that BEFORE we link the event (else we'll get a change event for the "_EventObj_stuff" attrib) !
      obj._EventObj_stuff = _EventObj_stuff(obj.__class__)
      
      # Change the class of the object.
      obj.__class__ = _create_class(obj, obj.__class__)
    else:
      # Change the class of the object.
      old_class     = obj.__class__
      obj.__class__ = _create_class(obj, obj.__class__)
      
      stuff_for_non_dyn_objs[id(obj)] = _EventObj_stuff(old_class)
    
    obj.__addevent__(event)
    
def hasevent(obj, event = None):
  """hasevent(obj[, event]) -> Boolean
Return wether the obj instance has the given event (or has any event, if event is None)."""
  return hasattr(obj, "__hasevent__") and obj.__hasevent__(event)
  
def removeevent(obj, event = dumper_event):
  """removeevent(obj, event = dumper_event)
Remove the given event from obj."""
  hasattr(obj, "__removeevent__") and obj.__removeevent__(event)
  
ADDITION   = "__added__"
REMOVAL = "__removed__"

NonEventableError = "NonEventableError"

# Private stuff :

# A dict to store the created classes.
#_classes = weakref.WeakKeyDictionary() # old-style class cannot be weakref'ed !
_classes = {}

# Create a with-event class for "clazz". the returned class is a "mixin" that will extends clazz and _EventObj (see below).
def _create_class(obj, clazz):
  try: return _classes[clazz]
  except:
    if hasattr(obj, "__dict__"):
      # The name of the new class is the same name of the original class (mimetism !)
      if   issubclass(clazz, list) or issubclass(clazz, UserList): cl = new.classobj(clazz.__name__, (_EventObj_List, _EventObj, clazz), {})
      elif issubclass(clazz, dict) or issubclass(clazz, UserDict): cl = new.classobj(clazz.__name__, (_EventObj_Dict, _EventObj, clazz), {})
      else:
        if issubclass(clazz, object):                              cl = new.classobj(clazz.__name__, (_EventObj, clazz), {})
        else:                                                      cl = new.classobj(clazz.__name__, (_EventObj_OldStyle, clazz), {})
        
    else:
      # list and dict were added in _classes at module initialization
      # Other types are not supported yet !
      raise NonEventableError, obj
    
    # Change also the module name.
    cl.__module__ = clazz.__module__
    _classes[clazz] = cl
    return cl
  

# A container for _EventObj attribs.
class _EventObj_stuff:
  def __init__(self, clazz):
    self.clazz  = clazz
    self.events = []
    
  def __call__(self, obj, attr, value, oldvalue):
    # Clone the list, since executing an event function may add or remove some events.
    for event in self.events[:]: event(obj, attr, value, oldvalue)
    
  def remove_event(self, event): self.events.remove(event)
  
  def has_event(self, event): return event in self.events
  
def _wrap_event(obj, event, hi = 0):
  if not isinstance(event, WrappedEvent):
    #dump = repr(event)
    
    try: obj = weakref.proxy(obj) # Avoid cyclic ref
    except TypeError: pass
    
    def callback(o):
      #print "attention !", dump, "est mourant !"
      # This seems buggy since it is called when some objects are being destructed
      try:
        ob = obj
        if ob:
          if removeevent and hasevent(ob, event): removeevent(ob, event)
      except: pass
    if hi:
      if type(event) is types.MethodType: event = WeakHiMethod(event, callback)
      else:                               event = WeakHiFunc  (event, callback)
    else:
      if type(event) is types.MethodType: event = WeakMethod(event, callback)
      else:                               event = WeakFunc  (event, callback)
      
  return event


class WrappedEvent: pass

class WeakFunc(WrappedEvent):
  def __init__(self, func, callback = None):
    if callback: self.func = weakref.ref(func, callback)
    else:        self.func = weakref.ref(func)
    
  def original(self): return self.func()
  
  def __call__(self, *args): self.func()(*args)
  
  def __eq__(self, other):
    return (self.func() == other) or (isinstance(other, WeakFunc) and (self.func() == other.func()))
  
  def __repr__(self): return "<WeakFunc for %s>" % self.func()
  
class WeakMethod(WrappedEvent):
  def __init__(self, method, callback = None):
    if callback: self.obj = weakref.ref(method.im_self, callback)
    else:        self.obj = weakref.ref(method.im_self)
    self.func = method.im_func
    
  def original(self):
    obj = self.obj()
    return new.instancemethod(self.func, obj, obj.__class__)
  
  def __call__(self, *args): self.func(self.obj(), *args)
  
  def __eq__(self, other):
    return ((type(other) is types.MethodType) and (self.obj() is other.im_self) and (self.func is other.im_func)) or (isinstance(other, WeakMethod) and (self.obj() is other.obj()) and (self.func is other.func))
  
  def __repr__(self): return "<WeakMethod for %s>" % self.original()
  
class HierarchyEvent:
  def __call__(self, obj, attr, value, oldvalue):
    if attr is ADDITION:
      try: 
        if isinstance(obj, _EventObj_List): addevent_rec(value, self.original())
        else:                               addevent_rec(value[1], self.original())
      except NonEventableError: pass
    elif attr is REMOVAL:
      try: 
        if isinstance(obj, _EventObj_List): removeevent_rec(value, self.original())
        else:                               removeevent_rec(value[1], self.original())
      except NonEventableError: pass
      
class WeakHiFunc(HierarchyEvent, WeakFunc):
  def __call__(self, obj, attr, value, oldvalue):
    HierarchyEvent.__call__(self, obj, attr, value, oldvalue)
    WeakFunc.__call__(self, obj, attr, value, oldvalue)
    
class WeakHiMethod(HierarchyEvent, WeakMethod):
  def __call__(self, obj, attr, value, oldvalue):
    HierarchyEvent.__call__(self, obj, attr, value, oldvalue)
    WeakMethod.__call__(self, obj, attr, value, oldvalue)
    

# Mixin class used as base class for any with-event class.
class _EventObj:
  stocks = []
  def __setattr__(self, attr, value):
    # Get the old value of the changing attrib.
    oldvalue = getattr(self, attr, None)
    if attr == "__class__":
      newclass = _create_class(self, value)
      self._EventObj_stuff.clazz.__setattr__(self, "__class__", newclass)
      self._EventObj_stuff.clazz = value
    else:
      # If a __setattr__ is defined for obj's old class, call it. Else, just set the attrib in obj's __dict__
      if hasattr(self._EventObj_stuff.clazz, "__setattr__"): self._EventObj_stuff.clazz.__setattr__(self, attr, value)
      else:                                                  self.__dict__[attr] = value
      
    # Comparison may fail
    try:
      if value == oldvalue: return
    except: pass
    
    # Call registered events, if needed
    for event in self._EventObj_stuff.events:
      event(self, attr, value, oldvalue)
      
  def __addevent__(self, event):
    self._EventObj_stuff.events.append(event)
    l = to_list(self)
    if (not l is None) and (not l is self): addevent(l, event)
  def __hasevent__(self, event = None):
    return (event is None) or (self._EventObj_stuff.has_event(event))
  def __removeevent__(self, event):
    self._EventObj_stuff.remove_event(event)
    l = to_list(self)
    if (not l is None) and (not l is self): removeevent(l, event)
    if len(self._EventObj_stuff.events) == 0: self.__restore__()
    
  def __restore__(self):
    # If no event left, reset obj to its original class.
    if hasattr(self._EventObj_stuff.clazz, "__setattr__"):
      self._EventObj_stuff.clazz.__setattr__(self, "__class__", self._EventObj_stuff.clazz)
    else:
      self.__class__ = self._EventObj_stuff.clazz
    # And delete the _EventObj_stuff.
    del self._EventObj_stuff
    
  # Called at pickling time
  def __getstate__(self):
    try:
      dict = self._EventObj_stuff.clazz.__getstate__(self)
      
      if dict is self.__dict__: dict = dict.copy()
    except: dict = self.__dict__.copy()
    
    try:
      del  dict["_EventObj_stuff"] # Remove what we have added.
      if   dict.has_key("children"): dict["children"] = list(dict["children"])
      elif dict.has_key("items"   ): dict["items"   ] = list(dict["items"   ])
    except: pass # Not a dictionary ??
    
    return dict
  
  def __reduce__(self):
    red = self._EventObj_stuff.clazz.__reduce__(self)
    if (not isinstance(red[1], list)) and (not isinstance(red[1], tuple)): return red
    
    def rec_check(t):
      if t is self.__class__: return self._EventObj_stuff.clazz
      if type(t) is tuple: return tuple(map(rec_check, t))
      return t
    
    if len(red) == 2: return red[0], tuple(map(rec_check, red[1]))
    else:             return red[0], tuple(map(rec_check, red[1])), red[2]

class _EventObj_OldStyle(_EventObj):
  def __deepcopy__(self, memo):
    if hasattr(self._EventObj_stuff.clazz, "__deepcopy__"):
      clone = self._EventObj_stuff.clazz.__deepcopy__(self, memo)
      if clone.__class__ is self.__class__:
        clone.__class__ = self._EventObj_stuff.clazz
      if hasattr(clone, "_EventObj_stuff"): del clone._EventObj_stuff
      return clone
    else:
      import copy
      
      if hasattr(self, '__getinitargs__'):
        args = self.__getinitargs__()
        copy._keep_alive(args, memo)
        args = copy.deepcopy(args, memo)
        return apply(self._EventObj_stuff.clazz, args)
      else:
        y = copy._EmptyClass()
        y.__class__ = self._EventObj_stuff.clazz
        memo[id(self)] = y
      if hasattr(self, '__getstate__'):
        state = self.__getstate__()
        copy._keep_alive(state, memo)
      else:
        state = self.__dict__
      state = copy.deepcopy(state, memo)
      if hasattr(y, '__setstate__'): y.__setstate__(state)
      else:                          y.__dict__.update(state)
      return y
    
  def __copy__(self):
    if hasattr(self._EventObj_stuff.clazz, "__copy__"):
      clone = self._EventObj_stuff.clazz.__copy__(self)
      if clone.__class__ is self.__class__:
        clone.__class__ = self._EventObj_stuff.clazz
      if hasattr(clone, "_EventObj_stuff"): del clone._EventObj_stuff
      return clone
    else:
      import copy
      
      if hasattr(self, '__getinitargs__'):
        args = self.__getinitargs__()
        return apply(self._EventObj_stuff.clazz, args)
      else:
        y = copy._EmptyClass()
        y.__class__ = self._EventObj_stuff.clazz
      if hasattr(self, '__getstate__'):
        state = self.__getstate__()
      else:
        state = self.__dict__
      if hasattr(y, '__setstate__'): y.__setstate__(state)
      else:                          y.__dict__.update(state)
      return y
    
    
class _EventObj_List(_EventObj):
  def __added__  (self, value): self._EventObj_stuff(self, ADDITION, value, None)
  def __removed__(self, value): self._EventObj_stuff(self, REMOVAL , value, None)
  
  def append(self, value):
    self._EventObj_stuff.clazz.append(self, value)
    self.__added__(value)
  def insert(self, before, value):
    self._EventObj_stuff.clazz.insert(self, before, value)
    self.__added__(value)
  def extend(self, list):
    self._EventObj_stuff.clazz.extend(self, list)
    for value in list: self.__added__(value)
    
  def remove(self, value):
    self._EventObj_stuff.clazz.remove(self, value)
    self.__removed__(value)
  def pop(self, index = -1):
    value = self._EventObj_stuff.clazz.pop(self, index)
    self.__removed__(value)
    return value
  
  def __setitem__(self, index, new):
    old = self[index]
    self._EventObj_stuff.clazz.__setitem__(self, index, new)
    self.__removed__(old)
    self.__added__  (new)
  def __delitem__(self, index):
    value = self[index]
    self._EventObj_stuff.clazz.__delitem__(self, index)
    self.__removed__(value)
  def __setslice__(self, i, j, slice):
    olds = self[i:j]
    self._EventObj_stuff.clazz.__setslice__(self, i, j, slice)
    for value in olds : self.__removed__(value)
    for value in slice: self.__added__  (value)
  def __delslice__(self, i, j):
    olds = self[i:j]
    self._EventObj_stuff.clazz.__delslice__(self, i, j)
    for value in olds : self.__removed__(value)
  def __iadd__(self, list):
    self._EventObj_stuff.clazz.__iadd__(self, list)
    for value in list: self.__added__(value)
    return self
  def __imul__(self, n):
    olds = self[:]
    self._EventObj_stuff.clazz.__imul__(self, n)
    if n == 0:
      for value in olds: self.__removed__(value)
    else:
      for value in olds * (n - 1): self.__added__(value)
    return self


class _EventObj_Dict(_EventObj):
  def __added__  (self, key, value): self._EventObj_stuff(self, ADDITION, (key, value), None)
  def __removed__(self, key, value): self._EventObj_stuff(self, REMOVAL , (key, value), None)

  def update(self, dict):
    old = {}
    for key, value in dict.items():
      if self.has_key(key): old[key] = value
    self._EventObj_stuff.clazz.update(self, dict)
    for key, value in old .items(): self.__removed__(key, value)
    for key, value in dict.items(): self.__added__  (key, value)
  def popitem(self):
    old = self._EventObj_stuff.clazz.popitem(self)
    self.__removed__(old[0], old[1])
    return old
  def clear(self):
    old = self.items()
    self._EventObj_stuff.clazz.clear(self)
    for key, value in old: self.__removed__(key, value)

  def __setitem__(self, key, new):
    if self.has_key(key):
      old = self[key]
      self._EventObj_stuff.clazz.__setitem__(self, key, new)
      self.__removed__(key, old)
    else:
      self._EventObj_stuff.clazz.__setitem__(self, key, new)
    self.__added__(key, new)
  def __delitem__(self, key):
    value = self[key]
    self._EventObj_stuff.clazz.__delitem__(self, key)
    self.__removed__(key, value)
    
# EventObj class for plain list (e.g. []) and plain dict :

# EventObj stuff is not stored in the object's dict (because no such dict...)
# but in this dictionary :
#stuff_for_non_dyn_objs = weakref.WeakKeyDictionary()
stuff_for_non_dyn_objs = {}

if sys.version_info[:2] == (2, 2):
  class _EventObj_PlainList(_EventObj_List, list):
    __slots__ = []
    
    def _get_EventObj_stuff(self): return stuff_for_non_dyn_objs[id(self)]
    def _set_EventObj_stuff(self, stuff): stuff_for_non_dyn_objs[id(self)] = stuff
    _EventObj_stuff = property(_get_EventObj_stuff, _set_EventObj_stuff)

    def __restore__(self):
      # If no event left, delete the _EventObj_stuff and reset obj to its original class.
      # Bypass the _EventObj.__setattr__ (it would crash since _EventObj_stuff is no longer available after the class change)
      self._EventObj_stuff.clazz.__setattr__(self, "__class__", self._EventObj_stuff.clazz)
      del stuff_for_non_dyn_objs[id(self)]

    def __getstate__(self): return None
    
  _classes[list] = _EventObj_PlainList
  
  class _EventObj_PlainDict(_EventObj_Dict, dict):
    __slots__ = []

    def _get_EventObj_stuff(self): return stuff_for_non_dyn_objs[id(self)]
    def _set_EventObj_stuff(self, stuff): stuff_for_non_dyn_objs[id(self)] = stuff
    _EventObj_stuff = property(_get_EventObj_stuff, _set_EventObj_stuff)

    def __restore__(self):
      # If no event left, delete the _EventObj_stuff and reset obj to its original class.
      # Bypass the _EventObj.__setattr__ (it would crash since _EventObj_stuff is no longer available after the class change)
      self._EventObj_stuff.clazz.__setattr__(self, "__class__", self._EventObj_stuff.clazz)
      del stuff_for_non_dyn_objs[id(self)]

    def __getstate__(self): return None

  _classes[dict] = _EventObj_PlainDict
  
else:
  class _EventObj_PlainList(list):
    __slots__ = []

    def _get_EventObj_stuff(self): return stuff_for_non_dyn_objs[id(self)]
    def _set_EventObj_stuff(self, stuff): stuff_for_non_dyn_objs[id(self)] = stuff
    _EventObj_stuff = property(_get_EventObj_stuff, _set_EventObj_stuff)

    def __restore__(self):
      # If no event left, delete the _EventObj_stuff and reset obj to its original class.
      # Bypass the _EventObj.__setattr__ (it would crash since _EventObj_stuff is no longer available after the class change)
      self._EventObj_stuff.clazz.__setattr__(self, "__class__", self._EventObj_stuff.clazz)
      del stuff_for_non_dyn_objs[id(self)]

    def __getstate__(self): return None

  # HACK !!!
  # The _EventObj_List base is not declared in the class, but added later.
  # This prevent the _EventObj_PlainList class to be based on object,
  # and e.g. to be allowed a weaklist.

  _EventObj_PlainList.__bases__ = (_EventObj_List, list)

  _classes[list] = _EventObj_PlainList

  class _EventObj_PlainDict(dict):
    __slots__ = []

    def _get_EventObj_stuff(self): return stuff_for_non_dyn_objs[id(self)]
    def _set_EventObj_stuff(self, stuff): stuff_for_non_dyn_objs[id(self)] = stuff
    _EventObj_stuff = property(_get_EventObj_stuff, _set_EventObj_stuff)

    def __restore__(self):
      # If no event left, delete the _EventObj_stuff and reset obj to its original class.
      # Bypass the _EventObj.__setattr__ (it would crash since _EventObj_stuff is no longer available after the class change)
      self._EventObj_stuff.clazz.__setattr__(self, "__class__", self._EventObj_stuff.clazz)
      del stuff_for_non_dyn_objs[id(self)]

    def __getstate__(self): return None

  # HACK strikes again !

  _EventObj_PlainDict.__bases__ = (_EventObj_Dict, dict)

  _classes[dict] = _EventObj_PlainDict


# Hierarchy stuff :

def addevent_rec(obj, event = dumper_event):
  """addevent_rec(obj, event = dumper_event)
Add event for obj, like addevent, but proceed recursively in all the hierarchy : if obj is a UserList/UserDict, event will be added to each instance obj contains, recursively.
If the hierarchy is changed, the newly added items will DO have the event, and the removed ones will no longuer have it."""
  if not hasevent(obj, event): # Avoid problem with cyclic list/dict
    # Wrap event in a hierarchy event
    if not isinstance(event, HierarchyEvent): wevent = _wrap_event(obj, event, 1)
    
    addevent(obj, wevent)
    
    for o in to_content(obj):
      try: addevent_rec(o, event)
      except NonEventableError: pass
      
def removeevent_rec(obj, event = dumper_event):
  """removeevent_rec(obj, event = dumper_event)
Remove event for obj, like removeevent, but proceed recursively."""
  if hasevent(obj, event): # Avoid problem with cyclic list/dict
    removeevent(obj, event)
    
    for o in to_content(obj):
      if isinstance(o, _EventObj): removeevent_rec(o, event)
      
def change_class(obj, newclass):
  """Change the class of OBJ to NEWCLASS, but keep the events it may have."""
  events = obj._EventObj_stuff.events[:]
  for event in events: removeevent(obj, event)
  obj.__class__ = newclass
  for event in events: addevent(obj, event)
  

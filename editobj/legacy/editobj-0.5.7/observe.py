# observe.py
# Copyright (C) 2003 Jean-Baptiste LAMY -- jiba@tuxfamily
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

"""editobj.observe -- Observation framework

observe(obj, listener) registers listener as a listener for obj; when obj is modified,
listener will be called (asynchronously). obj can be a Python instance (old-style or
new-style), a list or a dictionary. The listener is a function of the form:

def my_listener(obj, type, new, old):
  ...

where obj is the modified object, type is the type of the modification, and old and new
are the old and new values. Type can be:
  
  - object (the Python root class): one or more attributes have changed on obj. old and
new are the old and new attribute dictionary of obj (this dictionary includes attributes
in obj.__dict__, but also Python's property and C-level getset).
If you want to know which attribute has changed, use dictdiff on new and old (see the
diffdict function docstring).
  
  - list : one or more addition / deletion have occured on obj (which is a list). new
and old are the new and old list content of obj.

  - dict : one or more assignment / deletion have occured on obj (which is a mapping).
new and old are the new and old dictionary values.

  - "__class__" : the class of obj has changed. new and old are the new and old classes.

Before all, you need to start the observer daemon, either in a new thread by calling
start_observing(), or in the Tkinter thread with start_observing_tk(). You can also
call scan() yourself when you want to check for change.

This module is the successor of the deprecated eventobj; it is much much much cleaner.

Quick example :
>>> from editobj.observe import *
>>> start_observing()
>>> class C: pass
...
>>> c = C()
>>> def listener(obj, type, new, old):
...   if type is object:
...     for (attr, newvalue, oldvalue) in diffdict(new, old):
...       print "c.%s was %s, is now %s" % (attr, oldvalue, newvalue)
>>> observe(c, listener)
>>> c.x = 1
c.x was None, is now 1

See observe_tree and unobserve_tree for observing nested list and / or dict structures."""

__all__ = [
  "observe", "isobserved", "unobserve",
  "observe_tree", "unobserve_tree",
  "start_observing", "start_observing_tk", "stop_observing", "scan",
  "diffdict",
  ]

from weakref import ref

observed_lists   = {}
observed_dicts   = {}
observed_objects = {}

class_to_properties = {}

PROPERTY_TYPE_NAMES = ("property", "getset_descriptor")

def observe(object, listener):
  """observe(object, listener)

Registers LISTENER as a listener of OBJECT. When OBJECT will be changed, LISTENER will
be called (asynchronously).
See the module docstrings for more info about what argument receives a listener"""
  if hasattr(object, "__observe__"): object.__observe__(listener)
  
  i = id(object)
  
  if   isinstance(object, list):
    observation = observed_lists.get(i)
    if observation: observation.listeners.append(listener)
    else:
      observation = observed_lists[i] = Observation([listener], list(object))
      observation.object = object
      
  elif isinstance(object, dict):
    observation = observed_dicts.get(i)
    if observation: observation.listeners.append(listener)
    else:
      observation = observed_dicts[i] = Observation([listener], dict(object))
      observation.object = object
      
  if hasattr(object, "__dict__"):
    observation = observed_objects.get(i)
    
    if observation: observation.listeners.append(listener)
    else:
      observation = observed_objects[i] = Observation([listener], None)
      try:    observation.object = weakref.ref(object)
      except: observation.object = object
      observation.old_class = object.__class__
      
      # Checks for property and/or C level getset
      props = observation.props = class_to_properties.get(object.__class__)
      if props is None:
        props = observation.props = class_to_properties[object.__class__] = filter(lambda attr: type(getattr(object.__class__, attr)).__name__ in PROPERTY_TYPE_NAMES, dir(object.__class__))
      if props:
        observation.old = dict(map(lambda prop: (prop, getattr(object, prop, None)), observation.props))
        observation.old.update(object.__dict__)
      else: observation.old = object.__dict__.copy()
          
def isobserved(object, listener = None):
  """isobserved(object, listener = None)

Return true if LISTENER is observing OBJECT. If listener is None, returns the list
of observation for OBJECT."""
  
  i = id(object)
  observation = observed_lists.get(i) or observed_dicts.get(i) or (hasattr(object, "__dict__") and observed_objects.get(i))
  
  if listener: return observation and (listener in observation.listeners)
  else:        return observation and observation.listeners
  
def unobserve(object, listener = None):
  """unobserve(object, listener = None)

Unregisters the listener LISTENER for OBJECT. If LISTENER is not listening OBJECT,
nothing is done. If LISTENER is None, unregisters *all* listener on OBJECT."""
  
  if hasattr(object, "__unobserve__"): object.__unobserve__(listener)
  
  i = id(object)
  if listener:
    if   isinstance(object, list):
      observation = observed_lists.get(i)
      if observation:
        try: observation.listeners.remove(listener)
        except ValueError: pass
        if not observation.listeners: del observed_lists[i]
        
    elif isinstance(object, dict):
      observation = observed_dicts.get(i)
      if observation:
        try: observation.listeners.remove(listener)
        except ValueError: pass
        if not observation.listeners: del observed_dicts[i]
        
    if hasattr(object, "__dict__"):
      observation = observed_objects.get(i)
      if observation:
        try: observation.listeners.remove(listener)
        except ValueError: pass
        if not observation.listeners: del observed_objects[i]
        
        if observation.content_attr: unobserve(getattr(object, observation.content_attr), listener)
        
  else:
    if   observed_lists  .get(object): del observed_lists  [i]
    elif observed_dicts  .get(object): del observed_dicts  [i]
    if   observed_objects.get(object): del observed_objects[i]
    
class Observation:
  content_attr = ""
  def __init__(self, listeners, old):
    self.listeners = listeners
    self.old       = old
    
def scan():
  """scan()

Checks for changes in listened objects, and calls the corresponding listeners if needed."""
  
  for i, observation in observed_lists.items():
    if observation.old != observation.object:
      for listener in observation.listeners: listener(observation.object, list, observation.object, observation.old)
      observation.old = list(observation.object)
      
  for i, observation in observed_dicts.items():
    if observation.old != observation.object:
      for listener in observation.listeners: listener(observation.object, dict, observation.object, observation.old)
      observation.old = dict(observation.object)
      
  for i, observation in observed_objects.items():
    if type(observation.object) is ref: obj = observation.object()
    else:                               obj = observation.object
    
    if observation.props:
      new_dict = dict(map(lambda prop: (prop, getattr(obj, prop, None)), observation.props))
      new_dict.update(obj.__dict__)
      
      if observation.old != new_dict:
        for listener in observation.listeners: listener(obj, object, new_dict, observation.old)
        observation.old = new_dict
    else:
      if observation.old != obj.__dict__:
        for listener in observation.listeners: listener(obj, object, obj.__dict__, observation.old)
        observation.old = obj.__dict__.copy()
        
    if not observation.old_class is obj.__class__:
      for listener in observation.listeners: listener(obj, "__class__", obj.__class__, observation.old_class)
      observation.old_class = obj.__class__
      
SCANNING = 0

def _scan_loop(freq):
  from time import sleep
  while SCANNING:
    scan()
    sleep(freq)
    
def start_observing(freq = 0.2):
  """start_observing(freq = 0.2)

Starts the observer daemon. This thread calls scan() repetitively, each FREQ seconds."""
  
  global SCANNING
  import thread
  SCANNING = 1
  thread.start_new_thread(_scan_loop, (freq,))
  
def start_observing_tk(freq = 0.2):
  """start_observing_tk(freq = 0.2)

Starts the observer daemon in the Tkinter thread. This thread calls scan() repetitively,
each FREQ seconds."""
  
  global SCANNING
  SCANNING = 1
  _start_observing_tk(int(freq * 1000.0))
  
def _start_observing_tk(freq):
  from Tkinter import _default_root as tk
  scan()
  if SCANNING: tk.after(freq, _start_observing_tk2, freq)
  
def _start_observing_tk2(freq):
  from Tkinter import _default_root as tk
  tk.after_idle(_start_observing_tk, freq)
  
def stop_observing():
  """stop_observing()

Stops the observer daemon (started by start_observing() or start_observing_tk())."""
  
  SCANNING = 0


def diffdict(new, old):
  """diffdict(new, old) -> [(key, new_value, old_value),...]

Returns the differences between two dictionaries.
In case of addition or deletion, old or new values are None."""
  changes = []
  
  for key, val in old.iteritems():
    new_val = new.get(key, Ellipsis)
    if   new_val is Ellipsis: changes.append((key, None, val))
    elif new_val != val:      changes.append((key, new_val, val))
    
  for key, val in new.iteritems():
    old_val = old.get(key, Ellipsis)
    if old_val is Ellipsis: changes.append((key, val, None))
    
  return changes


import custom

def observe_tree(object, listener):
  """observe_tree(object, listener)

Observes OBJECT with LISTENER, as well as any item in OBJECT (if OBJECT is a list, a dict,
or have a "children" or "items" attribute / method). Items added to or removed from OBJECT
or one of its items are automatically observed or unobserved.
Although called "observe_tree", it works with any nested structure of lists and dicts,
including cyclic ones.

You must use unobserve_tree to remove the listener."""

  _observe_tree(object, _TreeListener(object, listener))
  
def _observe_tree(object, listener):
  if not isobserved(object, listener): # Avoid troubles with cyclic list / dict
    observe(object, listener)
    
    children = custom._find_children(object)
    if not children is None:
      if not children is object: observe(children, listener)
      for item in children: _observe_tree(item, listener)
      
def unobserve_tree(object, listener):
  """unobserve_tree(object, listener)

Unregisters the tree listener LISTENER for OBJECT."""
  
  if isobserved(object, listener): # Avoid troubles with cyclic list / dict
    unobserve(object, listener)
    
    children = custom._find_children(object)
    if not children is None:
      if not children is object: unobserve(children, listener)
      for item in children: unobserve_tree(item, listener)
      
class _TreeListener:
  def __init__(self, object, listener):
    self.object   = object
    self.listener = listener
    
  def __eq__(self, other): return other == self.listener
  
  def __call__(self, object, type, new, old):
    if type is list:
      for item in old:
        if not item in new: unobserve_tree(item, self)
        
      for item in new:
        if not item in old: _observe_tree(item, self)
        
    self.listener(object, type, new, old)

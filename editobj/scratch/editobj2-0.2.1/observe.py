# -*- coding: utf-8 -*-

# observe.py
# Copyright (C) 2003-2008 Jean-Baptiste LAMY -- jiba@tuxfamily.org
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
  "start_scanning", "start_scanning_tk", "start_scanning_gtk", "stop_scanning", "scan",
  "diffdict",
  ]

from weakref import ref

_observed_seqs    = {}
_observed_objects = {}

_class_2_properties = {}
def _get_class_properties(klass):
  props = _class_2_properties.get(klass)
  if props is None:
    props = _class_2_properties[klass] = [attr for attr in dir(klass) if (not attr in _IGNORED_ATTRS) and (type(getattr(klass, attr)).__name__ in PROPERTY_TYPE_NAMES)]
  return props
  

PROPERTY_TYPE_NAMES = ("property", "getset_descriptor")
_IGNORED_ATTRS = set(["__weakref__"])

def observe(o, listener):
  """observe(o, listener)

Registers LISTENER as a listener of O. When O will be changed, LISTENER will
be called (asynchronously).
See the module docstrings for more info about what argument receives a listener"""
  if hasattr(o, "__observe__"): o.__observe__(listener)
  
  i = id(o)
  
  observation = _observed_seqs.get(i)
  if observation: observation.listeners.append(listener)
  else:
    if   isinstance(o, list): _observed_seqs[i] = ListObservation(o, [listener])
    elif isinstance(o, set ): _observed_seqs[i] = SetObservation (o, [listener])
    elif isinstance(o, dict): _observed_seqs[i] = DictObservation(o, [listener])
    
  if hasattr(o, "__dict__"):
    observation = _observed_objects.get(i)
    if observation: observation.listeners.append(listener)
    else:           observation = _observed_objects[i] = ObjectObservation(o, [listener])
    
def isobserved(o, listener = None):
  """isobserved(o, listener = None)

Return true if LISTENER is observing O. If listener is None, returns the list
of listeners for O."""
  
  i = id(o)
  observation = _observed_seqs.get(i) or (hasattr(o, "__dict__") and _observed_objects.get(i))
  
  if listener: return observation and (listener in observation.listeners)
  else:        return observation and observation.listeners
  
def unobserve(o, listener = None):
  """unobserve(o, listener = None)

Unregisters the listener LISTENER for O. If LISTENER is not listening O,
nothing is done. If LISTENER is None, unregisters *all* listeners on O."""
  
  if hasattr(o, "__unobserve__"): o.__unobserve__(listener)
  
  i = id(o)
  if listener:
    observation = _observed_seqs.get(i)
    if observation:
      try: observation.listeners.remove(listener)
      except ValueError: pass
      if not observation.listeners: del _observed_seqs[i]
      
    if hasattr(o, "__dict__"):
      observation = _observed_objects.get(i)
      if observation:
        try: observation.listeners.remove(listener)
        except ValueError: pass
        if not observation.listeners: del _observed_objects[i]
        
  else:
    if   _observed_seqs   .has_key(i): del _observed_seqs   [i]
    if   _observed_objects.has_key(i): del _observed_objects[i]
    

class Observation(object):
  def __init__(self, o, listeners):
    self.object    = o
    self.listeners = listeners
    self.old       = self.current_value()

class ListObservation(Observation):
  type = list
  def current_value(self): return list(self.object)
  
class SetObservation(Observation):
  type = set
  def current_value(self): return set(self.object)
  
class DictObservation(Observation):
  type = dict
  def current_value(self): return dict(self.object)
  
class ObjectObservation(Observation):
  def __init__(self, o, listeners):
    self.listeners = listeners
    self.props     = _get_class_properties(o.__class__)
    self.old       = self.current_value(o)
    self.old_class = o.__class__
    try:    self.object = weakref.ref(o)
    except: self.object = o
    
  def current_value(self, o):
    if self.props:
      new = dict([(prop, getattr(o, prop, None)) for prop in self.props])
      new.update(o.__dict__)
      return new
    else: return o.__dict__.copy()
    

    
def scan():
  """scan()

Checks for changes in listened objects, and calls the corresponding listeners if needed."""
  for i, observation in _observed_seqs.items():
    if observation.old != observation.object:
      for listener in observation.listeners[:]: listener(observation.object, observation.type, observation.object, observation.old)
      observation.old = observation.current_value()
      
  for i, observation in _observed_objects.items():
    if type(observation.object) is ref:
      o = observation.object()
      if o is None:
        del _observed_objects[i]
        continue
    else: o = observation.object
    
    if observation.props:
      new = observation.current_value(o)
      
      if observation.old != new:
        for listener in observation.listeners[:]: listener(o, object, new, observation.old)
        observation.old = new
    else:
      if observation.old != o.__dict__:
        for listener in observation.listeners[:]: listener(o, object, o.__dict__, observation.old)
        observation.old = observation.current_value(o)
        
    if not observation.old_class is o.__class__:
      for listener in observation.listeners[:]: listener(o, "__class__", o.__class__, observation.old_class)
      observation.old_class = o.__class__
      
SCANNING = 0

def _scan_loop(freq):
  from time import sleep
  while SCANNING:
    scan()
    sleep(freq)
    
def start_scanning(freq = 0.2):
  """start_scanning(freq = 0.2)

Starts the observer daemon. This thread calls scan() repetitively, each FREQ seconds."""
  
  global SCANNING
  import thread
  SCANNING = 1
  thread.start_new_thread(_scan_loop, (freq,))


def start_scanning_gui(freq = 0.2):
  """start_scanning_gui(freq = 0.2)

Starts the observer daemon in the GUI thread. It calls start_scanning_tk or start_scanning_gtk,
according to the current GUI (i.e. editobj2.GUI)."""
  import editobj2
  if   editobj2.GUI == "Tk"    : start_scanning_tk()
  elif editobj2.GUI == "Gtk"   : start_scanning_gtk()
  elif editobj2.GUI == "Qt"    : start_scanning_qt()
  elif editobj2.GUI == "Qtopia": start_scanning_qt()
  

def start_scanning_tk(freq = 0.2):
  """start_scanning_tk(freq = 0.2)

Starts the observer daemon in the Tkinter thread. This thread calls scan() repetitively,
each FREQ seconds."""
  
  global SCANNING
  SCANNING = 1
  _start_scanning_tk(int(freq * 1000.0))
  
def _start_scanning_tk(freq):
  from Tkinter import _default_root as tk
  scan()
  if SCANNING: tk.after(freq, _start_scanning_tk2, freq)
  
def _start_scanning_tk2(freq):
  from Tkinter import _default_root as tk
  tk.after_idle(_start_scanning_tk, freq)

  
def start_scanning_gtk(freq = 0.2):
  """start_scanning_gtk(freq = 0.2)

Starts the observer daemon in the GTK thread. This thread calls scan() repetitively,
each FREQ seconds."""
  
  global SCANNING
  SCANNING = 1
  import gobject
  gobject.timeout_add(int(freq * 1000.0), _start_scanning_gtk)
  
def _start_scanning_gtk():
  scan()
  return SCANNING


def start_scanning_qt(freq = 0.2):
  """start_scanning_qt(freq = 0.2)

Starts the observer daemon in the Qt thread. This thread calls scan() repetitively,
each FREQ seconds."""
  
  global SCANNING
  SCANNING = 1
  import qt
  if qt.QApplication.startingUp():
    import sys, editobj2
    if   editobj2.GUI == "Qt": qt.app = qt.QApplication(sys.argv)
    elif editobj2.GUI == "Qtopia":
      import qtpe
      qt.app = qtpe.QPEApplication(sys.argv)
      
  timer = start_scanning_qt.timer = qt.QTimer(None)
  timer.start(freq * 1000, 0)
  timer.connect(timer, qt.SIGNAL("timeout()"), scan)

def stop_scanning():
  """stop_scanning()

Stops the observer daemon (started by start_scanning(), start_scanning_tk(), start_scanning_gtk(),...)."""
  
  SCANNING = 0


def diffdict(new, old, inexistent_value = None):
  """diffdict(new, old) -> [(key, new_value, old_value),...]

Returns the differences between two dictionaries.
In case of addition or deletion, old or new values are None."""
  changes = []
  
  for key, val in old.iteritems():
    new_val = new.get(key, Ellipsis)
    if   new_val is Ellipsis: changes.append((key, inexistent_value, val))
    elif new_val != val:      changes.append((key, new_val, val))
    
  for key, val in new.iteritems():
    old_val = old.get(key, Ellipsis)
    if old_val is Ellipsis: changes.append((key, val, inexistent_value))
    
  return changes


def find_all_children(o):
  if   isinstance(o, list): l = o
  elif isinstance(o, set) or isinstance(o, tuple) or isinstance(o, frozenset): l = list(o)
  elif isinstance(o, dict): l = o.keys() + o.values()
  else:                     l = []
  if   hasattr(o, "__dict__"): l += _get_class_properties(o.__class__) + o.__dict__.values()
  return l

def observe_tree(o, listener, find_children = find_all_children):
  """observe_tree(o, listener)

Observes O with LISTENER, as well as any item in O (if O is a list, a dict,
or have a "children" or "items" attribute / method). Items added to or removed from O
or one of its items are automatically observed or unobserved.
Although called "observe_tree", it works with any nested structure of lists and dicts,
including cyclic ones.

You must use unobserve_tree to remove the listener."""
  _observe_tree(o, _TreeListener(o, listener, find_children))
  
def _observe_tree(o, listener):
  if not isobserved(o, listener): # Avoid troubles with cyclic list / dict
    observe(o, listener)
    
    children = listener.find_children(o)
    for child in children:
      _observe_tree(child, listener)
      
def unobserve_tree(o, listener, find_children = find_all_children, already = None):
  """unobserve_tree(o, listener)

Unregisters the tree listener LISTENER for O."""
  if already is None: already = set()
  
  if not id(o) in already:
    already.add(id(o))
    unobserve(o, listener)
  #if isobserved(o, listener): # Avoid troubles with cyclic list / dict
  #  unobserve(o, listener)
    
  children = find_children(o)
  for child in children:
    if not id(child) in already:
      unobserve_tree(child, listener, find_children, already)
      
class _TreeListener:
  def __init__(self, o, listener, find_children = find_all_children):
    self.object        = o
    self.listener      = listener
    self.find_children = find_children
    
  def __eq__(self, other): return other == self.listener
  
  def __call__(self, o, type, new, old):
    if   type is list:
      for item in old:
        if not item in new: unobserve_tree(item, self)
        
      for item in new:
        if not item in old: _observe_tree (item, self)
        
    elif (type is dict) or (type is object):
      _new = new.values()
      _old = old.values()
      for item in _old:
        if not item in _new: unobserve_tree(item, self)
        
      for item in _new:
        if not item in _old: _observe_tree (item, self)

      
    self.listener(o, type, new, old)


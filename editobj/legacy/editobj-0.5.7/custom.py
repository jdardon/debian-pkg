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

from editobj import MultiEdit, EVAL_ENV

# Internationalization -- Set here your translator func
# (e.g. the "_" func from the GetText module)

TRANSLATOR = lambda key: key


# Editors customization

_attr_editors = {"children" : {None : None}}

def register_attr(attr, editor, clazz = None):
  """register_attr(attr, editor, clazz = None)

Registers EDITOR as the editor for atrribute ATTR of class CLAZZ, or for any class if
CLAZZ is None. EDITOR can be either a Tk widget subclass of editobj.editor.Editor, or
None to hide the attribute.
MRO is used in order to allow subclasses to use the editor registered for their mother."""
  
  for_attr = _attr_editors.get(attr)
  if for_attr: for_attr[clazz] = editor
  else:        _attr_editors[attr] = { clazz : editor }
  
def _find_editor(obj, attr):
  if isinstance(obj, MultiEdit): clazz = obj._objs[0].__class__
  else:                          clazz = obj.__class__
  
  for_attr = _attr_editors.get(attr)
  if for_attr:
    if (len(for_attr) == 1) and for_attr.has_key(None): return for_attr[None]
    
    for clazz in (getattr(clazz, "__mro__", None) or _mro(clazz)):
      editor = for_attr.get(clazz, 0)
      if not editor is 0: return editor
      
    if for_attr.has_key(None): return for_attr[None]

  if attr[0] == "_": return None # Hidden
  import editobj.editor as editor
  val = getattr(obj, attr)
  if isinstance(val, int  ): return editor.IntEditor
  if isinstance(val, float): return editor.FloatEditor
  if isinstance(val, basestring):
    if "\n" in val: return editor.TextEditor
    return editor.StringEditor
  return editor.EntryEditor


# Children customization

_children_attrs = {None : [("children", "insert", "__delitem__")]}

def register_children_attr(attr, insert = "insert", del_ = "__delitem__", clazz = None):
  """register_children_attr(attr, insert = "insert", del_ = "__delitem__", clazz = None)

Registers ATTR as an attribute that can act as the "content" or the "children"
of an object of class CLAZZ (or any class if None). If ATTR is None, the object is used
as its own list of children (automatically done for list / dict subclasses).
INSERT and DEL_ are the names of the methods called for inserting and deleting items.
INSERT can accept 2 arguments (as list.insert) or only one (as list.append), if you
don't care the children's order. Default values for INSERT and DEL_ are OK for lists;
for dicts, use INSERT = "__setitem__". EditObj will display these items in the tree view.
Only one such attribute can be set for a given class (several are accepted for None).
MRO is used in order to allow subclasses to use the children attribute registered for
their mother.
By default, "children" is considered for any class, and instances of classes
that inherits from list or dict are their own children."""
  
  if clazz: _children_attrs[clazz] = (attr, insert, del_)
  else:     _children_attrs[None].append((attr, insert, del_))
  
def _find_children(obj):
  if isinstance(obj, MultiEdit): clazz = obj._objs[0].__class__
  else:                          clazz = obj.__class__
  
  if issubclass(clazz, list) or issubclass(clazz, dict): return obj
  
  for clazz in (getattr(clazz, "__mro__", None) or _mro(clazz)):
    children_attrs = _children_attrs.get(clazz, None)
    if children_attrs:
      if children_attrs[0]:
        children = getattr(obj, children_attrs[0])
        if callable(children): return children()
        return children
      else: return obj
    
  for (children_attr, insert, del_) in _children_attrs[None]:
    children = getattr(obj, children_attr, None)
    
    if not children is None:
      if callable(children): return children()
      return children

def _find_children_insert_remove(obj):
  if isinstance(obj, MultiEdit): clazz = obj._objs[0].__class__
  else:                          clazz = obj.__class__
  
  if   issubclass(clazz, list): return obj, obj.insert,      obj.__delitem__
  elif issubclass(clazz, dict): return obj, obj.__setitem__, obj.__delitem__
  
  for clazz in (getattr(clazz, "__mro__", None) or _mro(clazz)):
    children_attrs = _children_attrs.get(clazz)
    if children_attrs:
      children_attr, insert, del_ = children_attrs
      if children_attr:
        children = getattr(obj, children_attr)
        if callable(children): return children()
      else: children = obj
      break
  else: 
    for (children_attr, insert, del_) in _children_attrs[None]:
      children = getattr(obj, children_attr, None)
      if not children is None:
        if callable(children): return children()
        break
    else: return None, None, None
  
  return children, getattr(obj, insert, None) or getattr(children, insert), getattr(obj, del_, None) or getattr(children, del_)


# Methods customization

_methods = {}

def register_method(method, clazz, *args_editor):
  """register_method(method, clazz, *args_editor)

Registers METHOD as a method that must be displayed in EditObj for instance of CLAZZ.
METHOD can be either a method name (a string), or a function (in this case, it is not
a method, strictly speaking).
*ARGS_EDITOR are the editors used for entering the argument, e.g. use
editobj.editor.FloatEditor for a float argument, or editobj.editor.EntryEditor for a
Python eval'ed line of code.
MRO is used in order to allow subclasses to use the methods registered for
their mother.
If *ARGS_EDITOR is (None,) the method is hidden. Use this on a subclass to hide a
method provided by a mother class."""
  
  methods = _methods.get(clazz)
  if methods: methods.append((method, args_editor))
  else:       _methods[clazz] = [(method, args_editor)]

def _find_methods(obj):
  methods = []
  
  if isinstance(obj, MultiEdit): clazz = obj._objs[0].__class__
  else:                          clazz = obj.__class__
  
  for clazz in (getattr(clazz, "__mro__", None) or _mro(clazz)): methods.extend(_methods.get(clazz, ()))
  return methods

def _find_methods(obj):
  methods = {}
  
  if isinstance(obj, MultiEdit): clazz = obj._objs[0].__class__
  else:                          clazz = obj.__class__
  
  mro = list(getattr(clazz, "__mro__", None) or _mro(clazz))
  mro.reverse()
  for clazz in mro:
    for method, args_editor in _methods.get(clazz, ()):
      if args_editor == (None,):
        if methods.has_key(method): del methods[method]
      else:
        methods[method] = method, args_editor
        
  return methods.values()

# Available and default children class customization (for the "Add..." dialog box)

_available_children = {}

def register_available_children(children_codes, clazz):
  """register_available_children(children_codes, clazz)

Register the CHILDREN_CODES that are proposed for addition in an instance of CLAZZ.
If CHILDREN_CODES is a list of strings (Python code), EditObj will display a dialog box.
If CHILDREN_CODES is a single string, no dialog box will be displayed, and this code
will automatically be used.
If CHILDREN_CODES is "", nothing is done when clicking on the "Add..." button.
The codes are just eval'ed to create the children; they can use the "parent" variable,
which is set to the list/dict we are adding into."""
  
  if isinstance(children_codes, list):
    try:    _available_children[clazz].extend(children_codes)
    except: _available_children[clazz] = children_codes
  else:
    _available_children[clazz] = children_codes

def _find_available_children(obj):
  available_children = []
  
  if isinstance(obj, MultiEdit): clazz = obj._objs[0].__class__
  else:                          clazz = obj.__class__
  
  for clazz in (getattr(clazz, "__mro__", None) or _mro(clazz)):
    a = _available_children.get(clazz)
    if   isinstance(a, list): available_children.extend(a)
    elif isinstance(a, str): return a
    
  return available_children

  
# Proposed values customization

_values = {}

def register_values(attr, code_expressions):
  """register_values(attr, code_expressions)

Registers CODE_EXPRESSIONS as a proposed value for ATTR."""
  
  code_expressions = map(unicodify, code_expressions)
  try:             _values[attr].extend(code_expressions)
  except KeyError: _values[attr] = list(code_expressions)
  
def _find_values(attr): return _values.get(attr) or []


# Editing events

_on_edit = {}
_on_children_visible = {}

def register_on_edit(func, clazz):
  """register_on_edit(func, clazz)

Register FUNC as an "on_edit" event for CLAZZ.
When an instance of CLAZZ is edited, FUNC is called with the instance and the editor
Tkinter window as arguments."""
  
  _on_edit[clazz] = func

def _call_on_edit(obj, window):
  if isinstance(obj, MultiEdit): clazz = obj._objs[0].__class__
  else:                          clazz = obj.__class__
  
  for clazz in (getattr(clazz, "__mro__", None) or _mro(clazz)):
    on_edit = _on_edit.get(clazz, None)
    if on_edit: on_edit(obj, window)


def register_on_children_visible(func, clazz):
  """register_on_children_visible(func, clazz)

Register FUNC as an "on_children_visible" event for CLAZZ.
When the children of an instance of CLAZZ are shown or hidden, FUNC is called
with the instance and the new visibility status (0 or 1) as arguments."""
  
  _on_children_visible[clazz] = func

def _call_on_children_visible(obj, visible):
  if isinstance(obj, MultiEdit): clazz = obj._objs[0].__class__
  else:                          clazz = obj.__class__
  
  for clazz in (getattr(clazz, "__mro__", None) or _mro(clazz)):
    on_children_visible = _on_children_visible.get(clazz, None)
    if on_children_visible: on_children_visible(obj, visible)
    
    
def encode(s):
  if type(s) is unicode: return s.encode("latin")
  return s

def unicodify(s):
  if type(s) is str:
    try:                 return unicode(s, "utf8")
    except UnicodeError: return unicode(s, "latin")
  return s

def _mro(clazz):
  mro = [clazz]
  for c in clazz.__bases__: mro.extend(_mro(c))
  return mro

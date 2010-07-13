#!/usr/bin/env python

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

import Tkinter, editobj, editobj.editor as editor, editobj.custom as custom

# This is a sample EditObj-based editor.
# Imagine you have the following object to edit :

class MyObj:
  def __init__(self, name = ""):
    self.name = name
    self.filename = ""
    
    self.x = 0.0
    self.y = 0.0
    
    self.visible = 1
    
    self.power2  = 4
    self.powers2 = [1, 2, 4, 8, 16, 32, 64]
    
    self.any = None
    
    self.content = []
    
  def __repr__(self): return "<MyObj %s>" % self.name
  
# This object has no real usage has is, but present some typical attributes.
# Editobj can already edit this object (as any other one) !
#
# But one typically wants that the "name" attribute can be only a string, "x" a
# float number, or "filename" a valid file name. EditObj can do that too, if you
# take the time to teach that to him.
#
# EditObj edits each attribute of an object in an editor. The default one is a
# one-line Python console, but many other are supported (See editobj.editor for
# more info).
# If you want so, you can map an attribute name to a specific editor with the
# editobj.editor.register_attr(attr, editor_class) function. Notice that only attribute
# names are mapped, and the class of the object is NOT involved (contrary to systems
# like Java Bean); this is pretty logic because Python is dynamic and often does so.
# It can also save you a lot of time, since you have to enter each attribute only
# once !

# Say "name" is a string.
custom.register_attr("name", editor.StringEditor)

# Say that for "name", the values "me" and "you" should be proposed to the user.
# Possible values are given as text; as if they were entered by the user in the
# editor.
custom.register_values("name", ["me", "you"])

# Say "filename" is a file name.
custom.register_attr("filename", editor.FilenameEditor)

# Say "x" and "y" are float numbers.
custom.register_attr("x", editor.FloatEditor)
custom.register_attr("y", editor.FloatEditor)

# Say "visible" is a boolean.
custom.register_attr("visible", editor.BoolEditor)

# Say "power2" is a value choosen in a list.
#
# The editor.ListEditor() function create a new class of editor with the given list
# of possible values.
custom.register_attr("power2", editor.ListEditor(["1", "2", "4", "8"]))

# "any" can be anything, so we do not provide a specific editor.
# It will be edited with a one-line Python console.

# Say that for "any", the value "None" should be proposed to the user.
custom.register_values("any", ["None"])

# Say that "content" contains the items of a MyObj object.
#
# EditObj automatically display a tree view if the object is a list or
# a dictionary, or if it we register a "children" attribute.

custom.register_children_attr("content", clazz = MyObj)

# Say "content" is hidden (because it is edited as "items", by the tree view).
custom.register_attr("content", None)


# Say that MyObj object can contains other MyObj object in their "items" attribute
# (which is the same that "content") Yes, it is a tree like structure, and EditObj
# deals very well with such structures !
#
# The editor.register_children function register a (non-exhaustive) list of
# possible children for a given class. Children are given as Python strings.

custom.register_available_children(["MyObj('new')"], MyObj)


# Make MyObj available in the evaluation environment

custom.EVAL_ENV["MyObj"] = MyObj


# No main Tk window
root = Tkinter.Tk(className = 'EditObj')
root.withdraw()

# Better Tk look
root.option_add("*bd", 1)
root.option_add("*Entry.background", "#FFFFFF")
root.option_add("*List.background", "#FFFFFF")


# Create a MyObj object, with another MyObj inside (yes, it is a tree like structure)

my_obj = MyObj("root")
my_obj.content.append(MyObj("child"))


# Edit my_obj !
editobj.edit(my_obj)

Tkinter.mainloop()

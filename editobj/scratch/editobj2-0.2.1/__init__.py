# -*- coding: utf-8 -*-

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

"""EditObj2 -- An automatic dialog box generator

EditObj2 is able to generate a dialog box for editing almost any Python object. The dialog box is
composed of an attribute list, a luxurious good-looking but useless icon and title bar, and a tree
view (if the edited object is part of a tree-like structure). The default dialog box can be
customized and adapted for a given class of object through the editobj2.introsp module.

EditObj2 has multiple GUI support; it currently supports GTK and TK.

EditObj2 was inspired by Java's "Bean Editor", however the intial concept have been extended by
adding icons, tree views, undo/redo, translation support, automatic update on object changes,
and multiple simultaneous editions (see editobj2.introsp.ObjectPack).


The editobj2 package contains the following modules:

 * editobj2.introsp: High level, highly customizable introspection (go there for customizing EditObj2 dialog boxes)

 * editobj2.observe: Observation framework

 * editobj2.undoredo: Multiple undo/redo support

 * editobj2.editor: The editor dialog boxes and related widgets

 * editobj2.field: The set of basic fields for attribute panes

 * editobj2.treewidget: A Tkinter Tree widget, and scrolled canvas and frame widget


The following global variables can be changed:

 * editobj.GUI: the default GUI system (default is GTK if available, else TK)

 * editobj.TRANSLATOR: the translator function used for translating dialog boxes.
It can be set to a translator function (such as the ones from the gettext module).


The edit() function in this module is an easy way to quickly edit an object. More complex edition
can be done using the widget available in editobj2.editor.
"""

import os, os.path

_ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
if not os.path.exists(_ICON_DIR):
  _ICON_DIR = os.path.join("/usr", "share", "editobj2")
  if not os.path.exists(_ICON_DIR):
    _ICON_DIR = os.path.join("/usr", "local", "share", "editobj2")
    if not os.path.exists(_ICON_DIR):
      _ICON_DIR = os.path.join("/usr", "share", "python-editobj2")
      
_eval = eval
def eval(s):
  return _eval(s)

VERSION = "0.2.1"

GUI = ""

TRANSLATOR = lambda s: s

def edit(o, on_validate = None, direction = "h", undo_stack = None, width = -1, height = -1, expand_tree_at_level = 0, selected = None, edit_child_in_self = 1, on_close = None):
  global GUI
  if not GUI:
    try:
      import gtk
      GUI = "Gtk"
    except:
      try:
        import qtpe
        GUI = "Qtopia"
      except:
        try:
          import qt
          GUI = "Qt"
        except:
          GUI = "Tk"
        
  if   GUI == "Qt":
    import sys, qt
    if qt.QApplication.startingUp():
      qt.app = qt.QApplication(sys.argv)
      
  elif GUI == "Qtopia":
    import sys, qt, qtpe
    if qt.QApplication.startingUp():
      qt.app = qtpe.QPEApplication(sys.argv)
      
  import editobj2.editor
  dialog = editobj2.editor.EditorDialog(GUI, direction, on_validate, edit_child_in_self, undo_stack, on_close)
  if (width != -1) or (height != -1): dialog.set_default_size(width, height)
  dialog.edit(o)
  if expand_tree_at_level: dialog.editor_pane.hierarchy_pane.expand_tree_at_level(expand_tree_at_level)
  if selected:
    dialog.editor_pane.hierarchy_pane.edit_child(selected)
  if on_validate: return dialog.wait_for_validation()
  else:           return dialog

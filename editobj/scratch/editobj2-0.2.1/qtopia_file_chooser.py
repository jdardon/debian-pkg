# -*- coding: utf-8 -*-

# field_gtk.py
# Copyright (C) 2008 Jean-Baptiste LAMY -- jiba@tuxfamily.org
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

import os, os.path
import editobj2, editobj2.introsp, editobj2.field
import locale
from locale import strcoll
locale.setlocale(locale.LC_ALL, "")

def file_sorter(a, b): return strcoll(a.filename, b.filename)

class File(object):
  def __init__(self, path, dir_only = 0, has_dot_dot = 0):
    if isinstance(path, str): path = path.decode("latin")
    self._path              = os.path.abspath (path)
    self._is_dir            = os.path.isdir   (path)
    self.filename           = os.path.basename(path)
    self.children           = None
    self._dir_only          = dir_only
    self._has_dot_dot       = has_dot_dot
    
  def result(self): return os.path.join(os.path.dirname(self._path), self.filename) # filename may have been changed by the user
    
  def __unicode__(self): return self.filename
  
  def get_icon_filename(self):
    if self._is_dir: return "/opt/QtPalmtop/pics144/slfolder.png"
    else:            return "/opt/QtPalmtop/pics/slUnknown14.png"

  def has_children(self): return self._is_dir
  
  def get_children(self):
    if self.children is None:
      if self._is_dir:
        dirs  = []
        files = []
        try:
          children_files = os.listdir(self._path)
        except OSError:
          pass
        else:
          for filename in children_files:
            if not filename.startswith("."):
              file = File(os.path.join(self._path, filename), self._dir_only)
              if file._is_dir:         dirs .append(file)
              elif not self._dir_only: files.append(file)
          dirs .sort(file_sorter)
          files.sort(file_sorter)
        if self._has_dot_dot and (self._path != "/"):
          self.children = [ParentsDir(self._path, self._dir_only)] + dirs + files
        else:
          self.children = dirs + files
      else: self.children = []
    return self.children


class ParentsDir(object):
  def __init__(self, path, dir_only = 0, filename = ""):
    if isinstance(path, str): path = path.decode("latin")
    self.filename           = os.path.abspath(path)
    self.children           = []
    self._dir_only          = dir_only
    path = self.filename
    while path != "/":
      path = os.path.dirname(path)
      self.children.insert(0, ParentDir(path, dir_only))
    
  def result(self): return self.filename
  
  def __unicode__(self): return u".."
  
  def get_icon_filename(self):
    return "/opt/QtPalmtop/pics144/slfolder.png"


class ParentDir(object):
  def __init__(self, path, dir_only = 0):
    if isinstance(path, str): path = path.decode("latin")
    self.filename  = os.path.abspath(path)
    self._dir_only = dir_only
    
  def result(self): return os.path.dirname(self.filename)
  
  def __unicode__(self): return self.filename
  
  def get_icon_filename(self):
    return "/opt/QtPalmtop/pics144/slfolder.png"



def goto_parent_dir(undo_stack, parent_dir, editor): editor.edit(File(parent_dir.filename, parent_dir._dir_only, 1))

descr = editobj2.introsp.description(ParentDir)
descr.set_field_for_attr("icon_filename", None)
descr.set_field_for_attr("filename", editobj2.field.StringField)
descr.add_action(editobj2.introsp.Action("Go to", goto_parent_dir, default = 1, pass_editor_in_args = 1))

def goto_dir(undo_stack, dir, editor): editor.edit(File(dir._path, dir._dir_only, 1))

descr = editobj2.introsp.description(File)
descr.set_field_for_attr("icon_filename", None)
descr.set_field_for_attr("filename", editobj2.field.StringField)
descr.add_action(editobj2.introsp.Action("Go to", goto_dir, filter = lambda file: file._is_dir, default = 1, pass_editor_in_args = 1))

def goto_parent(undo_stack, parent, editor): editor.edit(File(os.path.dirname(parent.filename), parent._dir_only, 1))

descr = editobj2.introsp.description(ParentsDir)
descr.set_field_for_attr("icon_filename", None)
descr.set_field_for_attr("filename", editobj2.field.StringField)
descr.add_action(editobj2.introsp.Action("Go to", goto_parent, default = 1, pass_editor_in_args = 1))

def ask_filename(on_validate, path = "/"):
  filename = os.path.basename(path)
  path     = os.path.dirname (path)
  file = File(path, 0, 1)
  for f in file.get_children():
    if f.filename == filename: break
  def _on_validate(o):
    if isinstance(o, File): on_validate(o.result())
  editobj2.edit(file, _on_validate, "v", selected = f)
  
def ask_dirname(on_validate, path = "/"):
  filename = os.path.basename(path)
  path = os.path.dirname(path)
  file = File(path, 1, 1)
  for f in file.get_children():
    if f.filename == filename: break
  def _on_validate(o):
    if isinstance(o, File): on_validate(o.result())
  editobj2.edit(file, _on_validate, "v", selected = f)

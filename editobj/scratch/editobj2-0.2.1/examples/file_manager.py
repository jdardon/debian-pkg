# -*- coding: utf-8 -*-

# A small file manager featuring image viewing capability

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

import sys, os, os.path, stat

import editobj2, editobj2.introsp as introsp, editobj2.observe as observe, editobj2.field as field


class Permissions(object):
  def __init__(self, can_read, can_write, can_execute):
    self.can_read    = can_read
    self.can_write   = can_write
    self.can_execute = can_execute
    
  #def set_can_read(self, can_read):
    # XXX change the permission here
    # (not done in the example)
    # (and so on for the other attributes)


class File(object):
  def __init__(self, path):
    if isinstance(path, str): path = path.decode("latin")
    self.path              = os.path.abspath(path)
    self.filename          = os.path.basename(path)
    try:    self.size = os.path.getsize(path)
    except: pass
    try:    mode = os.stat(path).st_mode
    except: mode = None
    if mode is not None:
      self.permissions_user  = Permissions(bool(mode & stat.S_IRUSR), bool(mode & stat.S_IWUSR), bool(mode & stat.S_IXUSR))
      self.permissions_group = Permissions(bool(mode & stat.S_IRGRP), bool(mode & stat.S_IWGRP), bool(mode & stat.S_IXGRP))
      self.permissions_other = Permissions(bool(mode & stat.S_IROTH), bool(mode & stat.S_IWOTH), bool(mode & stat.S_IXOTH))
      
    self.children = None
    
  def __unicode__(self): return self.filename
  
  def get_icon_filename(self):
    if os.path.isdir(self.path):    return os.path.join(os.path.dirname(sys.argv[0]), "./directory.png")
    elif self.path.endswith(".py"): return os.path.join(editobj2._ICON_DIR, "python.png")
    elif self.path.endswith(".png") or self.path.endswith(".jpeg") or self.path.endswith(".jpg"): return self.path
    else:                           return os.path.join(os.path.dirname(sys.argv[0]), "./file.png")

  def has_children(self): return os.path.isdir(self.path)
  
  def get_children(self):
    if self.children is None:
      if os.path.isdir(self.path):
        self.children = [File(os.path.join(self.path, filename)) for filename in os.listdir(self.path) if not filename.startswith(".")]
        #self.children = range(10)
      else: self.children = []
    return self.children


descr = introsp.description(File)
descr.set_icon_filename(lambda o: o.get_icon_filename())
descr.set_field_for_attr("icon_filename", None)
descr.set_field_for_attr("size", field.IntField, unit = "Ko")
descr.set_children_getter("children", None, "has_children")



file = File(os.path.join(".."))

if   "--gtk"    in sys.argv: editobj2.GUI = "Gtk"
elif "--tk"     in sys.argv: editobj2.GUI = "Tk"
elif "--qt"     in sys.argv: editobj2.GUI = "Qt"
elif "--qtopia" in sys.argv: editobj2.GUI = "Qtopia"

editobj2.edit(file).main()


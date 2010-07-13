#!/usr/bin/env python

# TreeWidget
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

from Tkinter import *
from editobj.treewidget import *
import os, os.path, sys, string, imp
import editobj.treewidget

# Gets the default icons directory (shipped with TreeWidget).
iconsdir = IconsDir(os.path.join(os.path.dirname(editobj.treewidget.__file__), "icons"))

class FileNode(Node):
  """Example Node subclass -- browse the file system."""
  def __init__(self, parent, path):
    self.path = path
    Node.__init__(self, parent)
    
  def __str__(self): return os.path.basename(self.path) or self.path

  # One may explicitely choose the icon as following (TreeWidget use those as default) :
  
  def geticon(self):
    if self.isexpandable():
      if self.expanded: return iconsdir["openfolder.pgm"]
      else: return iconsdir["folder.pgm"]
    else: return iconsdir["python.pgm"]
    
  def iseditable(self): return os.path.basename(self.path) != ""
  def isexpandable(self): return os.path.isdir(self.path)
  def createchildren(self, oldchildren = None):
    try: files = os.listdir(self.path)
    except os.error: return []
    files.sort(lambda a, b: cmp(os.path.normcase(a), os.path.normcase(b)))
    children = []
    for file in files: children.append(FileNode(self, os.path.join(self.path, file)))
    return children
    
  def settext(self, text):
    newpath = os.path.dirname(self.path)
    newpath = os.path.join(newpath, text)
    if os.path.dirname(newpath) != os.path.dirname(self.path): return
    try:
      os.rename(self.path, newpath)
      self.path = newpath
    except os.error: print "Cannot rename !"

  
root = Tk()
tree = Tree(root)
tree.frame.pack(expand=1, fill="both")

node = FileNode(tree, os.curdir)
root.mainloop()


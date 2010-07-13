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

class BigNode(Node):
  """Example of Node subclass -- Each BigNode has 1000 children. Enjoy !"""
  def __init__(self, parent, i):
    self.i = i
    Node.__init__(self, parent)
    
  def __str__(self): return str(self.i)
    
  def iseditable(self): return 0
  def isexpandable(self): return 1
  def createchildren(self, oldchildren = None):
    return map(BigNode, [self] * 1000, range(1000))
  
root = Tk()
tree = Tree(root)
tree.frame.pack(expand=1, fill="both")

node = BigNode(tree, 0)
root.mainloop()


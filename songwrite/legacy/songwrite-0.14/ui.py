# SongWrite
# Copyright (C) 2001-2004 Jean-Baptiste LAMY -- jibalamy@free.fr
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

import Tkinter

class LinksBar:
  def __init__(self, canvas, x, y, content, **kargs):
    self.links   = []
    self.delta_x = {}
    self.funcids = {}
    self.canvas  = canvas
    
    x0 = x
    
    for (text, func) in content:
      link = canvas.create_text(x, y, text = text, font = "Helvetica -12 underline", fill = "blue3", activefill = "red", anchor = "w", **kargs)
      self.links  .append(link)
      self.funcids[link] = canvas.tag_bind(link, "<ButtonRelease>", func)
      self.delta_x[link] = x - x0
      x = canvas.bbox(link)[2] + 20
      
  def coords(self, x, y):
    for link in self.links:
      self.canvas.coords(link, x + self.delta_x[link], y)
    
  def destroy(self):
    for link in self.links:
      self.canvas.tag_unbind(link, "<ButtonRelease>", self.funcids[link])
      
      
      

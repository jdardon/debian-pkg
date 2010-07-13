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

"""TreeWidget -- (yet another) Tree widget for Tk.

This tree has been greatly inspired from Guido's tree for IDLE, but has been totally rewritten.
Main difference are :
 - Great speed optimizations : only draws visible nodes, delete those who are no longer visible, and redraws only changed nodes !
 - Asynchronous drawing.
 - You directly inherit from the Node class.
 - Linux frendly icons (but removing lines adds also a good perf bonus !).

This tree support very big tree (10000+ nodes); the speed depends on the number of visible nodes, NOT on the total number of nodes !

See the __doc__ of Tree and Node for more info.

This module also include:
 - IconDir, a usefull tool for using image from a directory
 - ScrolledCanvas, a canvas with scrollbars
 - ScrollPane, a frame with scrollbars
"""

# This has been greatly inspired from Guido's tree for IDLE

import os, types
from Tkinter import *

class IconsDir:
  """IconsDir(path) -- Allows quick access to any image in the given directory.
You can get the image called "picture.png" as following :
>>>iconsdir["picture"]
Image are cached in a dict for speed up."""
  def __init__(self, path):
    self.path = path
    self.icons = {}
  def __getitem__(self, name):
    try: return self.icons[name]
    except KeyError:
      name2, ext = os.path.splitext(name)
      ext = ext or ".pgm" # I don't use gif for patent reasons.
      file = os.path.join(self.path, name2 + ext)
      icon = PhotoImage(file = file)
      self.icons[name] = icon
      return icon

def create_default_iconsdir():
  global iconsdir
  import os.path
  ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
  if not os.path.exists(ICON_DIR):
    ICON_DIR = os.path.join("/usr", "share", "editobj")
    if not os.path.exists(ICON_DIR):
      ICON_DIR = os.path.join("/usr", "share", "python-editobj")
  iconsdir = IconsDir(ICON_DIR)


class Node:
  """Tree's Node base class. You must inherit this class and override a few method :
 - __str__()                          -> string  : must return the Node's label.
 - __unicode__()                      -> unicode : must return the Node's label.
 - geticon()                          -> image   : must return the Node's icon (see IconsDir for a handy way to get images).
 - createchildren(oldchildren = None) -> list    : (Optionnal) called the first time we need the children; must return a list of child Node. oldchildren may contains the previous children, in case of an update.
 - isexpandable()                     -> boolean : (Optionnal) must return true if this Node has children.
 - iseditable()                       -> boolean : (Optionnal) must return true if the Node label is editable.
 - settext()                                     : (Optionnal) called when the Node's label has been edited.
 - getheight()                        -> height  : (Optionnal) override this if you use non-regular height.
 - destroy()                                     : (Optionnal) called when the node is destroyed.
In __str__(), __unicode__() or geticon(), you may check the values of self.selected, self.isexpandable() and self.expanded, for example to provide different icons for selected or expanded Nodes.

The "icon_width" attribute define the width of the icon. You can override it in geticon(), e.g. just before returning the icon, do 'self.icon_width = icon.width()'.
It defaults to 20.

If you override __init__(), you must call Node.__init__(parent), AT THE END OF YOUR __init__() !
"""
  icon_width = 20
  
  def __init__(self, parent):
    """Create a new Node. Parent can be either the parent's Node, or the tree (for the root Node).
If you override __init__(), you must call Node.__init__(parent), AT THE END OF YOUR __init__() !
"""
    if isinstance(parent, Node):
      self.parent        = parent
      self.tree          = parent.tree
      self.depth         = parent.depth + 1
    else:
      self.parent        = None
      self.tree          = parent
      self.depth         = 0
    self.children        = []
    self.childrencreated = 0
    self.expanded        = 0
    self.selected        = 0
    
    self.text_id      = 0
    self.image_id     = 0
    self.minusplus_id = 0
    
    self.oldy = -1000
    self.changed = 0
    
    if not self.parent: self.tree._setnode(self) # Root Node must be passed to the tree.
    
  def destroy(self):
    for child in self.children: child.destroy()
    
  def createchildren(self, oldchildren = None): return []
  
  def lastchild(self):
    if self.childrencreated and self.expanded: return self.children[-1].lastchild()
    else: return self
  def previous(self):
    if isinstance(self.parent, Node):
      if self.index == 0: return self.parent
      return self.parent.children[self.index - 1].lastchild()
    else: return None # Root Node
  def next(self):
    if self.expanded and self.children:
      return self.children[0]
    else:
      if isinstance(self.parent, Node): return self.parent._next(self)
      else: return None # Root Node
  def _next(self, node):
    if node.index + 1 >= len(self.children):
      if isinstance(self.parent, Node): return self.parent._next(self)
      else: return None # Root Node
    return self.children[node.index + 1]
    
  def update(self):
    self.changed = 1
    try: self.label["text"] = unicode(self)
    except: pass
  def updatetree(self):
    self.update()
    for child in self.children: child.updatetree()
  def updatechildren(self):
    if self.childrencreated:
      if self.expanded:
        oldchildren = self.children
        for child in self.children: child._undraw()
        self.children = self.createchildren(self.children)
        for child in oldchildren:
          if not child in self.children: child.destroy()
        i = 0
        if self.children:
          for child in self.children:
            child.index = i
            i = i + 1
        else:
          self.expanded = 0 # Cannot be expanded if no children
        self.tree.draw()
      else:
        for child in self.children: child.destroy()
        self.children = []
        self.childrencreated = 0
        self.redraw()
    else: self.redraw()
    
  def select(self, event = None):
    if not self.selected:
      self.tree.deselectall()
      self.selected = 1
      self.changed = 1
      self.tree.selection.append(self)
      self.label.configure(bg = "#CCCCFF")#bg = "#834cb4")
      self.redraw()
  def deselect(self, event = None):
    if self.selected:
      self.selected = 0
      self.changed = 1
      self.tree.selection.remove(self)
      self.label.configure(bg = self.tree["bg"])
      self.redraw()
      
  def selecttree(self):
    if not self.selected: self.select()
    for child in self.children: child.selecttree()
  def deselecttree(self):
    self.deselect()
    for child in self.children: child.deselecttree()
    
  def expand(self, event = None):
    if not self.expanded:
      if not self.childrencreated:
        self.children = self.createchildren()
        i = 0
        for child in self.children:
          child.index = i
          i = i + 1
        self.childrencreated = 1
      if len(self.children) > 0:
        self.changed = 1
        self.expanded = 1
        self.tree.draw()
  def collapse(self, event = None):
    if self.expanded:
      self.expanded = 0
      self.changed = 1
      self.tree.draw()
  def isexpandable(): return len(self.children)
  def toggle(self, event = None):
    if self.expanded: self.collapse()
    else: self.expand()
  
  def sizetree(self):
    if self.expanded:
      sizetree = 1
      for child in self.children: sizetree = sizetree + child.sizetree()
      return sizetree
    else: return 1
    
  def redraw(self):
    if self.oldy >=0: self._draw(self.oldy)
  def _draw(self, y):
    x = self.depth * 20
    if self.changed or y != self.oldy:
      #if self.changed: print "  draw because changed"
      #if y != self.oldy: print "  draw because move on y", y, self.oldy
      cx = x + 9
      cx = self._drawplusminusicon(cx, y + 7)
      cx = self._drawicon(cx, y)
      self._drawtext(cx, y)
      self.changed = 0
      self.oldy = y
  def _undraw(self):
    self.oldy = -1000
    if self.minusplus_id: self.tree.delete(self.minusplus_id)
    if self.image_id    : self.tree.delete(self.image_id)
    if self.text_id     : self.tree.delete(self.text_id)
    self.minusplus_id = self.image_id = self.text_id = 0
  def _undrawtree(self):
    self._undraw()
    for child in self.children: child._undrawtree()
  def _drawplusminusicon(self, x, y):
    if self.minusplus_id: self.tree.delete(self.minusplus_id)
    if self.isexpandable():
      if self.expanded: image = self.tree.minusicon
      else:             image = self.tree.plusicon
      self._plusminusicon = image # prevent image from garbage collection
      if image:
        self.minusplus_id = self.tree.create_image(x, y, image = image)
        self.tree.tag_bind(self.minusplus_id, "<1>", self.toggle) # XXX This leaks bindings until canvas is deleted
    else: self.minusplus_id = 0
    return x + 10
  def _drawicon(self, x, y):
    if self.image_id: self.tree.delete(self.image_id)
    image = self.geticon()
    self._icon = image # prevent image from garbage collection
    if image:
      self.image_id = self.tree.create_image(x, y, anchor = "nw", image = image)
      self.tree.tag_bind(self.image_id, "<1>", self.select)
      self.tree.tag_bind(self.image_id, "<Double-1>", self.toggle)
    else: self.image_id = 0
    return x + self.icon_width
    
  def geticon(self):
    global iconsdir
    if not iconsdir: create_default_iconsdir()
    
    if self.isexpandable():
      if self.expanded: return iconsdir["openfolder.pgm"]
      else: return iconsdir["folder.pgm"]
    else: return iconsdir["python.pgm"]
  def _drawtext(self, x, y):
    if self.text_id: self.tree.delete(self.text_id)
    if hasattr(self, "entry"): self._edit_finish()
    try: label = self.label
    except AttributeError:
      self.label = Label(self.tree, text = unicode(self).encode("latin"), fg = "black", bg = self.tree["bg"], bd = 0, padx = 2, pady = 2)
      self.label.bind("<1>", self.select_or_edit)
      self.label.bind("<Double-1>", self.toggle)
      self.label.bind("<4>"       , self.tree.unit_up)
      self.label.bind("<5>"       , self.tree.unit_down)
    self.text_id = self.tree.create_window(x, y, anchor = "nw", window = self.label)
    
  def select_or_edit(self, event = None):
    if self.selected and self.iseditable(): self.edit(event)
    else: self.select(event)
  def edit(self, event = None):
    self.entry = Entry(self.label, bd = 0, highlightthickness = 1, width = 0)
    self.entry.insert(0, self.label['text'])
    self.entry.selection_range(0, END)
    self.entry.pack(ipadx = 5)
    self.entry.focus_set()
    self.entry.bind("<Return>", self._edit_finish)
    self.entry.bind("<Escape>", self._edit_cancel)
  def _edit_finish(self, event = None):
    try:
      entry = self.entry
      del self.entry
    except AttributeError:
      return
    text = entry.get()
    entry.destroy()
    if text and text != unicode(self): self.settext(text)
    self.label['text'] = unicode(self)
    self.redraw()
    self.tree.focus_set()
  def _edit_cancel(self, event = None):
    self.redraw()
    self.tree.focus_set()
  def iseditable(self): return 0
  def settext(self, text): pass
  

  

# ScrolledCanvas and Tree widget (slightly modified)

class ScrolledCanvas(Canvas):
  """ScrolledCanvas -- A Tk canvas with scrollbar. Base class for Tree."""
  def __init__(self, master, kw = {}, **opts):
    if not opts.has_key('yscrollincrement'): opts['yscrollincrement'] = 20
    
    #self.master = master
    self.frame = Frame(master)
    self.frame.rowconfigure(0, weight=1)
    self.frame.columnconfigure(0, weight=1)
    
    #apply(Canvas.__init__, (self, self.frame, kw), opts)
    Canvas.__init__(self, self.frame, kw, **opts)
    self.grid(row=0, column=0, sticky="nsew")
    
    self.vbar = Scrollbar(self.frame, name="vbar")
    self.vbar.grid(row=0, column=1, sticky="nse")
    self.hbar = Scrollbar(self.frame, name="hbar", orient="horizontal")
    self.hbar.grid(row=1, column=0, sticky="ews")
    self['yscrollcommand'] = self.vbar.set
    self.vbar['command'] = self.yview
    self['xscrollcommand'] = self.hbar.set
    self.hbar['command'] = self.xview
    self.bind("<Key-Prior>", self.page_up)
    self.bind("<Key-Next>" , self.page_down)
    self.bind("<Key-Up>"   , self.unit_up)
    self.bind("<Key-Down>" , self.unit_down)
    self.bind("<4>"        , self.unit_up)
    self.bind("<5>"        , self.unit_down)
    
    self.focus_set()
    
    self.pack  = self.frame.pack
    self.grid  = self.frame.grid
    self.place = self.frame.place
    
    self["width"] = 280
    
  def destroy(self):
    Canvas.destroy(self)
    self.vbar.destroy()
    self.hbar.destroy()
    self.frame.destroy()
    
  def page_up(self, event):
    self.yview_scroll(-1, "pages")
    return "break"
  def page_down(self, event):
    self.yview_scroll(1, "pages")
    return "break"
  def unit_up(self, event):
    self.yview_scroll(-1, "units")
    return "break"
  def unit_down(self, event):
    self.yview_scroll(1, "units")
    return "break"
  
class ScrollPane(Canvas):
  """ScrollPane -- A Tk frame with scrollbar."""
  def __init__(self, master, scrollX = 1, scrollY = 1, max_width = 280, max_height = 360, kw = {}, **opts):
    if not opts.has_key('yscrollincrement'  ): opts['yscrollincrement'  ] = 20
    if not opts.has_key('highlightthickness'): opts["highlightthickness"] = 0
    self.frame = Frame(master)
    self.frame.rowconfigure   (0, weight = 1)
    self.frame.columnconfigure(0, weight = 1)
    
    Canvas.__init__(self, self.frame, kw, **opts)
    self.grid(row = 0, column = 0, sticky = "nsew")
    
    self.bind("<Key-Prior>", self.page_up)
    self.bind("<Key-Next>" , self.page_down)
    self.bind("<Key-Up>"   , self.unit_up)
    self.bind("<Key-Down>" , self.unit_down)
    
    self.pack  = self.frame.pack
    self.grid  = self.frame.grid
    self.place = self.frame.place
    
    self.content = None
    
    self["width"] = self["height"] = 0
    self.max_width  = max_width
    self.max_height = max_height
    
    self.scrollX = scrollX
    self.scrollY = scrollY
    
    if scrollX:
      self.hbar = Scrollbar(self.frame, name = "hbar", orient = "horizontal")
      self.hbar.grid(row = 1, column = 0, sticky = "ews")
      self['xscrollcommand'] = self.hbar.set
      self.hbar['command'] = self.xview
    if scrollY:
      self.vbar = Scrollbar(self.frame, name = "vbar")
      self.vbar.grid(row = 0, column = 1, sticky = "nse")
      self['yscrollcommand'] = self.vbar.set
      self.vbar['command'] = self.yview
      
    self.bind("<Configure>", self._resized)
    
  def setContent(self, content):
    self.content = content
    
    self.id = self.create_window(0, 5, window = content, anchor = "nw")
    
    self.updateContentSize()
    
  def updateContentSize(self):
    self.update_idletasks() # Required, else dimension of content may not have been computed ?
    
    x0, y0, x1, y1 = self.bbox(ALL)
    self.configure(scrollregion = (0, 0, x1, y1))
    
    if self.scrollX: self["width" ] = min(self.max_width , x1)
    else:            self["width" ] = x1
    if self.scrollY: self["height"] = min(self.max_height, y1)
    else:            self["height"] = y1
    self.yview_moveto(0)
    
  def _resized(self, event = None):
    width = self.winfo_width()
    if width <= 1: width = self.winfo_reqwidth()
    
    height = self.winfo_height()
    if height <= 1: height = self.winfo_reqheight()
  
    if not self.scrollX: self.itemconfigure(self.id, width  = width)
    if not self.scrollY: self.itemconfigure(self.id, height = height)
    
  def destroy(self):
    Canvas.destroy(self)
    if self.scrollX: self.hbar.destroy()
    if self.scrollY: self.vbar.destroy()
    self.frame.destroy()
    if self.content: self.content.destroy()
    
  def page_up(self, event):
    self.yview_scroll(-1, "page")
    return "break"
  def page_down(self, event):
    self.yview_scroll(1, "page")
    return "break"
  def unit_up(self, event):
    self.yview_scroll(-1, "unit")
    return "break"
  def unit_down(self, event):
    self.yview_scroll(1, "unit")
    return "break"

iconsdir = None


class Tree(ScrolledCanvas):
  """Tree widget for Tk.
First create a Tree widget.
Then create a root Node, by passing the tree as parent (= the first arg of the constructor).

>>> root = Tk()
>>> tree = Tree(root)
>>> tree.frame.pack(expand = 1, fill = "both")
>>> node = YourNode(tree [, your Node's data])
>>> root.mainloop()

You may want to custom the "plus" and "minus" icons, they correspond to the "plusicon" and "minusicon" attributes of the tree."""

  def __init__(self, master, async = 1, kw = {}, **opts):
    """Tree(master, async = 1, kw = {}, **opts) -- Create a new Tree. Set async to 0 to disable asynchronous drawing."""
    if not opts.has_key('bg'): opts['bg'] ="white"
    if not opts.has_key('highlightthickness'): opts['highlightthickness'] = 0
    ScrolledCanvas.__init__(self, master, kw, **opts)
    self.plusicon    = self.minusicon = None
    self.nodeheight  = 20
    self.sizetree    = 0
    self.node        = None
    self.first       = None
    self.y           = 0
    self.selection   = []
    self.displayed   = []
    self.async       = async
    self.cancel_draw = None
    self["width"]    = 280
    self["height"]   = 200
    
    # There must be a better way to register Resize Event...
    self.bind("<Configure>", self._resized)
    
  def destroy(self):
    if self.node: self.node.destroy()
    ScrolledCanvas.destroy(self)
    
  def _setnode(self, node):
    if self.cancel_draw:
      self.after_cancel(self.cancel_draw)
      self.cancel_draw = None
      
    if self.node:
      self.node.destroy()
      for n in self.displayed: n._undraw()
      
    node.index     = 0
    self.node      = node
    self.first     = node
    self.y         = 0
    self.sizetree  = 0
    self.selection = []
    self.displayed = []
    
    if node: node.expand()
    
  def updatescroll(self):
    """Update the scroll-bar size."""
    if self.node:
      #self.update_idletasks() # Required, else dimension of content may not have been computed ?
      forgetit, forgetit, x1, forgetit = self.bbox(ALL)
      self.sizetree = self.node.sizetree() + (self.winfo_height() / self.nodeheight) - 1
      self.configure(scrollregion = (0, 0, x1, self.sizetree * self.nodeheight))
      
  def updatetree(self):
    """Update the full tree. Notice that it is speeder to update only some Nodes (with Node.update() or Node.updatetree() and then tree.draw()), if you know which Nodes have changed."""
    if self.node:
      self.node.update()
      self.draw()
      
  def draw(self):
    """Draw the tree. Only visible AND modified parts of the tree will be really redrawn.
As the drawing is by default asynchronous, you can call draw() a lot of time without perf loss."""
    if self.node:
      if self.async:
        if self.cancel_draw:
          self.after_cancel(self.cancel_draw)
        self.cancel_draw = self.after(3, self._draw)
      else: self._draw()
      
  def _draw(self):
    self.cancel_draw = None
    
    if self.node:
      if not self.minusicon:
        global iconsdir
        if not iconsdir: create_default_iconsdir()
        
        self.plusicon  = iconsdir["plus"]
        self.minusicon = iconsdir["minus"]
        
      y = self.y
      height = self.winfo_height()
      
      node = self.first
      todisplay = []
      for i in range(height / self.nodeheight + 1):
        todisplay.append(node)
        node = node.next()
        if node is None: break
      
      # Undraw nodes that are no longer visible
      for node in self.displayed:
        if not node in todisplay: node._undraw()
        
      # Draw nodes that are visible -- the _draw method is no-op if the node hasn't moved nor changed.
      y = 2 + self.y * self.nodeheight
      for node in todisplay:
        node._draw(y)
        y = y + self.nodeheight
        
      self.displayed = todisplay
      
      self.updatescroll()
        
  def yview(self, *args):
    if args[0] == "scroll": self.yview_scroll(args[1], args[2])
    else:                   self.yview_moveto(args[1])
  def yview_scroll(self, *args):
    height = self.winfo_height()
    if self.sizetree * self.nodeheight <= height: return
    if args[1][:1] == "u":
      self._addy(int(args[0]))
      ScrolledCanvas.yview_scroll(self, *args)
      # Must redraw, as some new Node may be visible (But only those Nodes will be redrawn !).
      self.draw()
    else:
      # Convert page-scroll into increment scroll, as i don't know how much is a page-scroll... ;-)
      yscrollincrement = int(self['yscrollincrement'])
      nbincrements = int(args[0]) * (height / yscrollincrement - 1)
      self.yview_scroll(nbincrements, "unit")
  def yview_moveto(self, arg):
    newy = int(float(self.sizetree) * float(arg))
    
    if self.y != newy:
      self._addy(newy - self.y)
      
      arg = float(newy) / float(self.sizetree)
      ScrolledCanvas.yview_moveto(self, arg)
      # Must redraw, as some new Node may be visible (But only those Nodes will be redrawn !).
      self.draw()
      
  def _addy(self, delta):
    if delta < 0:
      for i in range(-delta):
        node = self.first.previous()
        if node is None: break
        self.first = node
        self.y = self.y - 1
    else:
      max = self.sizetree - self.winfo_height() / self.nodeheight
      if self.y + delta > max: delta = max - self.y
      for i in range( delta):
        node = self.first.next()
        if node is None: break
        self.first = node
        self.y = self.y + 1
        
  def deselectall(self):
    """Deselect all selected Nodes."""
    if self.selection:
      for node in self.selection[:]: node.deselect()
      
  def _resized(self, event = None):
    if self.node:
      # self.y may now be invalid (two high).
      max = self.sizetree - self.winfo_height() / self.nodeheight
      if self.y > max: self._addy(max - self.y)
      self.draw()
      

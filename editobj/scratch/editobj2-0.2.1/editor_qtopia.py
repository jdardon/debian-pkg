# -*- coding: utf-8 -*-

# editor_gtk.py
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

from editobj2.editor import *
from xml.sax.saxutils import escape
import sys, os, os.path, time
import qt

dialog_boxes = []

class QtopiaEditorDialog(EditorDialog):
  def __init__(self, gui, direction = "h", on_validate = None, edit_child_in_self = 1, undo_stack = None, on_close = None):
    if on_validate:
      self.q = qt.QDialog(None, "", 1, qt.QWidget.WDestructiveClose)
      qt.QVBoxLayout(self.q)
      self.q.layout().setAutoAdd(1)
      vbox = qt.QVBox(self.q)
      
    else:
      self.q = qt.QMainWindow(None, "", qt.QWidget.WDestructiveClose)
      vbox = qt.QVBox(self.q)
      self.q.setCentralWidget(vbox)
      
    super(QtopiaEditorDialog, self).__init__(gui, direction, on_validate, edit_child_in_self, undo_stack, on_close)
    
    #vbox.setMargin(5)
    self.editor_pane.q.reparent(vbox, qt.QPoint())
    
    l = qt.QLabel("", vbox)
    l.setFixedHeight(2)
    
    
    
    #if on_validate:
    #  self.cancel = qt.QPushButton(editobj2.TRANSLATOR("Cancel"), hbox)
    #  self.ok     = qt.QPushButton(editobj2.TRANSLATOR("Ok"    ), hbox)
    #  self.cancel.setAutoDefault(0)
    #  self.ok    .setAutoDefault(0)
      
    #  self.ok    .connect(self.ok    , qt.SIGNAL("clicked()"), self.on_ok)
    #  self.cancel.connect(self.cancel, qt.SIGNAL("clicked()"), self.on_cancel)
    #else:
    #  self.ok = qt.QPushButton(editobj2.TRANSLATOR("Close" ), hbox)
    #  self.ok.setAutoDefault(0)
    
    #  self.ok.connect(self.ok, qt.SIGNAL("clicked()"), self.on_close)
    
    dialog_boxes.append(self) # Qt destroy dialog boxes if they are not kept in memory
    
  def on_close (self): self.q.close (); dialog_boxes.remove(self)
  def on_ok    (self): self.q.accept(); dialog_boxes.remove(self)
  def on_cancel(self): self.q.reject(); dialog_boxes.remove(self)
  
  def edit(self, o):
    EditorDialog.edit(self, o)
    label = self.editor_pane.hierarchy_pane.descr.label_for(o)
    self.q.setCaption(label.replace(u"\n", u" ").replace(u"\t", u" "))
    self.q.showMaximized()
    return self
  
  def wait_for_validation(self):
    if self.on_validate:
      response = self.q.exec_loop()
      if response == qt.QDialog.Accepted: self.on_validate(self.editor_pane.attribute_pane.o)
      else:                               self.on_validate(None)
    return self

  def main(self):
    if getattr(qt, "app", None):
      return qt.app.exec_loop()

  def set_default_size(self, width, height): pass # Always maximized

  
class QtopiaHEditorPane(HEditorPane):
  def __init__(self, gui, master, edit_child_in_self = 1, undo_stack = None):
    self.q = qt.QHBox(master.q)
    self.q.setSpacing(3)
    super(QtopiaHEditorPane, self).__init__(gui, master, edit_child_in_self, undo_stack)
    
    self.hi_box = qt.QHBox(self.q)
    self.childhood_pane.q.reparent(self.hi_box, qt.QPoint())
    self.hierarchy_pane.q.reparent(self.hi_box, qt.QPoint())
    
    self.scroll2 = qt.QScrollView(self.q)
    self.scroll2.setHScrollBarMode(qt.QScrollView.AlwaysOff)
    self.grid = qt.QGrid(2, self.scroll2.viewport())
    self.grid.layout().setAutoAdd(0)
    self.scroll2.addChild(self.grid)
    self.icon_pane     .q.reparent(self.grid, qt.QPoint())
    self.attribute_pane.q.reparent(self.grid, qt.QPoint())
    self.grid.layout().addWidget(self.icon_pane     .q, 0, 0, qt.QWidget.AlignTop)
    self.grid.layout().addWidget(self.attribute_pane.q, 1, 0, qt.QWidget.AlignBottom)
    self.grid.layout().addColSpacing(1, 3)
    
    self.scroll2.setResizePolicy(qt.QScrollView.AutoOneFit)
    self.scroll2.setFrameShape(qt.QFrame.NoFrame)
    
    p = qt.QSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Expanding)
    self.q.setSizePolicy(p)
    
  def _set_hierarchy_visible(self, visible):
    if visible: self.hi_box.show()
    else:       self.hi_box.hide()
      
  def edit(self, o):
    HEditorPane.edit(self, o)
    self.scroll2.setMinimumWidth(max(self.attribute_pane.q.sizeHint().width(), self.icon_pane.q.sizeHint().width()) + 35)
    
  def edit_child(self, o):
    HEditorPane.edit_child(self, o)
    if self.edit_child_in_self:
      self.scroll2.setMinimumWidth(max(self.attribute_pane.q.sizeHint().width(), self.icon_pane.q.sizeHint().width()) + 35)
      

      
class QtopiaVEditorPane(VEditorPane):
  def __init__(self, gui, master, edit_child_in_self = 1, undo_stack = None):
    self.q = qt.QVBox(master.q)
    self.q.setSpacing(3)
    super(QtopiaVEditorPane, self).__init__(gui, master, edit_child_in_self, undo_stack)
    
    self.hi_box = qt.QHBox(self.q)
    self.childhood_pane.q.reparent(self.hi_box, qt.QPoint())
    self.hierarchy_pane.q.reparent(self.hi_box, qt.QPoint())
    
    self.scroll2 = qt.QScrollView(self.q)
    self.scroll2.setHScrollBarMode(qt.QScrollView.AlwaysOff)
    self.grid = qt.QGrid(2, self.scroll2.viewport())
    self.grid.layout().setAutoAdd(0)
    self.scroll2.addChild(self.grid)
    self.icon_pane     .q.reparent(self.grid, qt.QPoint())
    self.attribute_pane.q.reparent(self.grid, qt.QPoint())
    self.grid.layout().addWidget(self.icon_pane     .q, 0, 0, qt.QWidget.AlignTop)
    self.grid.layout().addWidget(self.attribute_pane.q, 1, 0, qt.QWidget.AlignBottom)
    self.grid.layout().addColSpacing(1, 3)
    
    self.scroll2.setResizePolicy(qt.QScrollView.AutoOneFit)
    self.scroll2.setFrameShape(qt.QFrame.NoFrame)
    
  def _set_hierarchy_visible(self, visible):
    if visible: self.hi_box.show()
    else:       self.hi_box.hide()
    
  def edit(self, o):
    VEditorPane.edit(self, o)
    self.scroll2.setMinimumWidth(max(self.attribute_pane.q.sizeHint().width(), self.icon_pane.q.sizeHint().width()) + 35)
    
  def edit_child(self, o):
    VEditorPane.edit_child(self, o)
    if self.edit_child_in_self:
      self.scroll2.setMinimumWidth(max(self.attribute_pane.q.sizeHint().width(), self.icon_pane.q.sizeHint().width()) + 35)


class QtopiaAttributePane(AttributePane):
  def __init__(self, gui, master, edit_child = None, undo_stack = None):
    self.q = qt.QVBox(master.q)
    self.q = qt.QGrid(0, qt.QWidget.Horizontal, self.q)
    super(QtopiaAttributePane, self).__init__(gui, master, edit_child, undo_stack)
    self.q.layout().setAutoAdd(0)
    self.q.layout().addColSpacing(1, 5)
    self.q.connect(self.q, qt.SIGNAL("destroyed()"), self._destroyed)
    self.can_expand = 0
    
  def edit(self, o):
    if self.o is o: return
    
    self.can_expand = 0
    
    AttributePane.edit(self, o)
    self.q.show()
    
    if   isinstance(self.master, HEditorPane):
      pass # XXX
      #if self.can_expand: self.master.box.set_child_packing(self, 1, 1, 0, qt.PACK_END)
      #else:               self.master.box.set_child_packing(self, 0, 1, 0, qt.PACK_END)
      #w, h = self.master.box.size_request()
      #self.master.scroll2.get_child().set_size_request(w + 20, min(h, 800))
    
    elif isinstance(self.master, VEditorPane):
      pass # XXX
      #if self.can_expand: self.master.box.set_child_packing(self, 1, 1, 0, qt.PACK_START)
      #else:               self.master.box.set_child_packing(self, 0, 1, 0, qt.PACK_START)
      #w, h = self.master.box.size_request()
      #self.master.scroll2.get_child().set_size_request(w + 20, min(h, 500))
    
  def _delete_all_fields(self):
    if isinstance(self.master, EditorPane):
      self.q.hide()
      self.q.disconnect(self.q, qt.SIGNAL("destroyed()"), self._destroyed)
      parent = self.q.parent()
      #parent.removeChild(self.q)
      
      self.q = qt.QGrid(0, qt.QWidget.Horizontal, parent)
      self.q.layout().setAutoAdd(0)
      self.q.layout().addColSpacing(1, 5)
      self.q.connect(self.q, qt.SIGNAL("destroyed()"), self._destroyed)
      self.master.grid.layout().addWidget(self.q, 1, 0, qt.QWidget.AlignBottom)
      
    else:
      for c in self.q.children()[:]:
        if isinstance(c, qt.QWidget):
          #c.hide()
          self.q.removeChild(c)
          
  def _set_nb_fields(self, nb): pass
  
  def _new_field(self, name, field, unit, i):
    if len(name) > 17: name = name.replace(u" ", u"\n")
    label = qt.QLabel(name, self.q)
    i *= 2
    if i > 0: self.q.layout().addRowSpacing(i - 1, 3)
    
    self.q.layout().addWidget(label  , i, 0, qt.QWidget.AlignLeft)
    self.q.layout().addWidget(field.q, i, 2)
    self.q.layout().setRowStretch(i, field.y_flags)
    if unit:
      unit_label = qt.QLabel(unit, self.q)
      self.q.layout().addWidget(unit_label, i, 3, qt.QWidget.AlignLeft)
      unit_label.show()
    if field.y_flags: self.can_expand = 1
    
    if isinstance(self.master, QtopiaHEditorPane) and self.master.hi_box.isVisible():
      field.q.setMaximumWidth(280)
      
    label  .show()
    field.q.show()
    
    
class QtopiaIconPane(IconPane):
  def __init__(self, gui, master, use_small_icon = 0, compact = 0, bold_label = 1):
    self.q = qt.QHBox(master.q)
    super(QtopiaIconPane, self).__init__(gui, master, use_small_icon, compact, bold_label)
    self.q.layout().setAutoAdd(0)
    if self.compact: self.q.layout().addSpacing(10)
    else:            self.q.layout().addSpacing(20)
    self.image = None
    self.label = qt.QLabel(self.q)
    self.q.setMargin(12)
    self.layout_done = 0
    self.q.connect(self.q, qt.SIGNAL("destroyed()"), self._destroyed)
    
  def _set_icon_filename_label_details(self, icon_filename, label, details):
    if self.use_small_icon: load_icon = load_small_icon
    else:                   load_icon = load_big_icon
    
    if   not icon_filename:
      if self.image:
        self.q.removeChild(self.image)
        self.image = None
        self.pixmap_arrays = None
        
    elif isinstance(icon_filename, basestring):
      if self.image and not isinstance(self.image, qt.QLabel):
        self.q.removeChild(self.image)
        self.image = None
        self.pixmap_arrays = None
      if not self.image:
        self.image = qt.QLabel(self.q)
        self.q.layout().insertWidget(1, self.image, 0, qt.QWidget.AlignTop)
        
      self.image.setPixmap(load_icon(icon_filename))
      self.image.show()
      
    else:
      if self.image:
        self.image.hide()
        self.q.removeChild(self.image)
        
      import qtcanvas
      canvas = self.canvas = qtcanvas.QCanvas(self.q)
      canvas.setBackgroundColor(self.q.backgroundColor())
      
      self.pixmap_arrays = []
      
      x = y = z = 0
      icon_filename.sort()
      icon_filename.reverse()
      for filename in icon_filename:
        pixmap = load_icon(filename)
        pixmap_array = qtcanvas.QCanvasPixmapArray([pixmap], [qt.QPoint(0, 0)])
        self.pixmap_arrays.append(pixmap_array)
        i = qtcanvas.QCanvasSprite(pixmap_array, canvas)
        i.move(x, y)
        i.setZ(z)
        i.show()
        if self.use_small_icon:
          x += 10
          y +=  5
        else:
          x += 30
          y += 15
        z += 1
      canvas.resize(int(i.x() + pixmap.width()), int(i.y() + pixmap.height()))
      self.image = qtcanvas.QCanvasView(canvas, self.q)
      self.image.setVScrollBarMode(qt.QScrollView.AlwaysOff)
      self.image.setHScrollBarMode(qt.QScrollView.AlwaysOff)
      self.image.setFixedSize(int(i.x() + pixmap.width()), int(i.y() + pixmap.height()))
      self.image.setFrameShape(qt.QFrame.NoFrame)
      self.q.layout().insertWidget(1, self.image, 0, qt.QWidget.AlignTop)
      self.image.show()
      
    label   = escape(label)
    details = escape(details)
    if details:
      if self.bold_label: self.label.setText("<b>%s</b><br><br>%s\n" % (label.replace("\n", "<br>"), details.replace("\n", "<br>")))
      else:               self.label.setText("%s\n\n%s\n" % (label, details))
      
    else:
      if self.bold_label: self.label.setText("<b>%s</b>" % label.replace("\n", "<br>"))
      else:               self.label.setText(label)

    if not self.layout_done:
      if self.compact: self.q.layout().insertSpacing(2, 10)
      else:            self.q.layout().insertSpacing(2, 20)
      self.q.layout().insertWidget(3, self.label, 1)
      self.layout_done = 1
    self.q.show()
  

class QtopiaChildhoodPane(ChildhoodPane):
  def __init__(self, gui, master, undo_stack = None):
    self.q = qt.QVBox(master.q)
    super(QtopiaChildhoodPane, self).__init__(gui, master, undo_stack)
    
    self.button_move_up   = qt.QToolButton(self.q)
    self.button_add       = qt.QToolButton(self.q)
    self.button_remove    = qt.QToolButton(self.q)
    self.button_move_down = qt.QToolButton(self.q)
    self.button_move_up  .setIconSet(MOVE_UP_ICON_SET)
    self.button_add      .setIconSet(ADD_ICON_SET)
    self.button_remove   .setIconSet(REMOVE_ICON_SET)
    self.button_move_down.setIconSet(MOVE_DOWN_ICON_SET)
    self.button_move_up  .setAutoRaise(1)
    self.button_add      .setAutoRaise(1)
    self.button_remove   .setAutoRaise(1)
    self.button_move_down.setAutoRaise(1)
    self.button_move_up  .connect(self.button_move_up  , qt.SIGNAL("clicked()"), self.on_move_up)
    self.button_add      .connect(self.button_add      , qt.SIGNAL("clicked()"), self.on_add)
    self.button_remove   .connect(self.button_remove   , qt.SIGNAL("clicked()"), self.on_remove)
    self.button_move_down.connect(self.button_move_down, qt.SIGNAL("clicked()"), self.on_move_down)
    self.q.hide()
    
  def set_button_visibilities(self, visible1, visible2, visible3, visible4):
    if visible1 or visible2 or visible3 or visible4:
      self.button_move_up  .setEnabled(bool(visible1))
      self.button_add      .setEnabled(bool(visible2))
      self.button_remove   .setEnabled(bool(visible3))
      self.button_move_down.setEnabled(bool(visible4))
      self.q.show()
    else:
      self.q.hide()
    

class DynamicNode(object):
  def __init__(self, parent):
    self.children         = []
    self.children_created = 0
    self.is_expandable    = 0
    self.index            = 0
    if isinstance(parent, DynamicNode):
      last = parent.qt_node.firstChild()
      while last:
        last2 = last.nextSibling()
        if not last2: break
        last = last2
      self.qt_node = qt.QListViewItem(parent.qt_node, last)
      self.parent         = parent
      self.tree           = parent.tree
    else:
      self.qt_node = qt.QListViewItem(parent.q)
      self.parent         = None
      self.tree           = parent
      self.update()
      self.update_children()
      
    self.qt_node.node = self
    
  def has_children(self): return 0
  def create_children(self, old_children = None): return []
  
  def expanded(self):
    if not self.children_created:
      self.children_created = 1
      self.update_children()
    return self.children
  
  def collapsed(self):
    if self.children_created:
      self.children_created = 0
      for child in self.children[::-1]: child.destroy()
      self.is_expandable = 0
      self.update_children()
      
  def update(self): pass
  
  def update_children(self):
    if self.children_created:
      old_children = self.children[:]
      new_children = self.create_children(old_children)

      old_children_set = set(old_children)
      new_children_set = set(new_children)
      
      for child in old_children[::-1]:
        if not child in new_children_set: child.destroy()
        
      i = 0
      prev_qt_node = None
      for child in new_children:
        child.index = i
        i += 1
        child.qt_node.moveItem(prev_qt_node)
        prev_qt_node = child.qt_node
        
      for child in new_children:
        if not child in old_children_set:
          child.update()
          child.update_children()
          
      self.children.__init__(new_children)
      
    else:
      self.is_expandable = bool(self.has_children())
      self.qt_node.setExpandable(self.is_expandable)
      
  def destroy(self):
    for child in self.children[::-1]: child.destroy()
    try:
      if self.parent:
        self.parent.children.remove(self)
        self.parent.qt_node.takeItem(self.qt_node)
      else:
        self.tree.q.takeItem(self.qt_node)
    except RuntimeError: pass
    self.qt_node = None
    

class Qtopia_HierarchyNode(HierarchyNode, DynamicNode):
  def update(self):
    self.qt_node.setText(0, self.descr.label_for(self.o))
    icon_filename = self.descr.icon_filename_for(self.o)
    if isinstance(icon_filename, basestring): pixmap = load_small_icon(icon_filename)
    else:                                     pixmap = None
    if pixmap: self.qt_node.setPixmap(0, pixmap)
    
    
    
class QtopiaHierarchyPane(HierarchyPane):
  Node = Qtopia_HierarchyNode
  def __init__(self, gui, master, edit_child, undo_stack = None):
    self.q = qt.QListView(master.q)
    self.q.addColumn("")
    self.q.setRootIsDecorated(1)
    self.q.header().hide()
    self.q.setSorting(-1)
    self.tree = self
    
    super(QtopiaHierarchyPane, self).__init__(gui, master, edit_child, undo_stack)
    self.q.connect(self.q, qt.SIGNAL("destroyed()"), self._destroyed)
    self.q.connect(self.q, qt.SIGNAL("selectionChanged()"), self._selection_changed)
    self.q.setSelectionMode(qt.QListView.Extended)
    self.selected = None
    
    self.q.connect(self.q, qt.SIGNAL("expanded(QListViewItem *)"      ), self._expanded)
    self.q.connect(self.q, qt.SIGNAL("collapsed(QListViewItem *)"     ), self._collapsed)
    self.q.connect(self.q, qt.SIGNAL("doubleClicked(QListViewItem *)"), self._on_double_click)
    self.q.connect(self.q, qt.SIGNAL("pressed(QListViewItem *, const QPoint &, int)"), self._on_pressed)
    
  def edit(self, o):
    HierarchyPane.edit(self, o)
    self.q.firstChild().setOpen(1)
    
  def expand_tree_at_level(self, level):
    pass
  
  def _expanded(self, qt_node):
    self.timer = qt.QTimer()
    self.timer.connect(self.timer, qt.SIGNAL("timeout()"), qt_node.node.expanded)
    self.timer.start(0, 1)
    #qt_node.node.expanded()
    
  def _collapsed(self, qt_node):
    self.timer = qt.QTimer()
    self.timer.connect(self.timer, qt.SIGNAL("timeout()"), qt_node.node.collapsed)
    self.timer.start(0, 1)
    #qt_node.node.collapsed()

  def _on_pressed(self, qt_node, point, c):
    self.click_point = qt.QPoint(point.x(), point.y())
    
  def _on_context_menu(self, qt_node):
    actions = self._get_actions(self.selected, self.selected_parent)
    self.actions_callbacks = []
    
    menu = qt.QPopupMenu(self.q)
    for action in actions:
      def do_action(arg, action = action):
        self._action_activated(None, self.selected, action, self.selected_parent)
      menu.insertItem(action.label, do_action)
      self.actions_callbacks.append(do_action)
    menu.popup(self.click_point)
    
  def _selection_changed(self):
    selections = []
    qt_node = self.q.firstChild()
    while qt_node:
      if qt_node.isSelected(): selections.append(qt_node.node)
      qt_node = qt_node.itemBelow()
      
    if len(selections) == 1:
      node = selections[0]
      if node.parent: self.selected_parent = node.parent.o
      else:           self.selected_parent = None
      if self.selected == node.o:
        self._on_context_menu(node.qt_node, )
        
      else:
        self.selected = node.o
        self.edit_child(self.selected)
        
        if self.childhood_pane: self.childhood_pane.edit(self.selected_parent, self.selected)
        
    elif len(selections) > 1:
      parents = []
      for node in selections:
        if node.parent: parents.append(node.parent.o)
        else:           parents.append(None)
      self.selected_parent = introsp.ObjectPack(parents)
      self.selected = introsp.ObjectPack([node.o for node in selections])
      self.edit_child(self.selected)
      
      if self.childhood_pane: self.childhood_pane.edit(self.selected_parent, self.selected)
      
  def _on_double_click(self, qt_node):
    if qt_node.node.parent: parent = qt_node.node.parent.o
    else:                   parent = None
    actions = self._get_actions(qt_node.node.o, parent)
    for action in actions:
      if action.default:
        self.timer = qt.QTimer()
        self.f = lambda: self._action_activated(None, qt_node.node.o, action, parent)
        self.timer.connect(self.timer, qt.SIGNAL("timeout()"), self.f)
        self.timer.start(0, 1)
        
SMALL_ICON_SIZE = 32

_small_icons = {}
_big_icons   = {}

def load_big_icon(filename):
  pixmap = _big_icons.get(filename)
  if not pixmap: pixmap = _big_icons[filename] = qt.QPixmap(filename)
  return pixmap

def load_small_icon(filename):
  pixmap = _small_icons.get(filename)
  if not pixmap:
    pixmap = load_big_icon(filename)
    w = pixmap.width()
    h = pixmap.height()
    if (w > SMALL_ICON_SIZE) or (h > SMALL_ICON_SIZE):
      image = pixmap.convertToImage()
      if w > h: w2 = SMALL_ICON_SIZE; h2 = int(float(SMALL_ICON_SIZE) * h / w)
      else:     w2 = int(float(SMALL_ICON_SIZE) * w / h); h2 = SMALL_ICON_SIZE
      pixmap = qt.QPixmap(w2, h2)
      pixmap.convertFromImage(image.smoothScale(w2, h2))
    _small_icons[filename] = pixmap
  return pixmap

MOVE_UP_ICON_SET   = qt.QIconSet(load_big_icon(os.path.join(os.path.dirname(__file__), "icons", "go-up.png"  )))
ADD_ICON_SET       = qt.QIconSet(load_big_icon(os.path.join(os.path.dirname(__file__), "icons", "add.png"    )))
REMOVE_ICON_SET    = qt.QIconSet(load_big_icon(os.path.join(os.path.dirname(__file__), "icons", "remove.png" )))
MOVE_DOWN_ICON_SET = qt.QIconSet(load_big_icon(os.path.join(os.path.dirname(__file__), "icons", "go-down.png")))


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
import sys, os, os.path
import qt

dialog_boxes = []

class QtEditorDialog(EditorDialog, qt.QDialog):
  def __init__(self, gui, direction = "h", on_validate = None, edit_child_in_self = 1, undo_stack = None, on_close = None):
    if on_validate: qt.QDialog.__init__(self, None, "", 1, qt.QWidget.WDestructiveClose)
    else:           qt.QDialog.__init__(self, None, "", 0, qt.QWidget.WDestructiveClose)
    super(QtEditorDialog, self).__init__(gui, direction, on_validate, edit_child_in_self, undo_stack, on_close)
    
    qt.QVBoxLayout(self)
    self.layout().setAutoAdd(1)
    
    vbox = qt.QVBox(self)
    vbox.setMargin(5)
    self.editor_pane.reparent(vbox, qt.QPoint())

    qt.QLabel("", vbox)
    
    hbox = qt.QHBox(vbox)
    if on_validate:
      self.cancel = qt.QPushButton(editobj2.TRANSLATOR("Cancel"), hbox)
      self.ok     = qt.QPushButton(editobj2.TRANSLATOR("Ok"    ), hbox)
      self.cancel.setAutoDefault(0)
      self.ok    .setAutoDefault(0)
      
      self.ok    .connect(self.ok    , qt.SIGNAL("clicked()"), self.on_ok)
      self.cancel.connect(self.cancel, qt.SIGNAL("clicked()"), self.on_cancel)
    else:
      self.ok = qt.QPushButton(editobj2.TRANSLATOR("Close" ), hbox)
      self.ok.setAutoDefault(0)
      
      self.ok.connect(self.ok, qt.SIGNAL("clicked()"), self.on_close)
      
    self.on_close = on_close
    
    dialog_boxes.append(self) # Qt destroy dialog boxes if they are not kept in memory
    
  def on_close (self):
    self.close(1); dialog_boxes.remove(self)
    if self.on_close: self.on_close()
    
  def on_ok    (self): self.accept(); dialog_boxes.remove(self)
  def on_cancel(self): self.reject(); dialog_boxes.remove(self)
  
  def edit(self, o):
    EditorDialog.edit(self, o)
    label = self.editor_pane.hierarchy_pane.descr.label_for(o)
    self.setCaption(label.replace(u"\n", u" ").replace(u"\t", u" "))
    self.show()
    return self
  
  def wait_for_validation(self):
    if self.on_validate:
      response = self.exec_loop()
      if response == qt.QDialog.Accepted: self.on_validate(self.editor_pane.attribute_pane.o)
      else:                               self.on_validate(None)
    return self

  def main(self):
    if getattr(qt, "app", None):
      return qt.app.exec_loop()

  def set_default_size(self, width, height):
    self.setGeometry((qt.QApplication.desktop().width() - width) / 2, (qt.QApplication.desktop().height() - height) / 2, width, height)

  
class QtHEditorPane(HEditorPane, qt.QSplitter):
  def __init__(self, gui, master, edit_child_in_self = 1, undo_stack = None):
    qt.QSplitter.__init__(self, master)
    super(QtHEditorPane, self).__init__(gui, master, edit_child_in_self, undo_stack)
    
    self.hi_box = qt.QHBox(self)
    self.childhood_pane.reparent(self.hi_box, qt.QPoint())
    self.hierarchy_pane.reparent(self.hi_box, qt.QPoint())
    
    self.scroll2 = qt.QScrollView(self)
    self.scroll2.setHScrollBarMode(qt.QScrollView.AlwaysOff)
    self.grid = qt.QGrid(2, self.scroll2.viewport())
    self.grid.layout().setAutoAdd(0)
    self.scroll2.addChild(self.grid)
    self.icon_pane     .reparent(self.grid, qt.QPoint())
    self.attribute_pane.reparent(self.grid, qt.QPoint())
    self.grid.layout().addWidget(self.icon_pane     , 0, 0, qt.QWidget.AlignTop)
    self.grid.layout().addWidget(self.attribute_pane, 1, 0, qt.QWidget.AlignBottom)
    self.grid.layout().setColSpacing(1, 3)
    
    self.setCollapsible(self.scroll2, 0)
    self.scroll2.setResizePolicy(qt.QScrollView.AutoOneFit)
    self.scroll2.setFrameShape(qt.QFrame.NoFrame)
    
    p = qt.QSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Expanding)
    self.setSizePolicy(p)
    
  def _set_hierarchy_visible(self, visible):
    if visible:
      if self.sizes()[0] == 0: self.setSizes([200, self.width() - 200])
      self.setCollapsible(self.hi_box, 0)
    else:
      self.setCollapsible(self.hi_box, 1)
      if self.sizes()[0] != 0: self.setSizes([0, self.width()])
      
  def edit(self, o):
    HEditorPane.edit(self, o)
    self.scroll2.setMinimumWidth(max(self.attribute_pane.sizeHint().width(), self.icon_pane.sizeHint().width()) + 25)
    
  def edit_child(self, o):
    HEditorPane.edit_child(self, o)
    if self.edit_child_in_self:
      self.scroll2.setMinimumWidth(max(self.attribute_pane.sizeHint().width(), self.icon_pane.sizeHint().width()) + 25)
      

      
class QtVEditorPane(VEditorPane, qt.QSplitter):
  def __init__(self, gui, master, edit_child_in_self = 1, undo_stack = None):
    qt.QSplitter.__init__(self, qt.QWidget.Vertical, master)
    super(QtVEditorPane, self).__init__(gui, master, edit_child_in_self, undo_stack)
    
    self.hi_box = qt.QHBox(self)
    self.childhood_pane.reparent(self.hi_box, qt.QPoint())
    self.hierarchy_pane.reparent(self.hi_box, qt.QPoint())
    
    self.scroll2 = qt.QScrollView(self)
    self.scroll2.setHScrollBarMode(qt.QScrollView.AlwaysOff)
    self.grid = qt.QGrid(2, self.scroll2.viewport())
    self.grid.layout().setAutoAdd(0)
    self.scroll2.addChild(self.grid)
    self.icon_pane     .reparent(self.grid, qt.QPoint())
    self.attribute_pane.reparent(self.grid, qt.QPoint())
    self.grid.layout().addWidget(self.icon_pane     , 0, 0, qt.QWidget.AlignTop)
    self.grid.layout().addWidget(self.attribute_pane, 1, 0, qt.QWidget.AlignBottom)
    self.grid.layout().setColSpacing(1, 3)
    
    self.setCollapsible(self.scroll2, 0)
    self.scroll2.setResizePolicy(qt.QScrollView.AutoOneFit)
    self.scroll2.setFrameShape(qt.QFrame.NoFrame)
    
  def _set_hierarchy_visible(self, visible):
    if visible:
      if self.sizes()[0] == 0: self.setSizes([200, self.height() - 200])
      self.setCollapsible(self.hi_box, 0)
    else:
      self.setCollapsible(self.hi_box, 1)
      if self.sizes()[0] != 0: self.setSizes([0, self.height()])
      
  def edit(self, o):
    VEditorPane.edit(self, o)
    self.scroll2.setMinimumWidth(max(self.attribute_pane.sizeHint().width(), self.icon_pane.sizeHint().width()) + 25)
    
  def edit_child(self, o):
    VEditorPane.edit_child(self, o)
    if self.edit_child_in_self:
      self.scroll2.setMinimumWidth(max(self.attribute_pane.sizeHint().width(), self.icon_pane.sizeHint().width()) + 25)


class QtAttributePane(AttributePane, qt.QGrid):
  def __init__(self, gui, master, edit_child = None, undo_stack = None):
    qt.QGrid.__init__(self, 0, qt.QWidget.Horizontal, master)
    super(QtAttributePane, self).__init__(gui, master, edit_child, undo_stack)
    self.layout().setAutoAdd(0)
    self.layout().setColSpacing(1, 5)
    self.connect(self, qt.SIGNAL("destroyed()"), self._destroyed)
    self.can_expand = 0

  def edit(self, o):
    if self.o is o: return
    
    self.can_expand = 0
    
    AttributePane.edit(self, o)
    
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
    for c in self.children()[:]:
      if isinstance(c, qt.QWidget):
        #self.removeChild(c) # Segfault
        c.hide()
        self.layout().remove(c)
        c.deleteLater()
        
  def _set_nb_fields(self, nb): pass
  
  def _new_field(self, name, field, unit, i):
    label = qt.QLabel(name, self)
    i *= 2
    if i > 0: self.layout().setRowSpacing(i - 1, 3)
    
    self.layout().addWidget(label, i, 0, qt.QWidget.AlignLeft)
    #self.layout().addWidget(field, i, 2, qt.QWidget.AlignAuto)
    self.layout().addWidget(field, i, 2)
    self.layout().setRowStretch(i, field.y_flags)
    if unit:
      unit_label = qt.QLabel(unit, self)
      self.layout().addWidget(unit_label, i, 3, qt.QWidget.AlignLeft)
      unit_label.show()
    if field.y_flags: self.can_expand = 1
    
    label.show()
    field.show()
    
    
class QtIconPane(IconPane, qt.QHBox):
  def __init__(self, gui, master, use_small_icon = 0, compact = 0, bold_label = 1):
    qt.QHBox.__init__(self, master)
    super(QtIconPane, self).__init__(gui, master, use_small_icon, compact, bold_label)
    self.layout().setAutoAdd(0)
    if self.compact: self.layout().addSpacing(10)
    else:            self.layout().addSpacing(20)
    self.image = None
    self.label = qt.QLabel(self)
    self.setMargin(12)
    self.layout_done = 0
    self.connect(self, qt.SIGNAL("destroyed()"), self._destroyed)
    
  def _set_icon_filename_label_details(self, icon_filename, label, details):
    if self.use_small_icon: load_icon = load_small_icon
    else:                   load_icon = load_big_icon
    
    if   not icon_filename:
      if self.image:
        self.removeChild(self.image)
        self.image = None
        self.pixmap_arrays = None
        
    elif isinstance(icon_filename, basestring):
      if self.image and not isinstance(self.image, qt.QLabel):
        self.removeChild(self.image)
        self.image = None
        self.pixmap_arrays = None
      if not self.image:
        self.image = qt.QLabel(self)
        self.layout().insertWidget(1, self.image, 0, qt.QWidget.AlignTop)
        
      self.image.setPixmap(load_icon(icon_filename))
      self.image.show()
      
    else:
      if self.image:
        self.layout().remove(self.image)
        self.removeChild(self.image)
        
      import qtcanvas
      canvas = self.canvas = qtcanvas.QCanvas(self)
      canvas.setBackgroundColor(self.paletteBackgroundColor())
      
      self.pixmap_arrays = []
      
      x = y = z = 0
      icon_filename.sort()
      icon_filename.reverse()
      for filename in icon_filename:
        pixmap = load_icon(filename)
        pixmap_array = qtcanvas.QCanvasPixmapArray()
        pixmap_array.setImage(0, qtcanvas.QCanvasPixmap(pixmap, qt.QPoint()))
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
      self.image = qtcanvas.QCanvasView(canvas, self)
      self.image.setVScrollBarMode(qt.QScrollView.AlwaysOff)
      self.image.setHScrollBarMode(qt.QScrollView.AlwaysOff)
      self.image.setFixedSize(int(i.x() + pixmap.width()), int(i.y() + pixmap.height()))
      self.image.setFrameShape(qt.QFrame.NoFrame)
      self.layout().insertWidget(1, self.image, 0, qt.QWidget.AlignTop)
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
      if self.compact: self.layout().insertSpacing(2, 10)
      else:            self.layout().insertSpacing(2, 20)
      self.layout().insertWidget(3, self.label, 1, qt.QWidget.AlignAuto)
      self.layout_done = 1
    self.show()
  

class QtChildhoodPane(ChildhoodPane, qt.QVBox):
  def __init__(self, gui, master, undo_stack = None):
    qt.QVBox.__init__(self, master)
    super(QtChildhoodPane, self).__init__(gui, master, undo_stack)
    
    self.button_move_up   = qt.QToolButton(self)
    self.button_add       = qt.QToolButton(self)
    self.button_remove    = qt.QToolButton(self)
    self.button_move_down = qt.QToolButton(self)
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
    self.hide()
    
  def set_button_visibilities(self, visible1, visible2, visible3, visible4):
    if visible1 or visible2 or visible3 or visible4:
      self.button_move_up  .setEnabled(bool(visible1))
      self.button_add      .setEnabled(bool(visible2))
      self.button_remove   .setEnabled(bool(visible3))
      self.button_move_down.setEnabled(bool(visible4))
      self.show()
    else:
      self.hide()
    

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
      self.qt_node = qt.QListViewItem(parent)
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
        self.tree.takeItem(self.qt_node)
    except RuntimeError: pass
    self.qt_node = None
    

class Qt_HierarchyNode(HierarchyNode, DynamicNode):
  def update(self):
    self.qt_node.setText(0, self.descr.label_for(self.o))
    icon_filename = self.descr.icon_filename_for(self.o)
    if isinstance(icon_filename, basestring): pixmap = load_small_icon(icon_filename)
    else:                                     pixmap = None
    if pixmap: self.qt_node.setPixmap(0, pixmap)
    
    
    
class QtHierarchyPane(HierarchyPane, qt.QListView):
  Node = Qt_HierarchyNode
  def __init__(self, gui, master, edit_child, undo_stack = None):
    qt.QListView.__init__(self, master)
    self.addColumn("")
    self.setRootIsDecorated(1)
    self.tree = self
    self.header().hide()
    self.setSorting(-1)
    
    super(QtHierarchyPane, self).__init__(gui, master, edit_child, undo_stack)
    self.connect(self, qt.SIGNAL("destroyed()"), self._destroyed)
    self.setSelectionMode(qt.QListView.Extended)
    self.connect(self, qt.SIGNAL("selectionChanged()"), self._selection_changed)
    self.selected = None
    
    self.connect(self, qt.SIGNAL("expanded(QListViewItem *)" )     , self._expanded)
    self.connect(self, qt.SIGNAL("collapsed(QListViewItem *)")     , self._collapsed)
    self.connect(self, qt.SIGNAL("contextMenuRequested(QListViewItem *, const QPoint &, int)"), self._on_context_menu)
    self.connect(self, qt.SIGNAL("doubleClicked (QListViewItem *, const QPoint &, int)"), self._on_double_click)
    
  def edit(self, o):
    HierarchyPane.edit(self, o)
    self.firstChild().setOpen(1)
    
  def expand_tree_at_level(self, level):
    self._expand_tree_at_level(self.firstChild(), level)
    
  def _expand_tree_at_level(self, node, level):
    level -= 1
    node = node.firstChild()
    while node:
      node.setOpen(1)
      if level: self._expand_tree_at_level(node, level)
      node = node.nextSibling()
      
  def _expanded(self, qt_node):
    qt_node.node.expanded()
    
  def _collapsed(self, qt_node):
    qt_node.node.collapsed()
    
  def _on_context_menu(self, qt_node, point, column):
    actions = self._get_actions(self.selected, self.selected_parent)
    
    menu = qt.QPopupMenu(self)
    for action in actions:
      def do_action(arg, action = action):
        self._action_activated(None, self.selected, action, self.selected_parent)
      menu.insertItem(action.label, do_action)
    menu.popup(point)
    
  def _selection_changed(self):
    selections = []
    qt_node = self.firstChild()
    while qt_node:
      if qt_node.isSelected(): selections.append(qt_node.node)
      qt_node = qt_node.itemBelow()
      
    if len(selections) == 1:
      node = selections[0]
      if node.parent: self.selected_parent = node.parent.o
      else:           self.selected_parent = None
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

  def _on_double_click(self, qt_node, point, c):
    if qt_node.node.parent: parent = qt_node.node.parent.o
    else:                   parent = None
    actions = self._get_actions(qt_node.node.o, parent)
    for action in actions:
      if action.default:
        self.timer = qt.QTimer(self)
        self.timer.start(0, 1)
        self.timer.connect(self.timer, qt.SIGNAL("timeout()"), lambda: self._action_activated(None, qt_node.node.o, action, parent))
        
    
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
      if w > h: image = image.smoothScale(SMALL_ICON_SIZE, int(float(SMALL_ICON_SIZE) * h / w))
      else:     image = image.smoothScale(int(float(SMALL_ICON_SIZE) * w / h), SMALL_ICON_SIZE)
      pixmap = qt.QPixmap(image)
    _small_icons[filename] = pixmap
  return pixmap

MOVE_UP_ICON_SET   = qt.QIconSet(load_big_icon(os.path.join(os.path.dirname(__file__), "icons", "go-up.png"  )))
ADD_ICON_SET       = qt.QIconSet(load_big_icon(os.path.join(os.path.dirname(__file__), "icons", "add.png"    )))
REMOVE_ICON_SET    = qt.QIconSet(load_big_icon(os.path.join(os.path.dirname(__file__), "icons", "remove.png" )))
MOVE_DOWN_ICON_SET = qt.QIconSet(load_big_icon(os.path.join(os.path.dirname(__file__), "icons", "go-down.png")))


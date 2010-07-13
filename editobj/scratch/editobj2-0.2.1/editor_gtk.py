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
import gobject, gtk


class GtkEditorDialog(EditorDialog, gtk.Dialog):
  def __init__(self, gui, direction = "h", on_validate = None, edit_child_in_self = 1, undo_stack = None, on_close = None):
    if on_validate:
      flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
      buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK)
    else:
      flags = 0
      buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
    gtk.Dialog.__init__(self, None, None, flags, buttons)
    super(GtkEditorDialog, self).__init__(gui, direction, on_validate, edit_child_in_self, undo_stack, on_close)
    self.set_border_width(5)
    self.get_child().add(self.editor_pane)
    self.get_child().set_spacing(3)
    if not on_validate:
      self.get_child().get_children()[2].get_children()[0].connect("clicked", self.on_ok)
    self.on_close = on_close
    self.set_border_width(3)
    
  def on_ok(self, *args):
    self.destroy()
    if self.on_close: self.on_close()
    
  def edit(self, o):
    EditorDialog.edit(self, o)
    label = self.editor_pane.hierarchy_pane.descr.label_for(o)
    self.set_title(label.replace(u"\n", u" ").replace(u"\t", u" "))
    self.show_all()
    return self
  
  def wait_for_validation(self):
    if self.on_validate:
      response = self.run()
      if response == gtk.RESPONSE_OK: self.on_validate(self.editor_pane.attribute_pane.o)
      else:                           self.on_validate(None)
      self.destroy()
    return self
  
  def main(self): gtk.main()
  
  
class GtkHEditorPane(HEditorPane, gtk.HPaned):
  def __init__(self, gui, master, edit_child_in_self = 1, undo_stack = None):
    gtk.HPaned.__init__(self)
    super(GtkHEditorPane, self).__init__(gui, master, edit_child_in_self, undo_stack)
    
    self.box = gtk.VBox()
    self.box.pack_start(self.icon_pane     , 0, 1)
    self.box.pack_end  (self.attribute_pane, 0, 1)
    self.scroll1 = gtk.ScrolledWindow()
    self.scroll2 = gtk.ScrolledWindow()
    self.scroll1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.scroll2.set_policy(gtk.POLICY_NEVER    , gtk.POLICY_AUTOMATIC)
    self.scroll1.set_shadow_type(gtk.SHADOW_IN)
    self.scroll1.add(self.hierarchy_pane)
    self.scroll2.add_with_viewport(self.box)
    self.scroll2.get_child().set_shadow_type(gtk.SHADOW_NONE)
    self.hi_box = gtk.HBox()
    self.hi_box.pack_end  (self.scroll1       , 1, 1)
    self.hi_box.pack_start(self.childhood_pane, 0, 1)
    self.pack1(self.hi_box, 1, 0)
    self.pack2(self.scroll2, 1, 0)
    
  def edit(self, o):
    HEditorPane.edit(self, o)
    self.show_all()
    
  def _set_hierarchy_visible(self, visible):
    if visible:
      if self.get_position() == 0: self.set_position(300)
      self.scroll1.set_size_request(300, 200)
      self.child_set(self.hi_box, "shrink", 0)
    else:
      self.set_position(0)
      self.scroll1.set_size_request(0, 0)
      self.child_set(self.hi_box, "shrink", 1)
      
      
class GtkVEditorPane(VEditorPane, gtk.VPaned):
  def __init__(self, gui, master, edit_child_in_self = 1, undo_stack = None):
    gtk.VPaned.__init__(self)
    super(GtkVEditorPane, self).__init__(gui, master, edit_child_in_self, undo_stack)
    
    self.box = gtk.VBox()
    self.box.pack_start(self.icon_pane     , 0, 1)
    self.box.pack_start(self.attribute_pane, 0, 1)
    self.scroll1 = gtk.ScrolledWindow()
    self.scroll2 = gtk.ScrolledWindow()
    self.scroll1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.scroll2.set_policy(gtk.POLICY_NEVER    , gtk.POLICY_AUTOMATIC)
    self.scroll1.set_shadow_type(gtk.SHADOW_IN)
    self.scroll1.add(self.hierarchy_pane)
    self.scroll2.add_with_viewport(self.box)
    self.scroll2.get_child().set_shadow_type(gtk.SHADOW_NONE)
    self.hi_box = gtk.HBox()
    self.hi_box.pack_end  (self.scroll1       , 1, 1)
    self.hi_box.pack_start(self.childhood_pane, 0, 1)
    self.pack1(self.hi_box, 0, 0)
    self.pack2(self.scroll2, 1, 0)
    
  def edit(self, o):
    VEditorPane.edit(self, o)
    self.show_all()
    
  def _set_hierarchy_visible(self, visible):
    if visible:
      if self.get_position() == 0: self.set_position(200)
      self.scroll1.set_size_request(300, 200)
      self.child_set(self.hi_box, "shrink", 0)
    else:
      self.set_position(0)
      self.scroll1.set_size_request(0, 0)
      self.child_set(self.hi_box, "shrink", 1)
      
 


class GtkAttributePane(AttributePane, gtk.Table):
  def __init__(self, gui, master, edit_child = None, undo_stack = None):
    gtk.Table.__init__(self, 1, 3)
    super(GtkAttributePane, self).__init__(gui, master, edit_child, undo_stack)
    self.set_col_spacing(0, 3)
    self.set_row_spacings(3)
    self.connect("destroy", self._destroyed)
    self.can_expand = 0
    
  def edit(self, o):
    if self.o is o: return
    
    self.can_expand = 0
    AttributePane.edit(self, o)
    
    if   isinstance(self.master, HEditorPane):
      if self.can_expand: self.master.box.set_child_packing(self, 1, 1, 0, gtk.PACK_END)
      else:               self.master.box.set_child_packing(self, 0, 1, 0, gtk.PACK_END)
      self.master.box.show_all()
      w, h = self.master.box.size_request()
      self.master.scroll2.get_child().set_size_request(w + 20, min(h, 800))
      
    elif isinstance(self.master, VEditorPane):
      if self.can_expand: self.master.box.set_child_packing(self, 1, 1, 0, gtk.PACK_START)
      else:               self.master.box.set_child_packing(self, 0, 1, 0, gtk.PACK_START)
      self.master.box.show_all()
      w, h = self.master.box.size_request()
      self.master.scroll2.get_child().set_size_request(w + 20, min(h, 500))
      
    self.show_all()
    
  def _delete_all_fields(self):
    for widget in self.get_children(): widget.destroy()
    
  def _set_nb_fields(self, nb): self.resize(max(1, nb), 3)
  
  def _new_field(self, name, field, unit, i):
    label = gtk.Label(name)
    label.set_alignment(0.0, 0.5)
    self.attach(label, 0, 1, i, i + 1, gtk.FILL, gtk.FILL)
    self.attach(field, 1, 2, i, i + 1, gtk.EXPAND | gtk.FILL, field.y_flags)
    if unit:
      unit_label = gtk.Label(unit)
      unit_label.set_alignment(0.0, 0.5)
      self.attach(unit_label, 2, 3, i, i + 1, gtk.FILL, gtk.FILL)
    if field.y_flags & gtk.EXPAND: self.can_expand = 1
    

class GtkIconPane(IconPane, gtk.HBox):
  def __init__(self, gui, master, use_small_icon = 0, compact = 0, bold_label = 1):
    gtk.HBox.__init__(self)
    super(GtkIconPane, self).__init__(gui, master, use_small_icon, compact, bold_label)
    
    self.image = None
    
    self.label = gtk.Label()
    self.label.set_line_wrap(1)
    self.label.set_alignment(0.0, 0.6)
    self.label.set_padding(10, 0)
    self.pack_end(self.label, 1, 1)
    self.connect("destroy", self._destroyed)
    
  def _set_icon_filename_label_details(self, icon_filename, label, details):
    if self.use_small_icon: load_icon = load_small_icon
    else:                   load_icon = load_big_icon
    
    if   not icon_filename:
      if self.image:
        self.image.destroy()
        self.image = None
        
    elif isinstance(icon_filename, basestring):
      if isinstance(self.image, gtk.Fixed):
        self.image.destroy()
        self.image = None
      if not self.image:
        self.image = gtk.Image()
        self.image.set_alignment(0.5, 0.0)
        if self.compact: self.image.set_padding(10,  0)
        else:            self.image.set_padding(20, 10)
        self.pack_start(self.image, 0, 1)
        self.image.show_all()
        
      self.image.set_from_pixbuf(load_icon(icon_filename))
    else:
      if self.image: self.image.destroy()
      self.image = gtk.Fixed()
      if self.compact: pass
      else:            self.image.set_border_width(5)
      x = y = 0
      icon_filename.sort()
      icon_filename.reverse()
      for filename in icon_filename:
        i = gtk.Image()
        i.set_from_pixbuf(load_icon(filename))
        self.image.put(i, x, y)
        if self.use_small_icon:
          x += 10
          y +=  5
        else:
          x += 30
          y += 15
      self.pack_start(self.image, 0, 1)
      self.image.show_all()
      
    label   = escape(label)
    details = escape(details)
    if details:
      if self.bold_label: self.label.set_markup("<b>%s</b>\n\n%s\n" % (label, details))
      else:               self.label.set_markup("%s\n\n%s\n" % (label, details))
      
    else:
      if self.bold_label: self.label.set_markup("<b>%s</b>" % label)
      else:               self.label.set_markup(label)
    self.show_all()
  

class GtkChildhoodPane(ChildhoodPane, gtk.VBox):
  def __init__(self, gui, master, undo_stack = None):
    gtk.VBox.__init__(self)
    super(GtkChildhoodPane, self).__init__(gui, master, undo_stack)
    
    self.button_move_up   = gtk.Button()
    self.button_add       = gtk.Button()
    self.button_remove    = gtk.Button()
    self.button_move_down = gtk.Button()
    self.button_move_up  .set_image(gtk.image_new_from_stock(gtk.STOCK_GO_UP  , gtk.ICON_SIZE_BUTTON))
    self.button_add      .set_image(gtk.image_new_from_stock(gtk.STOCK_ADD    , gtk.ICON_SIZE_BUTTON))
    self.button_remove   .set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE , gtk.ICON_SIZE_BUTTON))
    self.button_move_down.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON))
    self.button_move_up  .connect("clicked", self.on_move_up)
    self.button_add      .connect("clicked", self.on_add)
    self.button_remove   .connect("clicked", self.on_remove)
    self.button_move_down.connect("clicked", self.on_move_down)
    self.pack_start(self.button_move_up  , 1, 1)
    self.pack_start(self.button_add      , 1, 1)
    self.pack_start(self.button_remove   , 1, 1)
    self.pack_start(self.button_move_down, 1, 1)
    self.button_move_up  .set_relief(gtk.RELIEF_NONE)
    self.button_add      .set_relief(gtk.RELIEF_NONE)
    self.button_remove   .set_relief(gtk.RELIEF_NONE)
    self.button_move_down.set_relief(gtk.RELIEF_NONE)
    self.set_property("visible", 0)
    self.set_property("no-show-all", 1)
    
  def set_button_visibilities(self, visible1, visible2, visible3, visible4):
    if visible1 or visible2 or visible3 or visible4:
      self.button_move_up  .set_property("sensitive", visible1)
      self.button_add      .set_property("sensitive", visible2)
      self.button_remove   .set_property("sensitive", visible3)
      self.button_move_down.set_property("sensitive", visible4)
      self.set_property("visible", 1)
      self.set_property("no-show-all", 0)
      self.show_all()
    else:
      self.button_move_up  .set_property("sensitive", 0)
      self.button_add      .set_property("sensitive", 0)
      self.button_remove   .set_property("sensitive", 0)
      self.button_move_down.set_property("sensitive", 0)
      

class DynamicNode(object):
  def __init__(self, parent):
    self.children         = []
    self.children_created = 0
    self.is_expandable    = 0
    self.index            = 0
    if isinstance(parent, DynamicNode):
      self.parent         = parent
      self.tree           = parent.tree
    else:
      self.parent         = None
      self.tree           = parent
      self.tree.append(None)
      self.update()
      self.update_children()
      
  def path(self):
    if self.parent: return self.parent.path() + (self.index,)
    return (0,)

  def get_by_path(self, path, i = 0):
    if i == len(path) - 1: return self
    i += 1
    return self.children[path[i]].get_by_path(path, i)
    
  def has_children(self): return 0
  def create_children(self, old_children = None): return []
  
  def expanded(self):
    if not self.children_created:
      self.children_created = 1
      self.update_children()
      if self.is_expandable:
        del self.tree[self.path() + (len(self.children),)]
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
      for child in self.children:
        child.index = i
        i += 1
        
      reorder = []
      i = 0
      for child in new_children:
        if child in old_children_set:
          reorder.append(child.index)
          child.index = i
          i += 1
          
      if reorder:
        self.tree.reorder(self.tree.get_iter(self.path()), reorder)
        self.children.sort(lambda a, b: cmp(a.index, b.index))
      
      i = 0
      iter = self.tree.get_iter(self.path())
      for child in new_children:
        child.index = i
        if not child in old_children_set:
          self.children.insert(i, child)
          self.tree.insert(iter, i)
        i += 1
        
      for child in new_children:
        if not child in old_children_set:
          child.update()
          child.update_children()
      
    else:
      is_expandable = bool(self.has_children())
      if   is_expandable and (not self.is_expandable):
        self.tree.append(self.tree.get_iter(self.path()))
      elif self.is_expandable and (not is_expandable):
        del self.tree[self.path() + (0,)]
      self.is_expandable = is_expandable
      
      #if (self.parent is None) and is_expandable: self.tree.view.expand_to_path((0,))
      
  def destroy(self):
    for child in self.children[::-1]: child.destroy()
    path = self.path()
    if self.parent: self.parent.children.remove(self)
    del self.tree[path]
    

class Gtk_HierarchyNode(HierarchyNode, DynamicNode):
  def update(self):
    icon_filename = self.descr.icon_filename_for(self.o)
    if isinstance(icon_filename, basestring): pixbuf = load_small_icon(icon_filename)
    else:                                     pixbuf = None
    self.tree[self.path()] = self.descr.label_for(self.o), pixbuf
    
    
    
class GtkHierarchyPane(HierarchyPane, gtk.TreeView):
  Node = Gtk_HierarchyNode
  def __init__(self, gui, master, edit_child, undo_stack = None):
    self.tree = gtk.TreeStore(gobject.TYPE_STRING, gtk.gdk.Pixbuf)
    self.tree.view = self
    gtk.TreeView.__init__(self, self.tree)
    column = gtk.TreeViewColumn(None)
    
    self.set_headers_visible(0)
    pixbuf_render = gtk.CellRendererPixbuf()
    column.pack_start(pixbuf_render, 0)
    column.add_attribute(pixbuf_render, "pixbuf", 1)
    text_render = gtk.CellRendererText()
    column.pack_start(text_render)
    column.add_attribute(text_render, "text", 0)
    self.append_column(column)
    
    super(GtkHierarchyPane, self).__init__(gui, master, edit_child, undo_stack)
    self.connect("destroy", self._destroyed)
    self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
    self.get_selection().connect("changed", self._selection_changed)
    self.set_size_request(200, 200)
    self.selected = None
    
    self.connect("row-expanded"      , self._expanded)
    self.connect("row-collapsed"     , self._collapsed)
    self.connect("button_press_event", self._button_pressed)
    
  def edit(self, o):
    HierarchyPane.edit(self, o)
    self.expand_to_path((0,))
    self.show_all()
    
  def expand_tree_at_level(self, level):
    self._expand_tree_at_level(level, (0,))
    
  def _expand_tree_at_level(self, level, path):
    self.expand_to_path(path)
    if len(path) < level:
      for i in range(self.tree.iter_n_children(self.tree[path].iter)):
        self._expand_tree_at_level(level, path + (i,))
        
#  def select_object(self, o):
    
    
  def _expanded(self, treeview, iter, path):
    node = self.root_node.get_by_path(path)
    node.expanded()
    
  def _collapsed(self, treeview, iter, path):
    node = self.root_node.get_by_path(path)
    node.collapsed()
    
  def _button_pressed(self, widget, event):
    if event.type == gtk.gdk._2BUTTON_PRESS:
      actions = self._get_actions(self.selected, self.selected_parent)
      for action in actions:
        if action.default:
          self._action_activated(None, self.selected, action, self.selected_parent)
    else:
      self.last_button      = event.button
      self.last_button_time = event.time
      
  def _selection_changed(self, *args):
    tree, rows = self.get_selection().get_selected_rows()
    if len(rows) == 0:
      self.edit_child(None)
      if self.childhood_pane: self.childhood_pane.edit(None, None)
      return
    
    if len(rows) == 1:
      node   = self.root_node.get_by_path(rows[0])
      if node.parent: self.selected_parent = node.parent.o
      else:           self.selected_parent = None
      self.selected = node.o
      self.edit_child(self.selected)
      
      if self.childhood_pane: self.childhood_pane.edit(self.selected_parent, self.selected)
      
    elif rows:
      nodes = [self.root_node.get_by_path(row) for row in rows]
      parents = []
      for node in nodes:
        if node.parent: parents.append(node.parent.o)
        else:           parents.append(None)
      self.selected_parent = introsp.ObjectPack(parents)
      self.selected = introsp.ObjectPack([node.o for node in nodes])
      self.edit_child(self.selected)

      if self.childhood_pane: self.childhood_pane.edit(self.selected_parent, self.selected)
      
    if self.last_button == 3:
      self.last_button = 0
      actions = self._get_actions(self.selected, self.selected_parent)
      
      menu = gtk.Menu()
      for action in actions:
        menu_item = gtk.MenuItem(action.label)
        menu_item.connect("activate", self._action_activated, self.selected, action, self.selected_parent)
        menu.append(menu_item)
      menu.show_all()
      menu.popup(None, None, None, self.last_button, self.last_button_time)
   

SMALL_ICON_SIZE = 32

_small_icons = {}
_big_icons   = {}

def load_big_icon(filename):
  pixbuf = _big_icons.get(filename)
  if not pixbuf: pixbuf = _big_icons[filename] = gtk.gdk.pixbuf_new_from_file(filename)
  return pixbuf

def load_small_icon(filename):
  pixbuf = _small_icons.get(filename)
  if not pixbuf:
    pixbuf = load_big_icon(filename)
    w = pixbuf.get_width()
    h = pixbuf.get_height()
    if (w > SMALL_ICON_SIZE) or (h > SMALL_ICON_SIZE):
      if w > h: pixbuf = pixbuf.scale_simple(SMALL_ICON_SIZE, int(float(SMALL_ICON_SIZE) * h / w), gtk.gdk.INTERP_BILINEAR)
      else:     pixbuf = pixbuf.scale_simple(int(float(SMALL_ICON_SIZE) * w / h), SMALL_ICON_SIZE, gtk.gdk.INTERP_BILINEAR)
    _small_icons[filename] = pixbuf
  return pixbuf

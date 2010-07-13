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

from __future__ import nested_scopes

import os, os.path, types, Tkinter
import globdef, song, view, ui

class LyricView(view.View):
  def __init__(self, _song, partition, zoom = 1.0):
    view.View.__init__(self, _song, partition, zoom)
    self.partition      = partition
    
  def draw(self, canvas, x = 0, y = 0):
    if hasattr(self, "canvas"):
      self.canvas.itemconfigure(self.header, text = self.partition.header)
      x1, y1, x2, y2 = canvas.bbox(self.header)
      old_y1 = self.y1
      self.y1 = y + y2 - y1 + 8
      
      self.canvas.move(self.group, x - self.x, self.y1 - old_y1)
      
      self.canvas.coords(self.header, canvas.app.old_x1 + 20, y + 4)
      self.bar.coords(x2 + 20, y + 10)
      self.x = x
      
      self.canvas.itemconfigure(self.header, text = self.partition.header)
      
      self.update()
      
      self.y2 = self.y1 + self.height
    else:
      self.canvas = canvas
      
      self.group  = view.new_tag()
      self.header = canvas.create_text(canvas.app.old_x1 + 20, y + 4, text = self.partition.header, anchor = "nw", tag = (self.group, "noscroll"))
      x1, y1, x2, y2 = canvas.bbox(self.header)
      self.y1 = y + y2 - y1 + 8
      self.x = x
      
      self.bar = ui.LinksBar(canvas, x2 + 20, y + 10, ((_("Move up")   , lambda event: self.canvas.app.move_partition(self.partition, -1)),
                                                       (_("Move down") , lambda event: self.canvas.app.move_partition(self.partition,  1)),
                                                       (_("Delete")    , lambda event: self.canvas.app.on_partition_delete(self.partition)),
                                                       (_("Properties"), lambda event: self.on_prop()),
                                                       ),
                             tag = (self.group, "noscroll")
                             )
      
      self.text = Tkinter.Text(canvas, wrap = "word", font = "Helvetica -12", highlightthickness = 1, highlightcolor = "#AAAADD", selectbackground = "#CCCCFF")
      if self.partition.text and (self.partition.text[-1] == "\n"):
        self.text.insert("end", self.partition.text[:-1])
      else: self.text.insert("end", self.partition.text)
      
      self.text.bind("<FocusIn>"   , self.on_focus)
      self.text.bind("<FocusOut>"  , self.on_focus_out)
      self.text.bind("<KeyRelease>", self.on_text_key_release)
      self.text.bind("<KeyPress>"  , self.on_text_key_press)
      self.text_item = canvas.create_window(self.x, self.y1, window = self.text, anchor = "nw", tag = self.group)
      self.update()
      
      self.y2 = self.y1 + self.height
      
    return x, self.y2
  
  def on_focus(self, event):
    if self.canvas.app.partition:
      self.canvas.app.partition.view.deselect_all()
    self.canvas.app.set_partition(self.partition)
    self.old_text = self.partition.text
    
  def on_focus_out(self, event):
    if not hasattr(self, "canvas"): return # Being destroyed
    
    old_text = self.old_text
    new_text = self.partition.text
    
    def cancel_it():
      self.partition.text = old_text
      self.text.delete("0.0", "end")
      if self.partition.text and (self.partition.text[-1] == "\n"):
        self.text.insert("end", self.partition.text[:-1])
      else: self.text.insert("end", self.partition.text)
      
      self.canvas.app.cancel.add_redo(redo_it)
      
    def redo_it():
      self.partition.text = new_text
      self.text.delete("0.0", "end")
      if self.partition.text and (self.partition.text[-1] == "\n"):
        self.text.insert("end", self.partition.text[:-1])
      else: self.text.insert("end", self.partition.text)
      
      self.canvas.app.cancel.add_cancel(cancel_it)
      
    self.canvas.app.cancel.add_cancel(cancel_it)
    
  def on_text_key_release(self, event):
    self.partition.text = unicode(self.text.get("0.0", "end"))
    
    x1, y1, x2, y2 = self.text.bbox("insert")
    self.canvas.app.ensure_visible_x(x1 + self.text_x)
    
  def on_text_key_press(self, event):
    if   event.char == "-":
      self.text.insert("insert", "-\t")
      return "break"
    
    elif event.char == "_":
      self.text.insert("insert", "_\t")
      return "break"
    
    elif event.char == " ":
      self.text.insert("insert", "\t")
      return "break"
    
    elif event.keysym == "Return":
      self.text.insert("insert", "\n")
      self.canvas.draw()
      return "break"
    
  def update(self):
    self.height = self.text.get("0.0", "end").count("\n") * 15 + 10
    
    melody = self.partition.get_melody()
    if melody and melody.notes:
      #melody = filter(lambda note: not (note.linked and note.linked_from), melody.notes)
      melody = melody.notes
      x0 = self.time_to_x(melody[0].time) - 2
      tabs = map(lambda note: str(self.time_to_x(note.time) - x0), melody[1:])
      
      self.text.configure(tabs  = " ".join(tabs))
      self.text_x = self.time_to_x(melody[0].time) - 10
    else:
      self.text_x = self.x
      
    self.canvas.coords       (self.text_item, self.text_x, self.y1)
    self.canvas.itemconfigure(self.text_item,
                              width = max(self.canvas.app.width - self.x - 20,
                                          int(self.time_to_x(self.song.mesures[-1].endtime() + self.song.mesures[-1].duration)) - self.text_x - 40
                                          ),
                              height = self.height,
                              )
    
  def rythm_changed(self): pass
  
  def add_selection   (self, graphic_note): pass
  def remove_selection(self, graphic_note): pass
  def deselect_all(self): pass
    
  def set_default_note(self, default_note): pass
  
  def on_key_press    (self, event): pass
  def on_button_press1(self, event, x, y): pass
  def on_button_press2(self, event, x, y): pass
  def on_button_press3(self, event, x, y): # A right click on the header hide the lyrics view
    x1, y1, x2, y2 = self.canvas.bbox(self.header)
    if y1 <= y <= y2: self.hide()
    
  def select_at(self, time):
    self.text.focus_set()
    return None
    
  def select_in_box(self, x1, y1, x2, y2): return None
  def note_at(self, x, y, create = 0): return None
  
  def paste(self, graphic_note_y_notes): pass
  
  def big_change_done(self): pass
  
  def x_to_time      (self, x   ): return int((x - self.x - 10) / self.zoom)
  def x_to_round_time(self, x   ): return int(round(int(((x - self.x - 10.0) / self.zoom / self.default_note.time) + 0.4) * self.default_note.time))
  def time_to_x      (self, time): return time * self.zoom + self.x + 10
  
  def destroy(self):
    if hasattr(self, "canvas"): # else, not initialized by "draw"
      self.text.destroy()
      self.bar.destroy()
      self.canvas.delete(self.group)
      del self.canvas
      
  def selected_notes(self): return ()
  
  def __getstate__(self): return None
  def __setstate__(self, dict): pass
  def __getinitargs__(self): return self.song, self.partition, self.zoom
  
  def __str__(self): return _("Lyrics").encode("latin")
  
  def __xml__(self, xml, context, hidden = 0):
    xml.write('''\t\t<view type="lyrics"''')
    if hidden:       xml.write(' hidden="1"')
    xml.write("/>\n")
    
lyric_view_type =  view.ViewType("", _("Lyrics"), LyricView, register = 0)



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
  def __init__(self, _song, partition, strings = None, zoom = 1.0):
    view.View.__init__(self, _song, partition, zoom)
    self.partition      = partition
    self.graphic_notes  = {}
    self.selection      = []
    self.focus          = None
    self.mesures        = []
    self.mesuresmarks   = []
    self.height         = 25
    
    lyrics_view = self
    class GraphicNote(view.GraphicNote): # Internal class
      def __init__(self, note):
        self.note        = note
        self.selected    = 0
        self.focus       = 0
        self.label       = None
        self.x1 = self.x = lyrics_view.time_to_x(note.mesure.time)
        self.x2          = lyrics_view.time_to_x(note.mesure.endtime())
        self.text        = None
        self.tag         = lyrics_view.group + "_" + str(note.mesure.time)
        self.tag_all     = (self.tag, lyrics_view.group)
        
        lyrics_view.graphic_notes[note.mesure] = self
        
        self.draw_text()
        
      def draw_text(self):
        if self.label: lyrics_view.canvas.delete(self.label)
        self.label = lyrics_view.canvas.create_text(self.x1, self.y + 6, width = self.note.mesure.duration * lyrics_view.zoom - 15, text = self.note.text, anchor = "nw", tag = self.tag_all)
        x1, y1, x2, y2 = lyrics_view.canvas.bbox(self.label)
        self.height = y2 - y1 + 12
        if self.height > lyrics_view.height: lyrics_view.canvas.draw()
        
      def get_view(self): return lyrics_view
      def get_self(self):
        return lyrics_view.note_at(self.x, self.y) or lyrics_view.drawnote(self.note)
      
      def update(self, note = None):
        if note is None: note = self.note
        self.set_text(note.text)
        
      def delete(self):
        if self.note.text: lyrics_view.partition.delnote(self.note) # Else it is a "fake" lyric !
        self.destroy()
        
      def destroy(self):
        del lyrics_view.graphic_notes[self.note.mesure]
        if self.text:
          self.text.unbind("<FocusOut>", self.text_event)
          self.text.destroy()
          self.text = None
        if self.selected:
          self.set_selected(0)
          lyrics_view.selection.remove(self)
        lyrics_view.canvas.delete(self.tag)
        
      def is_at(self, x, y):
        return self.x1 <= x < self.x2 and lyrics_view.y1 <= y <= lyrics_view.y2
        
      def set_selected(self, selected):
        if selected == self.selected: return
        
        self.selected = selected
        if selected:
          self.selection = lyrics_view.canvas.create_rectangle(self.x1 - 6, self.y, self.x1 - 10 + self.note.mesure.duration * lyrics_view.zoom, self.y + lyrics_view.height, fill = "#DDDDFF", outline = "#AAAADD", width = 2)
          lyrics_view.canvas.tag_raise(self.label)
        else:
          lyrics_view.canvas.delete(self.selection)
          del self.selection
          
      def set_focus(self, focus):
        if focus == self.focus: return
        
        self.focus = focus
        if focus:
          self.old_note_text = self.note.text # Save the old text
          
          self.text = Tkinter.Text(lyrics_view.canvas, wrap = "word", font = "Helvetica -12", selectbackground = "#CCCCFF")
          self.text.insert("end", self.note.text)
          self.text_event = self.text.bind("<FocusOut>", self.on_text_focusout)
          self.text_item = lyrics_view.canvas.create_window(self.x1 - 7, self.y, window = self.text, width = self.note.mesure.duration * lyrics_view.zoom - 2, height = lyrics_view.height, anchor = "nw", tag = self.tag_all)
          self.text.focus_set()
          
          def test(*args): print "OK"
          self.text.bind("<KeyPress-->", test)
          self.text.bind("<KeyPress-\t>", test)
        else:
          self.on_text_focusout()
          lyrics_view.canvas.delete(self.text_item)
          lyrics_view.canvas.focus_set()
          
          def cancel_it():
            s = self.get_self()
            old_note_text = self.old_note_text
            self.old_note_text = s.note.text # Save the current text
            s.set_text(old_note_text)
            lyrics_view.canvas.app.cancel.add_redo(redo_it)
            
          def redo_it():
            s = self.get_self()
            old_note_text = self.old_note_text
            self.old_note_text = s.note.text # Save the current text
            s.set_text(old_note_text)
            lyrics_view.canvas.app.cancel.add_cancel(cancel_it)
            
          lyrics_view.canvas.app.cancel.add_cancel(cancel_it)
          
      def set_max_height(self, max_height):
        if self.text: lyrics_view.canvas.itemconfigure(self.text_item, height = max_height)
        
      def on_text_focusout(self, event = None):
        if self.text:
          self.set_text(unicode(self.text.get("0.0", "end")[0:-1]))
          
      def set_text(self, text):
        if self.note.text == "": # A fake lyric that become real...
          partition.addnote(self.note)
          lyrics_view.checktime(self.note.mesure.time)
          
        self.note.text = text
        if text == "": # A lyric that become a fake lyric !
          partition.delnote(self.note)
          self.delete()
        else: self.draw_text()
        
      def drag(self, canvas, tag):
        canvas.create_text(self.x1, self.y + 6, width = self.note.mesure.duration * lyrics_view.zoom - 15, text = self.note.text, anchor = "nw", tag = tag)
        
      def __repr__(self): return "<GraphicLyric for %s>" % self.note
      
    self.drawlyric = self.drawnote = GraphicNote
    
  def draw(self, canvas, x = 0, y = 0):
    if hasattr(self, "canvas"):
      self.canvas.itemconfigure(self.header, text = self.partition.header)
      x1, y1, x2, y2 = canvas.bbox(self.header)
      old_y1 = self.y1
      self.y1 = y + y2 - y1 + 8
      
      self.canvas.move(self.group, x - self.x, self.y1 - old_y1)

      self.bar.coords(x2 + 20, self.bar.y)
      self.x = x
      
      self.canvas.itemconfigure(self.header, text = self.partition.header)
      
      # All GraphicNote instance share the same y
      self.drawnote.y = self.y1 = y + y2 - y1 + 8
      
      old_height = self.height
      if self.graphic_notes:
        self.height = max(map(lambda graphic_note: graphic_note.height, self.graphic_notes.values()))
        if self.height < 25: self.height = 25
      self.y2 = self.y1 + self.height
      
      if old_height != self.height:
        self.rythm_changed()
        for graphic_note in self.graphic_notes.values(): graphic_note.set_max_height(self.height)
    else:
      self.canvas = canvas
      
      self.group  = view.new_tag()
      self.header = canvas.create_text(x, y + 4, text = self.partition.header, anchor = "nw", tag = self.group)
      x1, y1, x2, y2 = canvas.bbox(self.header)
      self.y1 = y + y2 - y1 + 8
      self.x = x
      
      self.bar = ui.LinksBar(canvas, x2 + 20, y + 10, ((_("Move up")   , lambda event: self.canvas.app.move_partition(self.partition, -1)),
                                                       (_("Move down") , lambda event: self.canvas.app.move_partition(self.partition,  1)),
                                                       (_("Delete")    , lambda event: self.canvas.app.on_partition_delete(self.partition)),
                                                       (_("Properties"), lambda event: self.on_prop()),
                                                       (_("Convert to the new lyrics system"), lambda event: self.on_convert()),
                                                       ),
                             tag = self.group
                             )
      
      # All GraphicNote instance share the same y
      self.drawnote.y = self.y1 = y + y2 - y1 + 8
      
      map(self.drawnote, self.partition.notes)
      
      self.y2 = self.y1 + self.height
      
      self.checktime()
      
    return x, self.y2
  
  def on_convert(self):
    canvas = self.canvas
    
    import lyric2
    lyrics2 = self.partition.to_lyrics2()
    lyrics2.setviewtype(lyric2.lyric_view_type)
    self.song.partitions.insert(self.song.partitions.index(self.partition), lyrics2)
    self.song.partitions.remove(self.partition)
    canvas.draw()
    
  def rythm_changed(self):
    self.canvas.delete(*self.mesuresmarks)
    self.mesures = []
    self.checktime()
    
  def checktime(self, time = 0):
    if len(self.mesures) < len(self.song.mesures):
      map(self.add_mesure, self.song.mesures[len(self.mesures):])
      self.canvas.app.set_scroll_region()
      
  def add_mesure(self, mesure):
    x = mesure.endtime() * self.zoom + 2 + self.x
    if mesure.syncope:
      self.mesuresmarks.append(self.canvas.create_text(self.x + mesure.time * self.zoom, self.y1 + 10, text = "3", tag = self.group))
      self.mesuresmarks.append(self.canvas.create_line(x, self.y1 + 20, x, self.y2, fill = 'gray50', width = 2, tag = self.group))
    else:
      self.mesuresmarks.append(self.canvas.create_line(x, self.y1, x, self.y2, fill = 'gray50', width = 2, tag = self.group))
    self.mesures.append(mesure)
    
  def add_selection(self, graphic_note):
    if graphic_note in self.selection: return
    
    self.selection.append(graphic_note)
    graphic_note.set_selected(1)
    
    self.previoustype = 0
    
  def set_focus(self, graphic_note):
    if self.focus: self.focus.set_focus(0)
    self.focus = graphic_note
    if graphic_note: graphic_note.set_focus(1)
    
  def remove_selection(self, graphic_note):
    self.selection.remove(graphic_note)
    graphic_note.set_selected(0)
    
  def deselect_all(self):
    for graphic_note in self.selection: graphic_note.set_selected(0)
    self.selection = []
    self.set_focus(None)
    
  def set_default_note(self, default_note): pass
  
  def on_key_press(self, event):
    key = event.keycode
    if (key == 107) or (key == 22): # Del or backspace
      if self.selection:
        oldnotes = map(lambda graphic_note: graphic_note.note, self.selection)
        def do_it():
          for note in oldnotes:
            self.graphic_notes[note.mesure].delete()
          self.canvas.app.cancel.add_cancel(cancel_it)
        def cancel_it():
          self.deselect_all() # Unselect and delete any "fake" note that may have been added under the note we are resurected.
          for note in oldnotes:
            self.partition.addnote(note)
            self.drawnote(note)
          self.canvas.app.cancel.add_redo(do_it)
        do_it()
        
  def on_button_press1(self, event, x, y):
    if self.y1 < y < self.y2: self.select_at(self.song.mesure_at(self.x_to_time(x), 1))
    else:                     self.deselect_all()
    
  def on_button_press3(self, event, x, y): # A right click on the header hide the lyrics view
    x1, y1, x2, y2 = self.canvas.bbox(self.header)
    if y1 <= y <= y2: self.hide()
    
  def select_at(self, mesure):
    self.deselect_all()
    
    # Check if we need to scroll in order to make the new section visible.
    self.canvas.app.ensure_visible_x(mesure.time * self.zoom + 30)
    
    try: graphic_note = self.graphic_notes[mesure]
    except (KeyError, NameError):
      # Creates a new "fake" lyric with an empty text
      note = song.Lyric(mesure, u"")
      graphic_note = self.drawnote(note)
      
    self.add_selection(graphic_note)
    self.set_focus(graphic_note)
    
    return graphic_note
    
  def select_in_box(self, x1, y1, x2, y2):
    self.deselect_all()
    
    if y1 < (self.y1 + self.y2) / 2 < y2:
      for graphic_note in self.graphic_notes.values():
        if (graphic_note.x1 < x2 - 20) and (graphic_note.x2 > x1 + 20):
          self.add_selection(graphic_note)
          
  def note_at(self, x, y, create = 0):
    for graphic_note in self.graphic_notes.values():
      if graphic_note.is_at(x, y): return graphic_note
      
    if create:
      # Creates a new empty lyric
      note = song.Lyric(self.song.mesure_at(self.x_to_time(x), 1), u"")
      return self.drawnote(note)
    
  def paste(self, graphic_note_y_notes):
    oldnotes = []
    
    def do_it():
      for i in range(len(oldnotes)): del oldnotes[0] # Empty the list
      
      # Remove any lyric already at the same position.
      for graphic_note, y, note in graphic_note_y_notes:
        if isinstance(note, song.Lyric):
          oldnote = self.graphic_notes.get(note.mesure)
          if oldnote:
            oldnote.delete()
            oldnotes.append(oldnote.note)
            
      for graphic_note, y, note in graphic_note_y_notes:
        if isinstance(note, song.Lyric):
          self.partition.addnote(note)
          self.add_selection(self.drawnote(note))
          
      self.checktime() # Add mesure bar if needed.
      
      self.canvas.app.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      for graphic_note, y, note in graphic_note_y_notes:
        if isinstance(note, song.Lyric):
          graphic_note = self.graphic_notes.get(note.mesure)
          if graphic_note: graphic_note.delete() # Else it was pasted out of the lyrics !
          
      for note in oldnotes:
        self.partition.addnote(note)
        self.drawnote(note)
        
      self.canvas.app.cancel.add_redo(do_it)
      
    do_it()
    
  def big_change_done(self): pass
  
  def x_to_time      (self, x   ): return int((x - self.x - 10) / self.zoom)
  def x_to_round_time(self, x   ): return int(round(int(((x - self.x - 10.0) / self.zoom / self.default_note.time) + 0.4) * self.default_note.time))
  def time_to_x      (self, time): return time * self.zoom + self.x + 10
  
  def destroy(self):
    if hasattr(self, "canvas"): # else, not initialized by "draw"
      for graphic_note in self.graphic_notes.values(): graphic_note.destroy()
      self.canvas.delete(self.group)
      del self.canvas
      
    # Re-init the lyric so it can be re-used
    self.graphic_notes = {}
    self.selection      = []
    self.mesures        = []
    self.mesuresmarks   = []
    
  def selected_notes(self): return self.selection
  
  def __getstate__(self): return None
  def __setstate__(self, dict): pass
  def __getinitargs__(self): return self.song, self.partition, self.zoom
  
  def __str__(self): return _("Lyrics").encode("latin")

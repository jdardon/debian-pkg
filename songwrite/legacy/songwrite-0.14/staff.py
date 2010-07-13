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

import globdef, song, view

#FA DO SOL RE LA MI SI
DIESES = [5, 0, 7, 2, 9, 4, 11]

#SI MI LA RE SOL DO FA
BEMOLS = [11, 4, 9, 2, 7, 0, 5]

TONALITIES = {
  "C"  : (),
  
  "G"  : DIESES[:1],
  "D"  : DIESES[:2],
  "A"  : DIESES[:3],
  "E"  : DIESES[:4],
  "B"  : DIESES[:5],
  "F#" : DIESES[:6],
  "C#" : DIESES,
  
  "F"  : BEMOLS[:1],
  "Bb" : BEMOLS[:2],
  "Eb" : BEMOLS[:3],
  "Ab" : BEMOLS[:4],
  "Db" : BEMOLS[:5],
  "Gb" : BEMOLS[:6],
  "Cb" : BEMOLS,
  }

OFFSETS = {
  "C"  : 0,
  "G"  : 7,
  "D"  : 2,
  "A"  : 9,
  "E"  : 4,
  "B"  : 11,
  "F#" : 6,
  "C#" : 1,
  
  "F"  : 5,
  "Bb" : 10,
  "Eb" : 3,
  "Ab" : 8,
  "Db" : 1,
  "Gb" : 6,
  "Cb" : 11,
  }

class String(view.String):
  def __init__(self, basenote = 55, notationpos = 1, stipple = 1, char = ""):
    view.String.__init__(self, basenote, notationpos)
    self.stipple = stipple
    self.char    = char
    
  def draw(self, canvas, group, x, y, length = 32000):
    self.y = y
    if   self.stipple == 1:
      self.lines = [
        canvas.create_line(x, y, length, y, tag = group),
        ]
    elif self.stipple == 2:
      self.lines = [
        canvas.create_line(x, y, length, y, fill = "gray80", tag = group),
        ]
    else: self.lines = []
    
    if   self.char == "#":
      self.lines.append(canvas.create_text(canvas.app.old_x1 + 20 + 5 * DIESES.index((self.basenote - 1) % 12), y, text = self.char, anchor = "w", fill = "gray60", tag = (group, "noscroll")))
    elif self.char == "b":
      self.lines.append(canvas.create_text(canvas.app.old_x1 + 20 + 5 * BEMOLS.index((self.basenote + 1) % 12), y, text = self.char, anchor = "w", fill = "gray60", tag = (group, "noscroll")))
      
  def __getinitargs__(self): return self.basenote, self.notationpos, self.stipple, self.char
  

class Staff(view.TabView):
  STRING_SEP = 5
  
  def set_tonality(self, tonality):
    old = TONALITIES[self.partition.tonality]
    new = TONALITIES[tonality]
    self.partition.tonality = tonality
    
    old_type = old and (((old[0] == DIESES[0]) and 1) or -1)
    new_type = new and (((new[0] == DIESES[0]) and 1) or -1)
    
    already = []
    
    for string in self.strings:
      if   (old_type ==  1) and (((string.basenote - 1) % 12) in old): string.basenote -= 1
      elif (old_type == -1) and (((string.basenote + 1) % 12) in old): string.basenote += 1
      
      string.char = ""
      if   (new_type ==  1) and ((string.basenote % 12) in new):
        string.basenote += 1
        if (string.stipple < 2) and (not (string.basenote % 12) in already):
          string.char = "#"
          already.append(string.basenote % 12)
      elif (new_type == -1) and ((string.basenote % 12) in new):
        string.basenote -= 1
        if (string.stipple < 2) and (not (string.basenote % 12) in already):
          string.char = "b"
          already.append(string.basenote % 12)
      
      self.canvas.delete(*string.lines)
      
    canvas = self.canvas
    self.destroy()
    canvas.draw()
    
  def __init__(self, _song, partition, strings = None, zoom = 0.66667, strings_args = None):
    if not hasattr(partition, "tonality"):
      partition.tonality = "C"
      
    if strings_args:
      strings = map(String, *zip(*strings_args))
      
      already = []
      
      new = TONALITIES[partition.tonality]
      if new:
        for string in strings:
          if (string.basenote % 12) in new:
            if new[0] == DIESES[0]:
              string.basenote += 1
              if (string.stipple < 2) and (not (string.basenote % 12) in already):
                string.char = "#"
                already.append(string.basenote % 12)
            else:
              string.basenote -= 1
              if (string.stipple < 2) and (not (string.basenote % 12) in already):
                string.char = "b"
                already.append(string.basenote % 12)
            
    view.TabView.__init__(self, _song, partition, strings, zoom)
    
    staff = self
    super = self.drawnote
    class StaffNote(super): # Internal class
      def __init__(self, note):
        super.__init__(self, note)
        self.alteration = None
        staff.canvas.move(self.text, 0, -1)
        staff.canvas.itemconfigure(self.text, font = "helvetica -12 bold")
        self._draw_effect()
        self._drawalteration()
        
      def _text(self): return ((self.note.value < 0) and "-") or "o"
      
      def _drawalteration(self):
        if abs(self.note.value) > self.string.basenote:
          if not self.alteration:
            self.alteration = staff.canvas.create_text(self.x - 8, self.y, text = "#", anchor = "center", tag = self.tag_all)
        elif self.alteration:
          staff.canvas.delete(self.alteration)
          self.alteration = None
          
#       def _drawnotation(self):
#         note = self.note
#         x = self.x
        
#         if self.string.notationpos == 0: # At the top of the staff
#           self.notations = staff.draw_stem_and_beam(x + 2, staff.y1 + 4, self.string.y, note.time, note.duration, self.tag_all)
#         else: # At the bottom
#           self.notations = staff.draw_stem_and_beam(x - 2, staff.y2 - 4, self.string.y, note.time, note.duration, self.tag_all)
          
      def _drawnotation(self):
        note = self.note
        x = self.x #10.0 + float(note.time) * staff.zoom
        
        mesure = partition.song.mesure_at(note.time) or partition.song.mesures[-1]
        
        if self.string.notationpos == 0: # At the top of the staff
          if not staff.uppernotation.has_key(note.time):
            staff.uppernotation[note.time] = note
            self.notations = staff.draw_stem_and_beam(x + 2, staff.y1 + 4, self.string.y, note.time - mesure.time, note.duration, self.tag_all, mesure)
          else:
            self.notations = None
        else: # At the bottom
          if not staff.lowernotation.has_key(note.time):
            staff.lowernotation[note.time] = note
            self.notations = staff.draw_stem_and_beam(x - 2, staff.y2 - 4, self.string.y, note.time - mesure.time, note.duration, self.tag_all, mesure)
          else:
            self.notations = None
          
      def _draw_effect(self):
        # Remove any previous effect's drawing
        if hasattr(self, "effects"):
          staff.canvas.delete(*self.effects)
        if isinstance(self.note, song.SpecialEffect):
          if self.note.must_be_linked_to and (not self.note.linked_to):
            return # Nothing to draw if the link has no destination !
          
          if   isinstance(self.note, song.HammerNote):
            linked_to_x = staff.time_to_x(self.note.linked_to.time)
            self.effects = (
              staff.canvas.create_line(self.x + 5, self.string.y + 3, (self.x + linked_to_x) / 2, self.string.y + 5, linked_to_x - 6, self.string.y + 3, tag = self.tag_all),
              )
            
          elif isinstance(self.note, song.BendNote):
            pitch = self.note.pitch
            if pitch == int(pitch): pitch = int(pitch) # Do not display decimal for integer pitch (e.g. 1 instead of 1.0)
            
            self.effects = (
              staff.canvas.create_line(self.x +  5, self.string.y + 4, self.x + 20, self.string.y + 2, self.x + 30, self.string.y - 2, self.x + 28, self.string.y - 3, self.x + 30, self.string.y - 2, self.x + 29, self.string.y + 1, tag = self.tag_all),
              staff.canvas.create_text(self.x + 14, self.string.y - 6, text = str(pitch), tag = self.tag_all),
              )
            
          elif isinstance(self.note, song.SlideNote):
            linked_to_x = staff.time_to_x(self.note.linked_to.time)
            self.effects = (staff.canvas.create_line(self.x + 5, self.string.y + 2, linked_to_x - 6, self.string.y + 2, linked_to_x - 10, self.string.y - 1, linked_to_x - 6, self.string.y + 2, linked_to_x - 10, self.string.y + 5, tag = self.tag_all),)
            
          elif isinstance(self.note, song.TremoloNote):
            self.effects = (
              staff.canvas.create_line(self.x + 5, self.string.y - 2, self.x + 10, self.string.y - 5, self.x + 15, self.string.y - 2, self.x + 20, self.string.y - 5, tag = self.tag_all),
              )
            
          elif isinstance(self.note, song.DeadNote):
            self.effects = (
              staff.canvas.create_line(self.x - 7, self.string.y - 8, self.x + 5, self.string.y + 7, tag = self.tag_all),
              staff.canvas.create_line(self.x - 7, self.string.y + 7, self.x + 5, self.string.y - 8, tag = self.tag_all),
              )
            
          elif isinstance(self.note, song.RollNote):
            if self.note.decal == 0: # Draw something ONLY for the lower note of the roll.
              self.effects = (
                staff.canvas.create_line(self.x +  5, self.string.y + 3, self.x + 9, self.string.y - 3, self.x + 12, self.string.y - 27, self.x + 8, self.string.y - 24, self.x + 12, self.string.y - 27, self.x + 15, self.string.y - 23, tag = self.tag_all),
                staff.canvas.create_text(self.x + 16, self.string.y - 1, text = "R", tag = self.tag_all),
                )
              
      def update(self, note = None, check_link = 1):
        if not self is staff.get_at(self.note.time, staff.stringid(self.note)): return
        if note is None: note = self.note
        
        if self.notations:
          staff.canvas.delete(*self.notations)
          self.notations = []
        self._drawnotation()
        
        if check_link: self.check_link_to(0) # Effect will be redrawn by "set_value"
        self.set_value(note.value)
        self._draw_effect()
        staff.canvas.itemconfigure(self.text, fill = self._color())
        
      def check_link_to(self, redraw_effect = 1):
        if self.note.must_be_linked_to:
          next = self.next()
          if next and (not self.note.linked_to is next.note):
            self.note.link_to(next.note)
            if redraw_effect: self._draw_effect()
        elif self.note.linked and self.note.linked_from:
          if not self.note.linked_from in staff.partition.notes:
            self.note.linked_from.link_to(None)
            
      def delete(self):
        if super.delete(self):
          if self.note.linked:
            if self.note.linked_from:
              graphic_note = staff.get_at(self.note.linked_from.time, staff.stringid(self.note.linked_from))
              if graphic_note: graphic_note.check_link_to()
              
      def destroy(self): # return 1 if the note was not already destroyed
        if super.destroy(self):
          if hasattr(self, "effects"):
            staff.canvas.delete(*self.effects)
          return 1
        
      def on_set_value(self, new):
        old = self.note.value
        
        def do_it():
          new_graphic_note = self.get_self().set_value(new)
          staff.canvas.app.cancel.add_cancel(cancel_it)
          return new_graphic_note
        
        def cancel_it():
          staff.deselect_all()  # XXX
          self.get_self().set_value(old)
          staff.canvas.app.cancel.add_redo(do_it)
          
        return do_it()
        
      def set_value(self, value):
        if not staff.is_in_string(value, self.string):
          key = self.note.time, staff.stringid_(value) # Compute the key BEFORE to reference staff.graphic_notes (calling stringid may change the staff.graphic_notes dict !).
          graphic_note = staff.graphic_notes.get(key)
          if not graphic_note:
            if self.selected: staff.remove_selection(self)
            self.destroy()
            self.note.value = value
            return staff.drawnote(self.note)
          else: return # The place is not free !
          
        new_note = (self.note.value < 0) and (value > 0)
        
        super.set_value(self, value)
        
        if new_note: # Check if the new note is in the middle of a link !
          previous = self.previous()
          if previous and previous.note.linked and previous.note.linked_to: previous.update()
          
        ## A hammer may turn to a pull, and so on...
        self._drawalteration()
        
        if self.note.linked and self.note.linked_from:
          graphic_note = staff.get_at(self.note.linked_from.time, staff.stringid(self.note.linked_from))
          if graphic_note: graphic_note.update()
          
      def previous(self):
        prev = partition.note_before(self.note)
        if prev: return staff.graphic_notes[prev.time, staff.stringid(prev)]
        
      def next(self):
        next = partition.note_after(self.note)
        if next: return staff.graphic_notes[next.time, staff.stringid(next)]
        
      def __repr__(self): return "<StaffNote for %s>" % self.note
      
    self.drawnote  = StaffNote
    
  def on_key_press(self, event):
    if not self.selection: return
    
    key = event.keycode
    if   (event.char == "+") or (event.char == "="):
      for selection in self.selection[:]:
        if selection.note.value > 0:
          new_graphic_note = selection.on_set_value(selection.note.value + 1 * cmp(selection.note.value, 0))
          if new_graphic_note: self.add_selection(new_graphic_note)
        else:
          selection.on_set_value(-selection.note.value)
          
      if (len(self.selection) == 1) and (self.selection[0].note.value > 0): view.playnote(self.partition.instrument, self.selection[0].note.value)
      
    elif event.char == "-":
      for selection in self.selection[:]:
        if selection.note.value > 0:
          new_graphic_note = selection.on_set_value(selection.note.value - 1 * cmp(selection.note.value, 0))
          if new_graphic_note: self.add_selection(new_graphic_note)
        else:
          selection.on_set_value(-selection.note.value)
          
      if (len(self.selection) == 1) and (self.selection[0].note.value > 0): view.playnote(self.partition.instrument, self.selection[0].note.value)
      
    elif key == 57: self.on_set_effect(song.Note)        # n : normal
    elif key == 43: self.on_set_effect(song.HammerNote)  # h : hammer
    elif key == 39: self.on_set_effect(song.SlideNote)   # s : slide
    elif key == 56: self.on_set_effect(song.BendNote)    # b : bend
    elif key == 28: self.on_set_effect(song.TremoloNote) # t : tremolo
    elif key == 40: self.on_set_effect(song.DeadNote)    # d : dead note
    
    else: return view.TabView.on_key_press(self, event)
    
  def on_set_effect(self, effect):
    sel = self.selection[:]
    old_effects = map(lambda graphic_note: graphic_note.note.get_effect(), sel)
    
    def do_it():
      for graphic_note in sel:
        graphic_note.get_self().set_effect(effect)
      self.canvas.app.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      for graphic_note, old_effect in zip(sel, old_effects):
        graphic_note.get_self().set_effect(old_effect)
      self.canvas.app.cancel.add_redo(do_it)
      
    do_it()
    
  def on_button_press3(self, event, x, y):
    if self.y1 < y < self.y2: # A right click toggle the note
      time     = self.x_to_round_time(x)
      stringid = min(int((y - self.y1 - 30.0) / 5.0), len(self.strings) - 1)
      self.select_at(time, stringid)
      
      for selection in self.selection: selection.on_set_value(-selection.note.value)
      
      if selection.note.value > 0: view.playnote(self.partition.instrument, selection.note.value)
        
      self.checktime()
    else: view.TabView.on_button_press3(self, event, x, y)
    
  def fake_note(self, time, stringid):
    note = song.Note(time, self.default_note.duration, -self.strings[stringid].basenote, self.default_note.volume)
    return note
    
  def big_change_done(self):
    view.TabView.big_change_done(self)
    self.check_all_links()
    
  def check_all_links(self):
    for graphic_note in self.graphic_notes.values(): graphic_note.check_link_to()
    
  def y_to_stringid (self, y): return max(0, min(int((y - self.y1 - 30.0) / self.STRING_SEP), len(self.strings) - 1))
  def y_to_stringid_(self, y):
    # Similar to y_to_stringid, but return None if y is out of the tab.
    stringid = int(round(((y - self.y1 - 30.0) / self.STRING_SEP)))
    if (stringid < 0) or (stringid >= len(self.strings)): return None
    return stringid
  
  def stringid (self, note, create = 1): return self.stringid_(abs(note.value), create)
  def stringid_(self, value, create = 1):
    i = 0
    if create and (value > self.strings[0].basenote + (not ((self.strings[0].basenote - OFFSETS[self.partition.tonality]) % 12) in (4, 11))):
      for string in self.strings: self.canvas.delete(*string.lines)
      
      self.strings.insert(0, String(
        self.strings[0].basenote + 2 - (((self.strings[0].basenote - OFFSETS[self.partition.tonality]) % 12) in (4, 11)),
        0,
        (2, 0, 0)[self.strings[0].stipple]))
      
      # self.graphic_notes identify graphic notes by time and stringid!
      # Adding a new string at the top change all stringid !
      graphic_notes = {}
      for (time, stringid), graphic_note in self.graphic_notes.items():
        graphic_note.y += 5
        graphic_notes[time, stringid + 1] = graphic_note
      self.graphic_notes = graphic_notes
      
      self.draw_strings()
      self.canvas.draw()
      
      for graphic_note in self.graphic_notes.values():
        self.canvas.move(graphic_note.text, 0, 5)
        if graphic_note.alteration: self.canvas.move(graphic_note.alteration, 0, 5)
        graphic_note.update(check_link = 0)
        
      return self.stringid_(value, 1)
      return 0
    
    for i in range(len(self.strings)):
      if value >= self.strings[i].basenote: return i
      
    if create:
      for string in self.strings: self.canvas.delete(*string.lines)
      
      self.strings.append(String(
        self.strings[-1].basenote - 2 + (((self.strings[-1].basenote - OFFSETS[self.partition.tonality]) % 12) in (5, 0)),
        0,
        (2, 0, 0)[self.strings[-1].stipple]))
      
      self.draw_strings()
      self.canvas.draw()
      return self.stringid_(value, 1)
      return len(self.strings) - 1
      
    return -1
  
  def is_in_string(self, value, string):
    value = abs(value)
    if value < string.basenote: return 0
    if value > string.basenote + (not ((string.basenote - OFFSETS[self.partition.tonality]) % 12) in (4, 11)): return 0
    return 1
  
  def is_g8(self):
    for string in self.strings:
      if string.stipple == 1: break # Get the first non dashed string
    return 65 <= string.basenote <= 66
  
  def __str__(self): return _("staff").encode("latin")
  
  def __xml__(self, xml, context, hidden = 0):
    xml.write('''\t\t<view type="staff"''')
    if self.is_g8(): xml.write(' g8="1"')
    if hidden:       xml.write(' hidden="1"')
    xml.write("/>\n")
    
#piano_view_type = view.ViewType("staff", _("Piano" ), Staff, { "strings_args": ((67, 0, 0), (65, 0, 1), (64, 0, 0), (62, 0, 1), (60, 0, 0), (59, 0, 1), (57, 0, 0), (55, 0, 1), (53, 0, 0), (52, 0, 1), (50, 0, 0)) }, 0)
piano_view_type = view.ViewType("staff", _("Piano" ), Staff, { "strings_args": ((79, 0, 0), (77, 0, 1), (76, 0, 0), (74, 0, 1), (72, 0, 0), (71, 0, 1), (69, 0, 0), (67, 0, 1), (65, 0, 0), (64, 0, 1), (62, 0, 0)) }, 0)
view.ViewType("staff", _("Vocals"), Staff, { "strings_args": ((79, 0, 0), (77, 0, 1), (76, 0, 0), (74, 0, 1), (72, 0, 0), (71, 0, 1), (69, 0, 0), (67, 0, 1), (65, 0, 0), (64, 0, 1), (62, 0, 0)) }, 52)
g8_view_type = view.ViewType("staff", _("Guitar (staff 1 octavo above)"), Staff, { "strings_args": ((67, 0, 0), (65, 0, 1), (64, 0, 0), (62, 0, 1), (60, 0, 0), (59, 0, 1), (57, 0, 0), (55, 0, 1), (53, 0, 0), (52, 0, 1), (50, 0, 0)) }, 24)

# "strings_args": (67, 0, 0), (65, 0, 1), (64, 0, 0), (62, 0, 1), (60, 0, 0), (59, 0, 1), (57, 0, 0), (55, 0, 1), (53, 0, 0), (52, 0, 1), (50, 0, 0) 

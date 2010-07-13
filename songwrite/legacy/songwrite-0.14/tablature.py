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

import Tkinter, string
import globdef, view, song


class String:
  """A guitar string in a tablature. Nothing to see with char string !"""
  def __init__(self, basenote = 50, notationpos = 1):
    self.basenote    = basenote
    self.notationpos = notationpos # The position of the notation of the note duration (0 at top, 1 at bottom)
    
  def draw(self, canvas, group, x, y, length = 32000):
    self.y = y
    if   self.basenote < 31:
      self.lines = (
        canvas.create_line(x, y - 1, length, y - 1, fill = "gray60", tag = group),
        canvas.create_line(x, y + 1, length, y + 1, fill = "gray35", tag = group, width = 2),
        )
    elif self.basenote < 36:
      self.lines = (
        canvas.create_line(x, y - 1, length, y - 1, fill = "gray65", tag = group),
        canvas.create_line(x, y + 1, length, y + 1, fill = "gray40", tag = group, width = 2),
        )
    elif self.basenote < 41:
      self.lines = (
        canvas.create_line(x, y - 1, length, y - 1, fill = "gray60", tag = group),
        canvas.create_line(x, y    , length, y    , fill = "gray35", tag = group),
        )
    elif self.basenote < 46:
      self.lines = (
        canvas.create_line(x, y - 1, length, y - 1, fill = "gray65", tag = group),
        canvas.create_line(x, y    , length, y    , fill = "gray50", tag = group),
        )
    elif self.basenote < 52:
      self.lines = (
        canvas.create_line(x, y    , length, y    , fill = "gray45", tag = group),
        )
    elif self.basenote < 57:
      self.lines = (
        canvas.create_line(x, y    , length, y    , fill = "gray57", tag = group),
        )
    elif self.basenote < 62:
      self.lines = (
        canvas.create_line(x, y    , length, y    , fill = "gray70", tag = group),
        )
    else:
      self.lines = (
        canvas.create_line(x, y    , length, y    , fill = "gray82", tag = group),
        )
      
  def text(self, value): return str(value - self.basenote)
  
  def typed_to_value(self, typed): return typed + self.basenote
  
  def before(self, value): return max(self.basenote, value - 1)
  def after (self, value): return max(self.basenote, value + 1)
  
  def __getstate__(self):
    dict = self.__dict__.copy()
    try: del dict["y"], dict["lines"]
    except: pass # Hidden partition's string may not have "y" or "lines"
    return dict
  
  def __unicode__(self):
    return _("String") + ", " + _("base = %s") % song.note_label(self.basenote)
  
  
class Banjo5GString(String):
  def text(self, value):
    if value == self.basenote: return "0"
    return str(value - self.basenote + 5)
  
  def typed_to_value(self, typed):
    if typed <= 5: return self.basenote
    return typed + self.basenote - 5
  
  def __unicode__(self):
    return _("String (Banjo 5G)") + ", " + _("base = %s") % song.note_label(self.basenote)
  
class Tablature(view.TabView):
  REQUIRE_STRINGID = 1
  
  def set_capo(self, capo):
    dif = capo - self.partition.capo
    self.partition.capo = capo
    
    for note in self.partition.notes:
      note.value += dif
      
  def is_g8(self): return 1 # All tab are considered as G8
  
  def __init__(self, _song, partition, strings = None, zoom = 0.66667, strings_args = None):
    if strings_args:
      strings = []
      for string_arg in strings_args:
        if len(string_arg) == 2: strings.append(String(*string_arg))
        else:                    strings.append(string_arg[0](*string_arg[1:]))
        
    if not hasattr(partition, "capo"):
      partition.capo = 0
      
    view.TabView.__init__(self, _song, partition, strings, zoom)
    self.previoustype   = 0
    
    if not hasattr(partition, "print_with_staff_too"):
      partition.print_with_staff_too = 0
      
    tablature = self
    super     = self.drawnote
    class TablatureNote(super): # Internal class
      def __init__(self, note):
        super.__init__(self, note)
        self._draw_effect()
        
      def _text(self):
        return ((self.note.value < 0) and "_") or self.string.text(self.note.value - partition.capo)
      
      def _draw_effect(self):
        # Remove any previous effect's drawing
        if hasattr(self, "effects"):
          tablature.canvas.delete(*self.effects)
        if isinstance(self.note, song.SpecialEffect):
          if self.note.must_be_linked_to and (not self.note.linked_to):
            return # Nothing to draw if the link has no destination !
          
          if   isinstance(self.note, song.HammerNote):
            self.effects = []
            linked_to_x = tablature.time_to_x(self.note.linked_to.time)
            self.effects.append(tablature.canvas.create_line(self.x + 5, self.string.y + 3, (self.x + linked_to_x) / 2, self.string.y + 5, linked_to_x - 6, self.string.y + 3, tag = self.tag_all))
            if   self.note.value < self.note.linked_to.value: # Hammer
              self.effects.append(tablature.canvas.create_text((self.x + linked_to_x) / 2, self.string.y - 1, text = "H", tag = self.tag_all))
            elif self.note.value > self.note.linked_to.value: # Pull
              self.effects.append(tablature.canvas.create_text((self.x + linked_to_x) / 2, self.string.y - 1, text = "P", tag = self.tag_all))
              
          elif isinstance(self.note, song.BendNote):
            pitch = self.note.pitch
            if pitch == int(pitch): pitch = int(pitch) # Do not display decimal for integer pitch (e.g. 1 instead of 1.0)
            
            self.effects = (
              tablature.canvas.create_line(self.x +  5, self.string.y + 4, self.x + 20, self.string.y + 2, self.x + 30, self.string.y - 2, self.x + 28, self.string.y - 3, self.x + 30, self.string.y - 2, self.x + 29, self.string.y + 1, tag = self.tag_all),
              tablature.canvas.create_text(self.x + 14, self.string.y - 6, text = str(pitch), tag = self.tag_all),
              )
            
          elif isinstance(self.note, song.SlideNote):
            linked_to_x = tablature.time_to_x(self.note.linked_to.time)
            self.effects = (tablature.canvas.create_line(self.x + 5, self.string.y + 2, linked_to_x - 6, self.string.y + 2, linked_to_x - 10, self.string.y - 1, linked_to_x - 6, self.string.y + 2, linked_to_x - 10, self.string.y + 5, tag = self.tag_all),)
            
          elif isinstance(self.note, song.TremoloNote):
            self.effects = (
              tablature.canvas.create_line(self.x + 5, self.string.y - 2, self.x + 10, self.string.y - 5, self.x + 15, self.string.y - 2, self.x + 20, self.string.y - 5, tag = self.tag_all),
              )
            
          elif isinstance(self.note, song.DeadNote):
            self.effects = (
              tablature.canvas.create_line(self.x - 7, self.string.y - 8, self.x + 5, self.string.y + 7, tag = self.tag_all),
              tablature.canvas.create_line(self.x - 7, self.string.y + 7, self.x + 5, self.string.y - 8, tag = self.tag_all),
              )
            
          elif isinstance(self.note, song.RollNote):
            if self.note.decal == 0: # Draw something ONLY for the lower note of the roll.
              self.effects = (
                tablature.canvas.create_line(self.x +  5, self.string.y + 3, self.x + 9, self.string.y - 3, self.x + 12, self.string.y - 27, self.x + 8, self.string.y - 24, self.x + 12, self.string.y - 27, self.x + 15, self.string.y - 23, tag = self.tag_all),
                tablature.canvas.create_text(self.x + 16, self.string.y - 1, text = "R", tag = self.tag_all),
                )
              
      def update(self, note = None):
        if not self is tablature.get_at(self.note.time, tablature.stringid(self.note)): return
        if note is None: note = self.note
        
        if tablature.uppernotation.get(self.note.time) is self.note: del tablature.uppernotation[self.note.time]
        if tablature.lowernotation.get(self.note.time) is self.note: del tablature.lowernotation[self.note.time]
        if self.notations:
          tablature.canvas.delete(*self.notations)
          self.notations = []
        self._drawnotation()
        
        self.check_link_to(0) # Effect will be redrawn by "set_value"
        self.set_value(note.value) # Update effect
        tablature.canvas.itemconfigure(self.text, fill = self._color())
        
      def check_link_to(self, redraw_effect = 1):
        if self.note.must_be_linked_to:
          next = self.next()
          if next and (not self.note.linked_to is next.note):
            self.note.link_to(next.note)
            if redraw_effect: self._draw_effect()
        elif self.note.linked and self.note.linked_from:
          if not self.note.linked_from in tablature.partition.notes:
            self.note.linked_from.link_to(None)
            
      def delete(self):
        if super.delete(self):
          if self.note.linked:
            if self.note.linked_from:
              graphic_note = tablature.get_at(self.note.linked_from.time, tablature.stringid(self.note.linked_from))
              if graphic_note: graphic_note.check_link_to()
              
      def destroy(self): # return 1 if the note was not already destroyed
        if super.destroy(self):
          if hasattr(self, "effects"):
            tablature.canvas.delete(*self.effects)
          return 1
        
      def on_note_typed(self, typed_value):
        self.on_set_value(self.string.typed_to_value(typed_value) + partition.capo)
        
      def on_set_value(self, value):
        oldvalue = self.note.value
        
        def do_it():
          self.get_self().set_value(value)
          tablature.canvas.app.cancel.add_cancel(cancel_it)
          
        def cancel_it():
          tablature.deselect_all()  # XXX
          self.get_self().set_value(oldvalue)
          tablature.canvas.app.cancel.add_redo(do_it)
          
        do_it()
        
      def set_value(self, value):
        new_note = (self.note.value < 0) and (value > 0)
        
        super.set_value(self, value)
        
        if new_note: # Check if the new note is in the middle of a link !
          previous = self.previous()
          if previous and previous.note.linked and previous.note.linked_to: previous.update()
          
        # A hammer may turn to a pull, and so on...
        self._draw_effect()
        if self.note.linked and self.note.linked_from:
          graphic_note = tablature.get_at(self.note.linked_from.time, tablature.stringid(self.note.linked_from))
          if graphic_note: graphic_note.update()
          
      def __repr__(self): return "<TablatureNote for %s>" % self.note
      
    self.drawnote  = TablatureNote
    
    
  def on_key_press(self, event):
    if not self.selection: return
    
    key = event.keycode
    if (len(event.char) == 1) and (event.char in string.digits):
      self.on_note_typed(int(event.char))
      
    elif (event.char == "+") or (event.char == "="):
      for selection in self.selection:
        selection.on_set_value(selection.string.after(selection.note.value - self.partition.capo) + self.partition.capo)
    elif event.char == "-":
      for selection in self.selection:
        newvalue = selection.string.before(selection.note.value - self.partition.capo) + self.partition.capo
        if newvalue >= 0: selection.on_set_value(newvalue)
        
    elif key == 57: self.on_set_effect(song.Note)        # n : normal
    elif key == 43: self.on_set_effect(song.HammerNote)  # h : hammer
    elif key == 39: self.on_set_effect(song.SlideNote)   # s : slide
    elif key == 56: self.on_set_effect(song.BendNote)    # b : bend
    elif key == 28: self.on_set_effect(song.TremoloNote) # t : tremolo
    elif key == 40: self.on_set_effect(song.DeadNote)    # d : dead note
    elif key == 27: self.on_set_effect(song.RollNote)    # d : dead note
    
    else: return view.TabView.on_key_press(self, event)
    
  def on_note_typed(self, key):
    if self.selection:
      self.previoustype = 10 * self.previoustype + key
      for graphic_note in self.selection: graphic_note.on_note_typed(self.previoustype)
      
      if len(self.selection) == 1: self.selection[0].playnote()
      
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
    
  def fake_note(self, time, stringid):
    note = song.Note(time, self.default_note.duration, -1, self.default_note.volume)
    note.stringid = stringid
    return note
  
  def paste(self, graphic_note_y_notes):
    for graphic_note, y, note in graphic_note_y_notes:
      if isinstance(graphic_note.get_view(), Tablature):
        stringid = self.y_to_stringid_(y)
        if not stringid is None:
          note.value = note.value - graphic_note.get_view().strings[note.stringid].basenote + self.strings[stringid].basenote
      
    view.TabView.paste(self, graphic_note_y_notes)
    return
    
  def big_change_done(self):
    view.TabView.big_change_done(self)
    self.check_all_links()
    
  def check_all_links(self):
    for graphic_note in self.graphic_notes.values(): graphic_note.check_link_to()
    
  def arrange_selection_at_fret(self, fret):
    selection = map(lambda graphic_note: graphic_note.note, filter(lambda graphic_note: graphic_note.note.value > 0, self.selection))
    old_stringids = dict(map(lambda note: (note, getattr(note, "stringid", None)), selection))
    
    def do_it():
      self.deselect_all()
      notes_changed = []
      
      for note in selection:
        stringid = old_stringid = self.stringid(note)
        if note.value - self.strings[stringid].basenote < fret:
          while (stringid < len(self.strings) - 1) and (note.value - self.strings[stringid].basenote < fret):
            stringid += 1
        else:
          while (stringid > 0) and (note.value - self.strings[stringid - 1].basenote >= fret):
            stringid -= 1
            
        if stringid != old_stringid:
          graphic_note = self.graphic_notes[note.time, old_stringid]
          graphic_note.destroy()
          note.stringid = stringid
          notes_changed.append(note)
          
      for note in notes_changed:
        while (note.stringid > 0) and (self.graphic_notes.get((note.time, note.stringid))):
          note.stringid -= 1
        self.drawnote(note)
        
      self.canvas.app.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      self.deselect_all()
      
      for note in selection:
        stringid     = self.stringid(note)
        old_stringid = old_stringids[note]
        if stringid != old_stringid:
          graphic_note = self.graphic_notes[note.time, stringid]
          graphic_note.destroy()
          note.stringid = old_stringid
          self.drawnote(note)
          
      self.canvas.app.cancel.add_redo(do_it)
      
    do_it()
    
  def stringid(self, note):
    #try: return min(len(self.strings) - 1, max(0, note.stringid))
    try: return note.stringid
    except (AttributeError, NameError, KeyError):
      i = 0
      for string in self.strings:
        if (note.value >= string.basenote) and (not self.graphic_notes.get((note.time, i))):
          note.stringid = i
          return i
        i = i + 1
        
      return len(self.strings) - 1
    
  def __str__(self): return _("tab").encode("latin")
  
  def __xml__(self, xml, context, hidden = 0):
    if hidden:
      xml.write("""\t\t<view type="tablature" hidden="1">
\t\t\t<strings>
""")
    else:
      xml.write("""\t\t<view type="tablature">
\t\t\t<strings>
""")
    for string in self.strings:
      if string.__class__ is String:
        xml.write("""\t\t\t\t<string pitch="%s" notation="%s"/>\n""" % (string.basenote, ("top", "down")[string.notationpos]))
      else:
        xml.write("""\t\t\t\t<string pitch="%s" notation="%s" type="%s"/>\n""" % (string.basenote, ("top", "down")[string.notationpos], string.__class__.__name__))
    xml.write("""\t\t\t</strings>
\t\t</view>
""")
    
guitar_view_type = view.ViewType("tab", _("Guitar"       ), Tablature, { "strings_args": ((64, 0), (59, 0), (55, 0), (50, 1), (45, 1), (40, 1)) }, 24)
view.ViewType("tab", _("Guitar DADGAD"), Tablature, { "strings_args": ((62, 0), (57, 0), (55, 0), (50, 1), (45, 1), (38, 1)) }, 24)
view.ViewType("tab", _("Bass"         ), Tablature, { "strings_args": ((43, 0), (38, 0), (33, 1), (28, 1)) }, 33)
view.ViewType("tab", _("Banjo 5G"     ), Tablature, { "strings_args": ((62, 0), (59, 0), (55, 0), (50, 0), (Banjo5GString, 67, 0)) }, 105)


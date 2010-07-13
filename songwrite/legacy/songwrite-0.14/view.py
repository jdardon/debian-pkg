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

import popen2, time, os, thread, Tkinter
import song

# Add a "view" property to each TemporalData (partition, lyrics, ...) instance,
# by adding a new superclass (=Viewable) to TemporalData.
# That's a dynamic object hack :-]

_next_tag = 0
def new_tag():
  global _next_tag
  _next_tag = _next_tag + 1
  return "_" + str(_next_tag)

class Viewable:
  "Abstract class for partition, lyric, battery, ..."
  def setviewtype(self, viewtype):
    if ((viewtype.__class__ is HiddenView) or (isinstance(viewtype, ViewType) and (viewtype.view is HiddenView))) and (not self.view.__class__ is HiddenView): # Hidden view => keep the previous view in memory, as a serialized form (a view can be used only once).
      self.oldview = self.view
    oldview = getattr(self, "view", None)
    if isinstance(viewtype, ViewType):
      self.view = viewtype.view(self.song, self, **viewtype.args)
    else:
      self.view = viewtype
    if oldview: oldview.destroy()
    
  def set_view(self, viewtype):
    canvas = self.view.canvas
    self.setviewtype(viewtype)
    canvas.draw()
    
  def set_capo(self, capo):
    if hasattr(self.view, "set_capo"): self.view.set_capo(capo)
    else:                              self.capo = capo
    
  def set_tonality(self, tonality):
    if hasattr(self.view, "set_tonality"): self.view.set_tonality(tonality)
    else:                                  self.tonality = tonality
    
  def unhide(self):
    "Restore the view after it was hidden (by partition.setviewtype(view.HiddenView.viewtype) )."
    self.view.destroy()
    self.view = self.oldview
    del self.oldview
    
song.TemporalData.__bases__ = song.TemporalData.__bases__ + (Viewable,)

view_types = []

class ViewType:
  def __init__(self, group, name, view, args = {}, instrument = 24, register = 1):
    self.group      = group
    self.name       = name
    self.view       = view
    self.args       = args
    self.instrument = instrument
    
    if register: view_types.append(self)
    
  def __str__(self):
    if self.group: return _(self.group) + " -> " + self.name
    else:          return self.name
    
    #if self.group: return (_(self.group) + " -> " + self.name).encode("latin")
    #else:          return self.name.encode("latin")
    
class GraphicNote:
  """A visual representation of a note.
Has a note, x, y and selected properties, and some methods.
This class is suclassed by an inner class in each View, in order to add view-specific data."""
  def update     (self): "Update the note. Called when the note has changed."
  def get_view   (self): "Gets the view associated with this graphic note (e.g. the tablature, ...)."
  def delete     (self): "Removes the note from the partition and destroy the graphic note in the view. No-op if called more than once."
  def destroy    (self): "Destroys the graphic note in the view (but keeps the note in the partition; only the graphic representation is affected). No-op if called more than once."
  def drag       (self, drag_box): "Draws the given note in the drag_box (a GnomeCanvasGroup), as it is represented by this view. Called when the note is dragged."
  
  def previous(self): "Returns the graphic note just before this one. This is view-dependant, e.g. for tablature, the previous note is understood to be on the same string."
  def next    (self): "Returns the graphic note just after this one. This is view-dependant, e.g. for tablature, the next note is understood to be on the same string."
  
  def set_effect(self, effect):
    "GraphicNote.set_effect(effect) -- Set the given class of special effect (e.g. song.HammerNote) for the note of this graphic note."
    note = self.note
    note.remove_effect() # Remove previous effect
    if effect.linked: note.link_to(self.next().note)
    else:             note.link_to(None)
    if not effect is song.Note:
      note.__class__ = effect
      note.init_effect()
      
    if effect is song.RollNote: # decal is k times the number of rolled notes at the same time and below this one ! (Hey ! All that takes a SINGLE line of Python) !
      note.decal = 2 * len(filter(lambda n: n.value < note.value, self.get_view().partition.notes_at(self.note)))
      
    self.update()
    
    
def _dot(drawer): # Create a doted drawer from a "normal" drawer
  return lambda view, x, y1, y2, time, tag: (view.canvas.create_line(x + 3, y2, x + 5, y2, width = 2, tag = tag),) + drawer(view, x, y1, y2, time, tag)



class View:
  def __init__(self, song, partition, zoom):
    self.song      = song
    self.partition = partition
    self.zoom      = zoom
    
  def draw(self, canvas, x = 0, y = 0): "Draws the view in the given Gnome canvas, at the given x-y position. Can be called more than once; in this case the view is moved to the new position."
  
  def note_at         (self, x, y, create = 0): """Gets the graphic note at the given x-y coordinates. If there is no such graphic note, None is returned if create is false, else a new empty "fake" note is created and returned."""
  #def paste           (self, graphic_note, x, y, note): "Pastes the given note at the given x-y location. If needed so, the note is already cloned and/or time-aligned. note is the note to add (already cloned), and graphic_note the graphic note that is copied."
  def paste           (self, graphic_note_y_notes): "Pastes the given list of notes. graphic_note_y_notes is a list of (graphic_note, y, note) tuple, where x and y are the location, note is the note to add (already cloned and at the right time !), and graphic_note the graphic note that is copied (not a clone !). If needed so, note is already cloned and/or time-aligned."
  def select_in_box   (self, x1, y1, x2, y2): "Selects all notes inside the given rect in this view."
  def add_selection   (self, graphic_note): "Adds the given graphic note to the current selection."
  def remove_selection(self, graphic_note): "Removes the given graphic note from the current selection."
  def selected_notes  (self):
    "Gets a sequence of all the selected graphic notes in this view."
    return ()
  def deselect_all(self): "Deselect all selected notes in this view."
  
  def set_default_note(self, default_note): "Sets the default note. The default note is used as a template for newly created note in this view, and thus the new notes will have its duration, its volume, ...."
  def rythm_changed(self): "Redraws all the mesure bar. Must be called when the song's rythm is changed."
  
  def on_prop(self):
    "Displays a dialog box to edit this view's specific properties (If there are some). Called when the 'view properties' button is clicked in the partition properties dialog."
    import init_editobj
    init_editobj.edit(self.partition, cancel = self.canvas.app.cancel)
    
  def set_chord(self, chord): """Set the chord at the current position. chord is a sequence  like ["", "3", "2", "0", "1", "0"]."""
  def get_chord(self):
    """Get the chord displayed at the current position. chord is a sequence  like ["", "3", "2", "0", "1", "0"]."""
    return ["", "", "", "", "", ""]
  
  def destroy(self): "Destroy this view."
  
  def arrange_selection_at_fret(self, fret): pass
  
  def hide(self):
    canvas = self.canvas # self.destroy() delete the canvas attribute => we must stock it now
    self.partition.setviewtype(hidden_view_type) # Call self.destroy()
    canvas.draw()
    
    
  # Drawing funcs:
  def _nothing(self, x, y1, y2, time, tag):
    return ()
  _round = _nothing
  
  def _white(self, x, y1, y2, time, tag):
    return (
      self.canvas.create_line(x, y2, x, y1, fill = "gray80", width = 2, tag = tag),
      )
  
  def _black(self, x, y1, y2, time, tag):
    d = cmp(y2, y1) * 3
    return (
      self.canvas.create_line(x, y2, x, y1 + d, tag = tag),
      )
  
  def _quarter(self, x, y1, y2, time, tag):
    dx = time % 96
    if not dx: dx = -10
    return (
      self.canvas.create_line(x, y2, x                 , y1           , tag = tag),
      self.canvas.create_line(x, y1, x - dx * self.zoom, y1, width = 2, tag = tag),
      )

  def _hquarter(self, x, y1, y2, time, tag):
    d = cmp(y2, y1) * 4
    dx = time % 48
    if not dx: dx = -8
    notations = (
      self.canvas.create_line(x, y2    , x                          , y1               , tag = tag),
      self.canvas.create_line(x, y1    , x - (time % 96) * self.zoom, y1    , width = 2, tag = tag),
      self.canvas.create_line(x, y1 + d, x - dx          * self.zoom, y1 + d, width = 2, tag = tag),
      )
    return notations

  def _hhquarter(self, x, y1, y2, time, tag):
    d = cmp(y2, y1) * 4
    dx = time % 24
    if not dx: dx = -6
    notations = (
      self.canvas.create_line(x, y2        , x                          , y1                   , tag = tag),
      self.canvas.create_line(x, y1        , x - (time % 96) * self.zoom, y1        , width = 2, tag = tag),
      self.canvas.create_line(x, y1 + d    , x - (time % 48) * self.zoom, y1 + d    , width = 2, tag = tag),
      self.canvas.create_line(x, y1 + 2 * d, x - dx          * self.zoom, y1 + 2 * d, width = 2, tag = tag),
      )
    return notations

  def _quarter_triplet(self, x, y1, y2, time, tag):
    dx = time % 96
    if not dx: dx = -10
    if (time % 96) == 32:
      if cmp(y2, y1) > 0: anchor = "s"
      else:               anchor = "n"
      triplet = (
        self.canvas.create_text(x, y1, text = "3", anchor = anchor, tag = tag),
        )
    else: triplet = ()
    return triplet + (
      self.canvas.create_line(x, y2, x                 , y1           , tag = tag),
      self.canvas.create_line(x, y1, x - dx * self.zoom, y1, width = 2, tag = tag),
      )
  
  def _hquarter_triplet(self, x, y1, y2, time, tag):
    d = cmp(y2, y1) * 4
    dx = time % 48
    if not dx: dx = -8
    if (time % 48) == 16:
      if cmp(y2, y1) > 0: anchor = "s"
      else:               anchor = "n"
      triplet = (
        self.canvas.create_text(x, y1, text = "3", anchor = anchor, tag = tag),
        )
    else: triplet = ()
    return triplet + (
      self.canvas.create_line(x, y2    , x                          , y1               , tag = tag),
      self.canvas.create_line(x, y1    , x - (time % 96) * self.zoom, y1    , width = 2, tag = tag),
      self.canvas.create_line(x, y1 + d, x - dx          * self.zoom, y1 + d, width = 2, tag = tag),
      )
  
  def _hhquarter_triplet(self, x, y1, y2, time, tag):
    d = cmp(y2, y1) * 4
    dx = time % 24
    if not dx: dx = -6
    if (time % 24) == 8:
      if cmp(y2, y1) > 0: anchor = "s"
      else:               anchor = "n"
      triplet = (
        self.canvas.create_text(x, y1, text = "3", anchor = anchor, tag = tag),
        )
    else: triplet = ()
    return triplet + (
      self.canvas.create_line(x, y2        , x                          , y1                          , tag = tag),
      self.canvas.create_line(x, y1        , x - (time % 96) * self.zoom, y1        , width = 2, tag = tag),
      self.canvas.create_line(x, y1 +     d, x - (time % 48) * self.zoom, y1 +     d, width = 2, tag = tag),
      self.canvas.create_line(x, y1 + 2 * d, x - dx          * self.zoom, y1 + 2 * d, width = 2, tag = tag),
      )
  
  def _quarter8(self, x, y1, y2, time, tag):
    dx = time % 144
    if not dx: dx = -10
    return (
      self.canvas.create_line(x, y2, x                 , y1           , tag = tag),
      self.canvas.create_line(x, y1, x - dx * self.zoom, y1, width = 2, tag = tag),
      )
  
  def _hquarter8(self, x, y1, y2, time, tag):
    d = cmp(y2, y1) * 4
    dx = time % 48
    if not dx: dx = -8
    notations = (
      self.canvas.create_line(x, y2    , x                           , y1               , tag = tag),
      self.canvas.create_line(x, y1    , x - (time % 144) * self.zoom, y1    , width = 2, tag = tag),
      self.canvas.create_line(x, y1 + d, x - dx           * self.zoom, y1 + d, width = 2, tag = tag),
      )
    return notations
  
  def _hhquarter8(self, x, y1, y2, time, tag):
    d = cmp(y2, y1) * 4
    dx = time % 24
    if not dx: dx = -6
    notations = (
      self.canvas.create_line(x, y2        , x                           , y1                   , tag = tag),
      self.canvas.create_line(x, y1        , x - (time % 144) * self.zoom, y1        , width = 2, tag = tag),
      self.canvas.create_line(x, y1 + d    , x - (time %  48) * self.zoom, y1 + d    , width = 2, tag = tag),
      self.canvas.create_line(x, y1 + 2 * d, x - dx           * self.zoom, y1 + 2 * d, width = 2, tag = tag),
      )
    return notations
  
  _drawers = { # Maps durations to the corresponding drawer function
    576 : _dot(_round),
    288 : _dot(_white),
    144 : _dot(_black),
    72  : _dot(_quarter),
    36  : _dot(_hquarter),
    18  : _dot(_hhquarter),

    384 : _round,
    192 : _white,
    96  : _black,
    48  : _quarter,
    24  : _hquarter,
    12  : _hhquarter,

    32  : _quarter_triplet,
    16  : _hquarter_triplet,
    8   : _hhquarter_triplet,
    }
  _drawers8 = { # Maps durations to the corresponding drawer function for x/8 rythms
    576 : _dot(_round),
    288 : _dot(_white),
    144 : _dot(_black),
    72  : _dot(_quarter8),
    36  : _dot(_hquarter8),
    18  : _dot(_hhquarter8),

    384 : _round,
    192 : _white,
    96  : _black,
    48  : _quarter8,
    24  : _hquarter8,
    12  : _hhquarter8,
    
    # Does triplets make sense in 6/8 rythms ???
    32  : _quarter_triplet,
    16  : _hquarter_triplet,
    8   : _hhquarter_triplet,
    }
  
  def draw_stem_and_beam(self, x, y1, y2, time, duration, tag, mesure = None):
    if mesure and (mesure.rythm2 == 8): return (View._drawers8.get(duration) or View._nothing)(self, x, y1, y2, time, tag)
    else:                               return (View._drawers .get(duration) or View._nothing)(self, x, y1, y2, time, tag)
    
  def __xml__(self, xml, context): pass
  
  def big_change_done(self): pass
  
  
  
class HiddenView(View):
  """A view that hide the partition instead of showing it.
Can be used as a demo/sample basic view !"""
  def __init__(self, song, partition): View.__init__(self, song, partition, 1.0)
  
  def draw(self, canvas, x = 0, y = 0):
    text = unicode(self.partition) + u" (" + _("hidden") + u")"
    
    if hasattr(self, "group"): # Draw was already called before. Just move to the new position.
      self.canvas.move(self.group, 0, y - self.y1)
      self.canvas.itemconfigure(self.text, text = text)
    else: # First time draw id called. Create and draws all the stuff !
      self.canvas = canvas
      self.group  = new_tag()
      self.text = canvas.create_text(canvas.app.old_x1 + 20, y + 11, text = text, anchor = "w", tag = (self.group, "noscroll"))
      
    self.x = x
    self.y1 = y
    self.height = 20
    self.y2 = y + self.height
    
    return x, self.y2
  
  def destroy(self):
    if hasattr(self, "group"): # else, not initialized by "draw"
      self.canvas.delete(self.group)
      del self.group
      
  def on_key_press(self, event): pass
  def on_button_press1(self, event, x, y): pass
  def on_button_press2(self, event, x, y): pass
  def on_button_press3(self, event, x, y):
    if self.y1 <= y <= self.y2: self.unhide()
    
  def on_event(self, obj, event):
    if (event.type == gtk.gdk.BUTTON_PRESS) and (event.button == 3):
      x, y = self.canvas.get_pointer_abs()
      if self.y1 <= y <= self.y2: self.unhide()
      
  def unhide(self):
    self.partition.unhide() # partition instance keep the previous view when hidden.
    self.canvas.draw()
    
  def __getstate__(self): return None
  def __setstate__(self, dict): pass
  def __getinitargs__(self): return self.song, self.partition
  
  def __str__(self): return _("Hidden").encode("latin")
  
  def __xml__(self, xml, context):
    self.partition.oldview.__xml__(xml, context, 1)
    
hidden_view_type = ViewType("", _("Hidden"), HiddenView)


import song, player

noteplayer = None

def playnote(instrument, value):
  global noteplayer
  if not noteplayer:
    noteplayer = song.Song()
    noteplayer.partitions.append(song.Partition(noteplayer))
    noteplayer.partitions[0].notes.append(song.Note(0, 48, 0))
  noteplayer.partitions[0].instrument = instrument
  noteplayer.partitions[0].notes[0].value = value
  
  player.play_async(noteplayer.midi()[0])

import copy, ui

class String:
  """A guitar string in a tablature. Nothing to see with char string !"""
  def __init__(self, basenote = 50, notationpos = 1):
    self.basenote    = basenote
    self.notationpos = notationpos # The position of the notation of the note duration (0 at top, 1 at bottom)
    
  def draw(self, canvas, group, x, y, length = 32000):
    self.y = y
    self.lines = (
      canvas.create_line(x, y, length, y, fill = "gray20", tag = group),
      )
    
  def __getstate__(self): return None
  def __setstate__(self, dict): pass
  def __getinitargs__(self): return self.basenote, self.notationpos
    

# Base class for drums and tablature

class TabView(View):
  STRING_SEP = 20
  REQUIRE_STRINGID = 0
  
  def __init__(self, _song, partition, strings, zoom = 0.66667):
    View.__init__(self, _song, partition, zoom)
    self.graphic_notes  = {}
    self.selection      = []
    self.mesures        = []
    self.mesuresmarks   = []
    self.default_note   = None
    self.strings        = strings
    self.selection_box  = None
    self.update_selection_box_delayed = self.update_lyrics_delayed = 0
    
    tablature = self
    class TabNote(GraphicNote): # Internal class
      def __init__(self, note):
        stringid = tablature.stringid(note)
        self.string = tablature.strings[stringid]
        self.x = tablature.time_to_x(note.time)
        self.y = self.string.y
        self.selected = 0
        self.note     = note
        self.tag      = tablature.group + "_" + str(note.time) + " " + str(stringid)
        self.tag_all  = (self.tag, tablature.group)
        
        self._drawnotation()
        self.text = tablature.canvas.create_text(self.x, self.y + 1, text = self._text(), anchor = "center", fill = self._color(), tag = self.tag_all)
        
        tablature.graphic_notes[note.time, stringid] = self
        
      def _text(self): return "?"
      
      def get_view(self): return tablature
      
      def _drawnotation(self):
        note = self.note
        x = self.x #10.0 + float(note.time) * tablature.zoom
        
        mesure = partition.song.mesure_at(note.time) or partition.song.mesures[-1]
        
        if self.string.notationpos == 0: # At the top of the tablature
          if not tablature.uppernotation.has_key(note.time):
            tablature.uppernotation[note.time] = note
            self.notations = tablature.draw_stem_and_beam(x, tablature.y1 + 4, tablature.y1 + 17, note.time - mesure.time, note.duration, self.tag_all, mesure)
          else:
            self.notations = None
        else: # At the bottom
          if not tablature.lowernotation.has_key(note.time):
            tablature.lowernotation[note.time] = note
            self.notations = tablature.draw_stem_and_beam(x, tablature.y2 - 4, tablature.y2 - 17, note.time - mesure.time, note.duration, self.tag_all, mesure)
          else:
            self.notations = None
            
      def _color(self):
        if self.note.volume > 220: return "red"
        return "gray%s" % int(100.0 - (self.note.volume / 2.55))
      
      def update(self, note = None):
        if not self is tablature.get_at(self.note.time, tablature.stringid(self.note)): return
        if note is None: note = self.note
        
        if tablature.uppernotation.get(self.note.time) is self.note: del tablature.uppernotation[self.note.time]
        if tablature.lowernotation.get(self.note.time) is self.note: del tablature.lowernotation[self.note.time]
        if self.notations:
          tablature.canvas.delete(*self.notations)
          self.notations = []
        self._drawnotation()
        
        self.set_value(note.value)
        tablature.canvas.itemconfigure(self.text, fill = self._color())
        
      def get_self(self):
        """Get the graphic note at the position of a graphic note.
It is usually the graphic note itself, except if it has been replaced by an other."""
        if self.tag: return self
        return tablature.get_at(self.note.time, tablature.stringid(self.note)) or tablature.drawnote(self.note)
        #return tablature.get_at(self.note.time, tablature.stringid(self.note), 1)
      
      def delete(self):
        if self.destroy():
          if self.note.value > 0:
            tablature.partition.delnote(self.note)
            tablature.delay_update_lyrics()
          return 1
        
      def destroy(self): # return 1 if the note was not already destroyed
        stringid = tablature.stringid(self.note)

        if tablature.graphic_notes.get((self.note.time, stringid)) is self: # Else already destroyed, or another note has replaced this one !!!
          if self.selected:
            tablature.selection.remove(self)
            self.selected = 0
          del tablature.graphic_notes[self.note.time, stringid]
          tablature.canvas.delete(self.tag)
          
          self.tag = None
          
          if tablature.uppernotation.get(self.note.time) is self.note: del tablature.uppernotation[self.note.time]
          if tablature.lowernotation.get(self.note.time) is self.note: del tablature.lowernotation[self.note.time]
          
          return 1
        
      def is_at(self, x, y):
        "Returns true if this graphic note is at the given x-y position."
        return (self.note.value != -1) and abs(x - self.x) < 5 and abs(y - self.y) < 12
      
      def get_bounds(self):
        x1, y1, x2, y2 = tablature.canvas.bbox(self.text)
        return x1, y1, max(x2, tablature.time_to_x(self.note.time + self.note.duration) - 12), y2
      
      def set_selected(self, selected):
        if selected == self.selected: return
        
        self.selected = selected
        if not selected and (self.note.value < 0): self.delete() # A fake note is unselected => remove it !
        
      def set_value(self, value):
        if self.note.value < 0: # A fake note that become real...
          partition.addnote(self.note)
          tablature.checktime(self.note.time)
          tablature.update_lyrics()
          
        self.note.value = value
        tablature.canvas.itemconfigure(self.text, text = self._text())
        if value < 0: # A note that become a fake note !
          partition.delnote(self.note)
          if not self.selected: self.delete()
          tablature.update_lyrics()
        if self.selected: tablature.delay_update_selection_box()
        
      def playnote(self): playnote(partition.instrument, self.note.value)
      
      def drag(self, canvas, tag):
        canvas.create_text(self.x, self.y, text = self._text(), anchor = "center", fill = self._color(), tag = tag)
        
      def previous(self):
        my_stringid = tablature.stringid(self.note)
        times = list(zip(*filter(lambda (time, stringid): stringid == my_stringid, tablature.graphic_notes.keys()))[0])
        times.sort()
        i = times.index(self.note.time)
        if i: return tablature.graphic_notes[times[i - 1], my_stringid]
        
      def next(self):
        my_stringid = tablature.stringid(self.note)
        times = list(zip(*filter(lambda (time, stringid): stringid == my_stringid, tablature.graphic_notes.keys()))[0])
        times.sort()
        i = times.index(self.note.time)
        if i + 1 < len(times): return tablature.graphic_notes[times[i + 1], my_stringid]
        
      def __repr__(self): return "<TabNote for %s>" % self.note
      
    self.drawnote  = TabNote
    
  def draw(self, canvas, x = 0, y = 0):
    if hasattr(self, "canvas"):
      self.canvas.itemconfigure(self.header, text = self.partition.header)
      x1, y1, x2, y2 = canvas.bbox(self.header)
      old_y1 = self.y1
      self.y1 = y + y2 - y1 + 8
      
      self.canvas.move(self.group, 0, self.y1 - old_y1)
      
      self.canvas.coords(self.header, canvas.app.old_x1 + 20, y + 4)
      self.bar.coords(x2 + 20, y + 10)
      self.x = x

      self.height = len(self.strings) * self.STRING_SEP + 40
      self.y2 = self.y1 + self.height
      
      # Update the strings's y coordinate
      for string in self.strings:
        string.y = string.y + self.y1 - old_y1
        
      # Update the graphic note's y coordinates
      for graphic_note in self.graphic_notes.values():
        graphic_note.y = graphic_note.string.y
      
    else:
      self.canvas        = canvas
      self.uppernotation = {}
      self.lowernotation = {}
      self.x             = x
      
      self.group  = new_tag()
      self.header = canvas.create_text(canvas.app.old_x1 + 20, y + 4, text = self.partition.header, anchor = "nw", tag = (self.group, "noscroll"))
      x1, y1, x2, y2 = canvas.bbox(self.header)
      self.y1 = y + y2 - y1 + 8
      
      self.bar = ui.LinksBar(canvas, x2 + 20, y + 10,
                             ((_("Move up")   , lambda event: self.canvas.app.move_partition(self.partition, -1)),
                              (_("Move down") , lambda event: self.canvas.app.move_partition(self.partition,  1)),
                              (_("Delete")    , lambda event: self.canvas.app.on_partition_delete(self.partition)),
                              (_("Properties"), lambda event: self.on_prop()),
                              ),
                             tag = (self.group, "noscroll"),
                             )
      
      self.draw_strings()
      self.checktime()
      #map(self.drawnote , self.partition.notes)
      
    return x, self.y2
  
  def ensure_drawn(self, time1, time2):
    notes = self.partition.notes_range(time1, time2)
    for note in notes:
      if not self.graphic_notes.has_key((note.time, self.stringid(note))):
        self.drawnote(note)
        
        
  def draw_strings(self):
    stringy = 30 + self.y1
    for string in self.strings:
      string.draw(self.canvas, self.group, self.x, stringy)
      stringy += self.STRING_SEP
    self.y2 = stringy + 10
    self.height = self.y2 - self.y1
    
  def rythm_changed(self):
    self.canvas.delete(*self.mesuresmarks)
    self.mesures = []
    self.checktime()
    
  def checktime(self, time = 0):
    if len(self.mesures) < len(self.song.mesures):
      map(self.add_mesure, self.song.mesures[len(self.mesures):])
      self.canvas.app.set_scroll_region()
      
  def add_mesure(self, mesure):
    width = 1
    x = mesure.endtime() * self.zoom + 2 + self.x
    self.mesures.append(mesure)
    if len(self.song.mesures) > len(self.mesures):
      next = self.song.mesures[len(self.mesures)]
    else: next = None
    
    symbols = self.song.playlist.symbols.get(next)
    if symbols:
      for symbol in symbols:
        h = self.STRING_SEP * (len(self.strings) - 1)
        if (symbol == "} % end repeat") or (symbol == "} % end alternative"):
          self.mesuresmarks.append(self.canvas.create_oval(x - 8, self.y1 + 28 + h * 0.35, x - 3, self.y1 + 33 + h * 0.35, fill = "black", tag = self.group))
          self.mesuresmarks.append(self.canvas.create_oval(x - 8, self.y1 + 27 + h * 0.65, x - 3, self.y1 + 32 + h * 0.65, fill = "black", tag = self.group))
          width = 2
          
        elif symbol.startswith(r"\repeat"):
          self.mesuresmarks.append(self.canvas.create_oval(x + 8, self.y1 + 28 + h * 0.35, x + 3, self.y1 + 33 + h * 0.35, fill = "black", tag = self.group))
          self.mesuresmarks.append(self.canvas.create_oval(x + 8, self.y1 + 27 + h * 0.65, x + 3, self.y1 + 32 + h * 0.65, fill = "black", tag = self.group))
          width = 2
          
        elif symbol.startswith(r"{ % start alternative"):
          alt = symbol[22:]
          self.mesuresmarks.append(self.canvas.create_line(x, self.y1, x + 60, self.y1, tag = self.group))
          self.mesuresmarks.append(self.canvas.create_text(x + 15, self.y1 + 7, text = alt, tag = self.group))
          
    if mesure.syncope:
      from main import icons
      self.mesuresmarks.append(self.canvas.create_image(self.x + mesure.time * self.zoom, self.y1 + 13, image = icons["syncope"], tag = self.group))
      self.mesuresmarks.append(self.canvas.create_line(x, self.y1 + 20, x, self.y2, fill = 'gray50', width = width, tag = self.group))
    else:
      self.mesuresmarks.append(self.canvas.create_line(x, self.y1, x, self.y2, fill = "black", width = width, tag = self.group))
      
  def add_selection(self, graphic_note):
    if graphic_note in self.selection: return
    
    b1 = graphic_note.get_bounds()
    
    if self.selection:
      b2 = self.canvas.bbox(self.selection_box)
      
      self.canvas.coords(self.selection_box,
                         min(b1[0] - 2, b2[0] + 1), # +1 / -1 because of the border ???
                         min(b1[1] - 1, b2[1] + 1),
                         max(b1[2] + 3, b2[2] - 1),
                         max(b1[3] + 2, b2[3] - 1),
                         )
    else:
      self.selection_box = self.canvas.create_rectangle(
        b1[0] - 2,
        b1[1] - 1,
        b1[2] + 3,
        b1[3] + 2,
        outline = "#AAAADD", fill = "#DDDDFF", width = 2, tag = self.group)
      self.canvas.tag_lower(self.selection_box, self.group)
      
    self.selection.append(graphic_note)
    graphic_note.set_selected(1)
    
    self.previoustype = 0
    
  def remove_selection(self, graphic_note):
    self.selection.remove(graphic_note)
    graphic_note.set_selected(0)
    self.update_selection_box()
    
  def delay_update_selection_box(self):
    if not self.update_selection_box_delayed: 
      self.update_selection_box_delayed = 1
      self.canvas.after(50, self.update_selection_box)
      
  def update_selection_box(self):
    self.update_selection_box_delayed = 0
    
    if self.selection:
      xys = zip(*map(lambda graphic_note: graphic_note.get_bounds(), self.selection))
      if self.selection_box:
        self.canvas.coords(self.selection_box,
                           min(xys[0]) - 2,
                           min(xys[1]) - 1,
                           max(xys[2]) + 3,
                           max(xys[3]) + 2,
                           )
      else:
        self.selection_box = self.canvas.create_rectangle(min(xys[0]) - 2,
                                                          min(xys[1]) - 1,
                                                          max(xys[2]) + 3,
                                                          max(xys[3]) + 2,
                                                          outline = "#AAAADD", fill = "#DDDDFF", width = 2, tag = self.group)
        self.canvas.tag_lower(self.selection_box, self.group)
    else:
      self.canvas.delete(self.selection_box)
      self.selection_box = None
      
  def deselect_all(self):
    for graphic_note in self.selection: graphic_note.set_selected(0)
    self.selection = []
    self.canvas.delete(self.selection_box)
    self.selection_box = None
    
  def set_default_note(self, default_note): self.default_note = default_note
  
  def on_key_press(self, event):
    if not self.selection: return

    key = event.keycode
    if   (key == 107) or (key == 22): # Del or backspace
      if self.selection:
        self.previoustype = 0
        
        oldnotes = map(lambda graphic_note: graphic_note.note, self.selection)
        def do_it():
          for note in oldnotes:
            self.get_at(note.time, self.stringid(note)).delete()
          self.select_at(oldnotes[0].time, self.stringid(oldnotes[0])) # Select something
          self.big_change_done()
          self.canvas.app.cancel.add_cancel(cancel_it)
          
        def cancel_it():
          self.deselect_all() # Unselect and delete any "fake" note that may have been added under the note we are resurected.
          for note in oldnotes:
            self.partition.addnote(note)
            self.drawnote(note)
            self.update_lyrics()
          self.select_at(oldnotes[0].time, self.stringid(oldnotes[0])) # Select something
          self.big_change_done()
          self.canvas.app.cancel.add_redo(do_it)
          
        do_it()
        
    elif (key == 102) and self.selection: # Right
      sel = self.selection[0]
      stringid = self.stringid(sel.note)
      #time = self.round(((sel.note.time / self.default_note.time) + 1) * self.default_note.time)
      time = sel.note.time + sel.note.duration
      next = sel.next()
      if next: time = min(time, next.note.time)
      self.select_at(time, stringid)
    elif (key == 100) and self.selection: # Left
      sel = self.selection[0]
      stringid = self.stringid(sel.note)
      #time = self.round(((sel.note.time / self.default_note.time) - 1) * self.default_note.time)
      time = sel.note.time - self.default_note.time
      previous = sel.previous()
      if previous: time = max(time, previous.note.time)
      self.select_at(time, stringid)
      
    elif (key == 98) and self.selection: # Up
      sel = self.selection[0]
      stringid = self.stringid(sel.note)
      if stringid > 0: self.select_at(sel.note.time, stringid - 1)
      else: # Select a note in the upper view.
        index = self.song.partitions.index(self.partition)
        if index > 0:
          self.deselect_all()
          view = self.song.partitions[index - 1].view
          view.add_selection(view.note_at(self.time_to_x(sel.note.time), view.y2, 1))
          
    elif (key == 104) and self.selection: # Down
      sel = self.selection[0]
      stringid = self.stringid(sel.note)
      if stringid < len(self.strings) - 1: self.select_at(sel.note.time, stringid + 1)
      else: # Select a note in the lower view.
        index = self.song.partitions.index(self.partition)
        if index < len(self.song.partitions) - 1:
          self.deselect_all()
          view = self.song.partitions[index + 1].view
          view.add_selection(view.note_at(self.time_to_x(sel.note.time), view.y1, 1))
          return 1 # Do not send the keydown event to the next view !!!
        
    elif key == 97: # origin
      sel = self.selection[0]
      stringid = self.stringid(sel.note)
      self.select_at(0, stringid)
    elif key == 103: # End
      sel = self.selection[0]
      stringid = self.stringid(sel.note)
      self.select_at(self.mesures[-1].endtime, stringid)
      
    elif key == 99: # page up
      sel = self.selection[0]
      stringid = self.stringid(sel.note)
      self.select_at(self.song.mesurebefore(sel.note.time).time, stringid)
    elif key == 105: # page down
      sel = self.selection[0]
      stringid = self.stringid(sel.note)
      self.select_at(self.song.mesure_at(sel.note.time).endtime(), stringid)
      
    elif (key == 23) and event.state: # Shift-tab : move to previous note on this string
      sel = self.selection[0]
      if sel:
        sel = sel.previous()
        if sel:
          self.deselect_all()
          self.add_selection(sel)
          
    elif key == 23: # Tab : move to next note on this string
      sel = self.selection[0]
      if sel:
        sel = sel.next()
        if sel:
          self.deselect_all()
          self.add_selection(sel)
          
  def on_button_press1(self, event, x, y):
    if self.y1 < y < self.y2:
      graphic_note = self.note_at(x, y)
      if graphic_note:
        self.deselect_all()
        self.add_selection(graphic_note)
      else:
        time     = self.x_to_round_time(x)
        self.select_at(time, self.y_to_stringid(y))
    else: self.deselect_all()
    
  def on_button_press2(self, event, x, y): pass
  
  def on_button_press3(self, event, x, y):
    # A right click on the header hide the tablature
    x1, y1, x2, y2 = self.canvas.bbox(self.header)
    if y1 <= y <= y2: self.hide()
    
  def select_at(self, time, stringid = 0):
    self.deselect_all()
    
    if   time < 0: time = 0
    elif time >= self.song.mesures[-1].time + 2 * self.song.mesures[-1].duration:
      time = self.song.mesures[-1].time + 2 * self.song.mesures[-1].duration - self.default_note.time
      
    # Check if we need to scroll in order to make the new section visible.
    self.canvas.app.ensure_visible_x(time * self.zoom + 30)
    
    graphic_note = self.get_at(time, stringid, 1)
    self.add_selection(graphic_note)
    return graphic_note
  
  def get_at(self, time, stringid, create = 0):
    try: graphic_note = self.graphic_notes[time, stringid]
    except (KeyError, NameError):
      if not create: return None
      # Creates a new "fake" note with no value (-1 as value means "fake notes", represented by a "_").
      graphic_note = self.drawnote(self.fake_note(time, stringid))
      
    return graphic_note
  
  def fake_note(self, time, stringid): pass
  
  def select_in_box(self, x1, y1, x2, y2):
    self.deselect_all()
    self.previoustype = 0
    
    for graphic_note in self.graphic_notes.values():
      if (x1 < graphic_note.x < x2) and y1 < graphic_note.y < y2:
        self.selection.append(graphic_note)
        graphic_note.set_selected(1)
        #self.add_selection(graphic_note)
        
    self.update_selection_box()
    
  def note_at(self, x, y, create = 0):
    for graphic_note in self.graphic_notes.values():
      if graphic_note.is_at(x, y): return graphic_note
      
    if create:
      # Creates a new "fake" note with no value (-1 as value means "fake notes", represented by a "_").
      note = song.Note(self.x_to_time(x), self.default_note.duration, -1, self.default_note.volume)
      if self.REQUIRE_STRINGID:
        note.stringid = self.y_to_stringid(y)
      graphic_note = self.drawnote(self.fake_note(self.x_to_time(x), self.y_to_stringid(y)))
      return graphic_note
    
  def paste(self, graphic_note_y_notes):
    oldnotes = []
    
    def do_it():
      self.deselect_all()
      
      for i in range(len(oldnotes)): del oldnotes[0] # Empty the list
      
      # Remove any note already at the same position as a new one.
      for graphic_note, y, note in graphic_note_y_notes:
        if isinstance(note, song.Note):
          stringid = self.y_to_stringid(y)
          
          oldnote = self.graphic_notes.get((note.time, stringid))
          if oldnote:
            oldnote.delete()
            oldnotes.append(oldnote.note)
            
      for graphic_note, y, note in graphic_note_y_notes:
        if isinstance(note, song.Note):
          stringid = self.y_to_stringid_(y)
          if stringid is None: # Out of the tab
            continue
          
          # Old tablature-specific code
          #
          #if isinstance(graphic_note.get_view(), Tablature):
          #  note.value = note.value - graphic_note.get_view().strings[note.stringid].basenote + self.strings[stringid].basenote

          if self.REQUIRE_STRINGID:
            note.stringid = stringid
            
          self.partition.addnote(note)
          self.add_selection(self.drawnote(note))
          
      self.big_change_done()
      self.checktime() # Add mesure bar if needed
      
      self.canvas.app.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      self.deselect_all()
      
      # Copy the notes before to remove them, since removing them may unlink some hammers...
      notes = map(lambda graphic_note_y_note: graphic_note_y_note[2], graphic_note_y_notes)
      notes = copy.deepcopy(notes)
      for i in range(len(graphic_note_y_notes)):
        graphic_note_y_notes[i] = graphic_note_y_notes[i][0], graphic_note_y_notes[i][1], notes[i]
        
      for graphic_note, y, note in graphic_note_y_notes:
        if isinstance(note, song.Note):
          graphic_note = self.get_at(note.time, self.y_to_stringid(y))
          if graphic_note: graphic_note.delete() # Else, it was pasted out of the tab !
          
      for note in copy.deepcopy(oldnotes): # Clone them, in order to keep "oldnotes" clean.
        self.partition.addnote(note)
        self.drawnote(note)
        
      self.big_change_done()
      
      self.canvas.app.cancel.add_redo(do_it)
      
    do_it()
  #def paste(self, graphic_note_y_notes): pass
  
  def big_change_done(self):
    """Called when important change has been done -- addition or deletion of a bunch of notes."""
    self.update_lyrics()
    
  def stringid(self, note): pass
  
  def x_to_time      (self, x   ): return int((x - self.x - 10) / self.zoom)
  def x_to_round_time(self, x   ): return int(round(int(((x - self.x - 10.0) / self.zoom / self.default_note.time) + 0.4) * self.default_note.time))
  def time_to_x      (self, time): return time * self.zoom + self.x + 10
  def y_to_stringid  (self, y   ): return max(0, min(int((y - self.y1 - 20.0) / self.STRING_SEP), len(self.strings) - 1))
  def round          (self, time): return int(round(int((time / self.default_note.time) + 0.4) * self.default_note.time))
  def y_to_stringid_ (self, y   ):
    # Similar to y_to_stringid, but return None if y is out of the tab.
    stringid = int(round(((y - self.y1 - self.STRING_SEP - 10.0) / self.STRING_SEP)))
    if (stringid < 0) or (stringid >= len(self.strings)): return None
    return stringid
  
  def destroy(self):
    if hasattr(self, "canvas"): # else, not initialized by "draw"
      self.bar.destroy()
      self.canvas.delete(self.group)
      for graphic_note in self.graphic_notes.itervalues(): graphic_note.tag = None # Mark them as deleted
      del self.canvas
      
    self.graphic_notes  = {} # Restore the view so it can be re-used !
    self.selection      = []
    self.mesures        = []
    self.mesuresmarks   = []
    
  def selected_notes(self): return self.selection
  
  def delay_update_lyrics(self):
    if not self.update_lyrics_delayed: 
      self.update_lyrics_delayed = 1
      self.canvas.after(50, self.update_lyrics)
      
  def update_lyrics(self):
    partitions = self.song.partitions
    i = partitions.index(self.partition) + 1
    while (i < len(partitions)) and isinstance(partitions[i], song.Lyrics2):
      partitions[i].view.update()
      i = i + 1
      
  def __getstate__(self): return None
  def __setstate__(self, dict): pass
  def __getinitargs__(self): return self.song, self.partition, self.strings, self.zoom
  

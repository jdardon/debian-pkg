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

# The list of (id, drum's patch)
DRUMS = map(lambda s: s.split(None, 1), globdef.translator.gettext("__percu__").split("\n"))

# The list of drums patches
PATCHES = map(lambda (id, patch): patch, DRUMS)

class String(view.String):
  def draw(self, canvas, group, x, y, length = 32000):
    self.y = y
    self.lines = (
      canvas.create_line(x, y, length, y, fill = "gray20", tag = group),
      canvas.create_text(canvas.app.old_x1 + 20, y + 2, text = PATCHES[self.basenote - 35], anchor = "sw", fill = "gray60", tag = (group, "noscroll")),
      )
  def __unicode__(self): return _("Drum patch, %s") % PATCHES[self.basenote - 35]

  
class DrumView(view.TabView):
  REQUIRE_STRINGID = 1
  
  def __init__(self, _song, partition, strings = None, zoom = 1.0, strings_args = None):
    if strings_args: strings = map(String, *zip(*strings_args))
    else:
      strings = []
      #d = dict(map(lambda string: (string.basenote, string), strings))
      d = {}
      for note in partition.notes:
        if (note.value > 0) and (not d.has_key(note.value)):
          d[note.value] = string = String(note.value)
          strings.append(string)
          
      if not strings: strings.append(String(50)) # Avoid empty drums
      
    view.TabView.__init__(self, _song, partition, strings, zoom)

    drums_view = self
    super      = self.drawnote
    class GraphicDrum(super): # Internal class
      def _text(self): return ((self.note.value > 0) and "X") or "_"
      
      def on_set_value(self, new):
        old = self.note.value
        
        def do_it():
          self.get_self().set_value(new)
          drums_view.canvas.app.cancel.add_cancel(cancel_it)
          
        def cancel_it():
          drums_view.deselect_all()  # XXX
          self.get_self().set_value(old)
          drums_view.canvas.app.cancel.add_redo(do_it)
          
        do_it()
        
      def __repr__(self): return u"<GraphicDrum for %s>" % self.note
      
    self.drawnote = GraphicDrum
    
  def on_key_press(self, event):
    if not self.selection: return
    
    if   event.char == "+":
      for selection in self.selection:
        selection.on_set_value(selection.string.basenote)
      self.checktime()
    elif event.char == "-":
      for selection in self.selection:
        selection.on_set_value(-selection.string.basenote)
        
    view.TabView.on_key_press(self, event)
    
  def on_button_press3(self, event, x, y):
    if self.y1 < y < self.y2: # A right click toggle the drum
      time     = self.x_to_round_time(x)
      stringid = min(int((y - self.y1 - 20.0) / 20.0), len(self.strings) - 1)
      self.select_at(time, stringid)
      
      for selection in self.selection: selection.on_set_value(-selection.note.value)
      
      self.checktime()
    else: view.TabView.on_button_press3(self, event, x, y)
    
  def fake_note(self, time, stringid):
    note = song.Note(time, self.default_note.duration, -self.strings[stringid].basenote, self.default_note.volume)
    note.stringid = stringid
    return note
  
  def paste(self, graphic_note_y_notes):
    for graphic_note, y, note in graphic_note_y_notes:
      if isinstance(graphic_note.get_view(), DrumView):
        stringid = self.y_to_stringid_(y)
        if not stringid is None:
          note.value = self.strings[stringid].basenote
          
    view.TabView.paste(self, graphic_note_y_notes)
    return
  
  def stringid(self, note, create = 0):
    value = abs(note.value)
    for i in range(len(self.strings)):
      if self.strings[i].basenote == value: return i
    if create:
      self.strings.append(String(value, 0))
      return len(self.strings) - 1
    return -1
  
  def __str__(self): return _("drums").encode("latin")
  
  def __xml__(self, xml, context, hidden = 0):
    if hidden:
      xml.write("""\t\t<view type="drums" hidden="0">
\t\t\t<strings>
""")
    else:
      xml.write("""\t\t<view type="drums">
\t\t\t<strings>
""")
    for string in self.strings:
      xml.write("""\t\t\t\t<string patch="%s" notation="%s"/>\n""" % (string.basenote, ("top", "down")[string.notationpos]))
    xml.write("""\t\t\t</strings>
\t\t</view>
""")
  
drums_view_type = view.ViewType("", _("EmptyDrums"), DrumView, { "strings_args": () }, 128)
view.ViewType("drums", _("Tom"     ), DrumView, { "strings_args": ((50, 0), (48, 0), (47, 0), (45, 1), (43, 1), (41, 1)) }, 128)
view.ViewType("drums", _("Cymbal"  ), DrumView, { "strings_args": ((49, 0), (57, 0), (55, 0), (52, 1), (51, 1), (59, 1)) }, 128)
view.ViewType("drums", _("Triangle"), DrumView, { "strings_args": ((80, 0), (81, 1)) }, 128)
view.ViewType("drums", _("Timbale" ), DrumView, { "strings_args": ((65, 0), (66, 1)) }, 128)
view.ViewType("drums", _("Bongo"   ), DrumView, { "strings_args": ((60, 0), (61, 1)) }, 128)
view.ViewType("drums", _("Conga"   ), DrumView, { "strings_args": ((62, 0), (63, 0), (64, 1)) }, 128)

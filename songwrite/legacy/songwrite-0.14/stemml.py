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

# This is the parser/reader for StemML.
# The writer is included in the song.py module.

import xml.sax as sax, xml.sax.handler as handler
from cStringIO import StringIO
import codecs

import song, songbook

def parse(file):
  if isinstance(file, unicode): file = file.encode("latin")
  
  parser = sax.make_parser()
  song_handler = SongHandler(parser, file)
  parser.setContentHandler(song_handler)
  parser.parse(file)

  if hasattr(song_handler, "songbook"): return song_handler.songbook
  else:                                 return song_handler.song
  
class SongHandler(handler.ContentHandler):
  def __init__(self, parser, file):
    self.parser = parser
    self.current    = ""
    self.need_strip = 0
    self.file = file
    
  def startElement(self, name, attrs):
    if   name == "bar":
      self.bar_attrs.update(attrs)
      rythm = self.bar_attrs["rythm"]
      i = rythm.index("/")
      if self.song.mesures:
        self.song.mesures.append(song.Mesure(self.song.mesures[-1].endtime(), int(self.bar_attrs["tempo"]), int(rythm[:i]), int(rythm[i + 1:]), int(self.bar_attrs["syncope"])))
      else:
        self.song.mesures.append(song.Mesure(0,                               int(self.bar_attrs["tempo"]), int(rythm[:i]), int(rythm[i + 1:]), int(self.bar_attrs["syncope"])))
        
    elif name == "play":
      self.song.playlist.playlist_items.append(song.PlaylistItem(self.song.playlist, int(attrs["from"]), int(attrs["to"])))
      
    elif name == "partition":
      partition_handler = PartitionHandler(self.parser, self, self.song, attrs)
      self.parser.setContentHandler(partition_handler)
      
    elif name == "lyrics":
      lyrics_handler = LyricsHandler(self.parser, self, self.song, attrs)
      self.parser.setContentHandler(lyrics_handler)
      
    elif name == "bars": pass
    elif name == "playlist": pass
    elif name == "song":
      self.bar_attrs = {"tempo" : 60, "syncope" : 0 , "rythm" : "4/4"}
      self.song = self.obj = song.Song()
      self.song.mesures *= 0
      self.song.version  = attrs.get("version", song.VERSION)
      self.song.lang     = attrs.get("lang", "en")[:2]
      self.song.filename = self.file
    elif name == "songfile":
      self.songbook.add_song(attrs.get("filename"), attrs.get("title"))
    elif name == "songbook":
      self.songbook = self.obj = songbook.Songbook(self.file, attrs.get("title", u""), attrs.get("authors", u""), attrs.get("comments", u""))
      self.songbook.version = attrs.get("version", song.VERSION)
    else: self.current = name
    
  def endElement(self, name):
    if   name == "song":
      self.song.playlist.analyse()
      
    if self.need_strip:
      setattr(self.obj, self.current, getattr(self.obj, self.current).strip())
      self.need_strip = 0
    self.current = ""
    
  def characters(self, content):
    if   self.current == "": pass
    else:
      setattr(self.obj, self.current, getattr(self.obj, self.current, u"") + content)
      self.need_strip = 1 # Will strip when the tag ends.

FX = {
  "normal"  : song.Note,
  "hammer"  : song.HammerNote,
  "legato"  : song.HammerNote,
  "slide"   : song.SlideNote,
  "bend"    : song.BendNote,
  "tremolo" : song.TremoloNote,
  "dead"    : song.DeadNote,
  "roll"    : song.RollNote,
  }
NOTATION_POS = {
  "top"  : 0,
  "down" : 1,
  }

class PartitionHandler(handler.ContentHandler):
  def __init__(self, parser, previous_handler, song_, attrs):
    self.parser               = parser
    self.previous_handler     = previous_handler
    self.partition            = song.Partition(song_)
    for attr, value in attrs.items():
      try: value = int(value)
      except:
        try: value = float(value)
        except: pass
      setattr(self.partition, attr, value)
    song_.partitions.append(self.partition)
    self.current     = ""
    self.id_to_notes = {}
    self.note_setter = {
      "time"        : None,
      "duration"    : None,
      "pitch"       : None,
      "volume"      : None,
      "linked_to"   : self.note_set_linked_to,
      "fx"          : self.note_set_fx,
      "id"          : self.note_set_id,
      "string"      : self.note_set_string,
      "bend_pitch"  : self.note_set_bend_pitch,
      }
    self.notes_linked_to = []
    self.roll_notes      = {}
    self.view_hidden     = 0
    self.need_strip      = 0
    
  def note_set_id(self, note, id): self.id_to_notes[id] = note
  
  def note_set_linked_to(self, note, id):
    # Cannot be done yet, since the following notes are not parsed yet !
    # We put this request somewhere and treat it later.
    if id:
      self.notes_linked_to.append((note, id))
      if note.__class__ is song.Note: note.__class__ = song.LinkedNote
    else: note.linked_to = None
    note.linked_from = None
    
  def note_set_fx(self, note, fx):
    note.__class__ = FX[fx]
    if fx == "roll":
      this_roll = self.roll_notes.get(note.time)
      if this_roll is None: self.roll_notes[note.time] = [note]
      else: this_roll.append(note)
      
  def note_set_string(self, note, stringid):
    note.stringid = int(stringid)
    
  def note_set_bend_pitch(self, note, bend_pitch):
    note.pitch = float(bend_pitch)
    
  def startElement(self, name, attrs):
    if   name == "note":
      note = song.Note(int(round(float(attrs["time"    ]) * 96.0)),
                       int(round(float(attrs["duration"]) * 96.0)),
                       int(attrs["pitch"]),
                       int(attrs.get("volume") or self.partition.notes[-1].volume),
                       )
      for attr in attrs.keys():
        setter = self.note_setter.get(attr, 1)
        if   setter is 1:
          value = attrs[attr]
          try: value = int(value)
          except:
            try: value = float(value)
            except: pass
          setattr(note, attr, value)
        elif setter: setter(note, attrs[attr])
        
      self.partition.notes.append(note)
      
    elif name == "notes"  : pass
    elif name == "strings": pass
    elif name == "string" :
      self.partition.view.strings.append(getattr(self.string_module, attrs.get("type") or "String")(int(attrs.get("pitch") or attrs.get("patch")), NOTATION_POS[attrs.get("notation", "top")]))
      
    elif name == "view":
      if   attrs["type"] == "tablature":
        import tablature
        
        self.partition.view = tablature.Tablature(self.partition.song, self.partition, [])
        self.string_module = tablature
        
      elif attrs["type"] == "drums":
        import drum
        
        self.partition.view = drum.DrumView(self.partition.song, self.partition, [])
        self.string_module = drum
        
      elif attrs["type"] == "staff":
        import staff
        
        if attrs.get("g8"): self.partition.setviewtype(staff.g8_view_type)
        else:               self.partition.setviewtype(staff.piano_view_type)
        self.string_module = staff
        
      if attrs.get("hidden"): self.view_hidden = 1
        
    else: self.current = name
    
  def endElement(self, name):
    if   name == "partition":
      # Finalize notes linked to another one
      for note, id in self.notes_linked_to:
        other = self.id_to_notes[id]
        note .linked_to   = other
        other.linked_from = note
        if other.__class__ is song.Note:
          other.__class__ = song.LinkedNote # other is linked !
          other.linked_to = None
          
      # Finalize rolls
      def sorter(b, a):
        try:    return cmp(a.stringid, b.stringid)
        except: return cmp(a.value, b.value)
      for roll in self.roll_notes.values():
        roll.sort(sorter)
        decal = 0
        for note in roll:
          note.decal = decal
          decal += 2
          
      self.parser.setContentHandler(self.previous_handler)
      
    elif name == "view":
      if self.view_hidden:
        import view
        
        self.partition.setviewtype(view.hidden_view_type)
        self.view_hidden     = 0
        
    elif name == self.current:
      if self.need_strip:
        setattr(self.partition, self.current, getattr(self.partition, self.current).strip())
        self.need_strip = 0
      self.current = ""
      
  def characters(self, content):
    if   self.current == ""    : pass
    else:
      setattr(self.partition, self.current, getattr(self.partition, self.current, u"") + content)
      self.need_strip = 1 # Will strip when the tag ends.
      
class LyricsHandler(handler.ContentHandler):
  def __init__(self, parser, previous_handler, song_, attrs):
    self.parser           = parser
    self.previous_handler = previous_handler
    self.lyrics           = song.Lyrics2(song_)
    song_.partitions.append(self.lyrics)
    self.texts      = []
    self.current    = ""
    self.need_strip = 0
    
  def startElement(self, name, attrs):
    if   name == "br":       self.texts.append("\\\\")
    elif name == "br-verse": self.texts.append("\n")
    else: self.current = name
    
  def endElement(self, name):
    if   name == "lyrics":
      import lyric2
      self.lyrics.text = "".join(self.texts).rstrip()
      self.lyrics.setviewtype(lyric2.lyric_view_type)
      self.parser.setContentHandler(self.previous_handler)
      
    elif name == self.current:
      if self.need_strip:
        setattr(self.lyrics, self.current, getattr(self.lyrics, self.current).strip())
        self.need_strip = 0
      self.current = ""
      
  def characters(self, content):
    if   self.current == ""    : pass
    elif self.current == "text":
      self.texts.append(content.replace("\n", ""))
    else:
      setattr(self.lyrics, self.current, getattr(self.lyrics, self.current, u"") + content)
      self.need_strip = 1 # Will strip when the tag ends.



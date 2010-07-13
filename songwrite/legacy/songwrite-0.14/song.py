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
import sys, os, struct, bisect, math, types

from xml.sax.saxutils import escape

VERSION = "0.14"

class SongwriteError(StandardError):
  pass

class TimeError(SongwriteError):
  def __init__(self, time, partition = None, note = None):
    self.time      = time
    self.partition = partition
    self.note      = note
    self.args      = time, partition, note
  def __unicode__(self):
    return _("__%s__" % self.__class__.__name__)
    
class UnsingablePartitionError(TimeError):
  pass
  
class _XMLContext:
  def __init__(self):
    self._next_id = 0
    self._ids = {}
    
  def id_for(self, obj):
    if obj is None: return ""
    
    id = self._ids.get(obj)
    if id is None:
      self._next_id += 1
      self._ids[obj] = self._next_id
      return self._next_id
    return id
  
  
def note_label(value):
  """note_label(value) -> string -- Return the string (e.g. "C(2)") for the given note int value."""
  if value == -1: return "_"
  return _("note_%s" % (value % 12,)) + u"(%s)" % (value / 12,)

DURATIONS = {
  384 : "Whole",
  192 : "Half",
   96 : "Quarter",
   48 : "Eighth",
   24 : "Sixteenth",
   12 : "Thirty-second",
  }

def duration_label(duration):
  """duration_label(duration) -> string -- Return the string (e.g. "Eighth") for the given note int duration."""
  global DURATIONS
  
  dur = DURATIONS.get(duration)
  if dur: return _(dur)
  
  dur = DURATIONS.get(int(duration / 1.5))
  if dur: return _(dur) + u" (.)"
  
  dur = DURATIONS.get(int(duration * 1.5))
  if dur: return _(dur) + u" (3)"
  
  return u"???"


class Song:
  def __init__(self):
    import getpass, time
    
    self.authors      = u""
    self.title        = u""
    self.copyright    = u""
    self.comments     = u""
    self.partitions   = []
    self.mesures      = [Mesure(0)]
    self.lang         = unicode(os.environ.get("LANG", "en")[:2])
    self.version      = 0.9
    self.playlist     = Playlist(self)
    self.filename     = ""
    
#  def __del__(self):
#    print "del song %s !!!" % self.title
    
  def __setstate__(self, state):
    self.__dict__ = state
    if not state.has_key("lang"): # New in 0.4
      self.lang = unicode(os.environ.get("LANG", "en")[:2])
      
    if not state.has_key("version"): # New in 0.5
      self.version = 0.4 # Or older...
      
    if self.version < 0.5:
      self.version = 0.6
      
      # Time unit has changed between 0.5 and 0.6
      durations = {
        256 : 384,
        128 : 192,
         64 :  96,
         32 :  48,
         16 :  24,
          8 :  12,
        
        384 : 576,
        192 : 288,
         96 : 144,
         48 :  72,
         24 :  36,
         12 :  18,
        
        170 : 256,
        171 : 256,
         85 : 128,
         86 : 128,
         42 :  64,
         43 :  64,
         21 :  32,
         22 :  32,
         10 :  16,
         11 :  16,
          5 :   8,
          6 :   8,
        }
      for mesure in self.mesures:
        mesure.time     = int(1.5 * mesure.time)
        mesure.duration = int(1.5 * mesure.duration)
        mesure.tempo    = int(1.5 * mesure.tempo)
        
      for partition in self.partitions:
        if isinstance(partition, Partition):
          for note in partition.notes:
            if   note.duration in (21, 22):
              x = note.time % 64
              note.time = int((note.time - x) * 1.5) + ((x > 0) * 32) + ((x > 30) * 32)
            elif note.duration in (10, 11):
              x = note.time % 32
              note.time = int((note.time - x) * 1.5) + ((x > 0) * 16) + ((x > 15) * 16)
            elif note.duration in (5, 6):
              x = note.time % 16
              note.time = int((note.time - x) * 1.5) + ((x > 0) *  8) + ((x >  7) *  8)
            else:
              note.time   = int(note.time * 1.5)
            note.duration = durations[note.duration]
            
    if self.version < 0.7:
      self.version = 0.7
      
      # We now use unicode !
      if isinstance(self.authors     , str): self.authors      = unicode(self.authors, "latin")
      if isinstance(self.title       , str): self.title        = unicode(self.title, "latin")
      if isinstance(self.copyright   , str): self.copyright    = unicode(self.copyright, "latin")
      if isinstance(self.comments    , str): self.comments     = unicode(self.comments, "latin")
      if isinstance(self.lang        , str): self.lang         = unicode(self.lang, "latin")
      
      for partition in self.partitions:
        if isinstance(partition.header, str): partition.header = unicode(partition.header, "latin")
        if hasattr(partition, "volume"):
          partition.volume = partition.volume * 2
          if partition.volume == 127 * 2: partition.volume = 255
        if isinstance(partition, Lyrics):
          for note in partition.notes:
            if isinstance(note.text, str): note.text = unicode(note.text, "latin")
            
    if self.version < 0.9:
      self.version = 0.9
      
      self.playlist = Playlist(self)
      self.playlist.analyse()
      
  def addmesure(self, mesure = None):
    if mesure is None:
      previous = self.mesures[-1]
      mesure   = Mesure(previous.time + previous.duration, previous.tempo, previous.rythm1, previous.rythm2, previous.syncope)
    self.mesures.append(mesure)
    return mesure
    
  def mesurebefore(self, time):
    if time > self.mesures[-1].endtime(): return self.mesures[-1]
    i = bisect.bisect_right(self.mesures, time) - 2
    if i < 0: return None
    return self.mesures[i]
    
#     previous = None
#     for mesure in self.mesures:
#       if mesure.endtime() > time: return previous
#       previous = mesure
#     return previous
  
  def mesure_at(self, time, create = 0):
    mesure = self.mesures[bisect.bisect_right(self.mesures, time) - 1]
    if create:
      while time >= mesure.endtime(): mesure = self.addmesure()
    elif    time >= mesure.endtime(): return None
    return mesure
  
    #for mesure in self.mesures:
    #  if mesure.endtime() > time: return mesure
    #if create:
    #  while 1:
    #    mesure = self.addmesure()
    #    if mesure.endtime() > time: return mesure
  
  def rythm_changed(self):
    time = 0
    for mesure in self.mesures:
      mesure.time = time
      time = time + mesure.duration
      
    # Check if we need to add or remove some mesures.
    maxtime = max(map(lambda partition: partition.endtime(), self.partitions))
    while maxtime >= self.mesures[-1].endtime(): self.addmesure()
    while maxtime <  self.mesures[-1].time:  del self.mesures[-1]
    
  def midi(self, start_time = 0, end_time = sys.maxint, rich_midi_tablature = 0):
    midifier = _Midi()
    
    for partition in self.partitions: partition.midi(midifier, start_time, end_time)
    if start_time != 0:
      return midifier.data(self.mesures, rich_midi_tablature, ())
    else:
      return midifier.data(self.mesures, rich_midi_tablature, self.playlist)
    
  def __unicode__(self): return self.title
  
  def __repr__(self):
    return u"""<Song %s
    Mesures :
%s
    Partitions :
%s
>""" % (
      self.title,
      u"\n".join(map(repr, self.mesures)),
      u"\n".join(map(repr, self.partitions)),
      )
  
  def date(self):
    import re
    year = re.findall(u"[0-9]{2,4}", self.copyright)
    if year: return year[0]
    return u""
  
  def __xml__(self, xml = None, context = None):
    if not xml:
      from cStringIO import StringIO
      import codecs
      _xml = StringIO()
      xml  = codecs.lookup("utf8")[3](_xml)
      
    if not context: context = _XMLContext()
    
    xml.write("""<?xml version="1.0" encoding="utf-8"?>

<song version="%s" lang="%s">
\t<title>%s</title>
\t<authors>%s</authors>
\t<copyright>%s</copyright>
\t<comments>%s</comments>
\t<bars>
""" % (VERSION, self.lang, escape(self.title), escape(self.authors), escape(self.copyright), escape(self.comments)))
    
    for mesure in self.mesures: mesure.__xml__(xml, context)
    xml.write('\t</bars>\n')
    xml.write('\t<playlist>\n')
    self.playlist.__xml__(xml, context)
    xml.write('\t</playlist>\n')
    
    for partition in self.partitions: partition.__xml__(xml, context)
    
    xml.write('</song>')
    
    xml.flush()
    return xml
  
TooManyChannelError = "TooManyChannelError"
  
class _Midi: # A midifier, for internal use
  def __init__(self):
    self.next_channel_id = 0
    self.events = []
    
    midi = self
    class BaseChannel: # A midi channel, for internal use
      def __init__(self, id):
        if id >= 16: raise TooManyChannelError
        self.special_id = self.id = id
        
      def set_init_events(self, init_events):
        self.init_events = init_events
        midi.events.extend(init_events)
        
      def __int__(self): return self.id
      
    class Channel(BaseChannel): # A normal midi channel, for internal use
      def __init__(self):
        BaseChannel.__init__(self, midi.next_channel_id)
        midi.next_channel_id += 1
        if midi.next_channel_id == 9: # Channel 9 is reserved for Drums !
          midi.next_channel_id += 1
          
      def fork_for_special_notes(self):
        self.special_id = midi.next_channel_id
        if self.special_id >= 16: raise TooManyChannelError
        midi.next_channel_id += 1
        
        midi.events.extend(map( # Transpose the initing events so it apply to the new channel -- the special channel must be initialized as the normal was !
          lambda data: (data[0], data[1], chr(ord(data[2][0]) - self.id + self.special_id) + data[2][1:]),
          self.init_events,
          ))
        
    self.Channel = Channel
    
    self.drums_channel = BaseChannel(9) # Play drums on channel 9 (10 if we start counting at 1)
    
  def data(self, mesures, rich_midi_tablature = 0, playlist = None):
    self.events.sort()
    
    lasttime = 0
    events2  = []
    
    playbar_info = [] # For displaying the playbar !!!
    
    time_factor = 1.0
    old_tempo   = mesures[0].tempo
    
    real_time = 0
    
    if playlist and playlist.playlist_items:
      events1 = []
      mesure2events = dict(map(lambda mesure: (mesure, []), mesures))
      
      for time_event in self.events:
        # Before event is a Midi meta-event that be stay JUST BEFORE event (this is for the Rich Tablature Midi Format)
        if len(time_event) == 3:
          time, mesure, event  = time_event
          source = None
        else: time, mesure, event, source = time_event
        
        if mesure is None:
          events2.append(varLength(0) + event)
          continue
          
        if time < 0: time = 0
        
        if mesure.syncope:
          t = (time - mesure.time) % 96
          if t < 48: t = t * 1.333333333      # First  half, longer
          else:      t = t * 0.666666666 + 32 # Second half, shorter
          time = mesure.time + ((time - mesure.time) / 96) * 96 + int(t)
          
        mesure2events[mesure].append((time, event, source))
        lasttime = time

      mesuretime = 0
      lasttime   = 0
      for item in playlist.playlist_items:
        for mesure in mesures[item.from_mesure : item.to_mesure + 1]:
          if mesure.tempo != old_tempo:
            time_factor = time_factor * old_tempo / mesure.tempo
            old_tempo = mesure.tempo
            
          for time_event in mesure2events[mesure]:
            time2, event, source = time_event
            time = time2 - mesure.time + mesuretime
            
            delta_time = (time - lasttime) * time_factor
            real_time += delta_time
            
            if ("\x90" <= event[0] < "\xA0") and ((not playbar_info) or (playbar_info[-1] != time)):
              playbar_info.append((time2, real_time))
              
            if rich_midi_tablature and source: # Add the rich midi tablature note event JUST BEFORE the event
              rich_midi_event = source.rich_midi_event()
              if rich_midi_event: events1.append((real_time, rich_midi_event))
              
            events1.append((real_time, event))
            lasttime = time
            
          mesuretime += mesure.duration
          
      events1.sort()
      lasttime = time
      for time, event in events1:
        events2.append(varLength(int(time - lasttime)) + event)
        lasttime = time
        
    else:
      for time_event in self.events:
        # Before event is a Midi meta-event that be stay JUST BEFORE event (this is for the Rich Tablature Midi Format)
        if len(time_event) == 3:
          time, mesure, event  = time_event
          source = None
        else: time, mesure, event, source = time_event
        
        if time < 0: time = 0
        
        if mesure:
          if mesure.syncope:
            t = (time - mesure.time) % 96
            if t < 48: t = t * 1.333333333      # First  half, longer
            else:      t = t * 0.666666666 + 32 # Second half, shorter
            time = mesure.time + ((time - mesure.time) / 96) * 96 + int(t)
            
          if mesure.tempo != old_tempo:
            time_factor = time_factor * old_tempo / mesure.tempo
            old_tempo = mesure.tempo
            
        delta_time = (time - lasttime) * time_factor
        real_time += delta_time
        
        if ("\x90" <= event[0] < "\xA0") and ((not playbar_info) or (playbar_info[-1] != time)):
          playbar_info.append((time, real_time))
          
        if rich_midi_tablature and source: # Add the rich midi tablature note event JUST BEFORE the event
          rich_midi_event = source.rich_midi_event()
          if rich_midi_event:
            events2.append(varLength(int(delta_time)) + rich_midi_event)
            lasttime = time
            
        events2.append(varLength(int(delta_time)) + event)
        lasttime = time

    events2.append(varLength(0) + END_TRACK)
    
    return chunk("MThd", struct.pack(">hhh", 0, 1, mesures[0].tempo)) + chunk("MTrk", "".join(events2)), playbar_info
    
    
class TemporalData:
  def midi(self, midifier, start_time, end_time): return ()
  
  # the view property and the corresponding methods are added in this class
  # (by adding a new super-class to it, what a hack !) by the "view" module.
  
  def __unicode__(self):
    text = self.header
    endofline = text.find("\n")
    if endofline != -1: return text[:endofline]
    else:               return text
    

class Partition(TemporalData):
  def __init__(self, song):
    self.song = song
    self.notes      = []
    self.instrument = 24
    self.chorus     = 0
    self.reverb     = 0
    self.header     = ""
    self.muted      = 0
    self.volume     = 255
    self.tonality   = "C"
    
  def __setstate__(self, state): # Compatibility with older format
    self.__dict__.update(state)
    if not state.has_key("header"): self.header = _("Guitar")
    if not state.has_key("muted" ): self.muted  = 0
    if not state.has_key("volume"): self.volume = 255
    
  def addnote(self, note):
    bisect.insort(self.notes, note)
    while note.time >= self.song.mesures[-1].endtime(): self.song.addmesure()
    
  def notes_at(self, time):
    if type(time) is types.IntType: time = Note(time, 0, 0)
    return self.notes[bisect.bisect_left(self.notes, time) : bisect.bisect_right(self.notes, time)]
  
  def notes_range(self, time1, time2):
    if type(time1) is types.IntType: time1 = Note(time1, 0, 0)
    if type(time2) is types.IntType: time2 = Note(time2, 0, 0)
    return self.notes[bisect.bisect_left(self.notes, time1) : bisect.bisect_left(self.notes, time2)]
  
  def note_before(self, time):
    if type(time) is types.IntType: time = Note(time, 0, 0)
    if (not self.notes) or (time.time <= self.notes[0].time): return None
    return self.notes[bisect.bisect_left(self.notes, time) - 1]
  
  def note_after(self, time):
    if type(time) is types.IntType: time = Note(time, 0, 0)
    if (not self.notes) or (time.time >= self.notes[-1].time): return None
    return self.notes[bisect.bisect_right(self.notes, time)]
  
  def delnote(self, note):
    note.deleted()
    self.notes.remove(note)
    
  def endtime(self):
    if self.notes: return self.notes[-1].endtime()
    return 0
  
  def midi(self, midifier, start_time, end_time):
    if not self.muted:
      if self.instrument == 128: # 128 means Drums
        channel = midifier.drums_channel
        channel.set_init_events((
          (-1, None, struct.pack(">bbb", 0xB0 + channel.id, 0x5B, self.reverb    )), # Reverb
          (-1, None, struct.pack(">bbb", 0xB0 + channel.id, 0x5D, self.chorus    )), # Chorus
          (-1, None, struct.pack(">bbb", 0xB0 + channel.id, 0x07, self.volume / 2)), # Volume
          ))
      else:
        channel = midifier.Channel()
        channel.set_init_events((
          (-1, None, struct.pack(">bb" , 0xC0 + channel.id, self.instrument), self),   # Instrument selection
          (-1, None, struct.pack(">bbb", 0xB0 + channel.id, 0x5B, self.reverb    )), # Reverb
          (-1, None, struct.pack(">bbb", 0xB0 + channel.id, 0x5D, self.chorus    )), # Chorus
          (-1, None, struct.pack(">bbb", 0xB0 + channel.id, 0x07, self.volume / 2)), # Volume
          ))
        
      # Check if some "special notes" (hammer, ...) are played at the same time that normal notes, and if so, play them on a different channel.
      special_notes = filter(lambda note: isinstance(note, SpecialEffect), self.notes)
      if special_notes:
        # We must ALWAYS fork since we don't know when a note really ends...
        channel.fork_for_special_notes()
        
      mesure   = self.song.mesures[0]
      idmesure = 0
      for note in self.notes:
        while note.time >= mesure.endtime():
          idmesure += 1
          mesure = self.song.mesures[idmesure]
          
        midifier.events.extend(note.midi_events(channel, mesure, start_time, end_time))
        
  def rich_midi_event(self):
    if not hasattr(self.view, "strings"): return None
    return "\xff\x10%s\x01\x00%s" % (struct.pack(">b", len(self.view.strings) + 2),
                                     "".join(map(lambda string: struct.pack(">b", string.basenote), self.view.strings)))
  
  def voices(self, single_voice = 0):
    "Gets the list of voices (non-overlapping sequence of notes) in this partition."
    if single_voice:
      voices = [[]]
      for note in self.notes:
        if self.is_in_chord(note) or self._clash_note_voice(note, voices[0]):
          raise UnsingablePartitionError(note.time, self, self._clash_note_voice(note, voices[0]))
        voices[0].append(note)
        
    else:
      voices = [[], []]
      for note in self.notes:
        if   self.is_in_chord(note): voices[0].append(note) # Chords are not bass !
        elif self._clash_note_voice(note, voices[0]): voices[1].append(note)
        elif self._clash_note_voice(note, voices[1]): voices[0].append(note)
        else:
          if   note.linked and note.linked_from: # Add with the other note !
            voices[note.linked_from in voices[1]].append(note)
          elif note.duration < 96: voices[0].append(note) # Too short for a bass !
          else:
            clashings = self.notes_at(note)
            if len(clashings) == 1:
              if getattr(note, "stringid", 6) >= 3: voices[1].append(note)
              else:                                 voices[0].append(note)
            else:
              clashings.sort(lambda a, b: cmp(a.value, b.value))
              if note is clashings[0]: voices[1].append(note)
              else:                    voices[0].append(note)

    return voices
  
  def __repr__(self):
    return u"""<Partition
    Notes :
%s
>""" % (
      "\n".join(map(repr, self.notes)),
      )
  
  def is_in_chord(self, note):
    """Check if the given note is part of a chord."""
    return len(self.notes_at(note)) >= 3
  
  def _clash_note_voice(self, note, voice):
    for n in voice:
      if note.clash(n): return n # not self.is_in_chord(note)
      
    return 0
  
  def __xml__(self, xml, context):
    xml.write("\t<partition")
    
    for attr, val in self.__dict__.items():
      if (not attr in ("header", "notes", "view", "song", "oldview")) and not attr.startswith("_"):
        xml.write(' %s="%s"' % (attr, unicode(val)))
        
    xml.write(">\n\t\t<header>%s</header>\n" % escape(self.header))
    
    if hasattr(self, "view"): self.view.__xml__(xml, context)
    xml.write("\t\t<notes>\n")
    
    for note in self.notes: note.__xml__(xml, context)
    
    xml.write("""\t\t</notes>
\t</partition>
""")
    
  
def Drums(song):
  drums = Partition(song)
  drums.instrument = 128
  drums.header     = ""
  return drums


class Note:
  linked = 0
  must_be_linked_to = 0
  
  def __init__(self, time = 0, duration = 0, value = 0, volume = 0xCC):
    self.time     = time
    self.duration = duration
    self.value    = value
    self.volume   = volume
    
  def endtime(self): return self.time + self.duration
  
  def clash(self, other):
    "Checks if this note clashes with (= overlaps) other, and are not part of the same chord."
    return (self.endtime() > other.time) and (other.endtime() > self.time)
    #return (self.time + self.duration > other.time) and (other.time + other.duration > self.time) and (not ((self.time == other.time) and (self.duration == other.duration)))
  
  def dissimilarity(self, other):
    "Gets a quantifier that quantifies how 2 notes differ."
    dissimilarity = 2 * abs(self.duration - other.duration) + 2 * abs(self.value - other.value) + abs(self.volume - other.volume) / 5
    if hasattr(self, "stringid") and hasattr(other, "stringid"):
      dissimilarity = dissimilarity + 10 * abs(self.stringid - other.stringid)
    return dissimilarity
  
  def midi_events(self, channel, mesure, start_time, end_time):
    if start_time <= self.time <= end_time:
      return (self.time - start_time, mesure, struct.pack(">bbb", 0x90 + channel.id, self.value, self.volume), self), (self.time - start_time + self.duration, mesure, struct.pack(">bbb", 0x80 + channel.id, self.value, self.volume))
    return ()
  
  def rich_midi_event(self):
    if not hasattr(self, "stringid"): return None
    return "\xff\x11\x01" + struct.pack(">b", self.stringid)
  
  def dotted    (self):
    return int(self.duration / 1.5) in DURATIONS.keys()
    return self.duration in (9, 18, 36, 72, 144, 288, 576)
  def is_triplet(self):
    return int(self.duration * 1.5) in DURATIONS.keys()
    return self.duration in (4,  8, 16, 32,  64, 128, 256)
  def is_start_triplet(self):
    return self.is_triplet() and ((self.time % int(self.duration * 1.5)) == 0)
  def is_end_triplet(self):
    return self.is_triplet() and (0 < (self.time % int(self.duration * 1.5)) < self.duration)
  
  def base_duration(self):
    """Gets the duration of the note, without taking into account dot or triplet."""
    dur = DURATIONS.keys()
    if self.duration            in dur: return self.duration
    if int(self.duration / 1.5) in dur: return int(self.duration / 1.5)
    if int(self.duration * 1.5) in dur: return int(self.duration * 1.5)
    return self.duration
  
  def link_to(self, other):
    if other:
      self ._link_to  (other)
      other._link_from(self)
  def _link_to(self, other):
    #print "linking %s to   %s" % (self, other)
    if other:
      self.__class__   = LinkedNote
      self.linked_to   = other
      self.linked_from = None
  def _link_from(self, other):
    #print "linking %s from %s" % (self, other)
    if other:
      self.__class__   = LinkedNote
      self.linked_to   = None
      self.linked_from = other
  def remove_effect(self):
    self.__class__ = Note
    
  def get_effect(self): return Note
  
  def deleted(self): pass
  
  def duration_with_link(self): return self.duration # No link
  
  def __repr__(self):
    s = u"<%s %s at %s" % (self.__class__.__name__, self.value, self.time)
    if hasattr(self, "stringid"): s = s + u" on string %s" % self.stringid
    s = s + u", duration %s, volume %s" % (self.duration, self.volume)
    return s + ">"
  
  def __eq__(self, other): return self is other
  def __cmp__(self, other): return self.time - other.time
  def __hash__(self): return id(self)
  
  def __xml__(self, xml, context):
    xml.write('\t\t\t<note pitch="%s" time="%s" duration="%s" volume="%s"' % (self.value, self.time / 96.0, self.duration / 96.0, self.volume))
    if hasattr(self, "stringid"): xml.write(' string="%s"' % self.stringid)
    xml.write('/>\n')
    
class LinkedNote(Note):
  "A note that may be linked to or/and from another."
  linked = 1
  must_be_linked_to = 0
  def __init__(self, *args):
    Note.__init__(self, *args)
    self.linked_from = self.linked_to = None
    
  def midi_events(self, channel, mesure, start_time, end_time): return ()
  
  def deleted(self):
    if self.linked_to  : self.link_to(None)
    
  def link_to(self, other):
    if self.linked_to: self.linked_to._link_from(None)
    if other and other.linked and other.linked_from:
      other.linked_from.link_to(None) # Call other._link_from(None) and other.linked_from._link_to(None)
      
    self._link_to(other)
    if other: other._link_from(self)
    
  def _link_to(self, other):
    if other:
      self.linked_to = other
    else:
      self.linked_to = None
      if (not self.linked_from) and (not self.must_be_linked_to): # No longer linked
        self.__class__ = Note
        del self.linked_to
        del self.linked_from
        
  def _link_from(self, other):
    if other:
      self.linked_from = other
    else:
      self.linked_from = None
      if (not self.linked_to) and (not self.must_be_linked_to): # No longer linked
        self.__class__ = Note
        del self.linked_to
        del self.linked_from
        
  def duration_with_link(self):
    if self.linked_to: return self.duration + self.linked_to.duration_with_link()
    return self.duration
  
  def min_max_values_in_link(self):
    "LinkedNote.min_max_values_in_link() -> min, max. Return the minimal and maximal note's value in the group of linked notes."
    if self.linked_from: return self.linked_from.min_max_values_in_link() # Start at the beginning of the link !
    return self._min_max_values_in_link()
    
  def _min_max_values_in_link(self):
    if self.linked_to:
      _min, _max = self.linked_to._min_max_values_in_link()
      return min(_min, self.value), max(_max, self.value)
    else: return self.value, self.value # no further link
    
  def first_value(self):
    "Gets the value of the first note of this group of linked notes."
    if self.linked_from: return self.linked_from.first_value()
    return self.value
    
  def remove_effect(self):
    self.__class__ = LinkedNote
    self.link_to(None)
    
  def __repr__(self):
    s = Note.__repr__(self)[:-1]
    if self.linked_to  : s = s + u" linked to note at %s"   % self.linked_to.time
    if self.linked_from: s = s + u" linked from note at %s" % self.linked_from.time
    return s + u">"
  
  def __xml__(self, xml, context):
    xml.write('\t\t\t<note pitch="%s" time="%s" duration="%s" volume="%s"' % (self.value, self.time / 96.0, self.duration / 96.0, self.volume))
    if self.linked_to:   xml.write(' linked_to="%s"' % context.id_for(self.linked_to))
    if self.linked_from: xml.write(' id="%s"'        % context.id_for(self))
    if hasattr(self, "stringid"): xml.write(' string="%s"' % self.stringid)
    xml.write('/>\n')
  
class SpecialEffect:
  def init_effect(self):
    "init_effect(note) -- Initialize the given note with this class of effect."
    pass
  
  def get_effect(self): return self.__class__

class HammerNote(SpecialEffect, LinkedNote):
  must_be_linked_to = 1
  
  def link_type(self):
    if   self.value > self.linked_to.value: return "pull"
    elif self.value < self.linked_to.value: return "hammer"
    else: return "link"
    
  def midi_events(self, channel, mesure, start_time, end_time):
    if start_time <= self.time <= end_time:
      _min, _max = self.min_max_values_in_link()
      midi_events = [] # Here we'll use the "special ID" channel, and not the channel normal ID, to avoid to change other notes played in parallel on the normal channel
      
      if _max - 2 <= self.first_value() <= _min + 2:
        if not self.linked_from:
          midi_events.append((self.time - start_time,                             mesure, struct.pack(">bbb", 0x90 + channel.special_id, self.value, self.volume), self))
          midi_events.append((self.time - start_time + self.duration_with_link(), mesure, struct.pack(">bbb", 0x80 + channel.special_id, self.value, self.volume)))
          midi_events.append((self.time - start_time,                             mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 63))) # Reset initial pitch bend
          
        midi_events.append((self.linked_to.time - start_time,                     mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 31.5 * (self.linked_to.value - self.first_value() + 2)))) # Pitch bend
        
      else:
        if not self.linked_from:
          midi_events.append((self.time - start_time,                             mesure, struct.pack(">bbb", 0x90 + channel.special_id, _min + 2, self.volume), self))
          midi_events.append((self.time - start_time + self.duration_with_link(), mesure, struct.pack(">bbb", 0x80 + channel.special_id, _min + 2, self.volume)))
          midi_events.append((self.time - start_time,                             mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 31.5 * (self.value - _min)))) # Initial pitch bend
          
        midi_events.append((self.linked_to.time - start_time,                     mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 31.5 * (self.linked_to.value - _min)))) # Pitch bend
        
        if not self.linked_to:
          pass
          # No need to reset : pitch bend is applied only to the "special" channel
          #midi_events.append((self.time - start_time + self.duration_with_link(), struct.pack(">bbb", 0xE0 + channel.special_id, 64, 64))) # Reset pitch bend
        
      return tuple(midi_events)
    return ()
  
  def rich_midi_event(self):
    if not hasattr(self, "stringid"): return None
    dif = cmp(self.value, self.linked_to.value)
    if   dif < 0: return "\xff\x11\x02%s\x01" % struct.pack(">b", self.stringid)
    elif dif > 0: return "\xff\x11\x02%s\x02" % struct.pack(">b", self.stringid)
    else:         return "\xff\x11\x02%s\x01" % struct.pack(">b", self.stringid) # Not supported by Rich Tablature Midi ???
    
  def __xml__(self, xml, context):
    xml.write('\t\t\t<note pitch="%s" time="%s" duration="%s" volume="%s" fx="hammer" linked_to="%s"' % (self.value, self.time / 96.0, self.duration / 96.0, self.volume, context.id_for(self.linked_to)))
    if self.linked_from: xml.write(' id="%s"'        % context.id_for(self))
    if hasattr(self, "stringid"): xml.write(' string="%s"' % self.stringid)
    xml.write('/>\n')
    
class SlideNote(SpecialEffect, LinkedNote):
  must_be_linked_to = 1
  def midi_events(self, channel, mesure, start_time, end_time):
    if start_time <= self.time <= end_time:
      _min, _max = self.min_max_values_in_link()
      midi_events = [] # Here we'll use the "special ID" channel, and not the channel normal ID, to avoid to change other notes played in parallel on the normal channel
      
      if _max - 2 <= self.first_value() <= _min + 2:
        if not self.linked_from:
          midi_events.append((self.time - start_time                            , mesure, struct.pack(">bbb", 0x90 + channel.special_id, self.value, self.volume), self))
          midi_events.append((self.time - start_time + self.duration_with_link(), mesure, struct.pack(">bbb", 0x80 + channel.special_id, self.value, self.volume)))
          midi_events.append((self.time - start_time                            , mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 63))) # Reset initial pitch bend
          
        delta_time  = self.linked_to.time  - self.time
        delta_value = self.linked_to.value - self.first_value()
        for i in xrange(10):
          f = i / 10.0
          midi_events.append((self.time + int(f * delta_time) - start_time,       mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 31.5 * (f * delta_value + 2)))) # Pitch bend
          
      else:
        if not self.linked_from:
          midi_events.append((self.time - start_time,                             mesure, struct.pack(">bbb", 0x90 + channel.special_id, _min + 2, self.volume), self))
          midi_events.append((self.time - start_time + self.duration_with_link(), mesure, struct.pack(">bbb", 0x80 + channel.special_id, _min + 2, self.volume)))
          midi_events.append((self.time - start_time,                             mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 31.5 * (self.value - _min)))) # Initial pitch bend
          
        delta_time  = self.linked_to.time  - self.time
        delta_value = self.linked_to.value - self.value
        for i in xrange(10):
          f = i / 10.0
          midi_events.append((self.time + int(f * delta_time) - start_time,       mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 31.5 * (f * delta_value + self.value - _min)))) # Pitch bend
          
      return tuple(midi_events)
    return ()
  
  def rich_midi_event(self):
    if not hasattr(self, "stringid"): return None
    if self.value < self.linked_to.value: return "\xff\x11\x02%s\x03" % struct.pack(">b", self.stringid)
    else:                                 return "\xff\x11\x02%s\x04" % struct.pack(">b", self.stringid)
    
  def __xml__(self, xml, context):
    xml.write('\t\t\t<note pitch="%s" time="%s" duration="%s" volume="%s" fx="slide" linked_to="%s"' % (self.value, self.time / 96.0, self.duration / 96.0, self.volume, context.id_for(self.linked_to)))
    if self.linked_from: xml.write(' id="%s"'        % context.id_for(self))
    if hasattr(self, "stringid"): xml.write(' string="%s"' % self.stringid)
    xml.write('/>\n')
  
class BendNote(SpecialEffect, Note):
  def midi_events(self, channel, mesure, start_time, end_time):
    if start_time <= self.time <= end_time:
      midi_events = [] # Here we'll use the "special ID" channel, and not the channel normal ID, to avoid to change other notes played in parallel on the normal channel
      
      midi_events.append((self.time - start_time                            , mesure, struct.pack(">bbb", 0x90 + channel.special_id, self.value, self.volume), self))
      midi_events.append((self.time - start_time + self.duration_with_link(), mesure, struct.pack(">bbb", 0x80 + channel.special_id, self.value, self.volume)))
      midi_events.append((self.time - start_time                            , mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 63))) # Reset initial pitch bend
      
      delta_time  = self.duration
      delta_value = 2.0 * self.pitch
      for i in xrange(10):
        f = i / 10.0
        midi_events.append((self.time + int(f * delta_time) - start_time, mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 31.5 * (f * delta_value + 2)))) # Pitch bend
        
      return tuple(midi_events)
    return ()
  
  def init_effect(self, pitch = 0.5):
    self.pitch = pitch
    
  def remove_effect(self):
    del self.pitch # Useless attribute
    Note.remove_effect(self)
    
  def rich_midi_event(self):
    if not hasattr(self, "stringid"): return None
    return "\xff\x11\x03%s\x0C%s" % (struct.pack(">b", self.stringid), struct.pack(">b", self.pitch / 0.25))
    
  def __xml__(self, xml, context):
    xml.write('\t\t\t<note pitch="%s" time="%s" duration="%s" volume="%s" fx="bend" bend_pitch="%s"' % (self.value, self.time / 96.0, self.duration / 96.0, self.volume, self.pitch))
    if hasattr(self, "stringid"): xml.write(' string="%s"' % self.stringid)
    xml.write('/>\n')
  
class TremoloNote(SpecialEffect, Note):
  def midi_events(self, channel, mesure, start_time, end_time):
    if start_time <= self.time <= end_time:
      midi_events = [] # Here we'll use the "special ID" channel, and not the channel normal ID, to avoid to change other notes played in parallel on the normal channel
      
      midi_events.append((self.time - start_time,                             mesure, struct.pack(">bbb", 0x90 + channel.special_id, self.value, self.volume), self))
      midi_events.append((self.time - start_time + self.duration_with_link(), mesure, struct.pack(">bbb", 0x80 + channel.special_id, self.value, self.volume)))
      midi_events.append((self.time - start_time,                             mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 63))) # Reset initial pitch bend
      
      val = 0.0
      for time in xrange(self.time - start_time, self.time - start_time + self.duration, 2):
        midi_events.append((time, mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 31.5 * (math.sin(val) * 0.3 + 2)))) # Pitch bend
        val += 0.3
        
      return tuple(midi_events)
    return ()
    
  def rich_midi_event(self):
    if not hasattr(self, "stringid"): return None
    return "\xff\x11\x02%s\x0A" % struct.pack(">b", self.stringid)
  
  def __xml__(self, xml, context):
    xml.write('\t\t\t<note pitch="%s" time="%s" duration="%s" volume="%s" fx="tremolo"' % (self.value, self.time / 96.0, self.duration / 96.0, self.volume))
    if hasattr(self, "stringid"): xml.write(' string="%s"' % self.stringid)
    xml.write('/>\n')
  
class DeadNote(SpecialEffect, Note):
  def midi_events(self, channel, mesure, start_time, end_time):
    if start_time <= self.time <= end_time:
      midi_events = [] # Here we'll use the "special ID" channel, and not the channel normal ID, to avoid to change other notes played in parallel on the normal channel
      
      midi_events.append((self.time - start_time,                             mesure, struct.pack(">bbb", 0x90 + channel.special_id, self.value, self.volume), self))
      midi_events.append((self.time - start_time + self.duration_with_link(), mesure, struct.pack(">bbb", 0x80 + channel.special_id, self.value, self.volume)))
      midi_events.append((self.time - start_time,                             mesure, struct.pack(">bbb", 0xE0 + channel.special_id, 63, 63))) # Reset initial pitch bend
      
      midi_events.append((self.time - start_time + 16,                        mesure, struct.pack(">bbb", 0xB0 + channel.special_id, 120, 0))) # Stop all sounds
      
      return tuple(midi_events)
    return ()
    
  def rich_midi_event(self):
    if not hasattr(self, "stringid"): return None
    return "\xff\x11\x02%s\x0E" % struct.pack(">b", self.stringid)
  
  def __xml__(self, xml, context):
    xml.write('\t\t\t<note pitch="%s" time="%s" duration="%s" volume="%s" fx="dead"' % (self.value, self.time / 96.0, self.duration / 96.0, self.volume))
    if hasattr(self, "stringid"): xml.write(' string="%s"' % self.stringid)
    xml.write('/>\n')
  
class RollNote(SpecialEffect, Note):
  def midi_events(self, channel, mesure, start_time, end_time):
    if start_time <= self.time <= end_time:
      return (self.time - start_time + self.decal, mesure, struct.pack(">bbb", 0x90 + channel.id, self.value, self.volume), self), (self.time - start_time + self.duration, mesure, struct.pack(">bbb", 0x80 + channel.id, self.value, self.volume))
    return ()
  
  def init_effect(self, decal = 2):
    self.decal = decal
    
  def remove_effect(self):
    del self.decal # Useless attribute
    Note.remove_effect(self)
    
  def rich_midi_event(self):
    if not hasattr(self, "stringid"): return None
    if self.decal: return Note.rich_midi_event(self)
    return "\xff\x11\x02%s\x06" % struct.pack(">b", self.stringid)
    
  def __xml__(self, xml, context):
    xml.write('\t\t\t<note pitch="%s" time="%s" duration="%s" volume="%s" fx="roll"' % (self.value, self.time / 96.0, self.duration / 96.0, self.volume))
    if hasattr(self, "stringid"): xml.write(' string="%s"' % self.stringid)
    xml.write('/>\n')
  

class Lyrics(TemporalData):
  def __init__(self, song):
    self.song  = song
    self.notes = self.lyrics = []
    self.header = ""
    
  def __setstate__(self, state): # Compatibility with old format
    self.__dict__ = state
    if not state.has_key("header"): self.header = _("Lyric")
    
  def addlyric(self, lyric):
    bisect.insort(self.lyrics, lyric)
    
  def dellyric(self, lyric):
    self.lyrics.remove(lyric)
    
  addnote = addlyric
  delnote = dellyric
  
  def endtime(self):
    if self.lyrics: return self.lyrics[-1].endtime()
    return 0
  
  def __repr__(self):
    return u"""<Lyrics :
%s
>""" % (
      "\n".join(map(repr, self.lyrics)),
      )
  
  def to_lyrics2(self):
    texts = map(lambda lyric: lyric.text.split("\n"), self.notes)
    text  = u""
    
    cont = 1
    i    = 0
    while cont:
      cont = 0
      for t in texts:
        if i < len(t):
          text = text + "\t" + t[i]
          cont = 1
      text = text + "\n"
      i = i + 1
      
    text = text.replace(" ", "\t").replace("- ", "-\t")
    
    lyrics2 = Lyrics2(self.song, text[1:-1])
    lyrics2.header = self.header
    return lyrics2
  
class Lyric:
  def __init__(self, mesure, text = u""):
    self.mesure = mesure
    self.text   = text
    
  def endtime(self): return self.mesure.endtime()
  def midi_events(self, channel, start_time, end_time): return ()
  
  def __unicode__(self): return self.text
  def __repr__(self): return u"<Lyric %s at %s>" % (self.text, self.mesure.time)
  
  def __eq__(self, other): return self is other
  def __cmp__(self, other): return self.mesure.time - other.mesure.time


class Lyrics2(TemporalData):
  def __init__(self, song, text = u""):
    self.song  = song
    self.header = ""
    self.text = text
    
  def get_melody(self):
    index = self.song.partitions.index(self)
    while index >= 0:
      if isinstance(self.song.partitions[index], Partition):
        return self.song.partitions[index]
      index = index - 1
    return None
  
  def endtime(self): return 0
  
  def __repr__(self):
    return u"""<Lyrics :
%s
>""" % self.text
      
  def __xml__(self, xml, context):
    xml.write(u"""\t<lyrics>
\t\t<header>%s</header>
""" % escape(self.header))
    
    if hasattr(self, "view"): self.view.__xml__(xml, context)
    
    text = self.text.replace("\\\\", "<br/>")
    if text and (text[-1] == "\n"): text = text[:-1]
    text = text.replace("\n", "<br-verse/>")
    
    xml.write(u"""\t\t<text>
%s
\t\t</text>
\t</lyrics>
""" % text)
#""" % (self.text.replace("\\\\", "<br/>").replace("\n", "<br-verse/>")))  
  

class Sounds(TemporalData):
  def __init__(self, song):
    self.song   = song
    self.sounds = []
    self.notes  = self.sounds
    self.header = ""
    
  def addsound(self, sound):
    bisect.insort(self.sounds, sound)
    while sound.time >= self.song.mesures[-1].endtime(): self.song.addmesure()
    
  def delsound(self, sound):
    self.sounds.remove(sound)
    
  addnote = addsound
  delnote = delsound
  
  def endtime(self):
    if self.sounds: return self.sounds[-1].endtime()
    return 0
  
  def __repr__(self):
    return u"""<Sounds :
%s
>""" % (
      "\n".join(map(repr, self.sounds)),
      )

class Sound:
  def __init__(self, time, bsound):
    self.time     = time
    self.bsound   = bsound
    
  def endtime(self): return self.time + self.bsound.duration
  
  def __repr__(self):
    s = "<Base Sound %s at %s" % (self.bsound.filename, self.time)
    return s + ">"

  def __deepcopy__(self, memo):
    dict = self.__dict__.copy()
    del dict["bsound"]
    clone =  Sound(self.time, self.bsound)
    clone.__dict__.update(dict)
    return clone

# TO DO ok ?  
  def __eq__(self, other): return self is other
  def __cmp__(self, other): return self.time - other.time
  
  def __getstate__(self):
    dict = self.__dict__.copy()
    dict["bsound"] = self.bsound.filename
# TO DO relative filename
    return dict
  
  def __setstate__(self, state):
    self.__dict__ = state
    filename = self.bsound
    
    import gtkwav
    self.bsound = gtkwav.load_sound(filename)
    
class Mesure:
  def __init__(self, time, tempo = 60, rythm1 = 4, rythm2 = 4, syncope = 0):
    self.time     = time
    self.tempo    = tempo
    self.rythm1   = rythm1
    self.rythm2   = rythm2
    self.syncope  = syncope
    self.compute_duration()
    
  def compute_duration(self):
    self.duration = 384 / self.rythm2 * self.rythm1
    if not((self.rythm2 == 4) or ((self.rythm2 == 8) and (self.rythm1 % 3 == 0))):
      print "Warning: unsupported rythm: %s/%s" % (self.rythm1, self.rythm2)
      
  def endtime(self): return self.time + self.duration
  
  def setrythm(self, tempo = 60, rythm1 = 4, rythm2 = 4, syncope = 0):
    if (rythm2 == 4) or ((rythm2 == 8) and (rythm1 % 3 == 0)):
      self.duration = 384 / rythm2 * rythm1
      self.tempo    = tempo
      self.rythm1   = rythm1
      self.rythm2   = rythm2
      self.syncope  = syncope
    else: raise UnsupportedRythmError, "%s/%s" % (rythm1, rythm2)
    
  def __repr__(self): return "<Mesure at %s, duration %s>" % (self.time, self.duration)
  
  def __xml__(self, xml, context):
    xml.write("""\t\t<bar rythm="%s/%s" tempo="%s" syncope="%s"/>\n""" % (self.rythm1, self.rythm2, self.tempo, self.syncope))
    
  def __eq__(self, other): return self is other
  
  def __cmp__(self, other):
    if isinstance(other, Mesure): return cmp(self.time, other.time)
    return cmp(self.time, other)
  
  __hash__ = object.__hash__
  
  
class Playlist:
  def __init__(self, song):
    self.song             = song
    self.playlist_items   = []
    self.symbols          = {}
    
  def __unicode__(self): return _("playlist")
  def __str__    (self): return _("playlist")
  
  def __xml__(self, xml, context):
    for item in self.playlist_items:
      xml.write("""\t\t<play from="%s" to="%s"/>\n""" % (item.from_mesure, item.to_mesure))
      
  def analyse(self):
    self.symbols.clear()
    symbols = self.symbols

    bornes = {}
    for item in self.playlist_items: bornes[item.from_mesure] = bornes[item.to_mesure + 1] = 1
    bornes = bornes.keys()
    bornes.sort()
    
    splitted_playlist = []
    for item in self.playlist_items:
      a = bisect.bisect_right(bornes, item.from_mesure)
      b = bisect.bisect_left (bornes, item.to_mesure + 1)
      if a == b: # No borne inside => OK
        splitted_playlist.append(item)
      else: # we need to split this one
        cur = item.from_mesure
        for borne in bornes[a : b + 1]:
          splitted_playlist.append(PlaylistItem(self, cur, borne))
          cur = borne

    alternatives = {} # map a start block to its list of alternatives.
    onces = []
    too_complex = 0
    
    next_new  = 0
    in_repeat = None
    prev = prev2 = None
    for item in splitted_playlist:
      if   item == prev:
        if not alternatives.has_key(item):
          alternatives[item] = []
          
      elif in_repeat:
        alts = alternatives[in_repeat]
        if (item.from_mesure == next_new) or (len(filter(lambda i: i == item, alts)) == len(alts)):
          alts.append(item)
          in_repeat = None
        else:
          too_complex = 1
          break
        
      elif item == prev2:
        in_repeat = item
        if not alternatives.has_key(item): alternatives[item] = [prev]
        
      elif item.from_mesure != next_new:
        too_complex = 1
        break
      
      if next_new < item.to_mesure + 1: next_new = item.to_mesure + 1
      
      prev2 = prev
      prev  = item
      
    def add_to(mesure_id, code):
      if mesure_id < len(self.song.mesures): mesure = self.song.mesures[mesure_id]
      else:                                  mesure = None # None means "at the end"
      if symbols.has_key(mesure): symbols[mesure].append(code)
      else:                       symbols[mesure] = [code]

      
    # Do NOT remove comment ("% ...") at the end of Lilypond code !
    # They are used by Songwrite drawing stuff.
    
    if too_complex: # Too complex...
      print "Warning: playlist is too complex!"
      for borne in bornes[ 1:]: add_to(borne, r"} % end repeat")
      for borne in bornes[:-1]: add_to(borne, r"\repeat volta 2 {")
      
    else:
      for start, alts in alternatives.iteritems():
        add_to(start.from_mesure, r"\repeat volta %s {" % (len(alts) or 2))
        if alts:
          add_to(start.to_mesure + 1, r"} % end repeat with alternatives")
          add_to(alts[0].from_mesure, r"\alternative {")
          
          for i in range(len(alts)):
            alt = alts[i]
            add_to(alt.from_mesure,   "{ % start alternative " + str(i + 1))
            if alt is alts[-1]: add_to(alt.to_mesure + 1, "} % end last alternative")
            else:               add_to(alt.to_mesure + 1, "} % end alternative")
            
          add_to(alts[-1].to_mesure + 1, r"} % end alternatives")
          
        else: # No alternatives
          add_to(start.to_mesure + 1, r"} % end repeat")
          
class PlaylistItem:
  def __init__(self, playlist, from_mesure, to_mesure):
    self.playlist = playlist
    self.from_mesure = from_mesure
    self.to_mesure   = to_mesure
    
  def __unicode__(self): return _(u"__PlaylistItem__") % (self.from_mesure, self.to_mesure)
  
  def __eq__(self, other): return isinstance(other, PlaylistItem) and (self.from_mesure == other.from_mesure) and (self.to_mesure == other.to_mesure)
  
  def __cmp__(self, other): return cmp(self.from_mesure, other.from_mesure)

  def __hash__(self): return hash(self.from_mesure) ^ hash(self.to_mesure)
  
# Midi stuff :

def chunk(name, data):
  return struct.pack(">4si", name, len(data)) + data

def varLength(i):
  array = [i & 0x7F]
  
  while i >= 128:
    i = i >> 7
    array.append((i & 0x7F) | 0x80)
    
  array.reverse()
  return struct.pack(">" + "b" * len(array), *array)

def readVarLength(file):
  result = 0
  
  while 1:
    b = struct.unpack(">B", file.read(1))[0]
    
    result = result | (b & 0x7F)
    if (b & 0x80) != 0x80: break
    result = result << 7
    
  return result

END_TRACK = struct.pack(">bbb", 0xFF, 0x2F, 0x00)



# Songwrite
# Copyright (C) 2001-2002 Jean-Baptiste LAMY
#
# This program is free software. See README or LICENSE for the license terms.

from __future__ import nested_scopes
import sys, array, bisect, cStringIO as StringIO
import string as string_module # not a guitar string !
import song, asciitab

GotoError = "GotoError"

class LilyVoice:
  def __init__(self, lily, mesures, mesure2repeatcodes):
    self.time               = 0
    self.lily               = lily
    self.mesures            = mesures[:]
    self.last_rythm         = None
    self.last_duration      = None
    self.mesure2repeatcodes = mesure2repeatcodes
    
  def goto(self, time):
    if   time < self.time: raise song.TimeError, time
    elif time > self.time:
      rab = time - self.time
      
      dur = 384
      
      while rab:
        nb = rab / dur
        if nb:
          next_time = self.time + nb * dur
          if self.mesures and (next_time >= self.mesures[0].time):
            mesure = self.mesures.pop(0)
            
            rab = rab - (mesure.time - self.time)
            
            self.goto(mesure.time)
            
            self.draw_mesure(mesure)
          else:
            self.time = next_time
            for i in range(nb): self.draw_wait(dur)
            rab = rab % dur
            dur = dur / 2
        else: dur = dur / 2
        
    else: # Do not advance the time, but check mesure
      mesure = None
      while self.mesures and (time >= self.mesures[0].time): mesure = self.mesures.pop(0)
      if mesure:
        self.draw_mesure(mesure)
        
    if self.time != time: raise GotoError
    
  def draw_mesure(self, mesure):
    #repeatcodes = self.mesure2repeatcodes.get(mesure)
    #if repeatcodes: self.lily.write("\n        " + repeatcodes + "\n        ")
    
    repeatcodes = self.mesure2repeatcodes.get(mesure)
    if repeatcodes:
      del self.mesure2repeatcodes[mesure]
      for code in repeatcodes:
        self.lily.write("\n        " + code)
        
    self.lily.write("\n       ")
    if self.last_rythm != (mesure.rythm1, mesure.rythm2):
      self.last_rythm = (mesure.rythm1, mesure.rythm2)
      self.lily.write(r" \time %s/%s" % self.last_rythm)
      
  def draw_wait(self, duration):
    if duration == self.last_duration:
      self.lily.write(" s")
    else:
      self.lily.write(" s%s" % _durations[duration])
      self.last_duration = duration
      
  def _draw_note(self, note, duration = None):
    octavo = note.value / 12
    if octavo < 4: self.lily.write(" " + _notes[note.value % 12] + "," * (4 - octavo))
    else:          self.lily.write(" " + _notes[note.value % 12] + "'" * (octavo - 4))
    duration = duration or note.duration
    if duration != self.last_duration:
      self.lily.write(_durations[duration])
      self.last_duration = duration
      
  def draw_note(self, note, duration = None):
    self._draw_note(note, duration)
    #if note.volume > 220: self.lily.write(r" \accent") # Does not render well...
    if isinstance(note, song.RollNote) and note.decal == 0: self.lily.write(r"\arpeggio")
    
  def draw_chord(self, notes, duration = None):
    first = notes[0]
    if first.is_start_triplet(): self.lily.write(r" \times 2/3 {")
    
    if len(notes) > 1:
      self.lily.write(" <")
      for note in notes: self.draw_note(note, duration)
      self.lily.write(" >")
      
      if   isinstance(first, song.HammerNote): self.lily.write(" ~")
    else:
      if isinstance(first, song.LinkedNote) and isinstance(first.linked_from, song.HammerNote): self.lily.write(" )")
      self.draw_note(first, duration)
      if isinstance(first, song.HammerNote): self.lily.write(" (")
      
    if isinstance(first, song.SlideNote): self.lily.write(" \glissando")
    
    if first.is_end_triplet(): self.lily.write(r" }")
    
  def end(self):
    end_codes = self.mesure2repeatcodes.get(None, ())
    if end_codes: del self.mesure2repeatcodes[None]
    
    remnant_codes = map(lambda (mesure, codes): (mesure.time, codes),  self.mesure2repeatcodes.items())
    remnant_codes.sort()
    for time, codes in remnant_codes:
      for code in codes:
        self.lily.write("\n        " + code)
        
    for code in end_codes:
      self.lily.write("\n        " + code)
      
    self.lily.write(r"""
        \bar "|."
""")
    
class LilyStaffVoice(LilyVoice):
  def draw(self, notes):
    batch = []
    for note in notes:
      if (not batch) or note.time == batch[0].time: batch.append(note)
      else:
        first = batch[0]
        self.goto(first.time)
        duration = min(note.time - first.time, *map(lambda n: n.duration, batch))
        self.time = first.time + duration
        self.draw_chord(batch, duration)
        
        batch = [note]
        
    if batch:
      first = batch[0]
      self.goto(first.time)
      duration = min(map(lambda n: n.duration, batch))
      self.time = first.time + duration
      self.draw_chord(batch, duration)

class LilyTabVoice(LilyVoice):
  def __init__(self, lily, mesures, mesure2repeatcodes, strings):
    LilyVoice.__init__(self, lily, mesures, mesure2repeatcodes)
    self.strings = strings
    
  def _draw_note(self, note, duration = None):
    LilyVoice._draw_note(self, note, duration)
    self.lily.write(r"\%s" % (note.stringid + 1))
    
  def draw(self, notes):
    batch = []
    for note in notes:
      if (not batch) or note.time == batch[0].time: batch.append(note)
      else:
        first = batch[0]
        self.goto(first.time)
        duration = min(note.time - first.time, *map(lambda n: n.duration, batch))
        self.time = first.time + duration
        self.draw_chord(batch, duration)
        
        batch = [note]
        
    if batch:
      first = batch[0]
      self.goto(first.time)
      duration = min(map(lambda n: n.duration, batch))
      self.time = first.time + duration
      
      self.draw_chord(batch, duration)
      
      
def lilypond(_song, lily = None):
  mesure2repeatcodes = _song.playlist.symbols
  endtime = max(map(lambda partition: partition.endtime(), _song.partitions))
  
     
  
  if not lily: lily = StringIO.StringIO()
  lily.write(r"""
\include "italiano.ly"

\score { \simultaneous {
""")
  
  
  def draw_partition(partition, tablature, lyric):
      if lyric:
        i = _song.partitions.index(partition) + 1
        text = []
        while (i < len(_song.partitions)) and isinstance(_song.partitions[i], song.Lyrics2):
          texts = map(lambda line: line.split("\t"), _song.partitions[i].text.split("\n"))

          for line in texts:
            for j in range(len(line)):
              if j < len(text):
                if not text[j]: text[j] = line[j]
              else: text.append(line[j])
          i = i + 1

        if text:
          lyric = "\t".join(text)
          lyric = lyric.encode("latin").replace("-\t_", "- _").replace("_", " __ ").replace("-\t", " -- ").replace("\t", " ").replace("\\\\", " ").replace("  ", " ").strip()
        else: lyric = None
      
      if tablature:
        stafftype = "TabStaff"
        voicetype = "TabVoice"
      else:
        stafftype = "Staff"
        voicetype = "Voice"
        
      if lyric: lily.write(r"""  \addlyrics""")
      
      lily.write(r"""  \new StaffGroup << \new %s {
    \set Staff.instrument = "%s"
    <<
""" % (stafftype, first_word(partition.header).encode("latin")))
      
      if tablature:
        tunings = map(lambda string: str(string.basenote - 60), partition.view.strings)
        tunings = " ".join(tunings)
        if tunings != "4 -1 -5 -10 -15 -20": # Default value => skip
          lily.write(r"""      \property TabStaff.stringTunings = #'(%s)
""" % tunings)
      elif partition.view.is_g8():
        lily.write(r"""      \clef G_8""")
        
      voices = partition.voices(lyric)
      for voice in voices:
        if not voice: continue
        
        lily.write(r"""    {
     """)
        if voice is voices[-1]: lily.write(r""" \property %s.Stem \set #'direction = #'-1
       """ % voicetype)
        else:                   lily.write(r""" \property %s.Stem \set #'direction = #'1
       """ % voicetype)
        
        if tablature: voice_drawer = LilyTabVoice(lily, _song.mesures, {}, partition.view.strings)
        else:
          import staff
          voice_drawer = LilyStaffVoice(lily, _song.mesures, {})
          lily.write(r""" \key %s \major
        """ % _notes[staff.OFFSETS[partition.tonality]])
        if voice is voices[0]:
          voice_drawer.mesure2repeatcodes = mesure2repeatcodes.copy()
        try: voice_drawer.draw(voice)
        except song.TimeError, time: raise song.TimeError, (partition, time)
        except: raise ValueError, (partition, voice_drawer.time)
        
        voice_drawer.goto(endtime)
        
        if voice is voices[0]:
          #voice_drawer.goto(partition.endtime())
          voice_drawer.end()
          
        lily.write(r"""
    }
""")
            
      if lyric: lily.write(r"""  \context Lyrics \lyrics { %s }
""" % lyric)
      
      lily.write(r"""    >>
  }
  >>
""")
      
      
  
  for partition in _song.partitions:
    if   partition.view.__class__.__name__ == "Tablature":
      if partition.print_with_staff_too: draw_partition(partition, 0, 0)
      draw_partition(partition, 1, 1)
      
    elif partition.view.__class__.__name__ == "Staff":
      draw_partition(partition, 0, 1)


  lily.write(r"""}}""")

      
  
  return lily.getvalue()


_notes = (
  "do",
  "dod",
  "re",
  "red",
  "mi",
  "fa",
  "fad",
  "sol",
  "sold",
  "la",
  "lad",
  "si",
  )
_durations = {
  # Normal duration
  384 :   "1",
  192 :   "2",
   96 :   "4",
   48 :   "8",
   24 :  "16",
   12 :  "32",
    6 :  "64",
    3 : "128",

  # Doted durations
  576 :  "1.",
  288 :  "2.",
  144 :  "4.",
   72 :  "8.",
   36 : "16.",
   18 : "32.",
    9 : "64.",
  
  # Triplets
   32 :  "8",
   16 : "16",
    8 : "32",
    4 : "64",
  }

def first_word(text):
  return text.split()[0]

  br = min(text.find("\n"), text.find(" "))
  if br == -1: return text
  return text[0 : br]


class LilyPlaylistItem(song.PlaylistItem):
  def __init__(self, from_mesure, to_mesure, type):
    song.PlaylistItem.__init__(self, None, from_mesure, to_mesure)
    self.type = type
    
  def __unicode__(self): return u"%s : %s" % (song.PlaylistItem.__unicode__(self), self.type)
  
  
def contains_only(list, item):
  for i in list:
    if i != item: return 0
  return 1



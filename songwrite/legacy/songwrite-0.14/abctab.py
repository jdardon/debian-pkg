# SongWrite
# Copyright (C) 2004 Jean-Baptiste LAMY -- jibalamy@free.fr
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

import globdef, staff

import cStringIO

_tabnotes = "abcdefghiklmnopqrstuvwxyz"

_notes = {
  "C" : ( "c", "^c",  "d", "^d",  "e",  "f",  "f",  "g", "^g",  "a", "^a",  "b"),
  
  "G" : ( "c", "^c",  "d", "^d",  "e", "_f",  "f",  "g", "^g",  "a", "^a",  "b"),
  "D" : ("_c",  "c",  "d", "^d",  "e", "_f",  "f",  "g", "^g",  "a", "^a",  "b"),
  "A" : ("_c",  "c",  "d", "^d",  "e", "_f",  "f", "_g",  "g",  "a", "^a",  "b"),
  "E" : ("_c",  "c", "_d",  "d",  "e", "_f",  "f", "_g",  "g",  "a", "^a",  "b"),
  "B" : ("_c",  "c", "_d",  "d",  "e", "_f",  "f", "_g",  "g", "_a",  "a",  "b"),
  "F#": ("_c",  "c", "_d",  "d", "_e",  "e",  "f", "_g",  "g", "_a",  "a",  "b"),
  "C#": ( "b",  "c", "_d",  "d", "_e",  "e",  "f", "_g",  "g", "_a",  "a", "_b"),
  
  "F" : ( "c", "^c",  "d", "^d",  "e",  "f", "^f",  "g", "^g",  "a",  "b", "^b"),
  "Bb": ( "c", "^c",  "d",  "e", "^e",  "f", "^f",  "g", "^g",  "a",  "b", "^b"),
  "Eb": ( "c", "^c",  "d",  "e", "^e",  "f", "^f",  "g",  "a", "^a",  "b", "^b"),
  "Ab": ( "c",  "d", "^d",  "e", "^e",  "f", "^f",  "g",  "a", "^a",  "b", "^b"),
  "Db": ( "c",  "d", "^d",  "e", "^e",  "f",  "g", "^g",  "a", "^a",  "b", "^b"),
  "Gb": ("^c",  "d", "^d",  "e", "^e",  "f",  "g", "^g",  "a", "^a",  "b",  "c"),
  "Cb": ("^c",  "d", "^d",  "e",  "f", "^f",  "g", "^g",  "a", "^a",  "b",  "c"),
  }
_durations = {
  # Normal duration
  384 : "4",
  192 : "2",
   96 : "1",
   48 :  "/",
   24 :  "/4",
   12 :  "/8",
    6 :  "/16",
    3 :  "/32",
  
  # Doted durations
  576 : "6",
  288 : "3",
  144 : "3/2",
   72 : "3/4",
   36 : "3/8",
   18 : "3/16",
    9 : "3/32",
  
  # Triplets
   32 : "1/3",
   16 : "1/6",
    8 : "1/12",
    4 : "1/24",
  }
def abcduration(duration, note = None):
  if note and note.is_start_triplet(): return "(3" + _durations[duration]
  return _durations[duration]


class TimingError(Exception): pass


class Timer:
  def __init__(self, song):
    self.song      = song
    self.mesures   = song.mesures
    self.time      = 0
    self.mesure_id = 0
    
  def split(self, duration):
    time      = self.time
    mesure_id = self.mesure_id
    durations = []
    while 1:
      mesure_endtime = self.mesures[mesure_id].endtime()
      if time + duration < mesure_endtime:
        dur = duration
        durations.append(dur)
        time += duration
        break
      
      dur = mesure_endtime - time
      durations.append(dur)
      time = mesure_endtime
      mesure_id += 1
      duration -= dur
      if duration == 0: break
      
    return durations
    
  def advance(self, duration, add_rest = 0):
    print "avance de", duration, add_rest
    
    durations = []
    while 1:
      mesure_endtime = self.mesures[self.mesure_id].endtime()
      if self.time + duration < mesure_endtime:
        dur = duration
        if add_rest: self.add_rest(dur)
        durations.append(dur)
        self.time += duration
        break
      
      dur = mesure_endtime - self.time
      if add_rest: self.add_rest(dur)
      durations.append(dur)
      self.time = mesure_endtime
      self.mesure_id += 1
      duration -= dur
      self.change_mesure(self.mesures[self.mesure_id - 1], self.mesures[self.mesure_id])
      if duration == 0: break
      
    return durations
    
  def goto(self, time):
    if time < self.time: raise TimingError
    self.advance(time - self.time, 1)
    
    
class AbcTimer(Timer):
  def __init__(self, song, abc):
    Timer.__init__(self, song)
    self.abc = abc
    
  def add_rest(self, duration):
    dur = 384
    while duration:
      nb = duration / dur
      duration %= dur
      for i in range(nb): self.abc.write("z" + abcduration(dur))
      dur /= 2

  def start(self):
    for s in self.song.playlist.symbols.get(self.mesures[0], ()):
      if s.startswith(r"\repeat volta"):
        self.abc.write("|:")
        
  def end(self):
    self.abc.write("|]")
    
  def change_mesure(self, left, right):
    print "change mesure"
    #print left, self.song.playlist.symbols.get(left, None), right, self.song.playlist.symbols.get(right, None)
    
    for s in self.song.playlist.symbols.get(left, ()):
      if   s == r"} % end repeat":                   self.abc.write(":") 
      elif s == r"} % end repeat with alternatives": self.abc.write(":") 
      elif s == r"} % end alternative":              self.abc.write(":")
      elif s == r"} % end last alternative":         self.abc.write(":")
      
    self.abc.write("|")
    
    for s in self.song.playlist.symbols.get(right, ()):
      if   s.startswith(r"\repeat volta"):         self.abc.write(":")
      elif s.startswith(r"{ % start alternative"): self.abc.write("[" + s.split()[-1])
      
      
      
      
def abctab(s):
  abc = cStringIO.StringIO()
  print >> abc, "%%!abctab2ps -paper %s" % {"a3paper" : "a3", "a4paper" : "a4", "a5paper" : "a5", "letterpaper" : "letter", }[globdef.config.PAGE_FORMAT]
  print >> abc, "X:1"
  print >> abc, "L:1/4"
  if s.title   : print >> abc, "T:%s" % s.title
  if s.authors : print >> abc, "C:%s" % s.authors
  if s.comments: print >> abc, "N:%s" % s.comments.replace("\n", "N:\n")
  if s.filename: print >> abc, "F:%s" % s.filename
  
  for partition in s.partitions:
    if hasattr(partition, "tonality"):
      print >> abc, "K:%s" % partition.tonality
      break
  else:
    print >> abc, "K:C"
    
  nb = 0
  for partition in s.partitions:
    if   partition.view.__class__.__name__ == "Tablature":
      clef = " clef=guitartab"
      tab  = 6
    elif partition.view.__class__.__name__ == "Staff":
      clef = ""
      tab  = 0
    else: continue
    
    lyric    = None # XXX
    tonality = getattr(partition, "tonality", "C")
    
    print >> abc, "%"
    print >> abc, "V:%s name=%s%s" % (nb, partition.header, clef)
    print >> abc, "K:%s" % tonality
    
    nb += 1
    
    timer = AbcTimer(s, abc)
    timer.start()
    
    chords = chordify(partition.notes)
    for chord in chords:
      timer.goto(chord.time)
      
      if tab:
        for duration in timer.split(chord.duration):
          frets = [","] * tab
          for note in chord.notes:
            stringid = partition.view.stringid(note)
            frets[stringid] = _tabnotes[note.value - partition.view.strings[stringid].basenote]

          while frets and (frets[-1] == ","): frets.pop()
          abc.write("[%s%s]" % ("".join(frets), abcduration(duration)))
          
          timer.advance(duration)
          
      else:
        for duration in timer.advance(chord.duration):
          for note in chord.notes:
            abc.write(
              "[" * ((len(chord.notes) > 1) and (note is chord.notes[0])) +
              _notes[tonality][note.value % 12] +
              "," * (4 - note.value / 12) +
              "'" * (note.value / 12 - 4) +
              abcduration(duration, note) +
              "]" * ((len(chord.notes) > 1) and (note is chord.notes[-1]))
              )
      
    timer.end()
    
  print >> open("/home/jiba/tmp/test.abc", "w"), abc.getvalue()
  return abc.getvalue()



class Chord:
  def __init__(self, time):
    self.time  = time
    self.notes = []
    self.duration = 1000000
    
  def add(self, note):
    self.notes.append(note)
    self.duration = min(note.duration, self.duration)
    
  def __repr__(self):
    return "<Chord at %s duration %s %s>" % (self.time, self.duration, self.notes)
    
def chordify(notes):
  chords   = []
  previous = None
  notes    = notes[:]
  
  while notes:
    chord = Chord(notes[0].time)
    chords.append(chord)
    
    while notes:
      if notes[0].time == chord.time: chord.add(notes.pop(0))
      else: break
      
    if previous:
      if previous.time + previous.duration > chord.time: # Overlaps !!!
        previous.duration = chord.time - previous.time
        
    previous = chord

  return chords
  

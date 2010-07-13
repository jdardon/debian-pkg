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

PITCHS = {
  "C"  :  0,
  "D"  :  2,
  "E"  :  4,
  "F"  :  5,
  "G"  :  7,
  "A"  :  9,
  "B"  : 11,
  }

class MelodyNotePlacer:
  def __init__(self):
    self.pos = 1.0
    
  def __call__(self, note):
    if not note.time: note.time = self.pos
    self.pos = note.time + note.duration
    
class ChordNotePlacer:
  def __init__(self):
    self.pos = 1.0
    
  def __call__(self, note):
    if not note.time: note.time = self.pos
    else:             self.pos = note.time
    
class ComplexNotePlacer:
  def __init__(self, follow):
    self.pos    = 1.0
    try: self.offset = float(follow)
    except:
      a, b = follow.split("/")
      self.offset = a / b
      
  def __call__(self, note):
    if not note.time: note.time = self.pos
    self.pos = note.time + note.duration + self.offset
    
    
class Parser:
  def __init__(self):
    self.pitch    = 0
    self.octavo   = 48
    self.duration = 1.0
    self.volume   = 64
    
    self.parsers = {
      "pitch"    : self.parse_pitch,
      "duration" : self.parse_duration,
      "start"    : self.parse_start,
      }
    
  def parse_pitch(self, attr, pitch):
    try: self.cur_note.value = int(pitch)
    except:
      if ":" in pitch:
        pitch, octavo = pitch.split(":")
        self.octavo = octavo * 12
        
      self.pitch = PITCHS[pitch[0]]
      if len(pitch) > 1:
        if   pitch[1] == "#": self.pitch += 1
        elif pitch[1] == "b": self.pitch -= 1
      self.cur_note.value = self.pitch + self.octavo
      
  def parse_duration(self, attr, duration):
    try: self.cur_note.duration = float(duration)
    except:
      a, b = duration.split("/")
      self.cur_note.duration = a / b
      
  def parse_duration(self, attr, start):
    self.cur_note.time = float(start)
    
  def parse_other(self, attr, value):
    setattr(self.cur_note, attr, value)
    

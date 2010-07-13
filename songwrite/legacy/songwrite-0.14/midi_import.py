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

# This module is ONLY for midi importation.
# For exportation, see song.py.

import sys, struct, song

def parse(file):
  _song = song.Song()
  
  partitions = {}
  def channel2partition(channel):
    return partitions.get(channel) or new_partition(channel)
  def new_partition(channel):
    partition = song.Partition(_song)
    _song.partitions.append(partition)
    if channel == 9: # Drums
      import drum
      
      partition.instrument = 128
      
    partitions[channel] = partition
    return partition
  
  name, length = struct.unpack(">4si", file.read(8))
  if name != "MThd": raise ValueError, ("Not a midi file !", file)
  format, nb_tracks, tempo = struct.unpack(">hhh", file.read(6))
  
  for i in range(nb_tracks):
    name, length = struct.unpack(">4si", file.read(8))
    if name != "MTrk": raise ValueError, ("Not a track !", file)
    
    partitions = {}
    time = 0
    opened_notes = {}
    stringid = None
    Note = song.Note
    end_at = file.tell() + length
    while file.tell() < end_at:
      time  = time + song.readVarLength(file)
      event = struct.unpack(">B", file.read(1))[0]
      #print hex(event), file.tell() - 1
      
      if   0x80 <= event < 0x90: # Note off
        channel = event - 0x80
        
        value = struct.unpack(">B", file.read(1))[0]
        try:
          note = opened_notes[channel, value]
          note.duration = time - note.time
          del opened_notes[channel, value]
        except:
          print "Warning ! Note off without note on at time %s !" % time
        file.read(1)
        
      elif 0x90 <= event < 0xA0: # Note on
        channel = event - 0x90
        
        value, volume = struct.unpack(">BB", file.read(2))
        
        if volume == 0: # A Note on with wolume == 0 is a Note off ???
          try:
            note = opened_notes[channel, value]
            note.duration = time - note.time
            del opened_notes[channel, value]
          except:
            print "Warning ! Note off without note on at time %s !" % time
            
        else:          
          note = opened_notes[channel, value] = Note(time, 256, value, volume) # Duration is unknown
          if Note is not song.Note: Note = song.Note
          
          if stringid is not None:
            note.stringid = stringid
            stringid = None
            
          channel2partition(channel).addnote(note)
          
      elif 0xA0 <= event < 0xB0:
        print "Warning ! aftertouch not supported !"
        file.read(2)
        
      elif 0xB0 <= event < 0xC0:
        partition = channel2partition(event - 0xB0)
        
        event = struct.unpack(">B", file.read(1))[0]
        if   event == 0x5B: partition.reverb = struct.unpack(">B", file.read(1))[0]
        elif event == 0x5D: partition.chorus = struct.unpack(">B", file.read(1))[0]
        elif event == 0x07: partition.volume = struct.unpack(">B", file.read(1))[0]
        else:
          print "Warning ! unknown midi controller : %s, value : %s" % (hex(event), struct.unpack(">B", file.read(1))[0])
          
      elif 0xC0 <= event < 0xD0:
        partition = channel2partition(event - 0xC0)
        if partition.instrument != 128: # Else it is drums ; an instrument event has no sens for the drums channel but it occurs in some mids...
          partition.instrument = struct.unpack(">B", file.read(1))[0]
          
      elif 0xD0 <= event < 0xE0:
        print "Warning ! aftertouch not supported !"
        file.read(1)
        
      elif 0xE0 <= event < 0xF0:
        print "Warning ! pitchwheel not supported ! Use rich midi if you want to import hammer/bend/...."
        file.read(1)
        file.read(1)
        
      elif event == 0xF0: # System exclusive
        print repr(file.read(1))
        while struct.unpack(">B", file.read(1))[0] != 0xF7: pass
        
      elif event == 0xFF:
        event   = struct.unpack(">B", file.read(1))[0]
        length  = struct.unpack(">B", file.read(1))[0]
        content = file.read(length)
        
        if   event == 0x01: # Comment ?
          #print "Comment :", content
          if _song.comments: _song.comments = _song.comments + "\n" + content
          else:              _song.comments = content
          
        elif event == 0x02: # Copyright ?
          #print "Copyright :", content
          if _song.copyright: _song.copyright = _song.copyright + content
          else:               _song.copyright = content
          
        elif event == 0x2F: # End of track
          file.seek(end_at)
          break
        
        else:
          print "Warning ! unknow sequence 0xFF", hex(event), "  content (%s bytes) : %s" % (len(content), content)

  #       event = struct.unpack(">B", file.read(1))[0]

  #       if   event == 0x2F: # End
  #         file.seek(end_at)
  #         break

  #       elif event == 0x11: # Rich tab midi event
  #         event = struct.unpack(">B", file.read(1))[0]

  #         if   event == 0x01:
  #           stringid = struct.unpack(">B", file.read(1))[0]
  #         elif event == 0x02:
  #           stringid = struct.unpack(">B", file.read(1))[0]
  #           Note = song.HammerNote

      else:
        print "Warning ! unknown midi event :", hex(event)
        continue

  for partition in _song.partitions:
    if partition.instrument == 128: # Drums
      import drum
      partition.setviewtype(drum.drums_view_type)
  #    
  #    notes = {}
  #    for note in partition.notes: notes[note.value] = 1
  #    partition.view.strings = map(drum.String, notes.keys())
      
  for mesure in _song.mesures: mesure.tempo = tempo
  
  # Removes partition without any note
  _song.partitions = filter(lambda partition: partition.notes, _song.partitions)
  
  # Start the song at time == 0
  start = min(map(lambda partition: min([sys.maxint] + map(lambda note: note.time, partition.notes)), _song.partitions))
  for partition in _song.partitions:
    for note in partition.notes:
      note.time = note.time - start
      
  return _song
  
if __name__ == "__main__":
  import sys, globdef
  
  file = open(sys.argv[1])
  
  s = parse(file)
  
  #print len(s.partitions)
  #sys.exit()
  
  #print s
  
  import player
  player.play(s)
  
  import time
  
  while 1:
    time.sleep(1000)

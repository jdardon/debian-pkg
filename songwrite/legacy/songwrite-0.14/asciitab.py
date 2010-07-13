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
import sys, array, song, cStringIO as StringIO, re
import string as string_module # not a guitar string !
import tablature

#  ../tmp/test.asciitab

def parse(asciitab):
  if not isinstance(asciitab, unicode): asciitab = asciitab.decode("latin")
  ASCII_STRING    = u"-="
  ASCII_BAR       = u"|"
  ASCII_STRESSED  = u"'"
  ASCII_HAMMER    = u"hpl"
  ASCII_SLIDE     = u"/\s"
  ASCII_BEND      = u"b"
  ASCII_DEAD_NOTE = u"xd"
  ASCII_TREMOLO   = u"~vt"
  ASCII_TAB       = ASCII_STRING + ASCII_BAR + string_module.digits + ASCII_STRESSED + ASCII_HAMMER + ASCII_SLIDE + ASCII_BEND + ASCII_DEAD_NOTE + ASCII_TREMOLO
  
  TITRE_AUTHOR = re.compile(ur".*\(.*\)")
  COPYRIGHT    = re.compile(ur"(C|c)opy(right|left)\s*[0-9]{2,4}")
  TEMPO        = re.compile(ur"((?<=(T|t)empo(:|=)\s)|(?<=(T|t)empo(:|=))|(?<=(T|t)empo\s(:|=)\s)|(?<=(T|t)empo\s))([0-9]+)")
  
  _song = song.Song()
  lines = asciitab.split(u"\n")
  
  tempo = TEMPO.findall(asciitab)
  if tempo: tempo = tempo[0][-1]
  else:     tempo = 60
  
  i = 0
  header = u""
  song_comments_ended = 0
  if (not lines[i]) or (not lines[i][0] in ASCII_TAB): # First line is guessed to be the title.
    if TITRE_AUTHOR.match(lines[i]):
      start = lines[i].find(u"(")
      _song.title   = lines[i][: start]
      _song.authors = lines[i][start + 1 : lines[i].find(u")")]
    else: _song.title = lines[i]
    i = i + 1
    
  while 1:
    if   not lines[i]: song_comments_ended = 1
    elif not lines[i][0] in ASCII_TAB:
      if COPYRIGHT.search(lines[i]): _song.copyright = lines[i]
      else:
        if song_comments_ended:
          if header: header = header + u"\n" + lines[i]
          else:      header = lines[i]
        else:
          if _song.comments: _song.comments = _song.comments + u"\n" + lines[i]
          else:              _song.comments = lines[i]
    else: break
    i = i + 1
    
  # Compute rythm
  if lines[i][0] in ASCII_BAR: mesure_len = lines[i][1:].find(u"|")
  else:                        mesure_len = lines[i].find(u"|")
  
  if   mesure_len % 4 == 0: unit = float(mesure_len / 4) # Guess it is 4/4
  elif mesure_len % 3 == 0: unit = float(mesure_len / 3) # Guess it is 3/4
  
  pos              = []
  last_bar_pos     = 0
  current_note     = None
  next_note        = song.Note(0, 96, 0)
  partition        = song.Partition(_song)
  partition.header = header
  partition.setviewtype(tablature.guitar_view_type)
  _song.partitions.append(partition)
  _song.mesures *= 0
  
  while (i < len(lines)):
    stringid = 0
    
    while (i < len(lines)) and lines[i] and (lines[i][0] in ASCII_TAB):
      j = 0
      if stringid >= len(pos) - 1: pos.append(0)
      
      while j < len(lines[i]):
        char = lines[i][j]
        
        if char in ASCII_BAR:
          if (stringid == 0) and (partition is _song.partitions[0]):
            if j > 1:
              _song.addmesure(song.Mesure(int(round(last_bar_pos / unit * 96.0)),
                                          rythm1 = int(round((pos[stringid] - last_bar_pos) / unit)),
                                          tempo  = tempo))
            last_bar_pos = pos[stringid]
          j = j + 1
          continue
        
        elif char in string_module.digits:
          if (j + 1 < len(lines[i])) and (lines[i][j + 1] in string_module.digits):
            fret = int(char + lines[i][j + 1])
            pos[stringid] = pos[stringid] + 1
            j = j + 1
          else: fret = int(char)
          next_note.value    = partition.view.strings[stringid].basenote + fret
          next_note.time     = int(round((pos[stringid] - 1)/ unit * 96.0))
          next_note.stringid = stringid
          partition.notes.append(next_note)
          
          current_note = next_note
          next_note = song.Note(0, 96, 0)
          
          
          
        elif char in ASCII_STRESSED : next_note.volume = 255
        elif char in ASCII_TREMOLO  : current_note.__class__ = song.TremoloNote
        elif char in ASCII_DEAD_NOTE: current_note.__class__ = song.DeadNote
        elif char in ASCII_BEND     : current_note.__class__ = song.BendNote
        elif char in ASCII_HAMMER:
          current_note.link_to(next_note)
          current_note.__class__ = song.HammerNote
          current_note.init_effect()
        elif char in ASCII_SLIDE:
          current_note.link_to(next_note)
          current_note.__class__ = song.SlideNote
          current_note.init_effect()
        elif char in ASCII_STRING: pass
        else: print "* parse_asciitab * Unknown character %s at line %s, position %s ! Skipping." % (char, i, j)
          
        pos[stringid] = pos[stringid] + 1
        j = j + 1
        
      i = i + 1
      stringid = stringid + 1
      
    while (i < len(lines)) and (not lines[i]): i = i + 1
    
    if (i < len(lines)) and ((len(lines[i]) < 3) or (not lines[i][0] in ASCII_TAB) or (not lines[i][1] in ASCII_TAB)): break
    
    
  # Compute notes' durations
  partition.notes.sort()
  last_notes = []
  for note in partition.notes:
    if last_notes and (last_notes[0].time != note.time):
      for last_note in last_notes:
        last_note.duration = note.time - last_note.time
      last_notes = []
    last_notes.append(note)
    
  last_duration = _song.mesure_at(last_notes[0].time, 1).endtime() - last_notes[0].time
  for last_note in last_notes:
    last_note.duration = last_duration
    
  return _song


def asciitab(_song, cut_tab_at = 80):
  "asciitab(song) -> string -- Generates an ascii tablature from a song"
  min_duration = sys.maxint
  ternary      = 0
  partitions   = []
  
  for partition in _song.partitions:
    if hasattr(partition, "view") and (partition.view.__class__.__name__ == "Tablature"):
      partitions.append(partition)
      
      for note in partition.notes:
        dur = note.duration
        if note.is_triplet(): # Triplets are a hack...
          ternary = 1
          if note.duration == 32: dur = 48
          if note.duration == 16: dur = 24
          if note.duration ==  8: dur = 12
        else:
          rest = note.time % min_duration
          if rest > 0: min_duration = rest
          
        if dur < min_duration: min_duration = dur
        
  min_duration = float(min_duration)
  
  slotsize = 3
  duration = min_duration / slotsize
  
  alltabs = StringIO.StringIO()
  
  alltabs.write("%s (%s)\n" % (_song.title.encode("latin"), _song.authors.encode("latin")))
  if _song.copyright: alltabs.write(_song.copyright.encode("latin") + "\n\n")
  if _song.comments : alltabs.write(_song.comments .encode("latin") + "\n\n")
  
  for partition in _song.partitions:
    if   isinstance(partition, song.Lyrics2):
      alltabs.write(partition.header.encode("latin") + "\n")
      text = partition.text.encode("latin").replace("_", "").replace("-\t", "").replace("\t", " ").replace("\n", "").replace("\\\\", "\n").replace("  ", " ")
      alltabs.write("\n".join(map(string_module.strip, text.split("\n"))))
      alltabs.write("\n\n")
      
    elif isinstance(partition, song.Lyrics):
      alltabs.write(partition.header.encode("latin") + "\n")
      lyrics2text(partition, alltabs)
      alltabs.write("\n\n")
      
    elif partition.view.__class__.__name__ == "Tablature":
      alltabs.write(partition.header.encode("latin") + "\n")
      strings = partition.view.strings
      tabs    = [array.array("c", "-" * int(round(partition.endtime() / min_duration * slotsize))) for string in strings]
      
      def stringid(note):
        try: return note.stringid
        except (AttributeError, NameError, KeyError): return len(strings) - 1
      
      for note in partition.notes:
        sid  = stringid(note)
        time = int(round(note.time / min_duration * slotsize))
        text = str(note.value - strings[sid].basenote)
        
        if isinstance(note, song.LinkedNote):
          if note.linked_from:
            if   isinstance(note.linked_from, song.HammerNote):
              link_type = note.linked_from.link_type() # return "pull", "hammer" or "link"
              if link_type == "link": continue # Don't show linked note, since ascii tab doesn't matter note duration !
              else: tabs[sid][time] = link_type[0]
              
            elif isinstance(note.linked_from, song.SlideNote):
              if note.linked_from.value > note.value: tabs[sid][time] = "\\"
              else:                                   tabs[sid][time] = "/"
              
        if isinstance(note, song.SpecialEffect):
          if   isinstance(note, song.DeadNote   ): tabs[sid][time] = "x"
          elif isinstance(note, song.TremoloNote): tabs[sid][time] = "~"
          elif isinstance(note, song.BendNote   ): tabs[sid][time] = "b"
          
        if (note.volume > 220) and (tabs[sid][time] == "-"): tabs[sid][time] = "'" # Stressed note
        
        if len(text) == 1: tabs[sid][time + 1] = text
        else:
          tabs[sid][time + 1] = text[0]
          tabs[sid][time + 2] = text[1]
        
      tabs = map(lambda tab: tab.tostring(), tabs) # Turn arrays to strings.
      
      mesure = _song.mesures[0]
      i = 0
      while i < len(_song.mesures):
        mesures = []
        length = 1
        while i < len(_song.mesures):
          mesures.append(mesure)
          length = length + mesure.duration / min_duration * slotsize + 1
          
          i = i + 1
          if i >= len(_song.mesures): break
          mesure = _song.mesures[i]
          
          if length > cut_tab_at: break
          
        for tab in tabs:
          for mes in mesures:
            content = tab[int(round(mes.time / min_duration * slotsize)) : int(round(mes.endtime() / min_duration * slotsize))]
            if not content:
              i = sys.maxint
              break
            alltabs.write(u"|" + content)
          alltabs.write(u"|\n")
          
        alltabs.write(u"\n")
        
  return alltabs.getvalue()


# Where to add a break line
BREAK_LINE = re.compile(ur"(?<=,|\.)\s(?=[A-Z])")

def lyrics2text(lyrics, stringIO, line_sep = "\n"):
  lyrics_lines = map(lambda lyric: lyric.text.encode("latin").split("\n"), lyrics.lyrics)
  
  i = 0
  last_char = ""
  while 1:
    oldpos = stringIO.tell()
    for lines in lyrics_lines:
      if len(lines) > i:
        line = lines[i]
        if line:
          if last_char == "-":
            stringIO.seek(stringIO.tell() - 1)
          else:
            if line[0] in string_module.uppercase: stringIO.write(line_sep)
            else:                                  stringIO.write(" ") # Not a new verse
            
          line = BREAK_LINE.sub(line_sep, line)
          
          stringIO.write(line)
          last_char = line[-1]
          
    if oldpos == stringIO.tell(): break # Nothing has been written in this loop !
    i = i + 1
    

if __name__ == "__main__":
  import sys
  import cPickle as pickle
  
  if sys.argv[1].endswith("gtab"):
    _song = pickle.load(open(sys.argv[1]))
    
    print asciitab(_song)
    
  else:
    _song = parse(open(sys.argv[1]).read())
    
    import main, gtk
    main.App(edit_song = _song)
    
    gtk.mainloop()

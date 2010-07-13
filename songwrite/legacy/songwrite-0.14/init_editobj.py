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

import Tkinter
import editobj, editobj.editor as editor, editobj.custom as custom
import song, globdef, tablature, drum, staff, view, songbook

custom.TRANSLATOR = _

custom.register_children_attr("partitions",     clazz = song.Song)
custom.register_children_attr("playlist_items", clazz = song.Playlist)
custom.register_children_attr("songs", "on_add_song", "on_del_song", clazz = songbook.Songbook)

def edit_songref(songref, window):
  import main
  s = songref.get_song()
  main.App(edit_song = s)
  
custom.register_on_edit(edit_songref, songbook.SongRef)

def edit_song(song, window):
  if getattr(song, "app", None):
    if not window.hierarchyedited is song: song.app.tkraise()
  else:
    import main
    main.App(edit_song = song)
    
custom.register_on_edit(edit_song, song.Song)

def _partition_children(self):
  if self.view.__class__.__name__ in ("Tablature", "DrumView"): return self.view.strings
  return None

song.Partition.children = property(_partition_children)

def NewString(parent):
  if   isinstance(parent.view, tablature.Tablature): return tablature.String()
  elif isinstance(parent.view, drum.DrumView      ): return drum     .String()
  
custom.EVAL_ENV["song"]      = song
custom.EVAL_ENV["NewString"] = NewString
custom.register_available_children("NewString(parent)", song.Partition)

def NewPlaylistItem(parent):
  mesures = {}
  for partition in parent.song.partitions:
    for graphic_note in partition.view.selected_notes():
      mesure = parent.song.mesure_at(graphic_note.note.time)
      mesures[mesure] = 1
  mesures = map(lambda mesure: parent.song.mesures.index(mesure), mesures.keys())
  if mesures: return song.PlaylistItem(parent, min(mesures), max(mesures))
  else:       return song.PlaylistItem(parent, (parent.playlist_items and (parent.playlist_items[-1].to_mesure)) or 0, len(parent.song.mesures) - 1)
  
custom.EVAL_ENV["NewPlaylistItem"] = NewPlaylistItem
custom.register_available_children("NewPlaylistItem(parent)", song.Playlist)

def AddSong(songbook):
  import tkFileDialog
  filename = tkFileDialog.askopenfilename(filetypes = ((_("Songwrite files"), "*.sw.xml"),))
  if not filename: return
  if isinstance(filename, unicode): filename = filename.encode("latin")
  return filename
  
custom.EVAL_ENV["AddSong"] = AddSong
custom.register_available_children("AddSong(parent)", songbook.Songbook)
custom.register_method("preview_print", songbook.Songbook)

def preview_print(song):
  song.app.on_preview_print()

custom.register_method(preview_print, song.Song)

def redefine(p):
  parent = p.playlist
  mesures = {}
  for partition in parent.song.partitions:
    for graphic_note in partition.view.selected_notes():
      mesure = parent.song.mesure_at(graphic_note.note.time)
      mesures[mesure] = 1
  mesures = map(lambda mesure: parent.song.mesures.index(mesure), mesures.keys())
  if mesures:
    p.from_mesure = min(mesures)
    p.to_mesure   = max(mesures)
  else:
    p.from_mesure = (parent.playlist_items and (parent.playlist_items[-1].to_mesure)) or 0
    p.to_mesure   = len(parent.song.mesures) - 1
    
custom.register_method(redefine, song.PlaylistItem)

def on_edit_playlist_item(playlist_item, window):
  maxindex = len(playlist_item.playlist.song.mesures) - 1
  start = playlist_item.playlist.song.mesures[min(maxindex, playlist_item.from_mesure)].time
  end   = playlist_item.playlist.song.mesures[min(maxindex, playlist_item.to_mesure  )].endtime()
  for partition in playlist_item.playlist.song.partitions:
    if partition.view.__class__.__name__ != "HiddenView":
      partition.view.select_in_box(partition.view.time_to_x(start) - 1, 0, partition.view.time_to_x(end), 100000)
      
custom.register_on_edit(on_edit_playlist_item, song.PlaylistItem)


def NewPartition(parent):
  parent.app.partition_add_menu.tk_popup(*parent.app.winfo_pointerxy())
  raise NotImplementedError # Do not continue, do not return an object to add

custom.EVAL_ENV["NewPartition"] = NewPartition
custom.register_available_children("NewPartition(parent)", song.Song)

def _splitter(s):
  a, b = s.split(None, 1)
  return int(a), b

INSTRUMENTS = dict(map(_splitter, globdef.translator.gettext("__instru__").split("\n")))

Range_0_127 = editor.RangeEditor(0, 127)

class NoteValueEditor(editor.Editor, Tkinter.Frame):
  def __init__(self, master, obj, attr):
    editor.Editor.__init__(self, master, obj, attr)
    Tkinter.Frame.__init__(self, master)
    self.columnconfigure(0, weight = 0)
    self.columnconfigure(1, weight = 1)
    
    self.label = Tkinter.Label(self, width = 8)
    self.label.grid()
    
    self.scale = Tkinter.Scale(self, bigincrement = 12, command = self.update_label, orient = Tkinter.HORIZONTAL, from_ = 0, to = 90)
    self.scale.grid(row = 0, column = 1, sticky = "nsew")
    self.scale.bind("<ButtonRelease>", self.validate)
    self.update()
    
  def update_label(self, val):
    self.label.configure(text = song.note_label(int(val)))
    
  def validate(self, event): self.set_value(self.scale.get())
  
  def get_value(self): return int(getattr(self.obj, self.attr, 0))
  
  def update(self):
    try: val = getattr(self.obj, self.attr)
    except AttributeError: return 0 # Not readable => do not update !
    self.scale.set(val)
    self.label.configure(text = song.note_label(val))
    return 1
  
class DrumPatchEditor(editor.Editor, Tkinter.Frame):
  def __init__(self, master, obj, attr):
    editor.Editor.__init__(self, master, obj, attr)
    Tkinter.Frame.__init__(self, master)
    self.columnconfigure(0, weight = 0)
    self.columnconfigure(1, weight = 1)
    
    self.scale = Tkinter.Scale(self, bigincrement = 12, command = self.update_label, orient = Tkinter.HORIZONTAL, from_ = 35, to = 81)
    self.scale.grid(row = 0, column = 1, sticky = "nsew")
    self.scale.bind("<ButtonRelease>", self.validate)
    self.update()
    
  def update_label(self, val):
    self.scale.configure(label = drum.PATCHES[int(val) - 35])
    
  def validate(self, event): self.set_value(self.scale.get())
  
  def get_value(self): return int(getattr(self.obj, self.attr, 0))
  
  def update(self):
    try: val = getattr(self.obj, self.attr)
    except AttributeError: return 0 # Not readable => do not update !
    self.scale.set(val)
    self.scale.configure(label = drum.PATCHES[val - 35])
    return 1
  
class DurationEditor(editor.Editor, Tkinter.Frame):
  def __init__(self, master, obj, attr):
    editor.Editor.__init__(self, master, obj, attr)
    Tkinter.Frame.__init__(self, master)
    self.columnconfigure(0, weight = 1)
    self.columnconfigure(1, weight = 1)
    
    self.scale = Tkinter.Scale(self, bigincrement = 12, orient = Tkinter.HORIZONTAL, from_ = 1, to = 6)
    self.scale.bind("<ButtonRelease>", self.validate)
    self.scale.grid(row = 0, column = 0, columnspan = 2, sticky = "nsew")
    
    self.doted = Tkinter.BooleanVar()
    Tkinter.Checkbutton(self, text = _("Doted"), variable = self.doted, command = self.validate).grid(row = 1, column = 0)
    
    self.triplet = Tkinter.BooleanVar()
    Tkinter.Checkbutton(self, text = _("Triplet"), variable = self.triplet, command = self.validate).grid(row = 1, column = 1)
    
    self.update()
    
  def validate(self, event = None):
    val = 6 * 2 ** self.scale.get()
    if   self.doted  .get(): val = int(val * 1.5)
    elif self.triplet.get(): val = int(val / 1.5)
    self.set_value(val)
    self.scale.configure(label = song.duration_label(val))
    
  def get_value(self): return int(getattr(self.obj, self.attr, 0))
  
  def update(self):
    try: val = getattr(self.obj, self.attr)
    except AttributeError: return 0 # Not readable => do not update !
    
    self.scale.configure(label = song.duration_label(val))
    
    if val in (9, 18, 36, 72, 144, 288, 576):
      val = int(val / 1.5)
      self.doted.set(1)
    else:
      self.doted.set(0)
      
    if val in (4,  8, 16, 32,  64, 128, 256):
      val = int(val * 1.5)
      self.triplet.set(1)
    else:
      self.triplet.set(0)
      
    self.scale.set({ 0: 0, 6 : 0, 12 : 1, 24: 2, 48 : 3, 96 : 4, 192 : 5, 384 : 6 }[val])
    return 1

custom.register_attr("filename"           , None)
custom.register_attr("title"              , None, songbook.SongRef)
custom.register_attr("songs"              , None)
custom.register_attr("songbook"           , None)
custom.register_attr("children"           , None)
custom.register_attr("playlist_items"     , None)
custom.register_attr("playlist"           , editor.EditButtonEditor)
custom.register_attr("playlist"           , None, song.PlaylistItem)
custom.register_attr("view"               , editor.ListEditor(view.view_types), song.Partition)
custom.register_attr("view"               , None, song.Lyrics2)
custom.register_attr("partitions"         , None)
custom.register_attr("mesures"            , None)
custom.register_attr("version"            , None)
custom.register_attr("title"              , editor.StringEditor)
custom.register_attr("authors"            , editor.StringEditor)
custom.register_attr("copyright"          , editor.StringEditor)
custom.register_attr("comments"           , editor.TextEditor)
custom.register_attr("lang"               , editor.ListEditor((u"fr", u"en", u"de", u"es", u"it", u"pt", u"sw")))

custom.register_attr("symbols"            , None, song.Playlist)

custom.register_attr("song"                , None)
custom.register_attr("app"                 , None)
custom.register_attr("notes"               , None)
custom.register_attr("lyrics"              , None)
custom.register_attr("oldview"             , None)
custom.register_attr("header"              , editor.TextEditor)
custom.register_attr("chorus"              , Range_0_127)
custom.register_attr("reverb"              , Range_0_127)
custom.register_attr("muted"               , editor.BoolEditor)
custom.register_attr("volume"              , editor.RangeEditor(0, 255))
custom.register_attr("instrument"          , editor.EnumEditor(INSTRUMENTS))
custom.register_attr("capo"                , editor.IntEditor)
custom.register_attr("print_with_staff_too", editor.BoolEditor)

custom.register_attr("time"               , None)
custom.register_attr("mesure"             , None)
custom.register_attr("stringid"           , None)
custom.register_attr("linked_to"          , None)
custom.register_attr("linked_from"        , None)
custom.register_attr("stringid"           , None)
custom.register_attr("duration"           , DurationEditor)
custom.register_attr("value"              , NoteValueEditor)
custom.register_attr("text"               , None, song.Lyrics2)
custom.register_attr("pitch"              , editor.FloatEditor)
custom.register_attr("special_effect_name", editor.EnumEditor({
  song.Note.__name__        : _("Normal"),
  song.HammerNote.__name__  : _("Hammer / pull / legato"),
  song.BendNote.__name__    : _("Bend"),
  song.SlideNote.__name__   : _("Slide"),
  song.TremoloNote.__name__ : _("Tremolo"),
  song.DeadNote.__name__    : _("Dead note"),
  song.RollNote.__name__    : _("Roll"),
  }))

custom.register_attr("lines"              , None)
custom.register_attr("y"                  , None)
custom.register_attr("notationpos"        , editor.EnumEditor({ 0 : _("Upper"), 1 : _("Lower") }))
custom.register_attr("basenote"           , NoteValueEditor)
custom.register_attr("basenote"           , DrumPatchEditor, drum.String)

custom.register_attr("syncope"            , editor.BoolEditor)
custom.register_attr("tempo"              , editor.IntEditor)
custom.register_attr("rythm1"             , editor.IntEditor)
custom.register_attr("rythm2"             , editor.IntEditor)
custom.register_attr("duration"           , None, song.Mesure)

custom.register_attr("tonality"           , editor.EnumEditor(dict(map(lambda tonality: (tonality, _("note_%s" % staff.OFFSETS[tonality])), staff.TONALITIES.keys()))))

custom.register_attr("from_mesure"        , editor.IntEditor)
custom.register_attr("to_mesure"          , editor.IntEditor)

custom.register_attr("MIDI_COMMAND"       , editor.StringEditor)
custom.register_attr("MIDI_USE_TEMP_FILE" , None)
custom.register_attr("PREVIEW_COMMAND"    , editor.StringEditor)
custom.register_attr("PRINT_COMMAND"      , None) # No longer used
custom.register_attr("PAGE_FORMAT"        , editor.EnumEditor({ "a3paper" : _("A3"), "a4paper" : _("A4"), "a5paper" : _("A5"), "letterpaper" : _("letter") }))
custom.register_attr("PLAY_LOOP"          , editor.BoolEditor)
custom.register_attr("DISPLAY_PLAY_BAR"   , editor.BoolEditor)
custom.register_attr("PREVIOUS_FILES"     , None)
custom.register_attr("NUMBER_OF_CANCEL"   , editor.RangeEditor(0, 100))

def edit(obj, **kargs): editobj.edit(obj, show_right_menu = 0, dialog = 1, **kargs)


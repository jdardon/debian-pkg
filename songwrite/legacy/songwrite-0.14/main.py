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

import sys, time, getpass, copy, string, os, os.path, thread
import globdef, song, player, ui
import editobj.cancel as cancel, editobj.treewidget as treewidget
from editobj.observe import *

icons = treewidget.IconsDir(globdef.DATADIR)

NO_MODE             = 0
SELECTION_MODE      = 1
DRAGGING_NOTES_MODE = 2

# The clipboard / selection
selection        = []
selection_cloned = 0 # 1 if the selection has already be cloned

nb_apps = 0

from Tkinter import *

# Create, if needed, the root Tk.
try:
  from Tkinter import tkroot
except ImportError:
  tkroot = Tk(baseName = "songwrite", className = "Songwrite")
  import Tkinter
  Tkinter.tkroot = tkroot
  tkroot.withdraw()
  
# Better Tk look
tkroot.option_add("*Entry.relief"      , "flat")
tkroot.option_add("*Entry.background"  , "#FFFFFF")
tkroot.option_add("*Text.relief"       , "flat")
tkroot.option_add("*Text.background"   , "#FFFFFF")
tkroot.option_add("*Listbox.relief"    , "flat")
tkroot.option_add("*Listbox.background", "#FFFFFF")

#def set_window_icon(window):
#  t = Tkinter.Toplevel()
#  Tkinter.Label(t, image = icons["songwrite_64x64.gif"]).pack()
#  window.iconwindow(t)

def edit_songbook(songbook):
  global nb_apps
  nb_apps = nb_apps + 1

  def on_ok():
    songbook.save()
    global nb_apps
    if nb_apps == 1:
      globdef.config.save()
      sys.exit()
    else:
      nb_apps = nb_apps - 1

  import init_editobj
  init_editobj.edit(songbook, command = on_ok)

class App(Toplevel):
  def __init__(self, filename = None, edit_song = None):
    global nb_apps
    nb_apps = nb_apps + 1
    
    from Tkinter import tkroot
    
    menubar = Menu(tkroot)
    file_menu = Menu(menubar)
    file_menu.add_command(label = _("New")            , command = self.on_new)
    file_menu.add_command(label = _("New window...")  , command = self.on_new_app)
    file_menu.add_command(label = _("New songbook..."), command = self.on_new_songbook)
    file_menu.add_command(label = _("Open...")        , command = self.on_open)
    file_menu.add_command(label = _("Save")           , command = self.on_save, accelerator = "C-s")
    file_menu.add_command(label = _("Save as...")     , command = self.on_save_as)
    file_menu.add_separator()
    
    import_menu = Menu(menubar)
    import_menu.add_command(label = _("Midi...")           , command = self.on_import_midi)
    import_menu.add_command(label = _("Ascii tablature..."), command = self.on_import_ascii)
    import_menu.add_command(label = _("Guitar pro 3-4...") , command = self.on_import_gp)
    file_menu.add_cascade  (label = _("Import"), menu = import_menu)
    
    export_menu = Menu(menubar)
    export_menu.add_command(label = _("Midi...")                , command = self.on_export_midi)
    export_menu.add_command(label = _("Rich tablature Midi...") , command = self.on_export_rich_tablature_midi)
    export_menu.add_command(label = _("Ascii tablature...")     , command = self.on_export_ascii)
    export_menu.add_command(label = _("Lilypond (no lyrics)..."), command = self.on_export_lily)
    export_menu.add_command(label = _("LaTeX+Lilypond...")      , command = self.on_export_latex)
    export_menu.add_command(label = _("Postscipt...")           , command = self.on_export_ps)
#    export_menu.add_command(label = _("AbcTab...")              , command = self.on_export_abctab)
    file_menu.add_cascade  (label = _("Export"), menu = export_menu)
    
    file_menu.add_command(label = _("preview_print")     , command = self.on_preview_print)
    file_menu.add_separator()
    file_menu.add_command(label = _("Exit")              , command = self.on_close, accelerator = "q")
    
    file_menu.add_separator()
    for file in globdef.config.PREVIOUS_FILES:
      def on_open_recent(file = file):
        if self.check_save(): return
        self.open_filename(file)
        
      file_menu.add_command(label = file, command = on_open_recent)
    menubar.add_cascade  (label = _("File"), menu = file_menu)
    
    edit_menu = Menu(menubar)
    edit_menu.add_command(label = _("Cancel"), command = self.on_cancel, accelerator = "C-_ / C-z")
    edit_menu.add_command(label = _("Redo")  , command = self.on_redo  , accelerator = "C-r")
    edit_menu.add_separator()
    edit_menu.add_command(label = _("Insert/remove times...")     , command = self.on_insert_times)
    edit_menu.add_command(label = _("Insert/remove bars...")      , command = self.on_insert_mesures)
    edit_menu.add_separator()
    edit_menu.add_command(label = _("Preferences..."), command = self.on_preferences)
    menubar.add_cascade  (label = _("Edit"), menu = edit_menu)
    
    song_menu = Menu(menubar)
    song_menu.add_command(label = _("Play")          , command = self.on_play)
    song_menu.add_command(label = _("Play from here"), command = self.on_play_from_here, accelerator = _("Space"))
    song_menu.add_command(label = _("Play in loop")  , command = self.on_play_in_loop)
    song_menu.add_command(label = _("Stop playing")  , command = self.on_stop_playing)
    song_menu.add_separator()
    song_menu.add_command(label = _("Rhythm...")     , command = self.on_rythm_prop)
    song_menu.add_command(label = _("Repeat...")     , command = self.on_repeat)
    song_menu.add_command(label = _("Properties...") , command = self.on_song_prop)
    menubar.add_cascade  (label = _("Song"), menu = song_menu)
    
    partition_menu     = Menu(menubar)
    self.partition_add_menu = Menu(menubar)
    
    import view, tablature, drum, staff
    view.view_types.sort(lambda a, b: cmp(a.group, b.group))
    prev_group = ""
    for view_type in view.view_types:
      if not view_type.group: continue
      if view_type.group != prev_group:
        prev_group = view_type.group
        cur_menu   = Menu(menubar)
        partition_menu.add_cascade(label = _("New " + prev_group), menu = cur_menu)
        
      def on_click(view_type = view_type):
        partition = song.Partition(self.song)
        partition.instrument = view_type.instrument
        partition.setviewtype(view_type)
        partition.header = view_type.name
        self.add_partition(partition)
        self.ensure_visible_y(100000)
        
      cur_menu.add_command(label = view_type.name, command = on_click)
      self.partition_add_menu.add_command(label = view_type.name, command = on_click)
      
    self.partition_add_menu.add_separator()
    self.partition_add_menu.add_command(label = _("New lyrics"), command = self.on_new_lyrics2)
    partition_menu.add_command(label = _("New lyrics"), command = self.on_new_lyrics2)
    
    partition_menu.add_separator()
    partition_menu.add_command(label = _("Move up")      , command = self.on_partition_moveup)
    partition_menu.add_command(label = _("Move down")    , command = self.on_partition_movedown)
    partition_menu.add_command(label = _("Delete")       , command = self.on_partition_delete)
    partition_menu.add_command(label = _("Properties..."), command = self.on_partition_prop)
    menubar.add_cascade  (label = _("Partition"), menu = partition_menu)
    
    note_menu = Menu(menubar)
    note_menu.add_command(label = _("Paste")             , command = self.on_note_paste, accelerator = _("Middle click"))
    note_menu.add_command(label = _("Arrange at fret..."), command = self.on_note_arrange)
    note_menu.add_command(label = _("Properties...")     , command = self.on_note_prop)
    menubar.add_cascade  (label = _("Note"), menu = note_menu)
    
    help_menu = Menu(menubar)
    help_menu.add_command(label = _("About...")         , command = self.on_about)
    help_menu.add_command(label = _("Manual...")        , command = self.on_manual)
    help_menu.add_separator()
    help_menu.add_command(label = _("Dump")             , command = self.on_dump)
    help_menu.add_command(label = _("Dump clipboard")   , command = self.on_dump_clipboard)
    help_menu.add_command(label = _("GC")               , command = self.on_gc)
    help_menu.add_command(label = _("Python console..."), command = self.on_console)
    menubar.add_cascade  (label = _("Help"), menu = help_menu)
    
    Toplevel.__init__(self, tkroot, menu = menubar, class_ = "Songwrite")
    
    self.doted_duration = self.triplet_duration = 0
    self.default_note   = song.Note(96, 96, 0)
    self.mode           = NO_MODE
    self.selection_box  = self.drag_box = self.last_cancelable = None
    self.old_x1         = 0.0
    
    self.columnconfigure(0, weight = 1)
    self.rowconfigure(0, weight = 0)
    self.rowconfigure(1, weight = 1)
    
    toolbar = Frame(self, borderwidth = 2, relief = "raised")
    toolbar.grid(sticky = "nsew")
    col = 0
    self.duration = IntVar()
    self.duration_buttons = []
    durs = song.DURATIONS.items()
    durs.sort()
    durs.reverse()
    for duration, duration_label in durs:
      button = Button(toolbar, text = _(duration_label), padx = 5, relief = "flat")#, image = icons["round.pgm"])
      button.grid(row = 0, column = col, sticky = "nsew")
      button.duration = duration
      button["command"] = lambda button = button: self.on_note_duration(button)
      
      self.duration_buttons.append(button)
      col = col + 1
    self.base_duration       = 96
    self.old_duration_button = self.duration_buttons[2]
    self.old_duration_button["relief"] = "sunken"
    
    self.doted_button = Button(toolbar, command = self.on_note_doted, padx = 5, text = _("Doted"), relief = "flat")
    self.doted_button.grid(row = 0, column = col, sticky = "nsew"); col = col + 1
    
    self.triplet_button = Button(toolbar, command = self.on_note_triplet, padx = 5, text = _("Triplet"), relief = "flat")
    self.triplet_button.grid(row = 0, column = col, sticky = "nsew"); col = col + 1
    
    self.stressed_button = Button(toolbar, command = self.on_note_stressed, padx = 5, text = _("Stressed"), relief = "flat")
    self.stressed_button.grid(row = 0, column = col, sticky = "nsew"); col = col + 1
    
    Label(toolbar, text = _("Zoom")).grid(row = 0, column = col + 3, sticky = "nsew")
    Button(toolbar, text = "-", padx = 5, relief = "flat", command = lambda : self.incr_zoom(-1)).grid(row = 0, column = col + 2)
    Button(toolbar, text = "+", padx = 5, relief = "flat", command = lambda : self.incr_zoom( 1)).grid(row = 0, column = col + 4)
    
    toolbar.columnconfigure(col + 1, weight = 1)
    
    frame = Frame(self)
    frame.grid(sticky = "nsew")
    frame.rowconfigure   (0, weight = 1)
    frame.columnconfigure(0, weight = 1)
    self.canvas = Canvas(frame, bg = "white", highlightthickness = 0, height = 260)
    self.canvas.grid(sticky = "nsew")
    self.canvas.bind("<ButtonPress-1>"     , self.on_button_press1)
    self.canvas.bind("<ButtonPress-2>"     , self.on_button_press2)
    self.canvas.bind("<ButtonPress-3>"     , self.on_button_press3)
    self.canvas.bind("<ButtonRelease-1>"   , self.on_button_release1)
    self.canvas.bind("<ButtonRelease-2>"   , self.on_button_release2)
    self.canvas.bind("<ButtonRelease-3>"   , self.on_button_release3)
    self.canvas.bind("<Double-1>"          , self.on_note_prop)
    self.canvas.bind("<Motion>"            , self.on_motion)
    self.canvas.bind("<KeyPress>"          , self.on_key_press)
    self.canvas.bind("<Return>"            , self.on_note_stressed)
    self.canvas.bind("<KP_Enter>"          , self.on_note_stressed)
    self.canvas.bind("<space>"             , self.on_space)
    self.canvas.bind("<Control-s>"         , self.on_save)
    self.canvas.bind("<Control-underscore>", self.on_cancel)
    self.canvas.bind("<Control-z>"         , self.on_cancel)
    self.canvas.bind("<Control-r>"         , self.on_redo)
    self.canvas.bind("<q>"                 , self.on_close)
    
    self.canvas.focus_set()
    
    self.vbar   = Scrollbar(frame, takefocus = 0, orient = VERTICAL)
    self.hbar   = Scrollbar(frame, takefocus = 0, orient = HORIZONTAL)
    
    self.vbar.grid(row = 0, column = 1, sticky = "nsew")
    self.hbar.grid(row = 1, column = 0, sticky = "nsew")
    self.vbar['command'] = self.canvas.yview
    self.hbar['command'] = self.canvas_xview
    self.canvas['yscrollcommand'] = self.vbar.set
    self.canvas['xscrollcommand'] = self.hbar.set
    
    self.bar = ui.LinksBar(self.canvas, 0, 0, ((_("Play")              , self.on_play),
                                               (_("Save")              , self.on_save),
                                               (_("preview_print"), self.on_preview_print),
                                               (_("Properties")        , self.on_song_prop),
                                               ), tag = "noscroll",
                           )
    
    self.partition_focus = self.canvas.create_rectangle(10, 10, 100, 100, outline = "#AAAADD", fill = "#FFF8FF", width = 2)
    
    self.cancel      = cancel.Context()
    self.canvas.draw = self.draw # HACK
    self.canvas.app  = self
    self.zoom        = 0.66667
    self.width       = self.height = 0
    self.bind("<Expose>"  , self.on_expose)
    self.wm_protocol("WM_DELETE_WINDOW", self.on_close)
    self.wm_command("songwrite")
    
    self.song = None
    
    if filename: self.open_filename(filename)
    elif edit_song: self.set_song(edit_song)
    else: self.on_new()
    
    #set_window_icon(self)
    
  def on_new_songbook(self):
    filename = self.prompt_filename(defaultextension = ".sw.xml", filetypes = ((_("XML files"), "*.sw.xml"),))
    if not filename: return
    globdef.config.add_previous_file(filename)
    
    import songbook
    songbook = songbook.Songbook(filename)
    songbook.authors = unicode(getpass.getuser().title(), "latin")
    songbook.title   = _("%s's songbook") % songbook.authors
    songbook.save()
    edit_songbook(songbook)
    
  def on_repeat(self):
    import init_editobj
    init_editobj.edit(self.song.playlist, cancel = self.cancel)
    
    
  def play_bar_idle(self, from_time, info):
    if not info: return
    start   = time.time()
    bar     = self.canvas.create_rectangle(0, self.y, 0, self.height, outline = "#AAAADD", width = 2)
    next2, next = info.pop(0)
    first   = next
    playing = 0
    while 1:
      current = time.time() - start
      if current >= self.time_to_second(next - first):
        x = self.time_to_x(from_time + next2)
        self.canvas.coords(bar, x - 10, self.y, x + 10, self.height)
        self.ensure_visible_x(x)
        if not info:
          time.sleep(0.5)
          break
        next2, next = info.pop(0)
        
      else: time.sleep(0.05)
      
      if not player.is_playing(): # May not have started yet
        if playing: break
      else: playing = 1
      
    self.canvas.delete(bar)
    
  def on_expose(self, event):
    width = self.canvas.winfo_width()
    if width != self.width:
      self.width = width
      self.set_scroll_region()
      self.ensure_drawn()
      
  def canvas_xview(self, *args):
    self.canvas.xview(*args)
    x1 = self.canvas.canvasx(0)
    self.canvas.move("noscroll", x1 - self.old_x1, 0)
    self.old_x1 = x1
    self.ensure_drawn()
    
  def ensure_drawn(self, time1 = None, time2 = None):
    if time1 is None:
      time1 = int(self.x_to_time(self.old_x1))
      time2 = int(self.x_to_time(self.old_x1 + self.width))
      
    #print "ensure_drawn", time1, time2
    
    for partition in self.song.partitions:
      if hasattr(partition.view, "ensure_drawn"):
        partition.view.ensure_drawn(time1, time2)
        
  def set_scroll_region(self):
    self.max_x = self.time_to_x_vec(self.song.mesures[-1].endtime() + self.song.mesures[-1].duration)
    self.canvas.configure(scrollregion = (0, 0, self.max_x, self.height))
    self.set_partition(self.partition, 1)
    
  def ensure_visible_x(self, x):
    offx = self.canvas.canvasx(0)
    if x - 30 < offx:
      self.canvas_xview("moveto", max(x - 35, 0) / self.max_x)
    else:
      w = int(self.canvas.winfo_width())
      if x + 60 > offx + w: self.canvas_xview("moveto", (x + 65 - w) / self.max_x)
      
  def ensure_visible_y(self, y):
    offy = self.canvas.canvasy(0)
    if y - 30 < offy:
      self.canvas.yview_moveto(max(y - 35, 0) / self.canvas.bbox(ALL)[3])
    else:
      h = self.canvas.winfo_height()
      if y + 30 > offy + h: self.canvas.yview_moveto((y + 35 - h) / self.height)
      
  def on_new_app(self): App()
  def on_close(self, event = None):
    if self.check_save(): return
    
    unobserve_tree(self.song,          self.on_song_changed)
    unobserve_tree(self.song.playlist, self.on_playlist_changed)
    
    # Turn the song to a ref song
    import songbook
    self.song.__class__ = songbook.SongRef
    self.song.__dict__ = { "title" : self.song.title, "filename" : self.song.filename, "songbook" : getattr(self.song, "songbook", None) }
    
    global nb_apps
    if nb_apps == 1:
      globdef.config.save()
      sys.exit()
    else:
      nb_apps = nb_apps - 1
      self.destroy()
      
  def set_song(self, song_):
    if self.song:
      self.canvas_xview("moveto", 0.0)
      self.canvas.yview("moveto", 0.0)
      
      for partition in self.song.partitions: partition.view.destroy()
      unobserve_tree(self.song,          self.on_song_changed)
      unobserve_tree(self.song.playlist, self.on_playlist_changed)
      
    self.song = song_
    self.song.app = self
    scan() # Hack for speedup : avoid that "song.app = ..." cause a redraw.
    
    self.filename = song_.filename
    
    if song_.partitions:
      self.partition = song_.partitions[0]
      for partition in song_.partitions:
        if not hasattr(partition, "view"):
          if isinstance(partition, song.Lyrics2):
            import lyric2
            partition.setviewtype(lyric2.lyric_view_type)
          else:
            import tablature
            partition.setviewtype(tablature.guitar_view_type)
            
    else: self.partition = None
    self.show_info()
    self.draw()
    
    import init_editobj
    observe_tree(song_,          self.on_song_changed)
    observe_tree(song_.playlist, self.on_playlist_changed)
    
  def on_playlist_changed(self, obj, type, new, old):
    self.song.playlist.analyse()
    self.rythm_changed()
    
  def on_song_changed(self, obj, type, new, old):
    if (type is object) and (obj is self.song):
      print "song changed !", diffdict(new, old)
      self.show_info()
      self.draw()
      
    elif (type is list) and (obj is self.song.partitions):
      for partition in old:
        if not partition in new: partition.view.destroy()
      self.draw()
      
    elif isinstance(obj, song.TemporalData):
      #print (u"partition %s changed !" % unicode(obj)).encode("latin")
      self.draw()
      
    elif type is list:
      for partition in self.song.partitions:
        if hasattr(partition.view, "strings") and (obj is partition.view.strings):
          partition.view.destroy()
          self.draw()
          
    elif (type is object) and (obj.__class__.__name__ == "String") and ((new["basenote"] != old["basenote"]) or (new["notationpos"] != old["notationpos"])):
      for partition in self.song.partitions:
        if hasattr(partition.view, "strings") and (obj in partition.view.strings):
          partition.view.destroy()
          self.draw()
          
  def show_info(self):
    "Shows the title, the authors and the comments."
    self.wm_title((u"Songwrite -- " + self.song.title).encode("latin"))
    
    self.canvas.delete("info")
    title = self.canvas.create_text(10,  5, text = (self.song.title + u" (" + self.song.authors + u")").encode("latin"), font = "helvetica 20", anchor = "nw", tag = ("info", "noscroll"))
    self.canvas.create_text(13, 35, text = self.song.comments, anchor = "nw", tag = ("info", "noscroll"))
    
    self.bar.coords(self.canvas.bbox(title)[2] + 10, 23)
    
    x1, y1, x2, y2 = self.canvas.bbox("info")
    self.y = 20 + y2 - y1
    
  def set_partition(self, partition, force = 0):
    if force or (not self.partition is partition):
      self.partition = partition
      if partition:
        self.canvas.coords(self.partition_focus, 8, partition.view.y1, max(self.max_x - 2, self.canvas.winfo_width() + 2), partition.view.y2)
        
  def on_cancel(self, event = None):
    if not self.cancel.cancel(): self.bell()
  def on_redo  (self, event = None):
    if not self.cancel.redo(): self.bell()
    
  def on_new(self):
    if self.song and self.check_save(): return # Else, it is the fisrt time.
    
    s = song.Song()
    s.authors   = unicode(getpass.getuser().title(), "latin")
    s.title     = _("%s's song") % s.authors
    s.copyright = u"Copyright %s by %s" % (time.localtime(time.time())[0], s.authors)
    
    s.partitions.append(song.Partition(s))
    import tablature
    s.partitions[0].setviewtype(tablature.guitar_view_type)
    s.partitions[0].header = tablature.guitar_view_type.name
    
    self.set_song(s)
    self.filename = None
    self.last_cancelable = self.cancel.get_last_cancelable()
    
  def on_open(self):
    if self.check_save(): return
    
    import tkFileDialog
    filename = tkFileDialog.askopenfilename(filetypes = ((_("Songwrite files"), "*.sw.xml *.sw *.gtab"),))
    if not filename: return
    if isinstance(filename, unicode): filename = filename.encode("latin")
    self.open_filename(filename)
    
  def open_filename(self, filename):
    self.filename = filename
    if filename.endswith(".xml"):
      import stemml
      _song = stemml.parse(filename)
      if isinstance(_song, song.Song): self.set_song(_song)
      else:                            edit_songbook(_song)
    else:
      import cPickle as pickle
      self.set_song(pickle.load(open(filename)))
    globdef.config.add_previous_file(filename)
    
  def on_save_as(self, event = None):
    filename = self.prompt_filename(defaultextension = ".sw.xml", filetypes = ((_("XML files"), "*.sw.xml"),))
    if not filename: return
    if not filename.endswith(".sw.xml"): filename += ".sw.xml"
    globdef.config.add_previous_file(filename)
    self.filename = self.song.filename = filename
    self.on_save()
    
  def prompt_filename(self, **opts):
    import tkFileDialog
    filename = tkFileDialog.asksaveasfilename(**opts)
    if not filename: return
    if isinstance(filename, unicode): filename = filename.encode("latin")
    return filename
  
  def on_save(self, event = None):
    if not self.filename: return self.on_save_as()
    globdef.config.add_previous_file(self.filename)
    
    import codecs
    self.song.__xml__(codecs.lookup("utf8")[3](open(self.filename, "w"))) #.getvalue()
    
    self.last_cancelable = self.cancel.get_last_cancelable()
    
  def check_save(self):
    last_cancelable = self.cancel.get_last_cancelable()
    if last_cancelable and (not self.last_cancelable is last_cancelable):
      # The last cancelable action has changed => the song need to save.
      import tkMessageBox
      x = tkMessageBox._show(_("Confirmation"), _("The current song has been changed. Continue ?"), tkMessageBox.QUESTION, tkMessageBox.YESNO)
      if (x != "yes") and (not x is True):
      #if not tkMessageBox.askyesno(_("Confirmation"), _("The current song has been changed. Continue ?")):
        return 1
      
    self.cancel = cancel.Context()
    return 0
  
  def on_import_midi(self):
    if self.check_save(): return
    
    import midi_import, tablature, tkFileDialog
    
    filename = tkFileDialog.askopenfilename()
    if not filename: return
    if isinstance(filename, unicode): filename = filename.encode("latin")
    
    self.filename = filename
    _song = midi_import.parse(open(filename))
    
    for partition in _song.partitions:
      if not hasattr(partition, "view"):
        partition.setviewtype(tablature.guitar_view_type)
        
    self.set_song(_song)
    
  def on_import_ascii(self):
    if self.check_save(): return
    
    import asciitab, tkFileDialog
    
    filename = tkFileDialog.askopenfilename()
    if not filename: return
    if isinstance(filename, unicode): filename = filename.encode("latin")
    self.filename = filename
    self.set_song(asciitab.parse(open(filename).read()))
    
  def on_import_gp(self):
    if self.check_save(): return
    
    import gp3_loader, tkFileDialog
    
    filename = tkFileDialog.askopenfilename()
    if not filename: return
    if isinstance(filename, unicode): filename = filename.encode("latin")
    self.filename = filename
    self.set_song(gp3_loader.load_guitar_pro(filename))
    
  def on_export_midi(self):
    filename = self.prompt_filename()
    if not filename: return
    open(filename, "w").write(self.song.midi()[0])
    
  def on_export_rich_tablature_midi(self):
    filename = self.prompt_filename()
    if not filename: return
    open(filename, "w").write(self.song.midi(rich_midi_tablature = 1)[0])
    
  def on_export_ascii(self):
    import asciitab
    
    filename = self.prompt_filename()
    if not filename: return
    open(filename, "w").write(asciitab.asciitab(self.song))
    
  def on_export_lily(self):
    import lilypond
    
    filename = self.prompt_filename()
    if not filename: return
    try: open(filename, "w").write(lilypond.lilypond(self.song))
    except: self._treat_lily_error()
    
  def _treat_lily_error(self):
    error_class, error, trace = sys.exc_info()
    sys.excepthook(error_class, error, trace)
    print
    
    import tkMessageBox
    if isinstance(error, song.SongwriteError):
      tkMessageBox.showerror(_(error.__class__.__name__), unicode(error))
      if isinstance(error, song.TimeError):
        if   error.note: error.partition.view.select_at(error.note.time, getattr(error.note, "stringid", 0))
        elif error.partition and error.time: error.partition.view.select_at(error.time)
        elif error.time and self.partition: self.partition.view.select_at(error.time)
    else:
      tkMessageBox.showerror(_(error.__class__.__name__), _("__UnknownError__"))
        
  def on_export_latex(self):
    import latex
    
    filename = self.prompt_filename()
    if not filename: return
    try: open(filename, "w").write(latex.latexify(self.song))
    except: self._treat_lily_error()
    
  def on_export_ps(self):
    import latex
    
    filename = self.prompt_filename()
    if not filename: return
    try: latex.export2ps(self.song, filename)
    except: self._treat_lily_error()
    
#   def on_export_abctab(self):
#     import abctab
#     reload(abctab)
    
#     print abctab.abctab(self.song)
    
  def on_preview_print(self, event = None):
    import latex
    
    try: latex.preview(self.song, globdef.config.PREVIEW_COMMAND)
    except: self._treat_lily_error()
    
  def on_about(self):
    t = Toplevel()
    text = Text(t, wrap = "word", width = 50, height = 18, highlightthickness = 0, font = "Helvetica -12", selectbackground = "#CCCCFF")
    text.insert("end", _("__about__") % song.VERSION)
    text.pack(expand = 1, fill = BOTH)

    ok = Button(t, text = "OK", command = lambda : t.destroy())
    ok.pack(fill = X)
  
  def on_manual(self):
    import webbrowser, locale
    
    DOCDIR = os.path.join(globdef.APPDIR, "doc")
    if not os.path.exists(DOCDIR):
      import glob
      
      DOCDIR = glob.glob(os.path.join(globdef.APPDIR, "..", "doc", "Songwrite*"))[0]
      
    DOC = os.path.join(DOCDIR, locale.getdefaultlocale()[0][:2], "doc.html")
    if not os.path.exists(DOC):
      DOC = os.path.join(DOCDIR, "en", "doc.html")
      
    DOC = os.path.abspath(DOC)
    webbrowser.open_new("file://" + DOC)
    
  def on_song_prop(self, event = None):
    import init_editobj
    init_editobj.edit(self.song, cancel = self.cancel)
    
  def on_rythm_prop(self, event = None):
    import init_editobj, editobj
    
    mesures = self.selected_mesures() or self.song.mesures
    
    mesures_old_rythms = map(lambda mesure: (mesure, mesure.rythm1, mesure.rythm2), mesures)
    
    def on_ok():
      rythm1 = mesures[0].rythm1
      rythm2 = mesures[0].rythm2
      if not((rythm2 == 4) or ((rythm2 == 8) and (rythm1 % 3 == 0))):
        import tkMessageBox
        tkMessageBox.showwarning(_("__unsupported-rythm__"), _("__unsupported-rythm-message__") % (rythm1, rythm2))
      for mesure in mesures: mesure.compute_duration()
      
      time = 0
      for mesure in self.song.mesures:
        mesure.time = time
        time = time + mesure.duration
        
      self.rythm_changed()
      
      mesures_new_rythms = map(lambda mesure: (mesure, mesure.rythm1, mesure.rythm2), mesures)
      if mesures_old_rythms != mesures_new_rythms:
        for partition in self.song.partitions: partition.view.destroy()
        self.draw()
        
    init_editobj.edit(editobj.MultiEdit(mesures), command = on_ok, cancel = self.cancel, grab = 1)
    
  def on_partition_prop(self):
    self.partition.view.on_prop()
    
  def on_note_prop(self, event = None):
    import init_editobj, editobj
    graphic_notes = filter(lambda graphic_note: isinstance(graphic_note.note, song.Note), self.selected_notes())
    if not graphic_notes: return
    notes = map(lambda graphic_note: graphic_note.note, graphic_notes)
    
    for note in notes:
      note.special_effect_name = note.__class__.__name__
      if note.special_effect_name == "LinkedNote": note.special_effect_name = "Note"
      
    def on_ok():
      for graphic_note in graphic_notes:
        if hasattr(graphic_note.note, "special_effect_name"):
          if (graphic_note.note.special_effect_name != graphic_note.note.__class__.__name__) and not((graphic_note.note.special_effect_name == "Note") and (graphic_note.note.__class__.__name__ == "LinkedNote")):
            graphic_note.set_effect(getattr(song, graphic_note.note.special_effect_name))
            
          del graphic_note.note.special_effect_name
          
        graphic_note.get_self().update()
        
    init_editobj.edit(editobj.MultiEdit(notes), command = on_ok, cancel = self.cancel, grab = 1)
    
  def on_new_lyrics2(self):
    import lyric2
    
    lyrics = song.Lyrics2(self.song)
    lyrics.header = _("Lyrics")
    lyrics.setviewtype(lyric2.lyric_view_type)
    self.add_partition(lyrics)
    self.ensure_visible_y(100000)
    
  def add_partition(self, partition):
    def do_it():
      self.song.partitions.append(partition)
      self.draw()
      self.cancel.add_cancel(cancel_it)
    def cancel_it():
      partition.view.destroy()
      self.song.partitions.remove(partition)
      self.draw()
      self.cancel.add_redo(do_it)
      
    do_it()
    
  def on_partition_moveup  (self): self.move_partition(self.partition, -1)
  def on_partition_movedown(self): self.move_partition(self.partition,  1)
  def move_partition(self, partition, dir):
    index = self.song.partitions.index(partition)
    
    if 0 <= index + dir <= len(self.song.partitions) - 1:
      def do_it():
        del self.song.partitions[index]
        self.song.partitions.insert(index + dir, partition)
        self.draw()
        self.cancel.add_cancel(cancel_it)
        
      def cancel_it():
        del self.song.partitions[index + dir]
        self.song.partitions.insert(index, partition)
        self.draw()
        self.cancel.add_redo(do_it)
        
      do_it()
      
  def on_partition_delete(self, partition = None):
    if not partition: partition = self.partition
    index     = self.song.partitions.index(partition)
    
    def do_it():
      partition.view.destroy()
      self.song.partitions.remove(partition)
      self.draw()
      self.canvas.coords(self.partition_focus, -10, -10, -10, -10)
      if self.partition is partition: self.partition = None
      self.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      self.song.partitions.insert(index, partition)
      self.draw()
      self.canvas.coords(self.partition_focus, -10, -10, -10, -10)
      self.cancel.add_redo(do_it)
      
    do_it()
    
  def on_preferences   (self): globdef.config.edit()
  def on_play          (self, event = None):
    midi, playbar_info = self.song.midi()
    player.play_async(midi, globdef.config.PLAY_LOOP)
    if globdef.config.DISPLAY_PLAY_BAR: thread.start_new_thread(self.play_bar_idle, (0, playbar_info,))
  def on_play_in_loop  (self):
    midi, playbar_info = self.song.midi()
    player.play_async(midi, 1)
    if globdef.config.DISPLAY_PLAY_BAR: thread.start_new_thread(self.play_bar_idle, (0, playbar_info,))
  def on_play_from_here(self):
    selected_notes = self.selected_notes()
    if selected_notes: from_time = min(map(lambda graphic_note: graphic_note.note.time, selected_notes))
    else:              from_time = 0
    midi, playbar_info = self.song.midi(from_time)
    player.play_async(midi)
    if globdef.config.DISPLAY_PLAY_BAR: thread.start_new_thread(self.play_bar_idle, (from_time, playbar_info,))
  def on_stop_playing  (self): player.stop()
  def on_play_loop     (self): globdef.config.PLAY_LOOP = self.play_loop.active
    
  def incr_zoom(self, incr):
    x = self.x_to_time(self.canvas.canvasx(self.width / 2.0))
    
    if incr == 1: self.zoom = self.zoom * 2.0
    else:         self.zoom = self.zoom / 2.0
    
    for partition in self.song.partitions:
      partition.view.zoom = self.zoom
      partition.view.destroy()
    self.draw()
    
    x = self.time_to_x(x) - self.width / 2.0
    self.canvas_xview("moveto", x / self.max_x)
    
  def on_space(self, event = None): # space : play from the current position
    if player.is_playing(): player.stop()
    else: self.on_play_from_here()
    
  def on_key_press(self, event):
    #print event.keycode, event.state, event.char
    
    need_pop_cancel = 0
    char = event.char
    
    if not event.keycode in (23, 97, 98, 99, 100, 102, 103, 104, 105): # Deplacement key, handled by partitions' views
      self.cancel.push()
      need_pop_cancel = 1 # Propagate the event, and then pop the cancel stack

    if   char == "*":
      graphic_notes = self.selected_notes()
      if graphic_notes:
        index = {
          384 : 0,
          192 : 0,
          96 : 1,
          48 : 2,
          24 : 3,
          12 : 4,
          }[graphic_notes[0].note.base_duration()]
      else:
        index = max(0, self.duration_buttons.index(self.old_duration_button) - 1)
      self.on_note_duration(self.duration_buttons[index])
      
    elif char == "/":
      graphic_notes = self.selected_notes()
      if graphic_notes:
        index = {
          384 : 1,
          192 : 2,
           96 : 3,
           48 : 4,
           24 : 5,
           12 : 5,
          }[graphic_notes[0].note.base_duration()]
      else:
        index = min(len(self.duration_buttons), self.duration_buttons.index(self.old_duration_button) + 1)
      self.on_note_duration(self.duration_buttons[index])

    elif char == ".":
      self.on_note_doted()
      
    for partition in self.song.partitions:
      if partition.view.on_key_press(event): break
      
    if need_pop_cancel: self.cancel.pop()
    
    if event.keycode == 23: return "break"
    
  def on_button_press1(self, event):
    global selection
    
    self.canvas.focus_set()
    
    x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
    self.selection_x1 = x
    self.selection_y1 = y
    
    for partition in self.song.partitions:
      if partition.view.y1 < y < partition.view.y2:
        self.set_partition(partition)
        break
      
    # Check if the user is dragging an already selected note, or drawing a new selection
    for partition in self.song.partitions:
      graphic_note = partition.view.note_at(x, y)
      if graphic_note and graphic_note.selected: # There's a selected note at the clicked position => drag !
        self.mode = DRAGGING_NOTES_MODE
        selection = []
        for partition in self.song.partitions:
          selection.extend(partition.view.selected_notes())
          
        return # Don't send the event to the partitions' views
    self.mode = SELECTION_MODE
    
    for partition in self.song.partitions:
      if partition.view.on_button_press1(event, x, y): break
      
  def on_button_press2(self, event):
    self.canvas.focus_set()
    
    x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
    
    if selection: # Paste
      self.mode = DRAGGING_NOTES_MODE
      self.drag_box = 1
      for graphic_note in selection: graphic_note.drag(self.canvas, "drag")
      
      minx = miny = sys.maxint
      for graphic_note in selection:
        if graphic_note.x < minx: minx = graphic_note.x
        if graphic_note.y < miny: miny = graphic_note.y
        
      self.canvas.move("drag", x - minx, y - miny)
      
      self.selection_x1 = minx
      self.selection_y1 = miny
      self.selection_x2 = self.old_selection_x2 = x
      self.selection_y2 = self.old_selection_y2 = y
      
  def on_button_press3(self, event):
    self.canvas.focus_set()
    
    x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
    for partition in self.song.partitions:
      if partition.view.on_button_press3(event, x, y): break
      
  def on_button_release1(self, event):
    if   self.mode == DRAGGING_NOTES_MODE and self.drag_box:      self.drag_performed()
    elif self.mode == SELECTION_MODE      and self.selection_box: self.selection_performed()
    self.mode = NO_MODE
  def on_button_release2(self, event):
    if   self.mode == DRAGGING_NOTES_MODE and self.drag_box:      self.drag_performed(delete_source = 0)
    self.mode = NO_MODE
  def on_button_release3(self, event):
    if self.mode == DRAGGING_NOTES_MODE: # Cancel drag
      self.canvas.delete("drag")
      self.drag_box = None
    self.mode = NO_MODE
    
  def on_motion(self, event):
    #if event.state in (272, 528): # Do not work on all computer
    if event.state:
      if not self.mode: return # The motion was not initiated in the canvas but in an inner widget !!!
      
      self.selection_x2, self.selection_y2 = x, y = self.canvas.canvasx(event.x),  self.canvas.canvasy(event.y)
      
      self.ensure_visible_x(x)
      self.ensure_visible_y(y)
      
      if   self.mode == DRAGGING_NOTES_MODE:
        if self.drag_box:
          self.canvas.move("drag", self.selection_x2 - self.old_selection_x2, self.selection_y2 - self.old_selection_y2)
          self.old_selection_x2 = self.selection_x2
          self.old_selection_y2 = self.selection_y2
        else:
          self.drag_box = 1 #self.canvas.root().add(gcanvas.CanvasGroup)
          for graphic_note in selection: graphic_note.drag(self.canvas, "drag")
          
          self.old_selection_x2 = self.selection_x1
          self.old_selection_y2 = self.selection_y1
          
      elif self.mode == SELECTION_MODE:
        if self.selection_box:
          self.canvas.coords(self.selection_box,
                             min(self.selection_x1, self.selection_x2),
                             min(self.selection_y1, self.selection_y2),
                             max(self.selection_x1, self.selection_x2),
                             max(self.selection_y1, self.selection_y2),
                             )
        else:
          self.selection_box = self.canvas.create_rectangle(self.selection_x1, self.selection_y1, self.selection_x1, self.selection_y1, fill = "#DDDDFF", outline = "#AAAADD", width = 2)
          self.canvas.tag_lower(self.selection_box)
          self.canvas.tag_raise(self.selection_box, self.partition_focus)
          
  def selection_performed(self):
    global selection, selection_cloned
    self.canvas.delete(self.selection_box)
    self.selection_box = None
    
    # Avoid dummy selections of a very small rect if you drag a little the mouse when clicking
    if abs(self.selection_x1 - self.selection_x2) + abs(self.selection_y1 - self.selection_y2) > 15:
      selection        = []
      selection_cloned = 0
      for partition in self.song.partitions:
        partition.view.select_in_box(
          min(self.selection_x1, self.selection_x2),
          min(self.selection_y1, self.selection_y2),
          max(self.selection_x1, self.selection_x2),
          max(self.selection_y1, self.selection_y2),
          )
        selection.extend(partition.view.selected_notes())
        
    return 1 # Propagate the event
    
  def drag_performed(self, delete_source = 1):
    if self.drag_box:
      self.canvas.delete("drag")
      self.drag_box = None
      
    # dt and dy are the time and y deplacement. dt is rounded to the nearest current note duration (and that looks to require to work on its absolute part ?).
    dt_ = (self.selection_x2 - self.selection_x1) / self.zoom
    dy  = self.selection_y2 - self.selection_y1
    dt  = int(0.4 + float(abs(dt_)) / self.default_note.duration) * self.default_note.duration
    if dt_ < 0: dt = -dt
    
    # deepcopies the notes (in one big list, and NOT note by note, because some notes may be linked to or from other ones !)
    clones = copy.deepcopy(map(lambda graphic_note: graphic_note.note, selection))
    
    selection_and_clones = zip(selection, clones)
    
    self.cancel.push()
    
    if delete_source:
      sources = selection[:]
      def do_it():
        for i in range(len(sources)): sources.pop().delete()
        self.cancel.add_cancel(cancel_it)
        
      def cancel_it():
        for graphic_note, clone in selection_and_clones:
          graphic_note.get_view().partition.addnote(graphic_note.note)
          g = graphic_note.get_view().drawnote(graphic_note.note)
          g.get_view().add_selection(g)
          sources.append(g)
        self.cancel.add_redo(do_it)
        
        # Required, but should not be done here !!! But where and how ???
        for partition in self.song.partitions:
          partition.view.big_change_done()
      do_it()
      
    partition_pasted_notes = {} # Map partitions to the list of note pasted to them
    
    # Add them in the right partition -- We must do 2 different "for" because ALL the time must be OK when we add the notes in the partition (for linked notes)
    for graphic_note, clone in selection_and_clones:
      y = graphic_note.y + dy
      if   hasattr(clone, "time"  ): clone.time   = graphic_note.note.time + dt # Time-located element
      elif hasattr(clone, "mesure"): clone.mesure = self.song.mesure_at(clone.mesure.time + dt, 1) # Mesure-located element (note may be a Note but also a Lyric, ... !!!)
      
      for partition in self.song.partitions:
        if partition.view.y2 >= y: # The current note is over this partition.
          pasted_notes = partition_pasted_notes.get(partition)
          if not pasted_notes: pasted_notes = partition_pasted_notes[partition] = []
          
          pasted_notes.append((graphic_note, y, clone))
          break
        
    for partition, pasted_notes in partition_pasted_notes.items():
      partition.view.paste(pasted_notes)
      
    self.cancel.pop()
    return 1 # Propagate the event
  
  def on_note_paste(self):
    selected_notes = self.selected_notes()
    if selected_notes:
      # Hack the selection coordinates
      self.selection_x1 = min(map(lambda graphic_note: graphic_note.x, selection))
      self.selection_y1 = min(map(lambda graphic_note: graphic_note.y, selection))
      self.selection_x2 = selected_notes[0].x
      self.selection_y2 = selected_notes[0].y
      # End up a "fake" drag
      self.drag_performed(delete_source = 0)
      
  def on_insert_times(self):
    import tkSimpleDialog
    nb_time = tkSimpleDialog.askinteger(_("Insert times..."), _("Insert how many times? (negative for removing)"), parent = self)
    if not nb_time: return
    at = self.selected_notes()[0].note.time
    delta = nb_time * 96
    removed = []
    
    def shift(delta):
      old_removed = removed[:]
      del removed[:]
      
      for partition in self.song.partitions:
        if isinstance(partition, song.Partition):
          i = 0
          while i < len(partition.notes):
            note = partition.notes[i]
            if note.time >= at:
              if (delta < 0) and note.time < at - delta:
                del partition.notes[i]
                removed.append((partition, note))
                continue
              else: note.time += delta
            i += 1
            
      for partition, note in old_removed: partition.addnote(note)
      
      for partition in self.song.partitions: partition.view.destroy()
      self.draw()
      
    def do_it():
      shift(delta)
      self.cancel.add_cancel(cancel_it)
    
    def cancel_it():
      shift(-delta)
      self.cancel.add_redo(do_it)
      
    do_it()
    
  def on_insert_mesures(self):
    import tkSimpleDialog
    nb_mesure = tkSimpleDialog.askinteger(_("Insert bars..."), _("Insert how many bars? (negative for removing)"), parent = self)
    if not nb_mesure: return
    mesure = self.song.mesure_at(self.selected_notes()[0].note.time)
    mesure_pos = self.song.mesures.index(mesure)
    at = mesure.time
    removed = []
    playlist_items_values = []
    
    def shift(nb_mesure):
      # Add / remove mesures
      time = self.song.mesures[mesure_pos].time
      if nb_mesure > 0:
        for i in range(mesure_pos, mesure_pos + nb_mesure):
          self.song.mesures.insert(i, song.Mesure(time, mesure.tempo, mesure.rythm1, mesure.rythm2, mesure.syncope))
          time += mesure.duration
      else:
        del self.song.mesures[mesure_pos : mesure_pos - nb_mesure]
        i = mesure_pos
      for mes in self.song.mesures[i:]:
        mes.time = time
        time += mes.duration
        
      # Shift playlist
      unobserve_tree(self.song.playlist, self.on_playlist_changed)
      if playlist_items_values:
        for item, from_mesure, to_mesure in playlist_items_values:
          item.from_mesure = from_mesure
          item.to_mesure   = to_mesure
        del playlist_items_values[:]
      else:
        for item in self.song.playlist.playlist_items:
          playlist_items_values.append((item, item.from_mesure, item.to_mesure))
          if   item.from_mesure >= mesure_pos:
            if item.from_mesure <  mesure_pos - nb_mesure: item.from_mesure = mesure_pos
            else:                                          item.from_mesure += nb_mesure
          if   item.to_mesure   >= mesure_pos - 1:
            if item.to_mesure   <  mesure_pos-1-nb_mesure: item.to_mesure   = mesure_pos - 1
            else:                                          item.to_mesure   += nb_mesure

      # Shift notes
      old_removed = removed[:]
      del removed[:]
      
      delta = nb_mesure * mesure.duration
      for partition in self.song.partitions:
        if isinstance(partition, song.Partition):
          i = 0
          while i < len(partition.notes):
            note = partition.notes[i]
            if note.time >= at:
              if (delta < 0) and note.time < at - delta:
                del partition.notes[i]
                removed.append((partition, note))
                continue
              else: note.time += delta
            i += 1
            
      for partition, note in old_removed: partition.addnote(note)
      
      for partition in self.song.partitions: partition.view.destroy()
      self.draw()
      
      observe_tree(self.song.playlist, self.on_playlist_changed)
      self.on_playlist_changed(None, None, None, None)
      
    def do_it():
      shift(nb_mesure)
      self.cancel.add_cancel(cancel_it)
    
    def cancel_it():
      shift(-nb_mesure)
      self.cancel.add_redo(do_it)
      
    do_it()
    
  def on_note_arrange(self):
    import tkSimpleDialog
    fret = tkSimpleDialog.askinteger(_("Arrange at fret..."), _("Arrange selected notes at fret?"), parent = self)
    
    self.cancel.push()
    
    for partition in self.song.partitions:
      partition.view.arrange_selection_at_fret(fret)
      
    self.cancel.pop()
    
  def on_note_duration(self, button):
    self.old_duration_button["relief"] = "flat"
    button["relief"] = "sunken"
    self.base_duration = button.duration
    self.compute_duration()
    self.old_duration_button = button
    
  def on_note_doted(self, event = None):
    if self.triplet_duration: return
    
    graphic_notes = self.selected_notes()
    if graphic_notes and graphic_notes[0].note.value > 0:
      self.doted_duration = not graphic_notes[0].note.dotted()
    else: self.doted_duration = self.doted_button["relief"] == "flat"
    
    if self.doted_duration: self.doted_button["relief"] = "sunken"
    else:                   self.doted_button["relief"] = "flat"
    
    self.compute_duration(graphic_notes)
    
  def on_note_triplet(self, event = None):
    if self.doted_duration: return
    
    graphic_notes = self.selected_notes()
    if graphic_notes and graphic_notes[0].note.value > 0:
      self.triplet_duration = not graphic_notes[0].note.is_triplet()
    else: self.triplet_duration = self.triplet_button["relief"] == "flat"
    
    if self.triplet_duration: self.triplet_button["relief"] = "sunken"
    else:                     self.triplet_button["relief"] = "flat"
    
    self.compute_duration(graphic_notes)
    
  def compute_duration(self, graphic_notes = None):
    if graphic_notes is None: graphic_notes = self.selected_notes()
    
    duration = self.base_duration
    if self.doted_duration  : duration = int(duration * 1.5)
    if self.triplet_duration: duration = int(duration / 1.5)
    self.default_note.time = self.default_note.duration = duration
    
    def is_not_fake(graphic_note):
      if not isinstance(graphic_note.note, song.Note): return 0
      if graphic_note.note.value < 0:
        graphic_note.note.duration = duration
        graphic_note.update()
        return 0
      return 1
    graphic_notes = filter(is_not_fake, graphic_notes)
    if not graphic_notes: return
    
    old_values = map(lambda graphic_note: graphic_note.note.duration, graphic_notes)
    
    def do_it():
      for graphic_note in graphic_notes:
        g = graphic_note.get_self()
        g.note.duration = duration
        g.update()
        
      self.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      for graphic_note, old_value in zip(graphic_notes, old_values):
        g = graphic_note.get_self()
        g.note.duration = old_value
        g.update()
        
      self.cancel.add_redo(do_it)
      
    do_it()
    
  def on_note_stressed(self, event = None):
    graphic_notes = self.selected_notes()
    
    if graphic_notes: newvalue = graphic_notes[0].note.volume < 220
    else:             newvalue = self.stressed_button["relief"] == "flat"
    
    if newvalue:
      volume = self.default_note.volume = 0xFF
      self.stressed_button["relief"] = "sunken"
    else:
      volume = self.default_note.volume = 0xCC
      self.stressed_button["relief"] = "flat"
      
    def is_not_fake(graphic_note):
      if not isinstance(graphic_note.note, song.Note): return 0
      if graphic_note.note.value < 0:
        graphic_note.note.volume = volume
        graphic_note.update()
        return 0
      return 1
    graphic_notes = filter(is_not_fake, graphic_notes)
    if not graphic_notes: return
    
    old_values = map(lambda graphic_note: graphic_note.note.volume, graphic_notes)
    
    def do_it():
      for graphic_note in graphic_notes:
        g = graphic_note.get_self()
        g.note.volume = volume
        g.update()
        
      self.cancel.add_cancel(cancel_it)
      
    def cancel_it():
      for graphic_note, old_value in zip(graphic_notes, old_values):
        g = graphic_note.get_self()
        g.note.volume = old_value
        g.update()
        
      self.cancel.add_redo(do_it)
      
    do_it()
    
  def draw(self):
    y = self.y
    for partition in self.song.partitions:
      partition.view.zoom = self.zoom
      partition.view.set_default_note(self.default_note)
      x, y = partition.view.draw(self.canvas, 20, y)
      y = y + 10
    self.height = y
    self.set_scroll_region()
    self.ensure_drawn()
    
  def rythm_changed(self):
    self.song.rythm_changed()
    for partition in self.song.partitions: partition.view.rythm_changed()
    
  def selected_mesures(self):
    mesures = {}
    for graphic_note in self.selected_notes():
      mesure = self.song.mesure_at(graphic_note.note.time)
      mesures[mesure] = 1
    return mesures.keys()
  
  def selected_notes(self):
    notes = []
    for partition in self.song.partitions: notes.extend(partition.view.selected_notes())
    return notes
  def has_note_selected(self):
    for partition in self.song.partitions:
      if partition.view.selected_notes(): return 1
      
  def x_to_time(self, x   ): return int(x - 30) / self.zoom
  def time_to_x(self, time): return time * self.zoom + 30
  def time_to_x_vec(self, time): return time * self.zoom
  def time_to_second(self, time): return float(time) / (self.song.mesures[0].tempo * 2)
  
  def on_dump(self):
    print self.song.__xml__().getvalue()
    
    #import lilypond
    #reload(lilypond)
    
    #lily = lilypond.lilypond(self.song)
    #print lily
    #print >> open("/home/jiba/src/test2.ly", "w"), lily
    
    
  def on_dump_clipboard(self): print `selection`
  def on_gc(self):
    import gc
    
    print gc.collect()
    for o in gc.garbage:
      print getattr(o, "title", repr(o))
    print
    
  def on_console(self):
    from editobj.console import Console
    from Tkinter import tkroot
    import editobj, init_editobj, view, tablature, drum, staff, lyric2
    
    t = Toplevel(tkroot)
    c = Console(t, { "app"       : self,
                     "SONG"      : self.song,
                     "song"      : song,
                     "view"      : view,
                     "tablature" : tablature,
                     "drum"      : drum,
                     "staff"     : staff,
                     "lyric2"    : lyric2,
                     "os"        : os,
                     "sys"       : sys,
                     "editobj"   : editobj,
                     "edit"      : init_editobj.edit,
                     "observe"   : editobj.observe,
                     })
    c.text.insert("end", """\nYou can access the song as "SONG", and the main app window as "app". Use "edit(obj)" to edit any object.\n""")
    c.text.insert("end", sys.ps1)
    c.pack()

    

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

# GlobDef : global stuff (cannot be called global nor glob so...).

import os, os.path, gettext, sys, editobj.cancel as cancel

APPDIR = os.path.dirname(__file__)

DATADIR = os.path.join(APPDIR, "data")
if not os.path.exists(DATADIR):
  import warnings
  warnings.warn("Songwrite's data directory cannot be found !")
  
LOCALEDIR = os.path.join(APPDIR, "locale")
if not os.path.exists(LOCALEDIR):
  LOCALEDIR = os.path.join(APPDIR, "..", "locale")
  if not os.path.exists(LOCALEDIR):
    LOCALEDIR = os.path.join("/", "usr", "share", "locale")
    
try:
  translator = gettext.translation("songwrite", LOCALEDIR)
except IOError: # Non-supported language, defaults to english
  translator = gettext.translation("songwrite", LOCALEDIR, ("en",))
translator.install(1)

CONFIGFILE = os.path.expanduser(os.path.join("~", ".songwrite"))
NO_CONFIG  = 0

class Config:
  def __init__(self):
    # Default config
    self.MIDI_COMMAND       = "timidity -id -"
    self.MIDI_USE_TEMP_FILE = 0
    self.PLAY_LOOP          = 0
    self.PREVIEW_COMMAND    = "gv"
    self.NUMBER_OF_CANCEL   = 20
    self.PREVIOUS_FILES     = []
    self.PAGE_FORMAT        = "a4paper"
    self.DISPLAY_PLAY_BAR   = 1
    
    global NO_CONFIG
    if os.path.exists(CONFIGFILE):
      try:
        execfile(CONFIGFILE, self.__dict__)
        
        cancel.NUMBER_OF_CANCEL = self.NUMBER_OF_CANCEL + 1
        
        NO_CONFIG = 0
        return
      except:
        sys.excepthook(*sys.exc_info())
        print "Error in config file ~/.songwrite ! Please reconfigure Songwrite !"
        
    NO_CONFIG = 1
    
  def add_previous_file(self, file):
    try: self.PREVIOUS_FILES.remove(file) # No dupplicated item.
    except: pass
    self.PREVIOUS_FILES.insert(0, file)
    if len(self.PREVIOUS_FILES) > 12: del self.PREVIOUS_FILES[-1]
    
  def __str__(self):
    return """
# Songwrite config file. Use a Python syntax.

# 1 to use a temporary MIDI file (call this file %%s in the command line).
# 0 to use standard input.
MIDI_USE_TEMP_FILE = %s

# Command line to play a midi file.
MIDI_COMMAND = "%s"

# 1 to play in loop. 0 to play once.
PLAY_LOOP = %s

# 1 for enabling playbar
DISPLAY_PLAY_BAR = %s

# Page format (LaTeX)
PAGE_FORMAT = "%s"

# Command line to preview/print postscript.
PREVIEW_COMMAND = "%s"

# Size of cancel stack.
NUMBER_OF_CANCEL = %s

# Previous opened files.
PREVIOUS_FILES = %s
""" % (self.MIDI_USE_TEMP_FILE, self.MIDI_COMMAND, self.PLAY_LOOP, self.DISPLAY_PLAY_BAR, self.PAGE_FORMAT, self.PREVIEW_COMMAND, self.NUMBER_OF_CANCEL, `self.PREVIOUS_FILES`)

  def save(self):
    open(CONFIGFILE, "w").write(str(self))

  def edit(self):
    import init_editobj
    
    def on_ok():
      self.MIDI_USE_TEMP_FILE = self.MIDI_COMMAND.find("%s") != -1
      cancel.NUMBER_OF_CANCEL = self.NUMBER_OF_CANCEL + 1
      self.save()
      
    init_editobj.edit(self, command = on_ok, preamble = _("__config_preamble__"))
    
    
config = Config()


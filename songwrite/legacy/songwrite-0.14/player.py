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
import sys, popen2, os, thread, globdef

_p = None

def is_playing(): return _p and (_p.poll() == -1)
def stop():
  global _p
  if not _p is None:
    try: os.kill(_p.pid, 9)
    except OSError: pass
    _p  = None
    
def play(midi, loop = 0):
  global _p
  
  while 1:
    if globdef.config.MIDI_USE_TEMP_FILE:
      import tempfile
      file = tempfile.mktemp(".midi")
      open(file, "w").write(midi)
      _p = p = popen2.Popen4(globdef.config.MIDI_COMMAND % file)
    else:
      _p = p = popen2.Popen4(globdef.config.MIDI_COMMAND)
      _p.tochild.write(midi)
      _p.tochild.flush()
      
    p.wait()
    
    if (globdef.config.MIDI_COMMAND.find("timidity") != -1) and (p.fromchild.read().find("Couldn't open Arts device") != -1):
      # We are using the KDE / aRts version of Timidity
      # This fucking version can only play with aRts,
      # until we provide another config file for it.
      #
      # BTW am I alone to think that aRts is a pain ?
      
      # Get the default config file
      import re, tempfile
      timidity_verbose = os.popen4("timidity -idvvv")[1].read()
      timidity_cfg = re.findall(r"\S*\.cfg", timidity_verbose)
      if timidity_cfg:
        timidity_cfg = timidity_cfg[0]
        
        cfg = open(timidity_cfg).read()
        cfg = re.sub("-O\s+A", "# No longer use fucking aRts", cfg)
        
        temp_cfg = tempfile.mktemp(".timidity.noarts.cfg")
        open(temp_cfg, "w").write(cfg)
        
        globdef.config.MIDI_COMMAND += " -c %s" % temp_cfg
        
        import tkMessageBox
        tkMessageBox.showwarning(_("aRts is getting in the way"), _("__fucking-arts__") % temp_cfg)
        
    if (p.poll() != 0) or (not loop):
      break # Stop if _p has been killed (by stop()) or if not loop !
    

def play_async(midi, loop = 0):
  stop()
  thread.start_new_thread(play, (midi, loop))
  
  

# -*- coding: utf-8 -*-

# A login dialog box

# Copyright (C) 2007 Jean-Baptiste LAMY -- jiba@tuxfamily.org
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

import sys, os, os.path, time, thread, editobj2, editobj2.introsp as introsp, editobj2.observe as observe, editobj2.field as field
import editobj2.undoredo as undoredo

class Download(object):
  def __init__(self, url, filename):
    self.remote_url     = url
    self.local_filename = filename
    self.progress       = 0.0
    self.speed          = 10
    self.completed      = 0
    
  def __unicode__(self): return os.path.basename(self.remote_url) + u" (" + str(int(100 * self.progress)) + u"%)"
  def __repr__   (self): return os.path.basename(self.remote_url) +  " (" + str(int(100 * self.progress)) +  "%)"

  def start(self):
    self.progress = 0.0
    
  def stop(self): pass


class DownloadManager(object):
  def __init__(self):
    self.downloads = []
    
  def __unicode__(self): return "Download manager"

  def add(self, download):
    self.insert(len(self.downloads) + 1, download)

  def insert(self, index, download):
    self.downloads.insert(index, download)
    download.start()

  def remove(self, download):
    download.stop()
    self.downloads.remove(download)

icon_filename = os.path.join(os.path.dirname(sys.argv[0]), "./jiba.png")

dm = DownloadManager()
dm.downloads.append(Download("http://python.org", "./index_python.html"))
dm.downloads.append(Download("http://soyaproject.org/soya", "./index_soya.html"))
dm.downloads.append(Download("http://soyaproject.org/slune", "./index_slune.html"))
dm.downloads.append(Download("http://soyaproject.org/balazar_brother", "./index_balazar_brother.html"))

def downloader():
  for download in dm.downloads[:]:
    if download.progress < 1.0:
      download.progress = download.progress + 0.001 * download.speed
      if download.progress >= 1.0:
        download.progress = 1.0
        download.completed = 1
  return 1

def run_downloader():
  import time
  while 1:
    downloader()
    time.sleep(0.2)
  
descr = introsp.description(Download)
descr.set_field_for_attr("progress", field.ProgressBarField)
descr.set_field_for_attr("speed", field.RangeField(0, 100), "Ko/s")
descr.set_field_for_attr("completed", field.BoolField)
descr.set_icon_filename(os.path.join(os.path.dirname(sys.argv[0]), "./file.png"))

descr = introsp.description(DownloadManager)
descr.set_details("To add a new download, click on the '+' button on the right.\nUse the '-' button to remove and cancel a download.")

descr.set_children_getter(
  "downloads", # Children
  None, # Has children method
  lambda download_manager: Download("http://", ""), # New children method
  "insert", # Add method
  "remove", # Remove method
  1, # Reorderable
  )

descr.add_action(introsp.Action("Undo", lambda undo_stack, o: undo_stack.undo()))
descr.add_action(introsp.Action("Redo", lambda undo_stack, o: undo_stack.redo()))

if   "--gtk"    in sys.argv: editobj2.GUI = "Gtk"
elif "--tk"     in sys.argv: editobj2.GUI = "Tk"
elif "--qt"     in sys.argv: editobj2.GUI = "Qt"
elif "--qtopia" in sys.argv: editobj2.GUI = "Qtopia"


w = editobj2.edit(dm, direction = "v")

if editobj2.GUI == "Gtk":
  import gobject
  gobject.timeout_add(200, downloader) # Gtk / PyGtk does not like being used along with Python thread module
else:
  import thread; thread.start_new_thread(run_downloader, ())
 
observe.start_scanning_gui()

w.main()

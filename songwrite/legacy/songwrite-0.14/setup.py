#! /usr/bin/env python

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

import os, os.path, sys, glob, distutils.core

if "--no-lang" in sys.argv:
  sys.argv.remove("--no-lang")
  no_lang = 1
else: no_lang = 0

# data_files = [
#   (os.path.join("songwrite", "data"),
#   glob.glob(os.path.join(".", "data", "*"))),
#   ]
data_files = [
  (os.path.join("songwrite", "data"),
  [os.path.join("data", file) for file in os.listdir("data") if (file != "CVS") and (file != ".arch-ids")]),
  ]
if not no_lang:
  data_files = data_files + [
    (os.path.join(os.path.dirname(mo_file)), [mo_file])
    for mo_file
    in  glob.glob(os.path.join(".", "locale", "*", "LC_MESSAGES", "*"))
    ]

for doc_lang in glob.glob(os.path.join(".", "doc", "*")):
  data_files.append(
    (os.path.join("songwrite", doc_lang),
     glob.glob(os.path.join(".", doc_lang, "*"))),
    )

distutils.core.setup(name         = "Songwrite",
                     version      = "0.14",
                     license      = "GPL",
                     description  = "Tablature editor in Python with Tk, Timidity and Lilypond",
                     author       = "Lamy Jean-Baptiste",
                     author_email = "jiba@tuxfamily.org",
                     url          = "http://oomadness.tuxfamily.org/en/songwrite",
                     
                     package_dir  = {"songwrite" : ""},
                     packages     = ["songwrite"],
                     
                     scripts      = ["songwrite"],
                     
                     data_files   = data_files,
                     )

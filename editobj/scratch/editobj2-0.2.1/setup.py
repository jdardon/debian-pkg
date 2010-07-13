#! /usr/bin/env python

# Songwrite 2
# Copyright (C) 2001-2007 Jean-Baptiste LAMY -- jibalamy@free.fr
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

import os, os.path, sys, glob
import distutils.core, distutils.sysconfig

install_dir = distutils.sysconfig.get_python_lib()

distutils.core.setup(name         = "EditObj2",
                     version      = "0.2.1",
                     license      = "GPL",
                     description  = "A Java-Bean-like dialog box generator for Python objects, compatible with Gtk 2, Tk, Qt and Qtopia",
                     
                     long_description = """EditObj 2 is a dialog box generator for Python objects, using Gtk 2, Tk, Qt or Qtopia (at your choice). It behaves similarly to a Java Bean editor, but is devoted to Python, and it features several improvements. In particular, it can deal with tree structure of objects in a very efficient way.
Well... actually EditObj2 is more that just a dialog box generator. It is somehow a GUI per se... look at the examples directory to see its power :-)
EditObj2 is entirely written in Python.""",
                     
                     author       = "Lamy Jean-Baptiste",
                     author_email = "jibalamy@free.fr",
                     url          = "http://home.gna.org/oomadness/en/editobj/index.html",
                     
                     package_dir  = {"editobj2" : ""},
                     packages     = ["editobj2",
                                     ],
                     
                     data_files   = [(os.path.join(install_dir, "editobj2", "icons"),
                                      [os.path.join("icons", file) for file in os.listdir("icons") if (file != "CVS") and (file != ".arch-ids") and (file != ".svn")]
                                      )],
                     )

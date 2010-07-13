# EditObj
# Copyright (C) 2001-2002 Jean-Baptiste LAMY -- jiba@tuxfamily
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

import distutils.core, distutils.sysconfig, os, os.path
from distutils.core import setup, Extension

install_dir = distutils.sysconfig.get_python_lib()

setup(name         = "EditObj",
      version      = "0.5.7",
      description  = "EditObj can create a dialog box to edit ANY Python object.",
      long_description = """EditObj is an automatic GUI generator, similar to Java Bean but designed for Python objects.
It can create a dialog box to edit ANY object.
It also includes a Tk tree widget, an event and a multiple undo-redo frameworks.""",
      license      = "GPL",
      author       = "Lamy Jean-Baptiste (Jiba)",
      author_email = "jiba@tuxfamily.org",
      url          = "http://oomadness.tuxfamily.org/en/editobj",
      
      package_dir  = {"editobj" : ""},
      packages     = ["editobj"],
      
      data_files   = [(os.path.join(install_dir, "editobj", "icons"),
                       [os.path.join("icons", file) for file in os.listdir("icons") if (file != "CVS") and (file != ".arch-ids")]
                       )],
      )

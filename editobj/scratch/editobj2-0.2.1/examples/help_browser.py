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

import sys, os, os.path, re, editobj2, editobj2.introsp as introsp, editobj2.observe as observe, editobj2.field as field, editobj2.undoredo as undoredo, editobj2.editor as editor

class Module(object):
  def __init__(self, module, image = None):
    self.module          = module
    self.details         = re.sub(r"(?<!\n)\n(?!\n)", r"", module.__doc__ or "")
    self.submodules      = []
    if image:
      self.icon_filename = image
    
  def __unicode__(self): return self.module.__name__

mod = Module(editobj2, os.path.join(os.path.dirname(sys.argv[0]), "./dialog.png"))
mod.url = "http://home.gna.org/oomadness/en/editobj"
mod.version = editobj2.VERSION
mod.submodules.append(Module(introsp))
mod.submodules.append(Module(observe))
mod.submodules.append(Module(undoredo))
mod.submodules.append(Module(editor))
mod.submodules.append(Module(field))
#mod.submodules.append(Module(treewidget))


descr = introsp.description(Module)
descr.set_field_for_attr("details"      , None)
descr.set_field_for_attr("icon_filename", None)
descr.set_children_getter("submodules")

# The following are not needed because EditObj2 is smart enough to guess them;
# they are kept only for documentation purpose.

#descr.set_field_for_attr("submodules", None)
#descr.set_details(lambda o: o.details)
#descr.set_label  (lambda o: unicode(o))

if   "--gtk"    in sys.argv: editobj2.GUI = "Gtk"
elif "--tk"     in sys.argv: editobj2.GUI = "Tk"
elif "--qt"     in sys.argv: editobj2.GUI = "Qt"
elif "--qtopia" in sys.argv: editobj2.GUI = "Qtopia"

editobj2.edit(mod).main()

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

import sys, os, os.path, editobj2, editobj2.introsp as introsp, editobj2.observe as observe, editobj2.field as field, editobj2.undoredo as undoredo, editobj2.editor as editor

class Identification(object):
  def __init__(self):
    self.name          = "Jiba"
    self.password      = "123"
    self.age           = 27
    
class Connection(object):
  def __init__(self):
    self.type  = "modem"
    self.speed = 60
    
class Security(object):
  def __init__(self):
    self.level            = 2
    self.allow_javascript = 0
    self.block_popup      = 0

class Plugin(object):
  def __init__(self, name, **kargs):
    self.__dict__ = kargs
    self.name     = name
    self.active   = 1
    
  def __unicode__(self): return "Plugin '%s'" % self.name
  
class Config(object):
  def __init__(self):
    self.connection     = Connection()
    self.security       = Security()
    self.identification = Identification()
    self.plugins = [
      Plugin("GPG", command = "gpg"),
      Plugin("SVG"),
      Plugin("OggVorbis", driver_filename = "/dev/dsp")
      ]

config = Config()
# os.path.join(os.path.dirname(sys.argv[0]), "./jiba.png")


descr = introsp.description(Identification)
descr.set_label("Identification")
descr.set_field_for_attr("age", field.IntField, unit = "years")
descr.set_icon_filename(os.path.join(os.path.dirname(sys.argv[0]), "./jiba.png"))

descr = introsp.description(Connection)
descr.set_label("Connection")
descr.set_field_for_attr("type" , field.EnumField(["modem", "DSL", "ADSL"]))
descr.set_field_for_attr("speed", field.RangeField(0, 512), unit = "Ko/s")

descr = introsp.description(Security)
descr.set_label("Security")
descr.set_field_for_attr("level"           , field.EnumField({"low":0, "medium":1, "high":2, "paranoid":3}))
descr.set_field_for_attr("allow_javascript", field.BoolField)
descr.set_field_for_attr("block_popup"     , field.BoolField)

descr = introsp.description(Plugin)
descr.set_field_for_attr("active", field.BoolField)

descr = introsp.description(Config)
descr.set_label("Configuration")
descr.set_children_getter("plugins")

# The following are not needed because EditObj2 is smart enough to guess them;
# they are kept only for documentation purpose.

#descr.set_field_for_attr("identification", field.ObjectAttributeField)
#descr.set_field_for_attr("connection"    , field.ObjectAttributeField)
#descr.set_field_for_attr("security"      , field.ObjectAttributeField)
#descr.set_label  (lambda o: unicode(o))


if   "--gtk"    in sys.argv: editobj2.GUI = "Gtk"
elif "--tk"     in sys.argv: editobj2.GUI = "Tk"
elif "--qt"     in sys.argv: editobj2.GUI = "Qt"
elif "--qtopia" in sys.argv: editobj2.GUI = "Qtopia"

editobj2.edit(config).main()


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

import sys, os, os.path, editobj2, editobj2.introsp as introsp, editobj2.observe as observe, editobj2.field as field
import editobj2.undoredo as undoredo

class User(object):
  def __init__(self, login, icon_filename, session, language):
    self.login         = login
    self.password      = ""
    self.icon_filename = icon_filename
    self.session       = session
    self.language      = language
    
  def __unicode__(self): return self.login


class UserSelection(object):
  def __init__(self):
    self.users = []
    
  def __unicode__(self): return "User selection"
  

icon_filename = os.path.join(os.path.dirname(sys.argv[0]), "./jiba.png")

user_selection = UserSelection()
user_selection.users.append(User(u"Jiba"    , icon_filename, u"WindowMaker", u"Français"))
user_selection.users.append(User(u"Blam"    , icon_filename, u"FluxBox"    , u"Français"))
user_selection.users.append(User(u"Marmoute", icon_filename, u"MacOS X"    , u"Français"))


descr = introsp.description(User)
descr.set_field_for_attr("icon_filename", None)
descr.set_field_for_attr("session", field.EnumField([u"WindowMaker", u"FluxBox", u"MacOS X", u"Gnome", u"KDE"]))
descr.set_field_for_attr("language", field.EnumField([u"Français", u"Italiano", u"English", u"Esperanto"], long_list = 1))

# The following are not needed because EditObj2 is smart enough to guess them;
# they are kept only for example purpose.
#descr.set_field_for_attr("password", field.PasswordField)
#descr.set_icon_filename(lambda o: o.icon_filename)

descr = introsp.description(UserSelection)
descr.set_children_getter("users")
descr.set_details(u"1) Choose a user\n2) Type a valid password\n3) Login!")

descr.add_action(introsp.Action("Undo", lambda o: undoredo.stack.undo()))
descr.add_action(introsp.Action("Redo", lambda o: undoredo.stack.redo()))


def on_validate(user):
  if isinstance(user, User):
    print "%s has loged in in with password '%s', language '%s' and session type '%s'." % (user.login, user.password, user.language, user.session)
  else:
    print "User has canceled."

if   "--gtk"    in sys.argv: editobj2.GUI = "Gtk"
elif "--tk"     in sys.argv: editobj2.GUI = "Tk"
elif "--qt"     in sys.argv: editobj2.GUI = "Qt"
elif "--qtopia" in sys.argv: editobj2.GUI = "Qtopia"

editobj2.edit(user_selection, on_validate = on_validate).main()

# -*- coding: utf-8 -*-

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

import sys
import editobj2, editobj2.introsp as introsp, editobj2.observe as observe, editobj2.field as field

class Sum(object):
  def __init__(self):
    self.a = 0.0
    self.b = 0.0
  def get_result(self): return self.a + self.b

class Substract(object):
  def __init__(self):
    self.a = 0.0
    self.b = 0.0
  def get_result(self): return self.a - self.b
  
class Multiply(object):
  def __init__(self):
    self.a = 0.0
    self.b = 0.0
  def get_result(self): return self.a * self.b
  
class Divide(object):
  def __init__(self):
    self.a = 0.0
    self.b = 1.0
  def get_result(self): return self.a / self.b


class Calculator(object):
  def __init__(self):
    self.operations = [
      Sum(),
      Substract(),
      Multiply(),
      Divide(),
      ]

descr = introsp.description(Sum)
descr.set_label("Sum")

descr = introsp.description(Substract)
descr.set_label("Substract")

descr = introsp.description(Multiply)
descr.set_label("Multiply")

descr = introsp.description(Divide)
descr.set_label("Divide")


# Hint: 

descr = introsp.description(Calculator)
descr.set_children_getter(lambda calculator: tuple(calculator.operations))
descr.set_label("Calculator")
descr.set_details("A calculator in EditObj2!")


calculator = Calculator()

if   "--gtk"    in sys.argv: editobj2.GUI = "Gtk"
elif "--tk"     in sys.argv: editobj2.GUI = "Tk"
elif "--qt"     in sys.argv: editobj2.GUI = "Qt"
elif "--qtopia" in sys.argv: editobj2.GUI = "Qtopia"

editobj2.edit(calculator).main()


# -*- coding: utf-8 -*-

# field_gtk.py
# Copyright (C) 2007-2008 Jean-Baptiste LAMY -- jiba@tuxfamily.org
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

import editobj2
from editobj2.field import *
from editobj2.field import _RangeField, _ShortEnumField, _LongEnumField
import qt

class QtopiaField(MultiGUIField):
  y_flags = 0

class QtopiaEntryField(QtopiaField, EntryField):
  def __init__(self, gui, master, o, attr, undo_stack):
    self.q = qt.QLineEdit(master.q)
    super(QtopiaEntryField, self).__init__(gui, master, o, attr, undo_stack)
    self.timer = None
    
    self.update()
    self.q.connect(self.q, qt.SIGNAL("textChanged(const QString &)"), self.on_text_changed)
    self.q.connect(self.q, qt.SIGNAL("returnPressed()"), self.validate)
    
  def on_text_changed(self):
    #self.timer = qt.QTimer(self.q)
    #self.timer.connect(self.timer, qt.SIGNAL("timeout()"), self.validate)
    #self.timer.start(500, 1)
    self.validate()
    
  def validate(self):
    s = unicode(self.q.text())#.decode("utf-8")
    if s != self.old_str:
      self.old_str = s
      self.set_value(s)
      
  def update(self):
    self.updating = 1
    try:
      self.old_str = self.get_value()
      self.q.setText(self.old_str)
    finally: self.updating = 0
    
class QtopiaIntField   (QtopiaEntryField, IntField): pass # XXX no "spin-button" since they don't allow entering e.g. "1 + 2" as an integer !
class QtopiaFloatField (QtopiaEntryField, FloatField): pass
class QtopiaStringField(QtopiaEntryField, StringField): pass



class QtopiaPasswordField(QtopiaStringField, PasswordField):
  def __init__(self, gui, master, o, attr, undo_stack):
    QtopiaStringField.__init__(self, gui, master, o, attr, undo_stack)
    self.q.setEchoMode(qt.QLineEdit.Password)
  

class QtopiaBoolField(QtopiaField, BoolField):
  def __init__(self, gui, master, o, attr, undo_stack):
    self.q = qt.QCheckBox("         ", master.q)
    super(QtopiaBoolField, self).__init__(gui, master, o, attr, undo_stack)
    
    self.update()
    self.q.connect(self.q, qt.SIGNAL("stateChanged(int)"), self.validate)
    
  def validate(self, state):
    v = self.descr.get(self.o, self.attr)
    if   state == 1: self.q.setTristate(0)
    elif state == 0:
      if isinstance(v, int): self.set_value(0)
      else:                  self.set_value(False)
    else:
      if isinstance(v, int): self.set_value(1)
      else:                  self.set_value(True)
      
  def update(self):
    self.updating = 1
    try:
      v = self.descr.get(self.o, self.attr)
      if v is introsp.NonConsistent:
        self.q.setTristate(1)
        self.q.setNoChange()
      else:
        self.q.setChecked(v)
    finally:
      self.updating = 0
      

class QtopiaProgressBarField(QtopiaField, ProgressBarField):
  def __init__(self, gui, master, o, attr, undo_stack):
    self.q = qt.QProgressBar(master.q)
    super(ProgressBarField, self).__init__(gui, master, o, attr, undo_stack)
    self.update()
    
  def update(self):
    v = self.get_value()
    if v is introsp.NonConsistent: self.q.setTotalSteps(0)
    else:                          self.q.setTotalSteps(100); self.q.setProgress(int(v * 100))
    

class QtopiaEditButtonField(QtopiaField, EditButtonField):
  def __init__(self, gui, master, o, attr, undo_stack):
    self.q = qt.QPushButton(editobj2.TRANSLATOR(u"Edit..."), master.q)
    super(QtopiaEditButtonField, self).__init__(gui, master, o, attr, undo_stack)
    self.q.setAutoDefault(0)
    self.q.connect(self.q, qt.SIGNAL("clicked()"), self.on_click)
    self.update()
    
  def update(self):
    self.q.setEnabled(not self.get_value() is None)
    
    
class QtopiaWithButtonStringField(QtopiaField, WithButtonStringField):
  def __init__(self, gui, master, o, attr, undo_stack):
    self.q = qt.QHBox(master.q)
    super(QtopiaWithButtonStringField, self).__init__(gui, master, o, attr, undo_stack)
    button = qt.QPushButton(editobj2.TRANSLATOR(self.button_text), self.q)
    button.setAutoDefault(0)
    button.connect(button, qt.SIGNAL("clicked()"), self.on_button)
    
class QtopiaFilenameField(QtopiaWithButtonStringField, FilenameField):
  def on_button(self):
    import editobj2.qtopia_file_chooser
    editobj2.qtopia_file_chooser.ask_filename(self.string_field.set_value, self.string_field.get_value())
    
class QtopiaDirnameField(QtopiaWithButtonStringField, DirnameField):
  def on_button(self):
    import editobj2.qtopia_file_chooser
    editobj2.qtopia_file_chooser.ask_dirname(self.string_field.set_value, self.string_field.get_value())
    
class QtopiaURLField(QtopiaWithButtonStringField, URLField):
  def on_button(self):
    import webbrowser
    webbrowser.open_new(self.get_value())
    

class QtopiaTextField(QtopiaField, TextField):
  y_flags = 1
  def __init__(self, gui, master, o, attr, undo_stack):
    self.q = qt.QMultiLineEdit(master.q)
    super(QtopiaTextField, self).__init__(gui, master, o, attr, undo_stack)
    
    self.q.connect(self.q, qt.SIGNAL("textChanged()"), self.validate)
    self.update()
    
  def validate(self):
    s = unicode(self.q.text())
    self.set_value(s)
    
  def update(self):
    self.updating = 1
    try:
      self.old_str = self.get_value()
      if self.q.text() != self.old_str:
        self.q.setText(self.old_str)
    finally: self.updating = 0
    
class QtopiaObjectAttributeField(QtopiaField, ObjectAttributeField):
  def __init__(self, gui, master, o, attr, undo_stack):
    self.q = qt.QHBox(master.q)
    super(QtopiaObjectAttributeField, self).__init__(gui, master, o, attr, undo_stack)
    self.q.setFrameShape (qt.QFrame.Box)
    self.q.setFrameShadow(qt.QFrame.Sunken)
    self.q.setMargin(5)
    
class Qtopia_RangeField(QtopiaField, _RangeField):
  def __init__(self, gui, master, o, attr, undo_stack, min, max, incr = 1):
    self.q = qt.QHBox(master.q)
    self.q.setSpacing(5)
    self.label  = qt.QLabel (self.q)
    self.slider = qt.QSlider(min, max, 1, 0, qt.QSlider.Horizontal, self.q)
    super(Qtopia_RangeField, self).__init__(gui, master, o, attr, undo_stack, min, max, incr)
    self.slider.connect(self.slider, qt.SIGNAL("valueChanged(int)"), self.validate)
    
  def validate(self, v):
    self.set_value(v)
    self.label.setText(str(v))
    
  def update(self):
    self.updating = 1
    try:
      v = self.get_value()
      self.slider.setValue(v)
      self.label.setText(str(v))
    finally: self.updating = 0

class Qtopia_ShortEnumField(QtopiaField, _ShortEnumField):
  def __init__(self, gui, master, o, attr, undo_stack, choices, value_2_enum = None, enum_2_value = None):
    self.q = qt.QComboBox(master.q)
    super(Qtopia_ShortEnumField, self).__init__(gui, master, o, attr, undo_stack, choices, value_2_enum, enum_2_value)
    
    for choice in self.choice_keys: self.q.insertItem(choice)
    self.update()
    self.q.connect(self.q, qt.SIGNAL("activated(int)"), self.validate)
    
  def validate(self, enum):
    i = self.q.currentItem()
    self.set_value(self.choices[self.choice_keys[i]])
    
  def update(self):
    self.updating = 1
    try:
      i = self.choice_2_index.get(self.get_value())
      if not i is None: self.q.setCurrentItem(i)
      else: self.q.setCurrentItem(-1)
    finally: self.updating = 0
    
class Qtopia_LongEnumField(QtopiaField, _LongEnumField):
  y_flags = 1
  def __init__(self, gui, master, o, attr, undo_stack, choices, value_2_enum = None, enum_2_value = None):
    self.q = qt.QListBox(master.q)
    
    super(Qtopia_LongEnumField, self).__init__(gui, master, o, attr, undo_stack, choices, value_2_enum, enum_2_value)
    
    for choice in self.choice_keys: self.q.insertItem(choice)
    
    self.update()
    self.q.connect(self.q, qt.SIGNAL("selectionChanged()"), self.validate)
    
  def validate(self):
    i = self.q.currentItem()
    if i != self.i:
      self.i = i
      enum = self.choices[self.choice_keys[i]]
      self.set_value(enum)
    
  def update(self):
    self.updating = 1
    try:
      self.q.clearSelection()
      self.i = self.choice_2_index.get(self.get_value())
      if not self.i is None:
        self.q.setSelected(self.i, 1)
        self.q.ensureCurrentVisible()
    finally: self.updating = 0

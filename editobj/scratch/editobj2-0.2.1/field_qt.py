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

class QtField(MultiGUIField):
  y_flags = 0

class QtEntryField(QtField, EntryField, qt.QLineEdit):
  def __init__(self, gui, master, o, attr, undo_stack):
    qt.QLineEdit.__init__(self, master)
    super(QtEntryField, self).__init__(gui, master, o, attr, undo_stack)
    
    self.update()
    self.connect(self, qt.SIGNAL("lostFocus()"    ), self.validate)
    self.connect(self, qt.SIGNAL("returnPressed()"), self.validate)
    
  def validate(self):
    s = unicode(self.text())#.decode("utf-8")
    if s != self.old_str:
      self.old_str = s
      self.set_value(s)
      
  def update(self):
    self.updating = 1
    try:
      self.old_str = self.get_value()
      self.setText(self.old_str)
    finally: self.updating = 0
    
    
class QtIntField   (QtEntryField, IntField): pass # XXX no "spin-button" since they don't allow entering e.g. "1 + 2" as an integer !
class QtFloatField (QtEntryField, FloatField): pass
class QtStringField(QtEntryField, StringField): pass



class QtPasswordField(QtStringField, PasswordField):
  def __init__(self, gui, master, o, attr, undo_stack):
    QtStringField.__init__(self, gui, master, o, attr, undo_stack)
    self.setEchoMode(qt.QLineEdit.Password)
  

class QtBoolField(QtField, BoolField, qt.QCheckBox):
  def __init__(self, gui, master, o, attr, undo_stack):
    qt.QCheckBox.__init__(self, "         ", master)
    super(QtBoolField, self).__init__(gui, master, o, attr, undo_stack)
    
    self.update()
    self.connect(self, qt.SIGNAL("stateChanged(int)"), self.validate)
    
  def validate(self, state):
    v = self.descr.get(self.o, self.attr)
    if   state == 1: self.setTristate(0)
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
        self.setTristate(1)
        self.setNoChange()
      else:
        self.setChecked(v)
    finally: self.updating = 0
      

class QtProgressBarField(QtField, ProgressBarField, qt.QProgressBar):
  def __init__(self, gui, master, o, attr, undo_stack):
    qt.QProgressBar.__init__(self, master)
    super(ProgressBarField, self).__init__(gui, master, o, attr, undo_stack)
    self.update()
    
  def update(self):
    v = self.get_value()
    if v is introsp.NonConsistent: self.setTotalSteps(0)
    else:                          self.setProgress(int(v * 100), 100)
    

class QtEditButtonField(QtField, EditButtonField, qt.QPushButton):
  def __init__(self, gui, master, o, attr, undo_stack):
    qt.QPushButton.__init__(self, editobj2.TRANSLATOR(u"Edit..."), master)
    super(QtEditButtonField, self).__init__(gui, master, o, attr, undo_stack)
    self.setAutoDefault(0)
    self.connect(self, qt.SIGNAL("clicked()"), self.on_click)
    self.update()
    
  def update(self):
    self.setEnabled(not self.get_value() is None)
    
    
class QtWithButtonStringField(QtField, WithButtonStringField, qt.QHBox):
  def __init__(self, gui, master, o, attr, undo_stack):
    qt.QHBox.__init__(self, master)
    super(QtWithButtonStringField, self).__init__(gui, master, o, attr, undo_stack)
    button = qt.QPushButton(editobj2.TRANSLATOR(self.button_text), self)
    button.setAutoDefault(0)
    button.connect(button, qt.SIGNAL("clicked()"), self.on_button)
    
class QtFilenameField(QtWithButtonStringField, FilenameField):
  def on_button(self):
    filename = qt.QFileDialog.getSaveFileName(self.get_value(), "", self)
    if filename:
      filename = unicode(filename)
      self.string_field.set_value(filename)
      self.string_field.update()
      
class QtDirnameField(QtWithButtonStringField, DirnameField):
  def on_button(self):
    filename = qt.QFileDialog.getExistingDirectory(self.get_value(), self)
    if filename:
      filename = unicode(filename)
      self.string_field.set_value(filename)
      self.string_field.update()
      
class QtURLField(QtWithButtonStringField, URLField):
  def on_button(self):
    import webbrowser
    webbrowser.open_new(self.get_value())
    

class QtTextField(QtField, TextField, qt.QTextEdit):
  y_flags = 1
  def __init__(self, gui, master, o, attr, undo_stack):
    qt.QTextEdit.__init__(self, master)
    super(QtTextField, self).__init__(gui, master, o, attr, undo_stack)
    self.setTextFormat(qt.QTextEdit.PlainText)
    
    self.connect(self, qt.SIGNAL("textChanged()"), self.validate)
    self.update()
    
  def validate(self):
    s = unicode(self.text())
    self.set_value(s)
    
  def update(self):
    self.updating = 1
    try:
      self.old_str = self.get_value()
      if self.text() != self.old_str:
        self.setText(self.old_str)
    finally: self.updating = 0
      
class QtObjectAttributeField(QtField, ObjectAttributeField, qt.QHBox):
  def __init__(self, gui, master, o, attr, undo_stack):
    qt.QHBox.__init__(self, master)
    super(QtObjectAttributeField, self).__init__(gui, master, o, attr, undo_stack)
    self.setFrameShape (qt.QFrame.LineEditPanel)
    self.setFrameShadow(qt.QFrame.Sunken)
    self.setMargin(5)

# class QtObjectHEditorField(QtField, ObjectHEditorField, qt.Frame):
#   def __init__(self, gui, master, o, attr, undo_stack):
#     super(QtObjectHEditorField, self).__init__(gui, master, o, attr, undo_stack)
#     qt.Frame.__init__(self)
#     self.set_shadow_type(qt.SHADOW_IN)
#     self.add(self.editor_pane)

# class QtObjectVEditorField(QtField, ObjectVEditorField, qt.Frame):
#   def __init__(self, gui, master, o, attr, undo_stack):
#     super(QtObjectVEditorField, self).__init__(gui, master, o, attr, undo_stack)
#     qt.Frame.__init__(self)
#     self.set_shadow_type(qt.SHADOW_IN)
#     self.add(self.editor_pane)


class Qt_RangeField(QtField, _RangeField, qt.QHBox):
  def __init__(self, gui, master, o, attr, undo_stack, min, max, incr = 1):
    qt.QHBox.__init__(self, master)
    self.setSpacing(5)
    self.label  = qt.QLabel (self)
    self.slider = qt.QSlider(min, max, 1, 0, qt.QSlider.Horizontal, self)
    super(Qt_RangeField, self).__init__(gui, master, o, attr, undo_stack, min, max, incr)
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

class Qt_ShortEnumField(QtField, _ShortEnumField, qt.QComboBox):
  def __init__(self, gui, master, o, attr, undo_stack, choices, value_2_enum = None, enum_2_value = None):
    qt.QComboBox.__init__(self, master)
    super(Qt_ShortEnumField, self).__init__(gui, master, o, attr, undo_stack, choices, value_2_enum, enum_2_value)
    
    for choice in self.choice_keys: self.insertItem(choice)
    self.update()
    self.connect(self, qt.SIGNAL("activated(int)"), self.validate)
    
  def validate(self, enum):
    i = self.currentItem()
    self.set_value(self.choices[self.choice_keys[i]])
    
  def update(self):
    self.updating = 1
    try:
      i = self.choice_2_index.get(self.get_value())
      if not i is None: self.setCurrentItem(i)
      else: self.setCurrentItem(-1)
    finally: self.updating = 0
    
class Qt_LongEnumField(QtField, _LongEnumField, qt.QListBox):
  y_flags = 1
  def __init__(self, gui, master, o, attr, undo_stack, choices, value_2_enum = None, enum_2_value = None):
    qt.QListBox.__init__(self, master)
    
    super(Qt_LongEnumField, self).__init__(gui, master, o, attr, undo_stack, choices, value_2_enum, enum_2_value)
    
    for choice in self.choice_keys: self.insertItem(choice)
    
    self.update()
    self.connect(self, qt.SIGNAL("selectionChanged()"), self.validate)
    
  def validate(self):
    i = self.currentItem()
    if i != self.i:
      self.i = i
      enum = self.choices[self.choice_keys[i]]
      self.set_value(enum)
      
  def update(self):
    self.updating = 1
    try:
      self.clearSelection()
      self.i = self.choice_2_index.get(self.get_value())
      if not self.i is None:
        self.setSelected(self.i, 1)
        self.ensureCurrentVisible()
    finally: self.updating = 0

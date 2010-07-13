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


import unittest

import editobj2.introsp as introsp
import editobj2.observe as observe


class IntrospTest(object):
  def __init__(self):
    self.a = 0
    self.x = 0
    self.y = 0
    self.z = 0

  def get_x(self): return self.x
  def set_x(self, x): self.x = x

  def getY(self): return self.y
  def setY(self, y): self.y = y

  def set_z(self, z): self.z = z

  def set_b(self, b): pass
  b = property(None, set_b)
  
  def get_c(self): return 1
  

class TestIntrosp(unittest.TestCase):
  def setUp(self):
    pass
    
  def test_getset_1(self):
    d = introsp.description(IntrospTest)
    assert set(d.attributes.keys()) == set(["b", "c", "x", "y", "z"])
    assert d.attributes["b"].getter is None
    assert d.attributes["b"].setter is not None
    assert d.attributes["c"].getter == "get_c"
    assert d.attributes["c"].setter is not None
    assert d.attributes["x"].getter == "get_x"
    assert d.attributes["x"].setter == "set_x"
    assert d.attributes["y"].getter == "getY"
    assert d.attributes["y"].setter == "setY"
    assert d.attributes["z"].getter is not None
    assert d.attributes["z"].setter == "set_z"
    
  def test_getset_2(self):
    d = introsp.description(IntrospTest)
    i = IntrospTest()
    assert d.attrs_of(i) == set(['a', 'c', 'b', 'y', 'x', 'z'])
    

class C(object):
  pass

class TestObserve(unittest.TestCase):
  def setUp(self):
    self.listened = None
    
  def listener(self, *args): self.listened = args
  
  def test_object_1(self):
    c = C()
    observe.observe(c, self.listener)
    observe.scan()
    assert not self.listened
    c.x = 1
    observe.scan()
    assert self.listened == (c, object, {"x" : 1}, {})
  
  def test_object_2(self):
    c = C()
    observe.observe(c, self.listener)
    observe.scan()
    assert not self.listened
    c.x = 1
    c.y = "e"
    observe.scan()
    assert self.listened == (c, object, {"x" : 1, "y" : "e"}, {})
    
    
  def test_list_1(self):
    c = [0]
    observe.observe(c, self.listener)
    observe.scan()
    assert not self.listened
    c.append(1)
    observe.scan()
    assert self.listened == (c, list, [0, 1], [0])
    c.remove(0)
    observe.scan()
    assert self.listened == (c, list, [1], [0, 1])
    
    
  def test_set_1(self):
    c = set([0])
    observe.observe(c, self.listener)
    observe.scan()
    assert not self.listened
    c.add(1)
    observe.scan()
    assert self.listened == (c, set, set([0, 1]), set([0]))
    c.remove(0)
    observe.scan()
    assert self.listened == (c, set, set([1]), set([0, 1]))
    
   
  def test_tree_1(self):
    c  = C()
    c2 = C()
    c.l = [c2]
    observe.observe_tree(c, self.listener)
    assert observe.isobserved(c)
    assert observe.isobserved(c2)
    observe.unobserve_tree(c, self.listener)
    assert not observe.isobserved(c)
    assert not observe.isobserved(c2)
    
  def test_tree_2(self):
    c  = C()
    c2 = C()
    c.l = (1, 2, c2)
    observe.observe_tree(c, self.listener)
    assert observe.isobserved(c)
    assert observe.isobserved(c2)
    c.l = 1
    observe.scan()
    assert observe.isobserved(c)
    assert not observe.isobserved(c2)
    
    observe.unobserve_tree(c, self.listener)
    assert not observe.isobserved(c)
    assert not observe.isobserved(c2)
    
  def test_tree_3(self):
    c  = C()
    c2 = C()
    c.l = set([1, 2, c2])
    observe.observe_tree(c, self.listener)
    assert observe.isobserved(c)
    assert observe.isobserved(c2)
    
    observe.unobserve_tree(c, self.listener)
    assert not observe.isobserved(c)
    assert not observe.isobserved(c2)
    
  def test_tree_4(self):
    c  = C()
    c2 = C()
    c.l = []
    observe.observe_tree(c, self.listener)
    c.l.append(c2)
    observe.scan()
    assert observe.isobserved(c)
    assert observe.isobserved(c2)
    c.l.remove(c2)
    observe.scan()
    assert observe.isobserved(c)
    assert not observe.isobserved(c2)
    
    observe.unobserve_tree(c, self.listener)
    assert not observe.isobserved(c)
    assert not observe.isobserved(c2)
    
  def test_tree_5(self):
    c  = C()
    c2 = C()
    c .c = c2
    c2.c = c
    observe.observe_tree(c, self.listener)
    assert observe.isobserved(c)
    assert observe.isobserved(c2)
    
    observe.unobserve_tree(c, self.listener)
    assert not observe.isobserved(c)
    assert not observe.isobserved(c2)
        
#   def test_tree_6(self):
#     c  = C()
#     c2 = C()
#     c3 = C()
#     c.l = [c2, c3]
#     observe.observe_tree(c, self.listener)
#     assert observe.isobserved(c)
#     assert observe.isobserved(c2)
#     assert observe.isobserved(c3)
    
#     observe.unobserve_tree(c, self.listener)
#     assert not observe.isobserved(c)
#     assert not observe.isobserved(c2)

    





if __name__ == '__main__': unittest.main()

  

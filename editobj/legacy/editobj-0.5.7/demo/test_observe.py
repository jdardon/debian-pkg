# Unit test module for observe.py

import unittest

import editobj.observe as observe

class ObserveTestCase1(unittest.TestCase):
  def test_diffdict(self):
    def test(new, old, diff):
      result = observe.diffdict(new, old)
      if result != diff:
        self.fail("observe.diffdict(%s, %s) = %s,\nshould be %s" % (new, old, result, diff))      
        
    test({}, {}, [])
    test({"1" : 1, "2" : 2}, {"1" : 1, "2" : 2}, [])
    test({"1" : 1, "2" : 2}, {"1" : 1}, [("2", 2, None)])
    test({"1" : 1}, {"1" : 1, "2" : 2}, [("2", None, 2)])
    test({"1" : 2}, {"1" : 1}, [("1", 2, 1)])
    
  def test_observe_list(self):
    observed = []
    def f(object, type, new, old): observed.append((object, type, new, old))
    def check_observed(expected):
      observe.scan()
      if observed != expected:
        self.fail("observed %s\nshould be %s" % (observed, expected))
      for i in range(len(observed)): del observed[0]
      
    l = [0]
    observe.observe(l, f)
    
    if not observe.isobserved(l, f): self.fail("isobserved() is wrong")
    
    ol = l[:]; l.append(1); check_observed([(l, list, l, ol)])
    ol = l[:]; del l[1];    check_observed([(l, list, l, ol)])
    ol = l[:]; l[0] = 3;    check_observed([(l, list, l, ol)])
    
    observe.unobserve(l, f)
    l[0] = 1
    check_observed([])
    if observe.isobserved(l, f): self.fail("isobserved() is wrong")
    
  def test_observe_dict(self):
    observed = []
    def f(object, type, new, old): observed.append((object, type, new, old))
    def check_observed(expected):
      observe.scan()
      if observed != expected:
        self.fail("observed %s\nshould be %s" % (observed, expected))
      for i in range(len(observed)): del observed[0]
      
    d = {"a" : 1}
    observe.observe(d, f)
    if not observe.isobserved(d, f): self.fail("isobserved() is wrong")
    
    od = d.copy(); d["b"] = 2; check_observed([(d, dict, d, od)])
    od = d.copy(); d["a"] = 3; check_observed([(d, dict, d, od)])
    od = d.copy(); del d["b"]; check_observed([(d, dict, d, od)])
    
    observe.unobserve(d, f)
    d["c"] = 4; check_observed([])
    if observe.isobserved(d, f): self.fail("isobserved() is wrong")
    
  def test_observe_object(self):
    observed = []
    def f(object, type, new, old): observed.append((object, type, new, old))
    def check_observed(expected):
      observe.scan()
      if observed != expected:
        self.fail("observed %s\nshould be %s" % (observed, expected))
      for i in range(len(observed)): del observed[0]
      
    class O: pass
    class P: pass
    o = O()
    o.x = 1
    observe.observe(o, f)
    if not observe.isobserved(o, f): self.fail("isobserved() is wrong")
    
    old = o.__dict__.copy(); o.y = 2; check_observed([(o, object, o.__dict__, old)])
    old = o.__dict__.copy(); del o.x; check_observed([(o, object, o.__dict__, old)])
    old = o.__dict__.copy(); o.y = 3; check_observed([(o, object, o.__dict__, old)])
    
    o.__class__ = P; check_observed([(o, "__class__", P, O)])
    
    observe.unobserve(o, f)
    o.z = 4; check_observed([])
    if observe.isobserved(o, f): self.fail("isobserved() is wrong")
    
  def test_observe_tree(self):
    observed = []
    def f(object, type, new, old): observed.append((object, type, new, old))
    def check_observed(expected):
      observe.scan()
      if observed != expected:
        self.fail("observed %s\nshould be %s" % (observed, expected))
      for i in range(len(observed)): del observed[0]
      
    class O: pass
    o = O()
    
    l = [0]
    observe.observe_tree(l, f)
    
    if not observe.isobserved(l, f): self.fail("isobserved() is wrong")
    
    l2 = []
    
    old = l[:]; l.append(l2); check_observed([(l, list, l, old)])
    if not observe.isobserved(l2, f): self.fail("items added to the tree should be observed")
    old = l[:]; del l[0]; check_observed([(l, list, l, old)])
    
    old = l2[:]; l2.append(1); check_observed([(l2, list, l2, old)])
    old = l2[:]; l2.append(o); check_observed([(l2, list, l2, old)])
    
    old = o.__dict__.copy(); o.x = 1; check_observed([(o, object, o.__dict__, old)])
    
    old = l[:]; l.remove(l2); check_observed([(l, list, l, old)])
    l2.append(2); check_observed([])
    
    observe.unobserve_tree(l, f)
    l.append(3); check_observed([])
    if observe.isobserved(l, f): self.fail("isobserved() is wrong")
    
if __name__ == '__main__':
  unittest.main()
  

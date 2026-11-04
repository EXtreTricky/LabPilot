import unittest,os,tempfile
from pathlib import Path
from src.my_tool.core.rules import recommend,risk_hint
from src.my_tool import main
class TestRules(unittest.TestCase):
 def test_recommend(self):
  rooms=[{'id':1,'name':'A','capacity':20,'status':'available','tags':'Python,开发'},{'id':2,'name':'B','capacity':5,'status':'available','tags':'开发'}]
  self.assertEqual(recommend(rooms,'开发',10)[0]['id'],1)
 def test_risk(self):
  self.assertEqual(risk_hint('插座冒烟')['level'],'高')
  self.assertTrue(risk_hint('普通巡查')['human_review_required'])
class TestMvp(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();main.DB=Path(self.temp.name)/'test.db';main.setup()
 def tearDown(self):self.temp.cleanup()
 def test_booking_and_conflict(self):
  p={'room_id':1,'applicant':'学生A','day':'2026-12-01','period':'上午','purpose':'编程','participants':12}
  code,r=main.process('POST','/api/bookings',p);self.assertEqual(code,201)
  self.assertEqual(main.process('POST','/api/bookings',p)[0],409)
  self.assertEqual(main.process('POST',f"/api/bookings/{r['id']}/approve",{})[0],200)
 def test_inspection(self):
  status,result=main.process('POST','/api/inspections',{'room_id':1,'description':'设备漏电'})
  self.assertEqual(status,201);self.assertEqual(result['level'],'高')
if __name__=='__main__':unittest.main()

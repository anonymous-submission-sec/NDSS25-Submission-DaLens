#! /usr/bin/env python3

import unittest

from StatusTracker import StatusTracker
class TestStatusTracker(unittest.TestCase):

  def test1(self):
    tracker = StatusTracker(
      {"expected_status": "NOERROR"}, 
      3, 
      StatusTracker.wait_policy_if_expected, 
      StatusTracker.abort_policy_n_timeout_no_success)
    
    self.assertTrue(tracker.should_wait({"status": "NOERROR"}))
    self.assertFalse(tracker.should_wait({"status": "NXDOMAIN"}))

    self.assertFalse(tracker.should_abort({"status": "TIMEOUT"}))
    self.assertFalse(tracker.should_abort({"status": "TIMEOUT"}))
    self.assertTrue(tracker.should_abort({"status": "TIMEOUT"}))
    #self.assertTrue(tracker.should_abort({"status": "NOERROR"}))
  
  def test2(self):
    tracker = StatusTracker(
      {"expected_status": "NOERROR"}, 
      3, 
      StatusTracker.wait_policy_if_expected, 
      StatusTracker.abort_policy_n_timeout_no_success)
    
    self.assertTrue(tracker.should_wait({"status": "NOERROR"}))
    self.assertFalse(tracker.should_wait({"status": "NXDOMAIN"}))
    
    self.assertFalse(tracker.should_abort({"status": "NOERROR"}))
    self.assertFalse(tracker.should_abort({"status": "TIMEOUT"}))
    self.assertFalse(tracker.should_abort({"status": "TIMEOUT"}))
    self.assertFalse(tracker.should_abort({"status": "TIMEOUT"}))
    self.assertFalse(tracker.should_abort({"status": "TIMEOUT"}))

  def test3(self):
      tracker = StatusTracker(
          {"expected_status": "NOERROR"}, 
          3, 
          StatusTracker.wait_policy_always_wait, 
          StatusTracker.abort_policy_never_abort)
      
      self.assertTrue(tracker.should_wait({"status": "NOERROR"}))
      self.assertTrue(tracker.should_wait({"status": "NXDOMAIN"}))
      self.assertTrue(tracker.should_wait({"status": "TIMEOUT"}))

      self.assertFalse(tracker.should_abort({"status": "TIMEOUT"}))
      self.assertFalse(tracker.should_abort({"status": "TIMEOUT"}))
      self.assertFalse(tracker.should_abort({"status": "TIMEOUT"}))
      self.assertFalse(tracker.should_abort({"status": "TIMEOUT"}))
      self.assertFalse(tracker.should_abort({"status": "NOERROR"}))
      self.assertFalse(tracker.should_abort({"status": "NXDOMAIN"}))
  
  def test4(self):
      tracker = StatusTracker(
          {"expected_status": "NOERROR"}, 
          3, 
          StatusTracker.wait_policy_if_online, 
          StatusTracker.abort_policy_n_timeout_no_success)
      
      self.assertFalse(tracker.should_wait({"status": "TIMEOUT"}))
      self.assertTrue(tracker.should_wait({"status": "NXDOMAIN"}))
        
if __name__ == '__main__':
    unittest.main()


#!/usr/bin/env python3

class StatusTracker:

    """ Tracks the status of a measurement run. Decides whether to wait or abort based on the supplied policies."""
    def __init__(self, querytask, n, wait_policy:str, abort_policy:str):

        # Retrieve expected status 
        self.expected_status = querytask['expected_status']

        # Check that the supplied policies actually exist
        assert hasattr(self, wait_policy), f"Wait policy {wait_policy} is not implemented"
        assert hasattr(self, abort_policy), f"Abort policy {abort_policy} is not implemented"
        assert callable(getattr(self, wait_policy)), "Wait policy must be a function"
        assert callable(getattr(self, abort_policy)), "Abort policy must be a function"
        
        #self.abort_policy = getattr(self, abort_policy)
        self.abort_policy = self.__getattribute__(abort_policy)
        #self.wait_policy = getattr(self, wait_policy)
        self.wait_policy = self.__getattribute__(wait_policy)

        # Set thresholds
        self.MAX_FAILS = n
        
        # Initialize counters 
        self.num_successes = 0
        self.num_fails = 0

    # TODO: percentage based abort policies (e.g. based on planned number of queries)

    """ Function that takes the response of a query and decides whether to wait based on internal status"""
    def should_wait(self, response):
        return self.wait_policy(response)

    """ Wait policy function that returns true if the resolver is considered online""" 
    def wait_policy_if_online(self, response):
        considered_online = ["NOERROR", "NXDOMAIN", "SRVFAIL", "NOANSWER", "REFUSED"]
        return response['status'] in considered_online
    
    """ Wait policy function that returns true if the response status matches the expected one""" 
    def wait_policy_if_expected(self, response):
        return response['status'] == self.expected_status
    
    """ Wait policy function that always says to wait"""
    def wait_policy_always_wait(self, response):
        return True

    """ Function that takes the response of a query and decides whether to abort based on internal status"""
    def should_abort(self, response):
        return self.abort_policy(response)

    """ Polciy function that aborts if n timeouts are encountered without every having a success. """
    def abort_policy_n_timeout_no_success(self, response):
        if response['status'] == "TIMEOUT":
            self.num_fails += 1
        else:
            self.num_successes += 1

        return self.num_successes == 0 and self.num_fails >= self.MAX_FAILS 
    
    """ Polciy function that never aborts.""""" 
    def abort_policy_never_abort(self, response):
        return False
        
    """ Polciy function that aborts if n timeouts are encountered."""
    def policy_n_timeout(self, response):
        if response['status'] == "TIMEOUT":
            self.num_fails += 1
        else:
            self.num_successes += 1
        
        return self.num_fails >= self.MAX_FAILS
    
    """ Policy function that aborts if n *consecutive* timeouts are encountered."""
    def policy_n_timeout_consecutive(self, response):
        if response['status'] == "TIMEOUT":
            self.num_timeouts += 1
        else:
            self.num_fails = 0
            self.num_successes += 1
        return self.num_fails >= self.MAX_FAILS
    
    """ Policy function that aborts if n *consecutive* status codes that don't match the expected one are encountered."""
    def abort_policy_n_not_expected(self, response):
        if response['status'] != self.expected_status:
            self.num_fails += 1
        else:
            self.num_successes += 1
        return self.num_fails >= self.MAX_FAILS

    """ Policy function that aborts if n *consecutive* status codes that don't match the expected one are encountered, but only if no success has been encountered."""
    def abort_policy_n_not_expected_no_success(self, response):
        if response['status'] != self.expected_status:
            self.num_fails += 1
        else:
            self.num_successes += 1
        return self.num_fails >= self.MAX_FAILS and self.num_successes == 0
        
#! /usr/bin/env python3

# Functions in this file operate on the basic combined single querytask result dictionary


#from datetime import datetime
import datetime
from lib.ZoneConf import ZoneConf
from statistics import median


def print_timeout_stats(l:list):
  for i, d in enumerate(l, 1):
    print(f"Measurement {i}: ", end=' ')
    d.print_timeout_stats()

def print_measurement_stats(l:list):
  for i, d in enumerate(l, 1):
    print(f"Measurement {i}: ", end=' ')
    d.print_measurement_stats()



class BasicMeasurement:

  def __init__(self, d:dict, zoneconf=None):


    def parse_ts(s:str):
      try:
        return datetime.datetime.strptime(s.strip(), '%Y-%m-%d %H:%M:%S.%f')
      except ValueError:
        return datetime.datetime.strptime(s.strip(), '%Y-%m-%d %H:%M:%S')

    # Cast timestamps to datetime
    for r in d['responses']:
      if isinstance(r['timestamp'], str):
        r['timestamp'] = parse_ts(r['timestamp'])
      if isinstance(r['timestamp_sent'], str):
        r['timestamp_sent'] = parse_ts(r['timestamp_sent'])
      assert r['timestamp_sent'] <= r['timestamp'], "Response timestamp is before sent timestamp"
    # Assert responses are sorted by timestamp
    for i in range(len(d['responses']) - 1):
      assert d['responses'][i]['timestamp'] <= d['responses'][i+1]['timestamp'], "Responses are not sorted by timestamp"
    
    # Cast log entry timestamps to datetime
    if 'logentries' in d.keys():
      for l in d['logentries']:
        if isinstance(l['timestamp'], str):
          l['timestamp'] = datetime.datetime.strptime(l['timestamp'].strip(), '%d-%b-%Y %H:%M:%S.%f')

      # Sort log entries by timestamp
      d['logentries'].sort(key=lambda x: x['timestamp'])

    # Store data
    self.d = d
    # If data contains nameserver configuration, prefer it over separately specified config
    if 'nameservers' in d.keys():
      self.zoneconf = ZoneConf(self.d['nameservers'])
      del self.d['nameservers']
    else:
      self.zoneconf = zoneconf


# =========================
#   Getter Functions
# =========================
  """ Return name of the pattern used for this measurement""" 
  def get_pattern_name(self) -> str:
    return self.d['pattern']
  
  """ Returns a list of logentries associated with this measurement"""  
  def get_logentries(self, qname:str=None) -> list:
    if qname is None:
      return self.d['logentries']
    else:
      return [l for l in self.d['logentries'] if l['query'] == qname]
  
  """ Returns a list of timestamps of logentries associated with this measurement""" 
  def get_logentry_timestamps(self, qname:str=None) -> list:
    if qname is None:
      ts = [l['time'] for l in self.d['logentries']]
    else:
      ts = [l['time'] for l in self.d['logentries'] if l['query'] == qname]
    return ts
  
  """ Returns a list of unique query names associated with this measurement"""
  def get_qnames(self) -> list:
     # Server qnames are a subset of client qnames
     return set([r['name'] for r in self.d['responses']])

  """ Get a list of all egress resolvers observed in the measurement"""
  def get_egress_ips(self) -> list:
    return [i['ip'] for i in self.d['logentries']]

  """ Get a list of unique egress resolvers observed in the measurement"""
  def get_unique_egress_ips(self) -> list:
    #return list(set([i['ip'] for i in self.d['logentries']]))
    return list(set(self.get_egress_ips()))

  """ Get list of unique resolver tested in this measurement"""
  def get_resolvers(self):
    #server_ns =  set([e['ns'] for e in self.d['logentries']])
    client_ns = set([e['resolver'] for e in self.d['responses']])
    # Case of all timeouts / no query to auth nameserver simply use client-recording
    # The following condition is not valid: if two nameservers with dependency are involved, it might be expected that there are no log entries for one of them
    #if self.has_logentries():
    #  # Make sure decoded ingress resolver matches ingress resolver recorded by client
    #  assert client_ns == server_ns, "Measurement disagrees on nameservers under test"
    return list(client_ns)
  
  """ Get single unique resolver tested in this measurement"""
  def get_resolver(self):
    ns = self.get_resolvers()
    assert len(ns) == 1, "get_resolver requires that only one nameserver is measured within the BasicMeasurement"
    return ns[0]

  """ Get single unique vantagepoint used in this measurement"""
  def get_vantagepoint(self):
    vps = list(set([q['vp'] for q in self.d['queries']]))
    assert len(vps) == 1, "Basic Measurement corrupted: a Basic Measurement should only ever have one vantage point"
    return vps[0]

  """ Compute upper bound of measurement runtime in seconds"""
  def get_max_runtime(self):
    return sum([(q['wait'] + q['timeout']) * q['repeat'] + q['wait_after'] for q in self.d['queries']])

  """ Return timedelta between first sent query and first log entry. Add to log timestamps or subtract from query timestamps to align them"""
  def get_ts_delta(self):
    if len(self.d['logentries']) == 0 or len(self.d['responses']) == 0:
      return None
    first_sent = self.d['responses'][0]['timestamp_sent']
    first_log = self.d['logentries'][0]['timestamp']
    #assert first_sent >= first_log, "Corrupted measurement: logentry only carries time, no year, and should hence be before first query"
    return first_sent - first_log

# =========================
#   Status functions
# =========================
  """ Returns list of all response status codes"""
  def get_status_codes(self) -> list:
    return [r['status'] for r in self.d['responses']]

  """ Returns True if all responses have status code 'status'""" 
  def check_status_all(self, status:str) -> bool:
    assert status in ["NOERROR","TIMEOUT","NXDOMAIN","NOANSWER","REFUSED","SRVFAIL"], "Invalid status code"
    return all([r['status'] == status for r in self.d['responses']])
  
  """ Returns True if any response has status code 'status'""" 
  def check_status_any(self, status:str) -> bool:
    assert status in ["NOERROR","TIMEOUT","NXDOMAIN","NOANSWER","REFUSED","SRVFAIL"], "Invalid status code"
    return any([r['status'] == status for r in self.d['responses']])

  """ Returns number of responses with status code 'status'""" 
  def num_status(self, status:str) -> int:
    assert status in ["NOERROR","TIMEOUT","NXDOMAIN","NOANSWER","REFUSED","SRVFAIL"], "Invalid status code"
    return len([r for r in self.d['responses'] if r['status'] == status])
  
  """ Check if all client responses are timeouts"""
  def is_offline(self) -> bool:
    return all([r['status'] == "TIMEOUT" for r in self.d['responses']])

  """ Check that ANY responses have status other than TIMEOUT"""
  def is_online(self) -> bool:
    #if 'max_timeouts' not in self.d.keys(): # older data
    #  MAX_TIMEOUTS = self.d['max_timeouts']
    #else: # newer data
    #  MAX_TIMEOUTS = self.d['settings']['max_timeouts']
    
    # Check that more queries than the minimum were sent
    # BUG: this condition does not hold if less queries were planned than the maximum number of tolerated failures
    #c1 = int(self.d['num_queries_sent']) > int(MAX_TIMEOUTS)
    # Check that ANY responses have status other than TIMEOUT
    c2 = any([r['status'] in ["NOERROR","SRVFAIL","REFUSED","NOANSWER","NXDOMAIN"] for r in self.d['responses']])
    #return c1 and c2
    return c2

  """ Returns number of queries that were planned in this measurement"""
  def num_queries_planned(self) -> int:
    return sum([int(q['repeat']) for q in self.d['queries']])
    
  """ Returns number of queries that were actually sent in this measurement"""
  def num_queries_sent(self) -> int:
    return len(self.d['responses'])

  """ Returns True if number of actually sent queries equals number of planned queries"""
  def result_complete(self) -> bool:
    # Check that effectively sent queries equal number of planned queries
    return self.num_queries_planned() == self.num_queries_sent()

  """ Returns True if less queries than planned were sent"""
  def result_partial(self) -> bool:
    return self.num_queries_sent() < self.num_queries_planned() 

  """ Returns True if any logentries were found for the measurement"""
  def has_logentries(self) -> bool:
    # Check if any associated log entries have been found
    return len(self.d['logentries']) > 0
  
  """ Return number of logentries found in this measurement""" 
  def num_logentries(self) -> int:
    return len(self.d['logentries'])


# ===========================
#   Print / Trace functions
# ===========================
  
  def print_timeout_stats(self):
    loc = [i for i, r in enumerate(self.d['responses'], start=1) if r['status'] == "TIMEOUT"]
    if len(loc) > 10:
      p_loc = loc[0:20]
      print(f"{len(loc)} timeouts, {100 * len(loc) / len(self.d['responses'])} % of {len(self.d['responses'])} total responses, Locations: {str(p_loc)[0:-1]}, ...]")
    else:
      print(f"Timeouts: {loc}, {100 * len(loc) / len(self.d['responses'])} %, total responses: {len(self.d['responses'])}")

  def print_measurement_stats(self):
    names = set([a['name'] for a in self.d['responses'] if a['status'] != "FAIL"])
    num_timeouts = len([a for a in self.d['responses'] if a['status'] == "TIMEOUT"])
    unique_ips = set(l['ip'] for l in self.d['logentries'])
    num_queries_sent = self.d['num_queries_sent']
    print(f"queries: {num_queries_sent}\t timeouts: {num_timeouts}\t logentries: {len(self.d['logentries'])}\t\t egressIPs: {len(unique_ips)}")

# ======================
#   Decision functions
# ======================
  
 # """Check conditions satisfied for 'is_single'"""
 # def cs_is_single(self) -> bool:
 #   conditions = []
 #   conditions += [len(self.get_resolvers()) == 1] # only one nameserver involved in this measurement
 #   conditions += [self.has_logentries()] # measurement produced log entries
 #   return all(conditions)
 #   
 # """ Takes a standard measurement result dict and decides whether the measured resolver is a single machine or a resolver system.
 # Requieres that the resolver produced log entries!"""
 # def is_single(self) -> bool:
 #   assert self.cs_is_single(), "Conditions for 'single_resolver' not satisfied"
 #   
 #   # Check that all recorded egress resolver IPs in the server log are identical
 #   all_egress_identical = len(self.get_unique_egress_ips()) == 1

 #   # Check that the single ingress IP matches the unique egress IP
 #   ingress_egress_match = self.get_resolver() == self.d['logentries'][0]['ip']

 #   return all_egress_identical and ingress_egress_match

 # """ Check conditions satisfied for 'loadbalancing_ip_based'"""
 # def cs_loadbalancing_ip_based(self) -> bool:
 #   conditions = []
 #   conditions += [self.cs_is_single()] # loadbalancing_ip_based uses is_single
 #   conditions += [self.has_logentries()] 
 #   return all(conditions)

 # """ Returns True if the resolver uses IP-based loadbalancing and is not a single resolver""" 
 # def loadbalancing_ip_based(self) -> bool:
 #   # Condition 1: not a single-machine resolver
 #   c1 = not self.is_single()
 #   # Condition 2: only ever one egress IP observed
 #   c2 = len(self.get_unique_egress_ips()) == 1
 #   return c1 and c2
# ======================
#   MAF Patterns
# ======================

  """ Check conditions satisfied for 'maf'"""
  def cs_maf(self) -> bool:
    conditions = []
    # Pattern Parameters
    
    # Only one query sent
    conditions += [self.d['queries'][0]['repeat'] == 1]
    conditions += [len(self.d['queries']) == 1]

    # Successful Measurement
    conditions += [self.has_logentries()]
    # No Logentries before query sent (interference with previous measurements, synchronization)
    conditions += [all([l['timestamp'] >= self.d['responses'][0]['timestamp_sent'] for l in self.d['logentries']])]
    return all(conditions)
  
  """ Debug function to print relevant information for MAF measurements"""
  def _maf_debug(self):
    sent = self.d['responses'][0]['timestamp_sent']
    received = self.d['responses'][0]['timestamp']
    
    entries_before = [l for l in self.d['logentries'] if l['timestamp'] < sent]
    print(f"Entries before Query: {len(entries_before)}")
    entries_between = [l for l in self.d['logentries'] if l['timestamp'] >= sent and l['timestamp'] <= received]
    print(f"Entries between Query and Response: {len(entries_between)}")
    entries_after = [l for l in self.d['logentries'] if l['timestamp'] > received]
    print(f"Entries after Response: {len(entries_after)}")

    # Print time delta between first and last log entry
    print(f"Entries Time Delta: {self.d['logentries'][-1]['timestamp'] - self.d['logentries'][0]['timestamp']}")
    # Print time delta between query and response
    print(f"Query-Response Time Delta: {received - sent}")
    # Print Status of Response
    print(f"Response Status: {self.d['responses'][0]['status']}")
  
  """ Returns full number of log entries in this measurement without time limit"""
  def maf_total(self) -> int:
    assert self.cs_maf(), "Conditions for 'maf' not satisfied"
    return self.num_logentries()    # Return total number of log entries

  """ Returns number of log entries in the time window between query sent and query sent plus measurement timeout.
  This is to make the results comparable."""
  def maf_within_timeout(self) -> int:
    assert self.cs_maf(), "Conditions for 'maf' not satisfied"
    
    query_sent = self.d['responses'][0]['timestamp_sent']
    timeout = self.d['queries'][0]['timeout'] # Configured timeout of the client
    window = (query_sent, query_sent + datetime.timedelta(seconds=timeout))

    # Get log entries within the time window
    entries = self.get_logentries()
    relevant = [l for l in entries if window[0] <= l['timestamp'] and l['timestamp'] <= window[1]]

    return len(relevant)
  
  def maf_within_rtt(self) -> int:
    assert self.cs_maf(), "Conditions for 'maf' not satisfied"
    
    query_sent = self.d['responses'][0]['timestamp_sent']
    ans_received = self.d['responses'][0]['timestamp']
    window = (query_sent, ans_received)

    # Get log entries within the time window
    entries = self.get_logentries()
    relevant = [l for l in entries if window[0] <= l['timestamp'] and l['timestamp'] <= window[1]]

    return len(relevant)

  """ Returns round-trip time of the measurement in seconds, i.e. time between query sent and response received.
  Returns None if the response was a TIMEOUT."""
  def maf_rtt(self) -> float:
    assert self.cs_maf(), "Conditions for 'maf' not satisfied"
    if self.d['responses'][0]['status'] == "TIMEOUT":
      return None
    query_sent = self.d['responses'][0]['timestamp_sent']
    response_received = self.d['responses'][0]['timestamp']
    return (response_received - query_sent).total_seconds()
  
  """ Returns time delta between first and last log entry in seconds. Returns None if only one log entry was observed."""
  def maf_entry_delta(self) -> float:
    #assert self.cs_maf(), "Conditions for 'maf' not satisfied"
    entries = self.get_logentries()
    if len(entries) < 2:
      return None
    # Get time delta between first and last log entry
    return (entries[-1]['timestamp'] - entries[0]['timestamp']).total_seconds()


  
# ======================
#   Enum Pattern
# ======================

  def cs_enum(self):
    conditions = []
    # Pattern Parameters
    conditions += [len(self.get_resolvers()) == 1] # only one nameserver involved in this measurement

    # Successful Measurement
    conditions = [not self.check_status_all("TIMEOUT")]   # At least one non-TIMEOUT response
    conditions += [self.has_logentries()]                 # At least one log entry
    return all(conditions)

  """ Returns True if the ingress IP is in the set of observed egress IPs."""
  def enum_matching_ip(self):
    assert self.cs_enum(), "Conditions for 'enum' not satisfied"
    
    #c1 = len(self.get_unique_egress_ips()) == 1               # Only one distinct egress IP
    #c2 = self.get_resolver() == self.d['logentries'][0]['ip'] # Ingress and Egress IP match

    # Note: the above conditions are too restrictive: 
    #   for enough repetitions, we would observe more than one egress IP from any resolver..

    c1 = self.get_resolver() in set(self.get_unique_egress_ips()) # Ingress IP is among the egress IPs
    return c1

  """ Returns True if a single distinct egress IP was observed that is different from the ingress IP.""" 
  def enum_single_different_egress(self) -> bool:
    assert self.cs_enum(), "Conditions for 'enum' not satisfied"
    c1 = len(self.get_unique_egress_ips()) == 1               # Only one distinct egress IP
    c2 = self.get_resolver() != self.d['logentries'][0]['ip'] # Ingress and Egress IP are different
    return c1 and c2
  
  def enum_num_egress(self):
    assert self.cs_enum(), "Conditions for 'enum' not satisfied"
    return len(self.get_unique_egress_ips()) # Number of unique egress IPs
  
  def enum_discovery_quot(self):
    assert self.cs_enum(), "Conditions for 'enum' not satisfied"
    discovered = self.get_unique_egress_ips()
    entries = self.num_logentries()
    return len(discovered) / entries
  
  def enum_variance(self):
    ips = self.get_egress_ips()
    # Count occurences of each IP
    counts = {ip: ips.count(ip) for ip in set(ips)}
    # Compute variance
    mean = sum(counts.values()) / len(counts)
    variance = sum([(c - mean)**2 for c in counts.values()]) / len(counts)
    return variance



# =========================
#   Honor TTL 0 Pattern
# =========================
  """ Check conditions satisfied for 'ttl0'"""
  def cs_ttl0(self) -> bool:
    conditions = []
    # Technical
    conditions += [self.has_logentries()] 
    conditions += [self.num_status("NOERROR") > 0]  # At least one NOERROR response

    # Logical
    conditions += [all([ttl == 0 for ttl in self.zoneconf.get_ttl()])]  # All TTL in Zoneconf must be zero

    return all(conditions)
  """ Debug function to print logentries and responses for TTL 0 measurements""" 
  def _ttl_debug(self):
    num_logentries = len([e for e in self.d['logentries']])
    num_noerror = len([e for e in self.d['responses'] if e['status'] == "NOERROR"])
    print(f"Num Logentries: {num_logentries}, Num NOERROR: {num_noerror}")
    for l in self.get_logentries():
      print(f"{l['query']}, {l['type']}, {l['timestamp']}, {l['ip']}")

  """ True if subsequent queries return the same TTL, i.e. the server always gives the max"""
  def ttl_constant_client_ttl(self):
    # Get all responses with status 'NOERROR'
    responses = [e for e in self.d['responses'] if e['status'] == "NOERROR"]
    # Get unique set of TTLs returned by the resolver
    returned_ttl = list(set([e['data'][0]['ttl'] for e in responses]))
    return len(returned_ttl) == 1

  """ True if all client responses with status 'NOERROR' contain TTL zero"""
  def ttl_tell_client_zero(self):
    assert self.cs_ttl0(), "Conditions for 'ttl0' not satisfied"
    # Get all responses with status 'NOERROR'
    responses = [e for e in self.d['responses'] if e['status'] == "NOERROR"]
    # Get unique set of TTLs returned by the resolver
    returned_ttl = list(set([e['data'][0]['ttl'] for e in responses]))
    # All returned TTL must be zero
    return all([int(ttl) == 0 for ttl in returned_ttl])
  
  """ Max observed TTL at the client across responses with status 'NOERROR' """
  def ttl_max_client_ttl(self):
    assert self.cs_ttl0(), "Conditions for 'ttl0' not satisfied"
    # Get all responses with status 'NOERROR'
    responses = [e for e in self.d['responses'] if e['status'] == "NOERROR"]
    returned_ttl = [int(e['data'][0]['ttl']) for e in responses if e['status'] == "NOERROR"]
    return max(returned_ttl)

  """ Client receives TTL 0 and there are *at least* as many logentries as 'NOERROR' responses"""
  def ttl_server_honors_zero(self):
    assert self.cs_ttl0(), "Conditions for 'ttl0' not satisfied"

    num_logentries = len([e for e in self.d['logentries']])
    num_noerror = len([e for e in self.d['responses'] if e['status'] == "NOERROR"])
    
    ans = None
    # All returned TTL must be zero
    if not self.ttl_tell_client_zero() or num_logentries < num_noerror:
      # If client sees TTL > 0 or log entries are fewer than NOERROR responses, the server does not honor TTL 0
      ans = False
    else: # If there are at least as many log entries as NOERROR responses:
      
      unique_ips = set([l['ip'] for l in self.d['logentries']]) # Look at number of unique egress IPs

      if len(unique_ips) == 1: # Only one egress IP observed
        ans = True
      elif len(unique_ips) > 1: # More than one egress IP observed
        logentries = [e for e in self.d['logentries']]
        # We require that the same egress IP has been observed in consecutive log entries at least once
        # This guarantees that the minTTL is smaller than the probing interval even if the resolver has an open backend
        for i in range(len(logentries)-1):
          if logentries[i]['ip'] == logentries[i+1]['ip']:
            ans = True 
            break
          ans = None
      else:
        ans =  None

    return ans

# ================
#   Qmin Pattern
# ================

  """ Check conditions satisfied for 'qmin'"""
  def cs_qmin(self) -> bool:
    conditions = []
    # Pattern Parameters
    conditions += [len(set([q['query'] for q in self.d['queries']])) == 1]  # 1 unique name queried
    conditions += [len(self.d['queries'][0]['query'].split('.')) >= 5]      # at least 5 labels in query

    # Successful Measurement
    conditions += [self.num_logentries() > 0]       # At least one log entry
    return all(conditions)
  
  """ Returns True if the resolver performs full QMIN, i.e. queries every step"""
  def qmin_full(self) -> bool:
    assert self.cs_qmin(), "Conditions for 'qmin' not satisfied"
    # Get unique QNAMEs from log entries
    log_queries = set([l['query'] for l in self.d['logentries']]) 
    # Get number of labels in the query
    max_iter = len(self.d['queries'][0]['query'].split('.')) - 2  # subtract TLD and SLD label
    return len(log_queries) == max_iter
  
  """
  Returns the number of unique queries minus 1, i.e. the number of iterations the resolver performs qmin.
  This criteria is more resilient to special policies. """ 
  def qmin_iterations(self, debug=False) -> int:
    assert self.cs_qmin(), "Conditions for 'qmin' not satisfied"
    log_queries = set([l['query'] for l in self.d['logentries']])

    if debug:
      # Print log entries
      print("Log entries:")
      entries = sorted(list(set([l['query'] for l in self.d['logentries']])))
      for l in entries:
        print(f"\t{l}")
    return len(log_queries)

# ===========================
#   TTL Line Pattern
# ===========================
  
  def cs_ttl_line(self) -> bool:
    conditions = []
    conditions += [self.num_logentries() > 1] # measurement produced log entries
    # Only one zone entry is configured
    conditions += [self.zoneconf.get_num_records() == 1]
    # At least one NOERROR response
    conditions += [self.num_status("NOERROR") > 0]
    # at least one response has a key 'data'
    conditions += [any(['data' in r.keys() for r in self.d['responses']])]
    return all(conditions)
  
  def ttl_line(self) -> bool:
    assert self.cs_ttl_line(), "Conditions for 'shared_frontend' not satisfied"
    # Delta between all log entries is at least configured TTL
    # Problem: shared frontend that performs prefetching is classified as non-shared
    deltas = self.get_server_ttl()
    ttl = self.zoneconf.get_ttl()[0]
    tolerance = 0.1 # fraction
    ttl = ttl - ttl * tolerance
    # TODO: criteria based on TTL line?
    #ttl = datetime.timedelta(seconds=self.d['zone'][0]['ttl'])
    return all([d >= ttl for d in deltas])

# ===========================
#   Shared Frontend Pattern
# ===========================
  """ Check conditions satisfied for 'shared_frontend'""" 
  def cs_shared_frontend(self) -> bool:
    conditions = []

    # Pattern Parameters
    conditions += [self.zoneconf.get_num_records() == 1]    # Only one zone entry is configured

    # Successful Measurement
    conditions += [self.num_logentries() > 0]       # measurement produced log entries
    conditions += [self.num_status("NOERROR") > 1]  # At least two NOERROR response
    # Time difference between first and last NOERROR response should be less than TTL 
    t0, t1 = self.d['responses'][0]['timestamp_sent'], self.d['responses'][-1]['timestamp']
    conditions += [(t1 - t0).seconds < self.zoneconf.get_ttl()[0] / 2]

    return all(conditions)
  """ Returns True if the resolver exhibits shared cache behavior.""" 
  def shared_frontend(self, debug=False) -> bool:
    assert self.cs_shared_frontend(), "Conditions for 'shared_frontend' not satisfied"
    
    if self.num_logentries() == 1:
      ans = True       # Exactly one entry suggests shared cache behavior
    else:
      if len(self.get_unique_egress_ips()) > 1:
        ans = False   # Multiple entries from different egress IPs suggest open backend behavior
      else:
        ans = None    # Muliple entries fron single egress IP is not clear, refrain from deciding
    
    if debug:
      # Print log entries between timestamps of first response
      r1 = self.d['responses'][0]
      first_log = [l for l in self.d['logentries'] if l['timestamp'] <= r1['timestamp'] and l['timestamp'] >= r1['timestamp_sent']]
      print("Entries on first query")
      for l in first_log:
        print(f"\t{l['query']}, {l['type']}, {l['ip']}")
      print('All Entries')
      for e in self.get_logentries():
        print(f"\t{e['query']}, {e['type']}, {e['ip']}")
      print(f"Total Entries: {len(self.d['logentries'])}")
    return ans

# =========================
#   Respects RD=0 Pattern
# =========================

  """ Check conditions satisfied for 'respects_rd_zero'"""
  def cs_rd0(self) -> bool:
    conditions = []
    
    # Pattern Parameters
    conditions += [self.zoneconf.get_num_records() == 1]                # Only one record is configured
    conditions += [all([ttl > 0 for ttl in self.zoneconf.get_ttl()])]   # Make sure the TTL in the Zone configuration was > 0
    qname = self.d['queries'][0]['query']                               # Make sure the same query name was used for all queries
    conditions += [all([q['query'] == qname for q in self.d['queries'][1:]])]
    # Make sure three sets of queries were used, with the first and the last having 'recursion_desired' set to False
    if len(self.d['queries']) != 3:
      return False
    conditions += [self.d['queries'][0]['recursion_desired'] == False]
    conditions += [self.d['queries'][1]['recursion_desired'] == True]
    conditions += [self.d['queries'][2]['recursion_desired'] == False]

    # Successful measurement
    conditions += [self.result_complete()]                                        # Measurement must be complete
    conditions += [all([r['status'] != "TIMEOUT" for r in self.d['responses']])]  # No TIMEOUT anywhere for stage separation
    conditions += [self.has_logentries()]                                         # Has log entries
    # TODO: at least one NOERROR in second stage
    return all(conditions)
  
  """ Helper function: eturns responses and log entries grouped by 3 stages of the RD=0 pattern""" 
  def _rd0_group(self):
    # Find indices of stage boundaries
    s1, s2, s3 = self.d['queries'][0]['repeat'], self.d['queries'][1]['repeat'], self.d['queries'][2]['repeat']
    assert s1 + s2 + s3 == len(self.d['responses']), "Number of responses does not match number of queries"
    # Split responses
    grouped_responses = [self.d['responses'][0:s1], self.d['responses'][s1:s1+s2], self.d['responses'][s1+s2::]]
    # get timestamp tuples of each stage
    timeframe = [(r[0]['timestamp_sent'], r[-1]['timestamp']) for r in grouped_responses]
    # Group log entries by stages
    entries = self.d['logentries']
    grouped_entries = []
    for t in timeframe:
      grouped_entries.append([l for l in entries if l['timestamp'] >= t[0] and l['timestamp'] <= t[1]])
    return grouped_responses, grouped_entries

  """ Print useful debug information for the RD=0 pattern during manual traversal of data."""
  def _rd0_debug(self):
    responses, entries = self._rd0_group()
    for i, t in enumerate(zip(responses, entries), 1):
      print(f"Stage {i}:")
      for r in t[0]:
        print(f"\t{r['status']}")
      for e in t[1]:
        print(f"\t{e['query']}, {e['type']}, {e['timestamp']}")
    print(f"Total Logentries: {len(self.d['logentries'])}")
  
  """ Returns True if the resolver answers from cache if RD=0, 
  i.e. answers appropriately despite no RD towards client and does not query auth. nameserver when no RD"""
  def rd0_answers_honors(self):
    responses, entries = self._rd0_group()
    c1 = any([r['status'] != "NOERROR" for r in responses[0]])  # At least one status not NOERROR in stage 1
    c2 = any([r['status'] == "NOERROR" for r in responses[2]])  # At least one  NOERROR in stage 3
    c3 = len(entries[0]) == 0 and len(entries[2]) == 0          # Log entries only in stage 2
    return c1 and c2 and c3
  """ Returns True if the resolver answers with NOERROR despite RD=0 being set even if the answer is not in the cache,
  i.e. the resolver does not honor RD=0 server-side and answers in any case to the client"""
  def rd0_answers_ignores(self):
    responses, entries = self._rd0_group()
    c1 = any([r['status'] == "NOERROR" for r in responses[0]])  # At least one status NOERROR in stage 1
    c2 = any([r['status'] == "NOERROR" for r in responses[2]])  # At least one status NOERROR in stage 3
    c3 = len(entries[0]) > 0                                    # Log entries in stage 1
    return c1 and c2 and c3

  """ Returns True if the resolver refuses to answer when RD=0 is set but still queries the auth. nameserver."""
  def rd0_refuses_honors(self):
    responses, entries = self._rd0_group()
    c1 = all([r['status'] != "NOERROR" for r in responses[0]])  # No NOERROR in stage 1
    c2 = all([r['status'] != "NOERROR" for r in responses[2]])  # No NOERROR in stage 3
    c3 = len(entries[0]) == 0 and len(entries[2]) == 0          # Log entries only in stage 2
    return c1 and c2 and c3

  """ Returns True if the resolver refuses to answer when RD=0 is set and does not query the auth. nameserver."""
  def rd0_refuses_ignores(self):
    responses, entries = self._rd0_group()
    c1 = all([r['status'] != "NOERROR" for r in responses[0]])  # No NOERROR in stage 1
    c2 = all([r['status'] != "NOERROR" for r in responses[2]])  # No NOERROR in stage 3
    c3 = len(entries[0]) > 0                                    # Log entries in stage 1
    return c1 and c2 and c3
  
  """ Returns True if the resolver answers despite RD=0 being set."""
  def rd0_answers(self):
    responses, entries = self._rd0_group()
    ans = any([r['status'] == "NOERROR" for r in responses[2]])  # At least one status NOERROR in stage 3
    return ans
  """ Return True if the resolver honors RD=0 server-side, i.e. does not query the auth. nameserver when RD=0 is set."""
  def rd0_honors(self):
    responses, entries = self._rd0_group()
    ans = len(entries[0]) == 0 and len(entries[2]) == 0         # Log entries only in second stage
    return ans

# =============================
#   Order Patterns
# =============================
  """ Returns a list of logentries corresponding to the 4 querysets in the querytask""" 
  def order_group_logentries(self) -> list:

    assert self.cs_order_cachebased() or self.cs_order_rd0based(), "Conditions for 'flatten' functions not satisfied"
  
    # A flatten pattern has 4 stages
    # 1. Cache filling of ns0
    # 2. Probing ns1
    # 3. Cache filling of ns1
    # 4. Probing ns0
    # Consequently, index 0 and 3 concern ns0 and index 1 and 2 concern ns1

    # Group log entries by query name
    qnames = list(self.get_qnames())
    assert len(qnames) == 2, "Expected two unique query names"
    m1, m2 = self.get_logentries(qnames[0]), self.get_logentries(qnames[1])

    # Assert that the logentries are sorted according to timestamp
    for i in range(len(m1) - 1):
      assert m1[i]['timestamp'] <= m1[i+1]['timestamp'], "Logentries are not sorted"
    for i in range(len(m2) - 1):
      assert m2[i]['timestamp'] <= m2[i+1]['timestamp'], "Logentries are not sorted"

    # Order two sets of logentries by timestamp  
    if len(m1) > 0 and len(m2) > 0: # Make sure both sets of logentries are non-empty
      if m2[-1]['timestamp'] < m1[0]['timestamp']:
        tmp = m1
        m1 = m2
        m2 = tmp

    # Define function to find the index of the first gap in a list of logentries
    def find_slice_ind(m, gapsize):
      timestamps = [e['timestamp'] for e in m]
      deltas = [b - a for a, b in zip(timestamps[0:-1], timestamps[1:])]
      slice_ind = 0
      for i, d in enumerate(deltas):
        if d > datetime.timedelta(seconds=gapsize):
          slice_ind = i + 1
          break
      return slice_ind

    stages = []
    
    slice_ind1 = find_slice_ind(m1, self.d['queries'][0]['wait_after'])
    # PROBLEM: if the cache filling stage times out, and after timeout, another egress resolver is hit (i.e. new log entry), the slice_ind will be wrong
    # TODO: consult responses as well, make sure log entries are classified correctly by correlating them with response timestamps?

    # TODO: assert log entries are at most as many as queries sent / do it per query set 
    if slice_ind1 > 0:
      stages.append({'rr': self.d['queries'][0]['rr'], 'logentries': m1[0:slice_ind1]})
      stages.append({'rr': self.d['queries'][1]['rr'], 'logentries': m1[slice_ind1:]})
    else: # no gap found
      stages.append({'rr': self.d['queries'][0]['rr'], 'logentries': m1})
      stages.append({'rr': self.d['queries'][1]['rr'], 'logentries': []})

    slice_ind2 = find_slice_ind(m2, self.d['queries'][2]['wait_after'])

    if slice_ind2 > 0:
      stages.append({'rr': self.d['queries'][2]['rr'], 'logentries': m2[0:slice_ind2]})
      stages.append({'rr': self.d['queries'][3]['rr'], 'logentries': m2[slice_ind2:]})
    else: # no gap found
      stages.append({'rr': self.d['queries'][2]['rr'], 'logentries': m2})
      stages.append({'rr': self.d['queries'][3]['rr'], 'logentries': []})

    return stages

# =============================
#   Order RD0-based
# =============================
  
  """ Check conditions satisfied for 'order_rd0based' functions""" 
  def cs_order_rd0based(self) -> bool:
    conditions = []

    # Technical Conditions
    # 4 query sets were planned
    if len(self.d['queries']) != 4:
      return False
    # ns0 is used in query 0 and 3
    conditions += [self.d['queries'][0]['rr'] == self.d['queries'][3]['rr']]
    # ns1 is used in query 1 and 2
    conditions += [self.d['queries'][1]['rr'] == self.d['queries'][2]['rr']]
    # same qname in query 0 and 1
    conditions += [self.d['queries'][0]['query'] == self.d['queries'][1]['query']]
    # same qname in query 2 and 3
    conditions += [self.d['queries'][2]['query'] == self.d['queries'][3]['query']]
    # measurement is complete
    conditions += [self.result_complete()]

    # Logical Conditions
    # Require that each distinct qname is in the log at least once (i.e. both cache-filling stages produced a log entry)
    qnames = list(self.get_qnames())
    conditions += [len(qnames) == 2]
    conditions += [len(self.get_logentries(qnames[0])) > 0]
    conditions += [len(self.get_logentries(qnames[1])) > 0]
    # Both probing stages were performed with recursion desired set to False
    conditions += [self.d['queries'][1]['recursion_desired'] == False]
    conditions += [self.d['queries'][3]['recursion_desired'] == False]
    return all(conditions)

  """ Return a tuple of IP addresses (A,B) signifying that resolver A uses resolver B, or None if the conditions are not satisfied.""" 
  def order_rd0based(self, debug=False):
    assert self.cs_order_rd0based(), "Conditions for 'order_cachebased' functions not satisfied"

    stages = self.order_group_logentries()

    probe1_no_logentries = len(stages[1]['logentries']) == 0
    probe2_no_logentries = len(stages[3]['logentries']) == 0

    if not probe1_no_logentries or not probe2_no_logentries:
      return None
    # Retrieve responses from second and fourth query task
    probe1_start = self.d['queries'][0]['repeat']
    probe1_end = probe1_start + self.d['queries'][1]['repeat']
    probe1_responses = self.d['responses'][probe1_start:probe1_end]
    if debug:
      print(f"{probe1_start} - {probe1_end}")
      print([r['status'] for r in probe1_responses])

    probe2_start = probe1_end + self.d['queries'][2]['repeat']
    probe2_end = probe2_start + self.d['queries'][3]['repeat']
    probe2_responses = self.d['responses'][probe2_start:probe2_end]
    if debug:
      print(f"{probe2_start} - {probe2_end}")
      print([r['status'] for r in probe2_responses])
      print(len(self.d['responses']))
      print()

    probe1_any_noerror = any([r['status'] == "NOERROR" for r in probe1_responses])
    probe1_any_noanswer = any([r['status'] == "NOANSWER" for r in probe1_responses])
    probe2_any_noerror = any([r['status'] == "NOERROR" for r in probe2_responses])
    probe2_any_noanswer = any([r['status'] == "NOANSWER" for r in probe2_responses])

    if probe1_any_noerror and probe2_any_noanswer:
      return (self.d['queries'][0]['rr'], self.d['queries'][1]['rr'])
    elif probe1_any_noanswer and probe2_any_noerror:
      return (self.d['queries'][1]['rr'], self.d['queries'][0]['rr'])
    else:
      return None


# =============================
#   Order Cache-based Pattern
# =============================
  
  """ Check conditions satisfied for 'flatten' functions""" 
  def cs_order_cachebased(self) -> bool:
    conditions = []
    # Technical conditions
    if len(self.d['queries']) != 4:   # 4 query sets were planned
      return False
    # ns0 is used in query 0 and 3
    conditions += [self.d['queries'][0]['rr'] == self.d['queries'][3]['rr']]
    # ns1 is used in query 1 and 2
    conditions += [self.d['queries'][1]['rr'] == self.d['queries'][2]['rr']]
    # same qname in query 0 and 1
    conditions += [self.d['queries'][0]['query'] == self.d['queries'][1]['query']]
    # same qname in query 2 and 3
    conditions += [self.d['queries'][2]['query'] == self.d['queries'][3]['query']]
    # measurement is complete
    conditions += [self.result_complete()]
    # Require that each distinct qname is in the log at least once
    qnames = list(self.get_qnames())
    conditions += [len(qnames) == 2]
    conditions += [len(self.get_logentries(qnames[0])) > 0]
    conditions += [len(self.get_logentries(qnames[1])) > 0]
    return all(conditions)

  """ Return a tuple of IP addresses (A,B) signifying that resolver A uses resolver B, or None if the conditions are not satisfied.""" 
  def order_cachebased(self):
    assert self.cs_order_cachebased(), "Conditions for 'order_cachebased' functions not satisfied"

    stages = self.order_group_logentries()

    probe1_hit = len(stages[1]['logentries']) > 0
    probe2_hit = len(stages[3]['logentries']) > 0

    if not probe1_hit and not probe2_hit:
      return None
    elif probe1_hit and not probe2_hit:
      return (stages[0]['rr'], stages[1]['rr'])
    elif not probe1_hit and probe2_hit:
      return (stages[1]['rr'], stages[0]['rr'])
    else:
      return None


# =====================
#   Helper
# =====================

  """ Internal: Returns mean number of log entries per domain name from a list of filtered log entries.""" 
  def _mean_tries_per_name(self, entries):
    names = [l['query'] for l in entries]
    # Count number of tries per nameserver
    counts = [names.count(q) for q in list(set(names))]
    # Return mean number of tries
    return sum(counts) / len(list(set(names)))

  """ Internal: Returns number of unique domain names from a list of filtered log entries."""
  def _unique_names_tried(self, entries):
    names = [l['query'] for l in entries]
    # Return number of unique names
    return len(list(set(names)))

# =====================
#   Max Fetch Pattern
# =====================

  """ Check conditions satisfied for 'max_fetch'"""
  def cs_max_fetch(self) -> bool:
    conditions = []
    
    # Pattern Parameters
    nameservers = self.zoneconf.get_nameservers()
    if len(nameservers) != 2:   # Exactly two nameservers used
      return False
    
    # First nameserver
    ns0_records = self.zoneconf.get_records(ns=nameservers[0])
    conditions += [all([r['type'] == "NS" for r in ns0_records])]          # only NS records
    conditions += [all([r['ans'][0] == 'n' for r in ns0_records])]         # All answers start with 'n'
    conditions += [len(self.zoneconf.get_zone_names(nameservers[0])) == 1] # only 1 zone
    # Second nameserver
    ns1_records = self.zoneconf.get_records(ns=nameservers[1])
    conditions += [all([r['type'] == "A" for r in ns1_records])]           # only A records
    conditions += [len(self.zoneconf.get_zone_names(nameservers[1])) == 2] # exactly 2 zones

    # Successful Measurement
    
    # Log entries on both stages
    conditions += [len(self._fetch_get_logentries('succ')) > 0]
    conditions += [len(self._fetch_get_logentries('fail')) > 0]
    
    # Exactly two responses, first with NOERROR, second with SRVFAIL
    status = self.get_status_codes()
    if len(status) != 2:
      return False
    conditions += [status[0] == "NOERROR" and status[1] == "SRVFAIL"]

    return all(conditions)

  """ Internal: Returns log entries for a specific stage of the number-of-fetches pattern. (either 'succ' or 'fail')"""
  def _fetch_get_logentries(self, stage):

    # Determine the test SLD under which the successful / failed queries were made 
    suffix = None
    if stage == 'succ':
      ns = self.zoneconf.get_nameservers()[1]
      # Take zone name with fewer labels (main zone name of the ns)
      # Successful queries arrive at the second nameserver, which has two zones
      zones = self.zoneconf.get_zone_names(ns)
      suffix = zones[0] if len(zones[0].split(".")) < len(zones[1].split('.')) else zones[1]
      window  = (self.d['responses'][0]['timestamp_sent'], self.d['responses'][0]['timestamp'])
    elif stage == 'fail':
      ns = self.zoneconf.get_nameservers()[0]
      suffix = self.zoneconf.get_zone_names(ns)[0] # get only zone on this nameserver
      window  = (self.d['responses'][1]['timestamp_sent'], self.d['responses'][1]['timestamp'])
    else:
      assert False, "Invalid stage"

    # Filter log entries according to stage
    entries = self.get_logentries()
    relevant = [e for e in entries if e['query'].endswith(suffix) and e['query'].startswith('n')]
    within_window = [l for l in relevant if window[0] <= l['timestamp'] and l['timestamp'] <= window[1]]

    return within_window


  """ Returns average number of fetches the recursive resolver performs per NS record if the NS records *are* resolvable."""
  def fetch_on_succ_mean_tries(self, debug=False) -> int:
    assert self.cs_max_fetch(), "Conditions for 'max_fetch' not satisfied"

    entries = self._fetch_get_logentries('succ')    # Retrieve relevant log entries 
    ans = self._mean_tries_per_name(entries)        # Mean number of tries per nameserver
    
    if debug:
      print(f"Mean tries on Success: {str(ans)}")

    return ans 
  
  """ Returns average number of fetches the recursive resolver performs per NS record if the NS records are *not* resolvable."""
  def fetch_on_fail_mean_tries(self, debug=False) -> int:
    assert self.cs_max_fetch(), "Conditions for 'max_fetch' not satisfied"
    
    entries = self._fetch_get_logentries('fail')  # Retrieve relevant log entries
    ans = self._mean_tries_per_name(entries)      # Mean number of tries per nameserver
    
    if debug:
      print(f"Mean tries on Fail: {str(ans)}")
    return ans 

  """ Returns number of unique nameservers the recursive resolver tries if the NS records *are* resolvable."""
  def fetch_on_succ_ns_tried(self, debug=False) -> int:
    assert self.cs_max_fetch(), "Conditions for 'max_fetch' not satisfied"

    entries = self._fetch_get_logentries('succ')  # Retrieve relevant log entries
    ans = self._unique_names_tried(entries)           # Number of unique nameservers tried

    if debug:
      print(f"NS tried on Success: {ans}")
    return ans
  
  """ Returns number of unique nameservers the recursive resolver tries if the NS records are *not* resolvable."""
  def fetch_on_fail_ns_tried(self, debug=False) -> int:
    assert self.cs_max_fetch(), "Conditions for 'max_fetch' not satisfied"

    entries = self._fetch_get_logentries('fail')  # Retrieve relevant log entries
    ans = self._unique_names_tried(entries)           # Number of unique nameservers tried
    
    if debug:
      print(f"NS tried on fail: {ans}")
    return ans

  """ Returns total number of fetches the recursive resolver performs if the NS records *are* resolvable."""
  def fetch_on_succ_total(self, debug=False):
    assert self.cs_max_fetch(), "Conditions for 'max_fetch' not satisfied"
    
    entries = self._fetch_get_logentries('succ')  # Retrieve relevant log entries
    ans = len(entries)              # Total number of fetches

    if debug:
      names = [(l['query'],l['type']) for l in entries] # retrieve name,type tupleo for debugging
      print(f"Fetches on Success: {ans}, Response Status: {self.d['responses'][0]['status']}")
      for q in sorted(list(set(names)), key=lambda x: x[0]):
        print(f"{q[0]}  {q[1]}: {names.count(q)}")
    return ans

  """ Returns total number of fetches the recursive resolver performs if the NS records are *not* resolvable.""" 
  def fetch_on_fail_total(self, debug=False):
    assert self.cs_max_fetch(), "Conditions for 'max_fetch' not satisfied"

    entries = self._fetch_get_logentries('fail') # Retrieve relevant log entries
    ans = len(entries)             # Total number of fetches
    
    if debug:
      names = [(l['query'],l['type']) for l in entries] # retrieve name,type tupleo for debugging
      print(f"Fetches on Fail: {ans}, Response Status: {self.d['responses'][1]['status']}")
      for q in sorted(list(set(names)), key=lambda x: x[0]):
        print(f"{q[0]}  {q[1]}: {names.count(q)}")
      
      ts_d = self.get_ts_delta()
      print(f"Timestamp of second response: {self.d['responses'][1]['timestamp']}")
      print(f"Timestamp of last log entry: {self.get_logentries()[-1]['timestamp']+ts_d}")
    return ans

  """ Return True if more than one distinct egress IP is observed in the successful case, False otherwise.
  This suggests the resolver distributes queries for NS queries across multiple resolvers in a 'fine-grained' fashion."""
  def fetch_fine_subquery_granularity(self, debug=False):
    assert self.cs_max_fetch(), "Conditions for 'max_fetch' not satisfied"
    # Unique egress IPs in the successful resolution case (NOERROR was received)
    entries = self._fetch_get_logentries('succ')
    unique_ips = list(set([l['ip'] for l in entries]))

    # More than 1 egress IP suggests that the resolver uses a fine-grained subquery granularity
    ans = len(unique_ips) > 1
    
    if debug:
      print("Unique Egress IPs on Success:")
      for i in unique_ips:
        print(f"{i}")
      print(f"Fine subquery granularity: {ans}")

    return ans

    
# ==============================
#   Chain Length CNAME Pattern
# ==============================
  """ Check conditions satisfied for 'clen_cname' functions""" 
  def cs_clen_cname(self) -> bool:
    conditions = []

    # Pattern Parameters

    # Successful Measurement
    conditions += [self.has_logentries()]
    conditions += [len(self._clen_cname_get_logentries()) > 0] # At least one relevant log entry

    return all(conditions)

  """ Print useful debug information for the chain length CNAME pattern during manual traversal of data."""
  def _clen_cname_debug(self):
    
    entries = self._clen_cname_get_logentries() # Retrieve relevant log entries
    names = [(l['query'],l['type']) for l in entries] # retrieve name,type tupleo for debugging

    print(f"Total entries: {self.num_logentries()} Status: {self.d['responses'][0]['status']}")
    if 'data' in self.d['responses'][0].keys():
      print(f"Answer: {self.d['responses'][0]['data'][0]['answer']} from resolver {self.d['responses'][0]['resolver']}")
    print(f"Considered entries: {len(entries)}")

    # Grouped by unique, with count
    #for q in sorted(list(set(names)), key=lambda x: x[0]):
    #  print(f"\t{q[0]}  {q[1]}: {names.count(q)}")
    
    # Full trace sorted by timestamp
    names = [(l['query'],l['timestamp'], l['ip']) for l in entries] # retrieve name,type tupleo for debugging
    for q in sorted(list(set(names)), key=lambda x: x[1]):
      print(f"\t{q[0]}  {q[1]} {q[2]}: {names.count(q)}")


    
    wildcards = [l['query'] for l in self.get_logentries() if l['query'].startswith('_')]  # Get wildcard entries
    print(f"Wildcard entries: {len(wildcards)}")
    for w in list(set(wildcards)):
      print(f"\t{w}: {wildcards.count(w)}")
    
    ips = set([l['ip'] for l in entries])
    print(f"Unique IPs: {len(ips)}")
    #print(f"Unique IPs: {', '.join(ips)}")

  
  """ Internal: Returns log entries that are relevant for the chain length CNAME pattern."""
  def _clen_cname_get_logentries(self):

    entries = self.get_logentries()
    # Filter out shorter queries (e.g. enc(rr-vp).ta6.ch) caused by QMIN
    num_labels = len(self.d['queries'][0]['query'].split('.'))  # length of original client query
    same_length = [e for e in entries if len(e['query'].split('.')) == num_labels]
    # Filter out wildcard queries, i.e. starting with '_'
    no_wild = [e for e in same_length if not e['query'].startswith('_')]
    return no_wild
  
  """ Returns True if the recursive resolver uses a wildcard query in the chain length CNAME pattern.""" 
  def clen_cname_uses_wildcard(self) -> bool:
    assert self.cs_clen_cname(), "Conditions for 'clen_cname' not satisfied"

    entries = [l['query'] for l in self.get_logentries()] # Get UNFILTERED log entries
    ans = any([l.startswith('_') for l in entries])       # Check for wildcard queries
    return ans

  """ Returns mean number of tries the recursive resolver performs per CNAME chain"""
  def clen_cname_mean_tries(self) -> int:
    assert self.cs_clen_cname(), "Conditions for 'clen_cname' not satisfied"

    entries = self._clen_cname_get_logentries()                                   # Get relevant log entries (without wildcards)
    wildcards = [l for l in self.get_logentries() if l['query'].startswith('_')]  # Get wildcard entries
    unique_names = list(set([l['query'] for l in entries]))                       # Unique names that were tried

    total_entries = len(entries) + len(wildcards)            # Total number of entries
    mean = total_entries / len(unique_names)                 # Mean number of tries per name

    return mean

  """ Returns the maximum number of consecutive CNAMEs the recursive resolver follows""" 
  def clen_cname_chainlength(self) -> int:
    assert self.cs_clen_cname(), "Conditions for 'clen_cname' not satisfied"

    entries = self._clen_cname_get_logentries()   # Retrieve relevant log entries (without wildcards)
    ans = self._unique_names_tried(entries)       # Number of unique domain names in filtered entries
    # Since the records are chained and on *separate* nameservers,
    # the number of unique domain names is equal to the maximum chain length
    return ans

  """ Returns total number of log entries the recursive resolver produces for the chain length CNAME pattern.
  This includes wildcard queries but excludes shorter names caused by QMIN""" 
  def clen_cname_total(self) -> int:
    assert self.cs_clen_cname(), "Conditions for 'clen_cname' not satisfied"

    entries = self.get_logentries()
    # Filter out shorter queries (e.g. enc(rr-vp).ta6.ch) caused by QMIN
    num_labels = len(self.d['queries'][0]['query'].split('.'))  # length of original client query
    same_length = [e for e in entries if len(e['query'].split('.')) == num_labels]

    return len(same_length)
  """ Returns True if the recursive resolver uses a fine-grained subquery granularity in the chain length CNAME pattern.""" 
  def clen_cname_fine_subquery_granularity(self):
    assert self.cs_clen_cname(), "Conditions for 'clen_cname' not satisfied"
    
    entries = self._clen_cname_get_logentries() # Do NOT consider wildcard
    
    # Determine max queries per name across all names
    names = [l['query'] for l in entries]
    counts = [names.count(n) for n in list(set(names))]
    max_count = max(counts)
    # Get unique IPs
    unique_ips = len(list(set([l['ip'] for l in entries])))
    
    ans = unique_ips > max_count  # Pidgeonhole principle: more IPs than queries per name

    return ans




""" 
Process classes define the fields that should be outputted for a given measurement.
They are run once for each BasicMeasurement in the dataset.
Each subclass of Process must provide 3 functions:
  - get_fields: returns a list of field names that will be produced
  - process: returns a dictionary of results for a given BasicMeasurement
  - filter: returns a boolean indicating whether the BasicMeasurement should be processed
The parent class 'Process' accomodates adding a suffix to the fields, 
in case the same process is run on multiple datasets (e.g. MAF of different attacks).
"""
class ProcessCSV():
  def __init__(self, measurement, field_suffix=""):
    self.measurement = measurement
    self.field_suffix = field_suffix
 
  def get_fields(self, fields):
      return [f"{f}{self.field_suffix}" for f in fields]
  
  def process(self, ans):
    return {f"{k}{self.field_suffix}": v for k, v in ans.items()}

""" Process Specification for NumFetches pattern"""
class Process_NumFetches(ProcessCSV):
  def __init__(self, measurement, field_suffix=""):
    super().__init__(measurement, field_suffix)

  def get_fields(self):
    fields = ["fsucc_total", "fsucc_ns_tried", "fsucc_mean_tries", "ffail_total", "ffail_ns_tried", "ffail_mean_tries", "fsucc_fine_gran"]
    return super().get_fields(fields)

  def process(self, bm):
    ans = {
      "fsucc_total":      bm.fetch_on_succ_total(),
      "fsucc_ns_tried":   bm.fetch_on_succ_ns_tried(),
      "fsucc_mean_tries": "{:.2f}".format(bm.fetch_on_succ_mean_tries()),
      "ffail_total":      bm.fetch_on_fail_total(),
      "ffail_ns_tried":   bm.fetch_on_fail_ns_tried(),
      "ffail_mean_tries": "{:.2f}".format(bm.fetch_on_fail_mean_tries()),
      "fsucc_fine_gran":  bm.fetch_fine_subquery_granularity()
    }
    return super().process(ans)
  
  def filter(self, basic_measurement):
    return basic_measurement.cs_max_fetch()

""" Process Specification for CnameChainlength pattern"""
class Process_CnameChainlength(ProcessCSV):
  def __init__(self, measurement, field_suffix=""):
    super().__init__(measurement, field_suffix)
    
  def get_fields(self):
    return super().get_fields([
      "cc_tot",
      "cc_mean_tries",
      "cc_length",
      "cc_wildcard",
      "cc_fine_gran",
      #"status"
    ])
    
  def process(self, bm):
    ans = {
      "cc_tot": bm.clen_cname_total(),
      "cc_mean_tries": "{:.2f}".format(bm.clen_cname_mean_tries()),
      "cc_length": bm.clen_cname_chainlength(),
      "cc_wildcard": bm.clen_cname_uses_wildcard(),
      "cc_fine_gran": bm.clen_cname_fine_subquery_granularity(),
      #"status": bm.get_status_codes()[0]
    }
    return super().process(ans)
    
  def filter(self, bm):
    return bm.cs_clen_cname()

""" Process Specification for QMIN pattern""" 
class Process_Qmin(ProcessCSV):
  def __init__(self, measurement, field_suffix=""):
    super().__init__(measurement, field_suffix)

  def get_fields(self):
    fields = ["full_qmin", "qmin_iter"]
    return super().get_fields(fields)

  def process(self, bm):
    ans = {
      "full_qmin": bm.qmin_full(),
      "qmin_iter": bm.qmin_iterations(),
    }
    return super().process(ans)
  
  def filter(self, basic_measurement):
    return basic_measurement.has_logentries()

""" Process Specification for RD0 pattern"""
class Process_Rd0(ProcessCSV):
  def __init__(self, measurement, field_suffix=""):
    super().__init__(measurement, field_suffix)
    
  def get_fields(self):
    return super().get_fields([
      "rd0_ans_hon",
      "rd0_ans_ign",
      "rd0_ref_hon",
      "rd0_ref_ign"
    ])
  
  def process(self, bm):
    return super().process({
      "rd0_ans_hon": bm.rd0_answers_honors(),
      "rd0_ans_ign": bm.rd0_answers_ignores(),
      "rd0_ref_hon": bm.rd0_refuses_honors(),
      "rd0_ref_ign": bm.rd0_refuses_ignores(),
    })
    
  def filter(self, basic_measurement):
    return basic_measurement.cs_rd0()

""" Process Specification for Shared Cache pattern"""
class Process_SharedFrontend(ProcessCSV):
  def __init__(self, measurement, field_suffix=""):
    super().__init__(measurement, field_suffix)
      
  def get_fields(self):
    fields = ["shared_frontend"]
    return super().get_fields(fields)
    
  def process(self, bm):
    ans = {
      "shared_frontend": bm.shared_frontend(),
    }
    return super().process(ans)
      
  def filter(self, bm):
    return bm.cs_shared_frontend()

""" Process Specification for TTL0 pattern"""
class Process_TTL0(ProcessCSV):
  def __init__(self, measurement, field_suffix=""):
    super().__init__(measurement, field_suffix)
    
  def get_fields(self):
    fields = ["ttl_const", "ttl0_at_client", "ttl0_client_max", "ttl0_server_honors"]
    return super().get_fields(fields)
    
  def process(self, bm):
    return super().process({
      "ttl_const": bm.ttl_constant_client_ttl(),
      "ttl0_at_client": bm.ttl_tell_client_zero(),
      "ttl0_client_max": bm.ttl_max_client_ttl(),
      "ttl0_server_honors": bm.ttl_server_honors_zero(),
    })
    
  def filter(self, bm):
    return bm.cs_ttl0()

""" Process Specification for MAF patterns"""
class Process_MAF(ProcessCSV):
  def __init__(self, measurement, field_suffix=""):
    super().__init__(measurement, field_suffix)
    
  def get_fields(self):
    fields = ["maf_amp", "maf_within_rtt", "maf_total", "maf_rtt", "maf_entry_delta", "status"]
    return super().get_fields(fields)
    
  def process(self, bm):
    return super().process({
      "maf_amp": bm.maf_within_timeout(),
      "maf_within_rtt": bm.maf_within_rtt(),
      "maf_total": bm.maf_total(),
      "maf_rtt": bm.maf_rtt(),
      "maf_entry_delta": bm.maf_entry_delta(),
      "status": bm.get_status_codes()[0]
    })
    
  def filter(self, bm):
    return bm.cs_maf()

""" Process Specification for Enumerate pattern"""
class Process_Enumerate(ProcessCSV):
  def __init__(self, measurement, field_suffix=""):
    super().__init__(measurement, field_suffix)
    
  def get_fields(self):
    fields = ["ip_match", "single_egress", "num_egress", "num_entries", "discovery_quot", "variance"]
    return super().get_fields(fields)
    
  def process(self, bm):
    return super().process({
      "ip_match": bm.enum_matching_ip(),
      "single_egress": bm.enum_single_different_egress(),
      "num_egress": bm.enum_num_egress(),
      "num_entries": bm.num_logentries(),
      "discovery_quot": "{:.2f}".format(bm.enum_discovery_quot()),
      "variance": "{:.2f}".format(bm.enum_variance()),
    })
    
  def filter(self, bm):
    return bm.cs_enum()

""" Process Specification for Enumerate pattern more thoroughly"""
class Process_EnumerateThorough(ProcessCSV):
  def __init__(self, measurement, field_suffix=""):
    super().__init__(measurement, field_suffix)
    
  def get_fields(self):
    fields = ["ip_match", "single_egress", "num_egress", "num_entries", "discovery_quot", "variance", "num_timeout", 
              "num_noerror", "num_srvfail", "num_query_sent", "entry_delta"]
    return super().get_fields(fields)
    
  def process(self, bm):
    return super().process({
      "ip_match": bm.enum_matching_ip(),
      "single_egress": bm.enum_single_different_egress(),
      "num_egress": bm.enum_num_egress(),
      "num_entries": bm.num_logentries(),
      "discovery_quot": "{:.2f}".format(bm.enum_discovery_quot()),
      "variance": "{:.2f}".format(bm.enum_variance()),
      "num_timeout": bm.num_status("TIMEOUT"),
      "num_noerror": bm.num_status("NOERROR"),
      "num_srvfail": bm.num_status("SRVFAIL"),
      "num_query_sent": bm.num_queries_sent(),
      "entry_delta": bm.maf_entry_delta(),
    })
    
  def filter(self, bm):
    return bm.cs_enum()

#------------------
#  Order Patterns
#------------------

""" Process Specification for OrderCacheBased pattern"""
class Process_OrderCacheBased(ProcessCSV):
    def __init__(self, measurement, field_suffix=""):
      super().__init__(measurement, field_suffix)
      
    def get_fields(self):
      fields = ["orderc_A", "orderc_B"]
      return super().get_fields(fields)
      
    def process(self, bm):
      order = bm.order_cachebased()
      if order is None:
        order = [None, None]
      return super().process({
        "orderc_A": order[0],
        "orderc_B": order[1],
      })
      
    def filter(self, bm):
      return bm.has_logentries()



#=======================
#  ResolverMeasurement
#=======================
class ProcessJSON():
  def __init__(self, measurement):
    self.measurement = measurement
  
  def process(self, ans):
    pass

""" Process Specification to produce a JSONline file with egress IPs per vantage point."""
class Process_EgressList(ProcessJSON):
    def __init__(self, resolver_measurement):
      super().__init__(resolver_measurement)
      
    def process(self, rm):
      vps = dict()
      for v in rm.get_vantagepoints():
        vps[v] = rm.get_unique_egress_ips(v)

      return {
        "ns": rm.get_resolver(),
        "unique_egress": len(rm.get_unique_egress_ips()),
        "egress_ips": rm.get_unique_egress_ips(),
        "vps":  vps
      }
      
    def filter(self, rm):
      return rm.has_logentries()

#""" Get dict of unique egress IPs for a resolver for a given list of vantage points"""
#def agg_egress_ips(rr_measurement):
#
#  # Prepare output
#  vps = dict()
#  for v in rr_measurement.get_vantagepoints():
#    vps[v] = rr_measurement.get_unique_egress_ips(v)
#
#  return {
#    "ns": rr_measurement.get_resolver(),
#    "unique_egress": len(rr_measurement.get_unique_egress_ips()),
#    "egress_ips": rr_measurement.get_unique_egress_ips(),
#    "vps":  vps
#  }
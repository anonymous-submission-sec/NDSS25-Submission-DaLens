# /usr/bin/env python3


from lib.BasicMeasurement import BasicMeasurement
from itertools import combinations


class ResolverMeasurement:

    """ Construct a NameserverMeasurement object from a list of BasicMeasurement objects withe the same nameserver"""    
    def __init__(self, basic_measurements:list, ns:str=None):
        
        if ns is None:
            # Make sure all measurements are from the same nameserver
            assert len(set([m.get_resolver() for m in basic_measurements])) == 1, "Measurements involve more than one nameserver, please specify 'ns'"
            self.ns = basic_measurements[0].get_resolver() 
        else:
            # Make sure ns is involved in all measurements
            assert all([ns in m.get_resolvers() for m in basic_measurements]), f"Nameserver {ns} not found in measurements"
            self.ns = ns
        
        self.vps = dict()

        # Group basic measurements by vantage point
        for m in basic_measurements:
            vp = m.get_vantagepoint()
            if vp not in self.vps:
                self.vps[vp] = []
            self.vps[m.get_vantagepoint()].append(m)

    # Python does not support overloading
    #""" Construct a NameserverMeasurement without any basic measurements"""
    #def __init__(self, ns:str):
    #    self.ns = ns
    #    self.vps = dict()
    
    """ Add a basic measurement to this nameserver measurement"""
    def add_measurement(self, basic_measurement:BasicMeasurement):
        # Make sure the nameserver is involved in this measurement
        assert self.ns in basic_measurement.get_resolver(), f"Nameserver {self.ns} not found in measurement"
        vp = basic_measurement.get_vantagepoint()
        if vp not in self.vps:
            self.vps[vp] = []
        self.vps[vp].append(basic_measurement)


# ===========================
#   Getter / Info functions
# ===========================
    
    """ This function returns the list of vantage points of this nameserver measurement"""
    def get_vantagepoints(self):
        return self.vps.keys()
    
    """ This function returns the nameserver of this nameserver measurement""" 
    def get_resolver(self):
        return self.ns
    
    """ Get the list of egress IPs for a given nameserver across all vantage points if vp=None, or for a given vantage point by setting vp""" 
    def get_egress_ips(self, vp:str=None):
        if vp is None:
            # Return the list of egress IPs for all vantage points
            ips = []
            for m_list in self.vps.values():
                for m in m_list:
                  ips += m.get_egress_ips()
            return ips
        else:
            # Return the list of egress IPs for a given vantage point
            assert vp in self.vps, f"Vantage point {vp} not found"
            egress_ips = []
            for m in self.vps[vp]:
                egress_ips += m.get_egress_ips()
            return egress_ips
    
    """ Get the list of unique egress IPs for a given nameserver across all vantage points, or for a given vantage point by setting vp"""    
    def get_unique_egress_ips(self, vp:str=None):
        result =  list(set(self.get_egress_ips(vp)))
        # Check that the result is correct
        all_vps = self.vps.keys()
        all_egress = []
        for v in all_vps:
            v_egress = list(set(self.get_egress_ips(v)))
            all_egress += v_egress
        all_egress = list(set(all_egress))
        if vp is None:
            assert len(set(all_egress)) == len(set(result)), "Result does not contain all unique egress IPs"
        else:
            assert set(result).issubset(set(all_egress)), "Result contains egress IPs from other vantage points"
        return result
    
    """ This function returns the basic measurements for a given vantage point"""
    def get_basic_measurements(self, vp:str) -> list:
        assert vp in self.vps, f"Vantage point {vp} not found"
        return self.vps[vp]

    """ This function returns the basic measurements for a given vantage point"""
    def get_measurements(self, vp:str) -> list:
        assert vp in self.vps, f"Vantage point {vp} not found"
        return self.vps[vp]

    """ This function returns the number of log entries across all vantage points if vp=None, or for a given vantage point by setting vp"""
    def num_noerror_responses(self, vp:str=None):
        if vp is None:
            total_sum = 0
            for m_list in self.vps.values():
                total_sum += sum([m.num_noerror() for m in m_list])
            return total_sum
        else:
            return self.get_basic_measurement(vp).num_noerror_respones()
    
    """ This function returns the number of log entries across all vantage points if vp=None, or for a given vantage point by setting vp""" 
    def num_logentries(self, vp:str=None):
        if vp is None:
            return sum([self.num_logentries(v) for v in self.vps.keys()])
        else:
            return self.get_basic_measurement(vp).num_logentries()

# ===========================
#   Decision functions
# ===========================

    """ Decide whether a nameserver is a single-machine resolver or not"""    
    def is_single(self, vp:str=None):
        if vp is None:
            # Make sure the nameserver is single from ALL vantage points
            eligible_measurements = [m for vp in self.vps.keys() for m in self.vps[vp] if m.cs_is_single()]
            return all([m.is_single() for m in eligible_measurements])
        else:
            assert vp in self.vps, f"Vantage point {vp} not found"
            eligible_measurements = [m for m in self.vps[vp] if m.cs_is_single()]
            return all([m.is_single() for m in eligible_measurements])
    

    """ Return a list of shared egress IPs between the vantage points given in vps, or between all vantage points if vps is None""" 
    def get_unique_shared_egress_ips(self, vps:list=None) -> set:
        if vps is None:
            vps = self.vps.keys()
        # Find unique egress across all vps
        all_unique_egress = []
        for vp in vps:
            all_unique_egress += self.get_unique_egress_ips(vp)
        all_unique_egress = list(set(all_unique_egress))
        # Shared egress across all vantage points
        unique_egress_shared = set.intersection(*[set(self.get_unique_egress_ips(vp)) for vp in vps])
        return unique_egress_shared
    
    """ Return a list of exclusive egress IPs of a given vantage point vp""" 
    def get_exclusive_egress_ips(self, vp:str):
        assert vp in self.vps, f"Vantage point {vp} not found"
        other_vps = [v for v in self.vps.keys() if v != vp]
        other_egress = []
        for v in other_vps:
            other_egress += self.get_unique_egress_ips(v)
        result = list(set(self.get_unique_egress_ips(vp)) - set(other_egress))

        # Double-check that the result is correct
        for v in other_vps:
            assert len(set(self.get_unique_egress_ips(v)) & set(result)) == 0, f"Result contains IPs from vantage point {v}"
        return result
    
# ===========================
#   Honor TTL 0 Pattern
# ===========================
    
    """ This function returns True if the nameserver honors TTL=0 across all vantage points if vp=None, or for a given vantage point by setting vp"""
    def ttl_server_honors_zero(self, vp:str=None):
        if vp is None:
            return all([self.ttl_server_honors_zero(v) for v in self.vps.keys()])
        else:
            return self.get_basic_measurements(vp)[0].ttl_server_honors_zero()
    
    """ This function returns True if the client observes TTL 0 across all vantage points if vp=None, or for a given vantage point by setting vp"""
    def ttl_tell_client_zero(self, vp:str=None):
        if vp is None:
            return all([self.ttl_tell_client_zero(v) for v in self.vps.keys()])
        else:
            return self.get_basic_measurements(vp)[0].ttl_tell_client_zero()
    
    """ This function returns the maximum TTL that the client sees across all vantage points if vp=None, or for a given vantage point by setting vp"""
    def ttl_max_client_ttl(self, vp:str=None):
        if vp is None:
            all_max = 0
            for vp in self.vps.keys():
                vp_max = max([v.ttl_max_client_ttl() for v in self.vps[vp]])
                if vp_max > all_max:
                    all_max = vp_max
            return all_max
        else:
            return self.get_basic_measurements(vp)[0].ttl_max_client_ttl()  
   
    """ This function returns True if the client sees a constant TTL across all vantage points if vp=None, or for a given vantage point by setting vp"""
    def ttl_constant_client_ttl(self, vp:str=None):
        if vp is None:
            return all([self.ttl_constant_client_ttl(v) for v in self.vps.keys()])
        else:
            return self.get_basic_measurements(vp)[0].ttl_constant_client_ttl() 
    
    """ This function returns the time deltas between log entries across all vantage points if vp=None, or for a given vantage point by setting vp""" 
    def ttl_server_deltas(self, vp:str=None):
        if vp is None:
            deltas = []
            for v in self.vps.keys():
                deltas += self.ttl_server_deltas(v)
            return deltas
        else:
            return self.get_basic_measurements(vp)[0].get_server_ttl()

    """ Returns intersection of unique egress IPs between two nameserver measurements"""    
    def common_egress_ips(self, other):
        assert isinstance(other, NameserverMeasurement), "Expected NameserverMeasurement object"
        return set(self.get_unique_egress_ips()).intersection(set(other.get_unique_egress_ips()))

# ======================
#   Points of Presence
# ======================
    
    """ Take two vantage points present in this NameserverMeasurement object and return True if they hit the same PoP"""    
    def same_pop(self, vp0:str, vp1:str):
        assert vp0 in self.vps, f"Vantage point {vp0} not found"
        assert vp1 in self.vps, f"Vantage point {vp1} not found"
        # Condition 1: vantage points have at least one egress IP in common
        c1 =  len(set(self.get_unique_egress_ips(vp0)) & set(self.get_unique_egress_ips(vp1))) > 0
        # We cannot require that other vantage points are disjunct because they might also belong to the same PoP
        return c1

    """ Check conditions satisfied for 'get_pops' function"""
    def cs_get_pops(self):
        conditions = []
        conditions += [len(self.vps) > 1] # more than one vantage point required
        return all(conditions)

    """ Returns a list of lists of vantage points that hit the same Point of Presence (PoP)"""    
    def get_pops(self):
        assert self.cs_get_pops(), "Conditions not satisfied for 'get_pops' function"

        pops = [[vp] for vp in self.vps.keys()]

        # Cluster vantage points that hit the same PoP
        merge_happened = True
        while merge_happened:
            merge_happened = False
            for i in range(len(pops)):
                for j in range(i+1, len(pops)):
                    if self.same_pop(pops[i][0], pops[j][0]): # suffices to check [0] element because the rest already has intersection with [0]
                        pops[i] += pops[j]
                        pops.pop(j)
                        merge_happened = True
                        break # break out of inner loop
                if merge_happened:
                    break # break out of outer loop

        # Assert PoPs have disjunct egress IPs
        for p1, p2 in combinations(pops, 2):
            # Get union of unique egress IPs for PoP i and PoP j
            p1_egress = set().union(*[set(self.get_unique_egress_ips(vp)) for vp in p1])
            p2_egress = set().union(*[set(self.get_unique_egress_ips(vp)) for vp in p2])
            # Assert intersection is empty
            assert len(p1_egress & p2_egress) == 0, "PoPs must have disjunct egress IPs"
            
        #for i in range(len(pops)):
        #    for j in range(i+1, len(pops)):
        #        # Get union of unique egress IPs for PoP i and PoP j
        #        egress_i = set().union(*[set(self.get_unique_egress_ips(vp)) for vp in pops[i]])
        #        egress_j = set().union(*[set(self.get_unique_egress_ips(vp)) for vp in pops[j]])
        #        assert len(egress_i & egress_j) == 0, "PoPs must have disjunct egress IPs"

        # Assert each vantage point is in at least one PoP
        assert len(set().union(*pops)) == len(self.vps.keys()), "Each vantage point must at least in one PoP"
        # Assert each vantage point is in at most one PoP
        for vp in self.vps.keys():
            assert sum([vp in pop for pop in pops]) == 1, "Each vantage point must be in at most one PoP"
        return pops
    
# ==================
#   Load Balancing
# ==================
    
    def cs_loadbalancing_pops(self):
        conditions = []
        conditions += [len(self.vps) > 1]
        conditions += [self.cs_get_pops()]
        return all(conditions)

    """ Returns list of PoPs for which IP-based loadbalancing was observed"""
    def loadbalancing_ip_based_pops(self) -> list:
        pops = self.get_pops()
        with_ip_loadbalancing = []
        for pop in pops:
            basic_measurements = [basic for vp in pop for basic in self.vps[vp]]
            eligible = [bm for bm in basic_measurements if bm.cs_loadbalancing_ip_based()]
            # Check if all vantage points in this PoP observe IP loadbalancing
            if all([bm.loadbalancing_ip_based() for bm in eligible]):
                with_ip_loadbalancing.append(pop)
        return with_ip_loadbalancing
    
    """ Return True if IP based loadbalancing is observed for all PoPs"""
    def loadbalancing_ip_based_all_pops(self) -> bool:
        # Condition 1: IP based loadbalancing is observed for all PoPs
        c1 = len(self.loadbalancing_ip_based_pops()) == len(self.get_pops())
        # If all basic measurements observe IP loadbalancing, then every PoP must use IP loadbalancing too
        assert c1 == self.loadbalancing_ip_based(), "loadbalancing_ip_based_all_pops() and loadbalancing_ip_based() must return the same result"
        return c1

    """ Return True if IP based loadbalancing is observed for at least one PoP"""
    def loadbalancing_ip_based_any_pops(self) -> bool:
        # Condition 1: IP based loadbalancing is observed for at least one PoP
        c1 = len(self.loadbalancing_ip_based_pops()) > 0
        return c1
    
    """ Return True if ALL basic measurements from ALL vantage points observe loadbalancing based on IP addresses"""
    def loadbalancing_ip_based(self) -> bool:
        eligible = [bm for vp in self.vps.keys() for bm in self.vps[vp] if bm.cs_loadbalancing_ip_based()]
        return all([bm.loadbalancing_ip_based() for bm in eligible])
        #return all([bm.loadbalancing_ip_based() for vp in self.vps.keys() for bm in self.vps[vp]])


# =========================
#   Respects RD=0 Pattern
# =========================

    """ This function returns True if the nameserver respects RD=0 across all vantage points if vp=None, 
    or for a given vantage point by setting vp. 
    The function returns None if no eligible measurements are found"""
    def respects_rd_zero(self, vp:str=None):
        if vp is None:
            eligible = [m for vp in self.vps.keys() for m in self.vps[vp] if m.cs_respects_rd_zero()]
            return all([self.respects_rd_zero(v) for v in self.vps.keys()]) if len(eligible) > 0 else None
        else:
            eligible = [m for m in self.vps[vp] if m.cs_respects_rd_zero()]
            return all([m.respects_rd_zero() for m in eligible]) if len(eligible) > 0 else None


# ======================================================
#   Utility functions on NameserverMeasurement objects
# ======================================================

""" Take a list of basic measurements, group them by nameserver, and return a list of NameserverMeasurement objects"""
def group_by_nameserver(basic_measurements:list) -> list:
    # Group basic measurements by nameserver
    ns = dict()
    for m in basic_measurements:
        for n in m.get_resolvers():
            # Add basic measurement to ALL nameserver measurements whose nameserver is involved
            if n not in ns:
                ns[n] = ResolverMeasurement(n)
            ns[n].add_measurement(m)
    return ns.values()
    


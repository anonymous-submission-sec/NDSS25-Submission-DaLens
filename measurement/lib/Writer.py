
import os
import json

""" Responsible for writing zone files to disk. Manages one file per zone """
class ZoneWriter():
    
    """ Constructor for ZoneWriter. Initializes file handles and zone sets"""
    def __init__(self, materialize_dir, ns_config, max_records:int=10000, skip_duplicate_check:bool=False):
        
        self.ZONEFILE_TEMPLATE = "zone{shard}@{zone}@{ns}" # Filename template
        
        self.ns_config = ns_config      # Nameserver configuration
        self.file_handles = {}          # Dict of zone -> file handle 
        self.rr_sets = {}               # Dict of zone -> rr_set to check for duplication
        self.dir = os.path.join(os.getcwd(), materialize_dir)   # Directory to write zone files to
        self.skip_duplicate_check = skip_duplicate_check        # Whether to skip duplication check

        # Statistics
        self.num_records = {}           # Dict of ns_ip -> num_records of current shard, used for sharding
        self.num_records_total = {}     # Dict of ns_ip -> num_records across all finshed shards
        self.MAX_RECORDS = max_records  # Maximum number of records per nameserver
        self.shard_num = 0              # Number of current shard

    """ Close file handles on destruction of the object"""
    def __del__(self):
        for k in self.file_handles:
            self.file_handles[k].close()
    
    """ Internal function to create default header records (SOA,NS) for on-the-fly created zones"""
    def _create_default_header(self, ns_ip, zone):
        header = []
        header += [f"@  3600  IN  SOA ns1.{zone}.  dsec.team.proton.me (1 7200 3600 1209600 0)"]
        header += [f"@  5   IN    NS  ns1.{zone}."]
        header += [f"@  5   IN    NS  ns2.{zone}."]
        header += [f"ns1  5   IN    A  {ns_ip}"]
        header += [f"ns2  5   IN    A  {ns_ip}"]
        return "\n".join(header) + "\n"
    
    """ Return dictionary of ns_ip -> num_records emitted for that nameserver"""
    def get_stats(self):
        total = dict(self.num_records_total)                    # Total of finished shards
        for k in self.num_records:
            total[k] = total.get(k, 0) + self.num_records[k]    # Add num_records of current shard
        return total
    
    """ Write records to a zone file for specific nameserver"""
    def write(self, ns, zone, records):
        
        # Check if file handle exists
        if not (ns,zone) in self.file_handles:
            # Create Zone file, add handle to dict
            self.file_handles[(ns,zone)] = open(f"{self.dir}/{self.ZONEFILE_TEMPLATE.format(ns=ns, zone=zone, shard=self.shard_num)}", 'w')
            
            # Write SOA / Zone header
            # Check if zone is in ns_config, i.e. a main zone of one of the nameservers
            ns_id = [i for i in self.ns_config.keys() if self.ns_config[i]['DOMAIN'] == zone]
            if len(ns_id) > 0:
                for soa in self.ns_config[ns_id[0]]['SOA']:
                    self.file_handles[(ns,zone)].write(f"{soa}\n")   # If so, use predefined header
            else:
                # Create default SOA
                header = self._create_default_header(ns, zone)       # Create default header
                self.file_handles[(ns,zone)].write(header)           # Write header to new shard

        # Write records to file
        rrs = [f"{rr['name']} {rr['ttl']} {rr['class']}  {rr['type']}  {rr['ans']}" for rr in records]
        s = "\n".join(rrs)
        self.file_handles[(ns,zone)].write(s + "\n")

        if not self.skip_duplicate_check:
            # Duplication Check
            rr_set = set([rr['name'] for rr in records])
            if zone in self.rr_sets:            # Check for collisions with existing records in the zone
                if len(self.rr_sets[zone].intersection(rr_set)) != 0: 
                  print(f"WARNING: RRs of multiple measurements intersect!")
                  print(f"Offending record: {rr_set.intersection(self.rr_sets[zone])} in {zone}")
            else:                               # Create set for zone if non-existent
                self.rr_sets[zone] = set()

            self.rr_sets[zone] = self.rr_sets[zone].union(rr_set) # Add records to rr_set of zone
            
        # Update number of records per nameserver for sharding
        self.num_records[ns] = self.num_records.get(ns, 0) + len(records)

    """ Function to perform sharding. Closes all file handles, and opens new ones to continue"""
    def shard(self):

        self.shard_num += 1                               # Increment shard number
        for ns_ip, zone in self.file_handles.keys():      # Close and reopen all file handles
            self.file_handles[(ns_ip,zone)].close()
            self.file_handles[(ns_ip,zone)] = open(f"{self.dir}/{self.ZONEFILE_TEMPLATE.format(ns=ns_ip, zone=zone, shard=self.shard_num)}", 'w')
            
            # Write header
            # Check if zone is in ns_config, i.e. a main zone of one of the nameservers
            ns_id = [i for i in self.ns_config.keys() if self.ns_config[i]['DOMAIN'] == zone]
            if len(ns_id) > 0:                                          # If so, use predefined header
                for soa in self.ns_config[ns_id[0]]['SOA']:
                    self.file_handles[(ns_ip,zone)].write(f"{soa}\n")
            else:
                header = self._create_default_header(ns_ip, zone)       # Create default header
                self.file_handles[(ns_ip,zone)].write(header)           # Write header to new shard

        # Sum total number of records, reset number of records for new shard
        for k in self.num_records:
            self.num_records_total[k] = self.num_records_total.get(k, 0) + self.num_records[k]
            self.num_records[k] = 0

    """ Check internal counters and decide whether to shard """
    def should_shard(self) -> bool:
        # If counter for any nameserver exceeds MAX_RECORDS, return True
        for ns in self.num_records:
            if self.num_records[ns] > self.MAX_RECORDS:
                return True
        return False



""" Responsible for writing query tasks to files. Manages one file per client """
class TaskWriter():
    
    """ Constructor for TaskWriter. Initializes file handles and counters. """
    def __init__(self, materialize_dir, probe_config):
        
        self.TASKFILE_TEMPLATE = "tasks{shard}@{ip}"            # Filename template

        self.probe_config = probe_config        # Probe configuration
        self.file_handles = {}                  # Dict of probe_ip -> file handle 
        self.dir = os.path.join(os.getcwd(), materialize_dir)   # Directory to write client tasks to

        # Statistics
        self.num_tasks = {}                     # Dict of probe_ip -> num_tasks
        self.num_tasks_total = {}               # Dict of probe_ip -> num_tasks
        self.shard_num = 0                      # Number of current shard
    
    """ Close file handles on destruction of the object"""
    def __del__(self):
        for k in self.file_handles:
            self.file_handles[k].close()
    
    """ Return dictionary of probe_ip -> num_tasks emitted for that probe / client."""
    def get_stats(self):
        total = dict(self.num_tasks_total)                    # Total of finished shards
        for k in self.num_tasks:
            total[k] = total.get(k, 0) + self.num_tasks[k]    # Add num_tasks of current shard
        return total

    """ Write querytask to task file of specific probe / client. """ 
    def write(self, client, task:dict):
        
        if not client in self.file_handles:     # Check if file handle exists
            self.file_handles[client] = open(f"{self.dir}/{self.TASKFILE_TEMPLATE.format(ip=client, shard=self.shard_num)}", 'w')
        
        s = json.dumps(task)                    # Write task to file
        self.file_handles[client].write(s + "\n")

        # Increment counter
        self.num_tasks[client] = self.num_tasks.get(client, 0) + 1

    """ Function to perform sharding. Closes all file handles, and opens new ones to continue"""
    def shard(self):
        
        self.shard_num += 1                               # Increment shard number
        for p in self.file_handles.keys():                # Close and reopen all files with new shard num
            self.file_handles[p].close()
            self.file_handles[p] = open(f"{self.dir}/{self.TASKFILE_TEMPLATE.format(ip=p, shard=self.shard_num)}", 'w')

        for k in self.num_tasks:        # Sum total number of tasks
            self.num_tasks_total[k] = self.num_tasks_total.get(k, 0) + self.num_tasks[k]
            self.num_tasks[k] = 0       # Reset task counter for new shard
    
    """ Check internal counters and decide whether to shard """
    def should_shard(self) -> bool:
        return False
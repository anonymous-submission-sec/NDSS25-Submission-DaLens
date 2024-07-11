
import json

import os, sys
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

#import common.encoding as encoding

class ZoneConf():
#{
#  "207.154.207.150": [
#    {
#      "zone": "ta6.ch",
#      "records": [
#        {
#          "name": "enc(ns0-vp0)",
#          "type": "A",
#          "ttl": 300,
#          "ans": "207.154.207.150",
#          "random_subdomains": false
#        }
#      ]
#    }
#  ]
#}
    """ Load semi-materialized zone configuration from file."""
    def __init__(self, zoneconf:dict):
        self.zoneconf = zoneconf

    """ Get all names instantiated with given recursive resolver (rr) and vantage point (vp)"""
    def get_names(self, rr, vp):
        assert False, "Not implemented"
        return [r['name'] for z in self.zoneconf[rr] for r in z['records'] if vp in r['name']]

    """ Return number of records in the zone configuration.""" 
    def get_num_records(self):
        return sum([len(z['records']) for zones in self.zoneconf.values() for z in zones])
    
    """ Get records for a given zone and nameserver""" 
    def get_records(self, ns="", zone="", resolver_set:dict = None):
        records = []
        if ns == "" and zone == "":   # return all records
            records =  [r for zones in self.zoneconf.values() for z in zones for r in z['records']]
        elif ns != "" and zone == "":   # return all records for a given nameserver
            records =  [r for zones in self.zoneconf[ns] for r in zones['records']]
        elif ns == "" and zone != "":   # return all records for a given zone
            records =  [r for zones in self.zoneconf.values() for z in zones if z['zone'] == zone for r in z['records']]
        else:   # return all records for a given zone and nameserver
            records =  [r for zones in self.zoneconf[ns] for z in zones if z['zone'] == zone for r in z['records']]

        if resolver_set is not None:
          assert False, "Full materialization of zoneconf is not yet fully implemented"
          # Materialize records
          #for r in records:
          #    # Materialize name
          #    # TODO: Make rr0 and vp0 configurable: dump resolverlist headers into the zone config file
          #    enc_labels = []
          #    for l in r['name'].split('.'):
          #        enc_labels += [encoding.enc(l, resolver_set)] if l.startswith("enc(") else [l]
          #    r['name'] = '.'.join(enc_labels)
          #    # Materialize ans
          #    enc_labels = []
          #    for l in r['ans'].split('.'):
          #        enc_labels += [encoding.enc(l, resolver_set)] if l.startswith("enc(") else [l]
          #    r['ans'] = '.'.join(enc_labels)
        return records


    """ Return all TTLs in the zone configuration.""" 
    def get_ttl(self):
        return [r['ttl'] for zones in self.zoneconf.values() for z in zones for r in z['records']]

    """ Return list of zone names"""
    def get_zone_names(self, ns=""):
        if ns == "":
            return [z['zone'] for zones in self.zoneconf.values() for z in zones]
        else:
            return [z['zone'] for z in self.zoneconf[ns]]
    
    """ Return list of nameservers"""
    def get_nameservers(self):
        return list(self.zoneconf.keys())


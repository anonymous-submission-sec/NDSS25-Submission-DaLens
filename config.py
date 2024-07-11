#! /usr/bin/env python3

ETHICS_WEBSITE_IP = "207.154.207.150"

NAMESERVERS = {
  "0": {
    "IP": "207.154.207.150",
    "DOMAIN": "ta6.ch",
    "user": "root",
    "identity": "~/.ssh/id_probe01",
    "persistent_zones": ["ta6.ch", "qmin-tax.org"],
    "SOA": [
      "@  3600  IN  SOA ns1.qmin-tax.org.  dsec.team.proton.me (1 7200 3600 1209600 0)",
      "@  300   IN    NS  ns1.qmin-tax.org.",
      "@  300   IN    NS  ns2.qmin-tax.org.",
      "@  0     IN    A   207.154.207.150",
      "www  0     IN    A   207.154.207.150",
    ],
    "bind_config": {
      #"bind_dir": "/etc/bind",
      #"zoneconfig": "named.conf.local",
      #"systemd_service": "named.service",
      #"zone_dir": "/etc/bind/zones",
      #"zonefile_suffix": ".zone",
      "log_dir": "/mnt/ta6_ch_storage/bindlog",
      #"log_file": "query.log"
    }
  },
  "1": {
    "IP": "68.183.67.130",
    "DOMAIN": "ta7.ch",
    "user": "root",
    "identity": "~/.ssh/id_probe01",
    "persistent_zones": ["ta7.ch", "qmin-tax.net"],
    "SOA": [
      "@  3600  IN  SOA ns1.qmin-tax.net.  dsec.team.proton.me (1 7200 3600 1209600 0)",
      "@  300   IN    NS  ns1.qmin-tax.net.",
      "@  300   IN    NS  ns2.qmin-tax.net.",
      "@  0     IN    A   207.154.207.150",
      "www  0     IN    A   207.154.207.150",
    ],
    "bind_config": {
      #"bind_dir": "/etc/bind",
      #"zoneconfig": "named.conf.local",
      #"systemd_service": "named.service",
      #"zone_dir": "/etc/bind/zones",
      #"zonefile_suffix": ".zone",
      "log_dir": "/mnt/ans_ta7_ch_storage/bindlog",
      #"log_file": "query.log"
    }
  }
}

# Measurement Hosts

CLIENT_HOSTS = [
  {"IP": "138.68.96.43", "user": "root", "identity": "~/.ssh/id_probe01"},
  {"IP": "157.230.97.126", "user": "root", "identity": "~/.ssh/id_probe01"},
  {"IP": "146.190.91.208", "user": "root", "identity": "~/.ssh/id_probe01"},
  {"IP": "159.203.105.218", "user": "root", "identity": "~/.ssh/id_probe01"}
]

# 'measurement/'

"""
MATERIALIZE_DIR

Output directory of materialize.py and input directory of run_measurement.py

"""
MATERIALIZE_DIR = "materialized"

"""
RESULTS_DIR

Output directory of run_measurement.py and materialize.py (zoneconf.json)
"""
RESULTS_DIR = "results"

# TODO: settings.json name
# TODO: zoneconf.json name
# TODO: outfile templates
# TODO: on the fly zone header

#MAX_ZONE_ENTRIES = 2600000
MAX_ZONE_ENTRIES = 2800000


""" 
PATTERN_ZONE_DEFAULT

Resource Record defaults, used in case optional fields in the pattern are not defined.
"""
PATTERN_ZONE_DEFAULT = {
  "type": "A",
  "ttl": 30,
  "class": "IN",
  "ans": ETHICS_WEBSITE_IP,
  "random_subdomains": False,
}


"""
PATTERN_QUERY_DEFAULT

Query task defaults, used in case optional fields in the pattern are not defined.
The schema is defined in lib/schemas.py.
"""

PATTERN_QUERY_DEFAULT = {
  "type": "A",
  "wait": 0,
  "repeat": 1,
  "timeout": 15,
  "wait_after": 0,
  "random_subdomains": False,
  "concurrent": False,
  "recursion_desired": True,
  "expected_status": "NOERROR"
}

# ============
#   Analysis
# ============


"""
RE_LOGENTRY

Regular expression to parse a log entry from a BIND9 log file.

The parser requires named groups for the following fields:
- timestamp
- client_address
- query_type
- query
"""
timestamp = r"(?P<timestamp>\d+-[a-zA-Z]+-\d+ \d+:\d+:\d+\.\d+)"
client_address = r"(?P<client_address>(?:\d+\.){3}\d+)"
client_info = r"(?P<client_info>@(?:0x)?\S+)"
query_type = r"(?P<query_type>\S+)"
query = r"(?P<query>(?:[\*_a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})"
query2 = r"(?P<query2>(?:[\*_a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})"

RE_LOGENTRY = timestamp + " queries: info: client " + client_info + " " + client_address + "#\d+ \(" + query + "\): query: " + query2 + " IN " + query_type
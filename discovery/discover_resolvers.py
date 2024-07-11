#! /usr/bin/env python3

import subprocess

import os, sys
import shutil

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import config as c
from measurement.lib.SessionCtl import SessionCtl

# TODO: use interface option of xmap to use vpn (also use IP flag)
  
#def run_command(c, err):
#
#  r =  subprocess.Popen(
#    c.split(' '), 
#    stdout=subprocess.PIPE, bufsize=1, 
#    universal_newlines=True)
#  
#  for line in r.stdout:
#      print(line, end='')
#  
#  r.wait()
#  if r.returncode != 0:
#    print(err)
#    print(r.stderr)
#    return
#  else:
#    print("Done!")
#
#def check_running(remote:str):
#  last_line = None
#  try:
#    p = subprocess.run(f"ssh {remote} tail -n 1 {F}".split(' '), capture_output=True)
#    p.check_returncode()
#    last_line = p.stdout.decode('utf-8')
#  except:
#    # File not found
#    return False
#  try:
#    p = subprocess.run(f"ssh {remote} tail -n 1 {F}".split(' '), capture_output=True)
#    p.check_returncode()
#    if last_line == p.stdout.decode('utf-8'):
#      # Different last line: still running
#      return True
#    else:
#      return False
#  except:
#    print("Something went wrong while checking for running processes")
#    exit(1)


def find_good_hosts(host_handles:list):
  good_hosts = []  
  for h in host_handles:
    if h.check_installed(["xmap"]):
      good_hosts.append(h)
    else:
      print(f"Host at {h.ip} does not seem to have Xmap installed..")
  return good_hosts

if __name__ == "__main__"  :
  
    import argparse
    parser = argparse.ArgumentParser(description="Discovers DNS resolvers on the internet \
        using Xmap from a remote host using SSH.")
    subparsers = parser.add_subparsers(help="commands", dest='command', required=True)

    # Run command
    run_parser = subparsers.add_parser("discover")
    run_parser.add_argument("--o", default="out.json", metavar="out.json",
      help="Name of the output file")
    run_parser.add_argument("--n", type=int,
      help="Number of Resolvers to discover")
    run_parser.add_argument("--d", nargs="+", default=["google.com"], metavar="qname",
      help="One or more domains the resolver should resolve.")
    run_parser.add_argument("--r", type=int, default=100, metavar="pps",
      help="Packets per Second which Xmap should send.")
    run_parser.add_argument("--dry", action="store_true", required=False,)
    # Status command 
    status_parser = subparsers.add_parser("status")
    # Retrieve command 
    retrieve_parser = subparsers.add_parser("retrieve")
    # Clean command
    retrieve_parser = subparsers.add_parser("clean")
    # Kill command
    retrieve_parser = subparsers.add_parser("kill")
    
    args = parser.parse_args()

    # Load host handles
    host_handles = [SessionCtl(h['identity'], h['user'], h['IP']) for h in c.CLIENT_HOSTS]
    
    
    
    # SSH config
    #OUTFILE = args.o
    #NUM_RESOLVERS = args.n
    #DOMAIN = args.d
    #RATE = args.r



        #run_command(f"ssh {remote} echo 'Hello {IP}'", "Unable to connect via SSH")
    #print("Check if remote host is reachable")
    #run_command(f"ssh {remote} echo 'Hello {IP}'", "Unable to connect via SSH")
    
    #print("Check if Xmap is installed on remote host")
    #run_command(f"ssh {remote} which xmap", "Xmap not found on remote host")

    XMAP_BASE = "xmap -4 -M dnsx -p 53 --disable-syslog -v 1 --est-elements=100000000"
    OUTPUT_FIELDS = "saddr,daddr,ttl,app_success,udp_pkt_size,dns_rd,dns_tc,dns_aa,dns_opcode,dns_qr,dns_rcode,dns_cd,dns_ad,dns_z,dns_ra,dns_qdcount,dns_ancount,dns_nscount,dns_arcount,dns_unconsumed_bytes,dns_parse_err,repeat,cooldown,timestamp_str"
    OUTPUT_FILTER = "dns_rcode = 0 && dns_ra = 1"
    # How many retries / repetitions per IP
    PROBES_PER_IP = "--probes=1"
    DISCOVERY_SEED = 52
    # Filename to which xmap stdout is redirected
    LOGFILE_NAME = "discovery.log"
    SESSION_NAME = "discovery"
    STATE_FILE = "discovery.state"
    DRYRUN_DURATION = 30

    if args.command == "discover":

        # Check for state file
        files = os.listdir()
        if STATE_FILE in files:
          print(f"Found state file '{STATE_FILE}'.. is there an ongoing measurement?")
          exit(1)

        # Find good hosts
        good_hosts = find_good_hosts(host_handles)
        num_shards = len(good_hosts)
        print(f"Found {num_shards} hosts with Xmap installed")

        # Make sure no session is running
        print(f"Checking if any host has an ongoing measurement..")
        running_sessions = 0
        for h in good_hosts:
          if h.session_running(SESSION_NAME):
            print(f"Warning: a session with name '{SESSION_NAME}' seems to be running on host {h.ip}!")
            running_sessions += 1
        if running_sessions > 0:
          print(f"Please terminate all sessions with name '{SESSION_NAME}' before starting a new discovery.")
          exit(1)


        # Build command
        use_sharding = False # use sharding if --n is not set
        cmd = XMAP_BASE

        # Set rate (packets per second)
        cmd += f" -R {args.r}"

        # Set number of resolvers to discover
        if args.n is None:
          use_sharding = True
        else:
          cmd += f" -N {args.n}"
    
        # Set list of domains to probe per retry / repetition
        probe_args = [f"--probe-args=\"raw:recurse:text:A,{d}\"" for d in args.d]
        probes = f"-P {len(args.d)} {' '.join(probe_args)}"

        # Set output filename

        output = f"-O json -o {args.o}"

        cmd = f"{cmd} {output} --output-fields=\"{OUTPUT_FIELDS}\" --output-filter=\"{OUTPUT_FILTER}\" {PROBES_PER_IP} {probes}"
    

        # Check if there is an ongoing measurement (based on outfile)
        # Choose measurement command depending on whether --n is set
        # Start measurement

        # TODO: sharding only makes sense if ENTIRE space is scanned, i.e. if --n is set, don't do sharding
        with open(STATE_FILE, "w") as f:
            f.write(f"{args.o}\n")
            f.write(f"{num_shards}\n")
            if use_sharding and num_shards > 1:
              
              # Run individual shards
              # Only use SEED if we are sharding
              for i, host in enumerate(good_hosts, 0):
                host_cmd = f"{cmd} --seed={DISCOVERY_SEED} --shards={num_shards} --shard={i} | tee {LOGFILE_NAME}"
                if args.dry: # Overwrite command
                  host_cmd = f"sleep {DRYRUN_DURATION} && echo Host{i} > {args.o}-{i}"
                host.run_session(SESSION_NAME, host_cmd)
                f.write(f"{host.ip},{i}\n")
                print(host_cmd)
            else:
              # Run entire measurement on single host
              host = good_hosts[0]
              print("Running with single host")
              host_cmd = f"{cmd} | tee {LOGFILE_NAME}"
              if args.dry: # Overwrite command
                host_cmd = f"sleep {DRYRUN_DURATION} && echo Host0 > {args.o}"
              host.run_session(SESSION_NAME, host_cmd)
              print(f"send command to host {host.ip}:")
              f.write(f"{host.ip},0\n")
              print(cmd)

    #xmap -4 -M dnsx -p 53 -B 2000000000 --est-elements=100000000 --output-fields="saddr,daddr,ttl,app_success,udp_pkt_size,dns_rd,dns_tc,dns_aa,dns_opcode,dns_qr,dns_rcode,dns_cd,dns_ad,dns_z,dns_ra,dns_qdcount,dns_ancount,dns_nscount,dns_arcount,dns_unconsumed_bytes,dns_parse_err,repeat,cooldown,timestamp_str" --output-filter="dns_rcode = 0 && dns_ra = 1" --probes=1 -P 1 --probe-args="raw:recurse:text:A,ta6.ch" -O json -o out5.json --disable-syslog -v 1 --seed=52 --shards=6 --shard=5
    #nohup xmap -4 -p 53 --est-elements=100000 > test.json & echo $! > pid.txt

    #print("Running resolver discovery remotely")
    #run_command(f"ssh {remote} {xmap_cmd}", "Xmap crashed on remote host!")

    #print(f"Copying {OUTFILE} to local machine")
    #run_command(f"scp {remote}:~/{OUTFILE} .", f"Copying '{OUTFILE}' failed.")

    if args.command == "check":
      # TODO: check dependencies, try to install xmap, recheck
      pass

    if args.command == "kill":
      pass

    if args.command == "status":
        # Check all remote hosts
        for h in host_handles:
          print(f"Checking status of session '{SESSION_NAME}' on {h.ip}..", end=" ")
          if h.session_running(SESSION_NAME):
            print("running")
          else:
            print("not running")
        exit(0)


    if args.command == "retrieve":
        
        # Check for state file
        files = os.listdir()
        if STATE_FILE not in files:
          print(f"State file '{STATE_FILE}' not found.. start a measurement first!")
          exit(1)

        involved_hosts = []
        num_shards = 0
        outfile = None
        with open(STATE_FILE, "r") as f:
            outfile = f.readline().strip()
            num_shards = int(f.readline().strip())
            for line in f:
                ip, shard = line.strip().split(',')
                involved_hosts.append((ip, int(shard)))
        print(f"Found ongoing measurement with {num_shards} shards..")

        # Find handles for involved hosts
        good_hosts = [h for h in host_handles if h.ip in [ip for ip, _ in involved_hosts]]

        # Make sure all involved hosts have exited their session 
        print(f"Checking if any host has an ongoing measurement..")
        sessions_still_running = False
        for h in good_hosts:
            if h.session_running(SESSION_NAME):
                print(f"Session '{SESSION_NAME}' on {h.ip} is still running..")
                sessions_still_running = True

        if sessions_still_running:
          print(f"Not all sessions have finished yet.. retry later")
          exit(1)
        
        # Make sure client results file exists on all probes
        print(f"Checking if all probes produced a result file..")
        have_results = 0
        for h in good_hosts:
          i = [s for ip, s in involved_hosts if ip == h.ip][0]
          if h.file_exists(f"~/{outfile}"):
            have_results += 1
          else:
            print(f"Probe {h.ip} has no session running but {outfile} was not found.. failure")
        if have_results != len(good_hosts):
          print(f"Not all probes produced a result file.. check logs manually")
          exit(1)
        
        print(f"Collecting results from all probes..")
        complete_results = []
        for h in good_hosts:
          i = [s for ip, s in involved_hosts if ip == h.ip][0]
          status = []

          # Fetch results from remote
          status += [h.copy_file_from(f"~/{outfile}")]

          shutil.move(f"{outfile}", f"{outfile}-{i}")
        
        # Delete files
        os.remove(STATE_FILE)


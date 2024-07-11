#! /usr/bin/env python3

import os
import subprocess
import json
from multiprocessing import Pool
import time
import config as c

DRYRUN = False

def validate_query_tasks(qt:dict):
    assert('queries' in qt.keys())
    for q in qt['queries']:
      assert('rr' in q.keys())
      assert('vp' in q.keys())
      assert('query' in q.keys())



""" Takes a filename with a three letter prefix followed by an IP with dashes instead of dots (i.e. 1-2-3-4).
Returns the IP address (i.e. 1.2.3.4)
"""
def fn_to_ip(fn:str) -> str:
  octets = fn[3:].split("-")
  assert len(octets) == 4, f"Filename of file '{fn}' is not of the expect form."
  return ".".join(octets)

""" Takes a three letter prefix (e.g. tun) and an IP address (e.g. 1.2.3.4) and returns a filename (tun1-2-3-4)"""
def ip_to_fn(pre:str, ip:str) -> str:
  assert len(pre) == 3, f"Prefix {pre} must be of length 3"
  octets = ip.split(".")
  assert len(octets) == 4, f"IP address {ip} must contain 4 octets"
  return pre+"-".join(octets)

""" Takes a vantage point IP (vp) and launches a vantage point container"""
def run_vantage_point(vp:str):
  # Create Docker command
  docker_cmd = f"docker run --rm --privileged -v ./:/measurement {c.IMAGE_NAME}"
  # Prepare script arguments
  fn_in = ip_to_fn("tsk", vp)
  fn_out = ip_to_fn("out", vp)
  # Compose command
  cmd = f"{docker_cmd} {fn_in} {fn_out}"
  try:
    print(f"Starting query task for vantage point {vp}")
    r = subprocess.run(cmd.split(' '))
    r.check_returncode()
  except:
    print(f"Vantage point {vp} failed.")
  

if __name__ == "__main__":

  
  # Parse arguments
  import argparse
  parser = argparse.ArgumentParser(description="Run vantage points in docker containers and collect results")
  parser.add_argument("file", 
    help="json file containing a list of query tasks")
  parser.add_argument("localhost", 
    help="IP of machine this script is running on")
  parser.add_argument("outfile", 
    help="Output file for collected results")
  args = parser.parse_args()

  # Check if docker is installed 
  from shutil import which
  if which("docker") is None:
    print("docker does not seem to be installed..")
    exit(1)

  # Building Docker image
  assert "Dockerfile" in os.listdir(os.getcwd()), f"No Dockerfile found in {os.getcwd()}"
  try:
    print("Building docker image...", end=" ")
    cmd = f"docker build -t {c.IMAGE_NAME} ."
    r = subprocess.run(cmd.split(' '), capture_output=True)
    r.check_returncode()
  except:
    print(r.stdout.decode('utf-8'))
    print(f"Something went wrong while building the Docker Image...")
    exit(1)
  print("Done!")

  # NOTE: below process of separating taskfile by vantage points is a remnant of VPN based vantage points
  # Load existing VP configs
  vpn_vps = [fn_to_ip(fn) for fn in os.listdir(c.VPN_CONFIG_DIR)]

  # Make sure to process file streamlined
  with open(args.file, 'r') as f:
    filehandle_dict = dict()
    for line in f:
      
      # Load single task
      if line == None or line == "":
        continue
      q = json.loads(line)

      # Validate
      validate_query_tasks(q)
      vp = q['queries'][0]['vp']

      # Make sure the vp is either localhost or a VPN config exists
      if vp != args.localhost and vp not in vpn_vps:
        print(f"No configuration found for vantage point {vp}.. skipping")
        continue

      # Check if taskfile handle is already in dict, if not, open new file and add it to the dict
      if vp not in filehandle_dict.keys():
        fn = ip_to_fn("tsk", vp)
        filehandle_dict[vp] = open(f"{c.QUERY_TASK_DIR}/{fn}", 'w')

      # Write task to file
      filehandle_dict[vp].write(line)
    # Close all file handles
    for k in filehandle_dict.keys():
      filehandle_dict[k].close()

    # Run Vantage Points with a multiprocessing pool
    t_start = time.time()
    with Pool(c.NUM_VANTAGE_POINTS) as p:
      vps = [fn_to_ip(fn) for fn in os.listdir(c.QUERY_TASK_DIR) if fn.startswith("tsk")]
      results = p.map(run_vantage_point, vps)
    t_total = time.time() - t_start
    print(f"Total time: {str(t_total)}")

  # Gather tempoarary files
  outfiles = os.listdir(c.QUERY_TASK_DIR)

  # Sort outfiles, report successes and fails
  success = [fn for fn in outfiles if fn.startswith("out")]
  print(f"Gathered {len(success)} successful response files.")
  fail = [fn for fn in outfiles if fn.startswith("tsk")]
  print(f"{len(fail)} vantage points failed.")

  # Read all out files and write them to a single file streamlined
  print(f"Writing combined results to '{args.outfile}'")
  with open(args.outfile, 'w') as f_out:
    # Open successful files one by one
    for s in success:
      print(f"Writing {s} to combined file")
      with open(f"{c.QUERY_TASK_DIR}/{s}", 'r') as f_in:
        # Write each line in the successful result file to the combined file
        for line in f_in:
          if line != None and line != "":
            f_out.write(line)
  

  # Delete temporary files
  for f in outfiles:
    os.remove(f"{c.QUERY_TASK_DIR}/{f}")

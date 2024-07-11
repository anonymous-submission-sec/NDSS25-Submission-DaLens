#! /usr/bin/env python3


import os
import asyncio
import subprocess
import json
import time
import subprocess
import time
import datetime
import string
import random
import dns.resolver
import dns.asyncresolver
from StatusTracker import StatusTracker
import config as c


""" Parse an Answer object from the DNS stub resolver """
def parse_answer(ans:dns.resolver.Answer, ts_sent) -> dict:
  return {
    "class": dns.rdataclass.to_text(ans.rdclass),
    "name": str(ans.qname)[0:-1],
    "type": dns.rdatatype.to_text(ans.rdtype),
    "resolver": str(ans.nameserver),
    "protocol": "udp", # the resolver uses udp only by default
    "flags": dns.flags.to_text(ans.response.flags).split(' '),
    "data": [{
      "name":   a.split(' ')[0],
      "ttl":    a.split(' ')[1],
      "class":  a.split(' ')[2],
      "type":   a.split(' ')[3],
      "answer": a.split(' ')[4],
    } for a in ans.rrset.to_text().split('\n')],
    "status": dns.rcode.to_text(ans.response.rcode()),
    "timestamp": str(datetime.datetime.now()),
    "timestamp_sent": str(ts_sent),
  }


""" Return the static QNAME of the querytask, or if required, a randomly generated subdomain"""
def get_query_domain(qt) -> str:
  if qt['random_subdomains']:
      charset = string.ascii_lowercase + string.digits
      subdomain = ''.join(random.choice(charset) for _ in range(4))
      name = (f"{subdomain}.{qt['query']}")
  else:
      name = qt['query']
  return name

""" Given a resolver and a querytask dict, issue a single query to the nameserver"""
async def resolve_single(stub, qt, TIMEOUT):
  # Generate random subdomain if necessary
  name = get_query_domain(qt)

  # Resolve 
  try:
    ts_sent = datetime.datetime.now()
    ans = await stub.resolve(name, qt['type'], tcp=False, raise_on_no_answer=True, lifetime=TIMEOUT)
    return parse_answer(ans, ts_sent)
  
  # Resolver returned NXDOMAIN
  except dns.resolver.NXDOMAIN:
    return {"name": name,"type": qt['type'],"resolver": qt['rr'],"protocol": "udp",
      "status": "NXDOMAIN", "timestamp": str(datetime.datetime.now()), "timestamp_sent": str(ts_sent)}
  
  # Query timed out
  except dns.resolver.LifetimeTimeout:
    return {"name": name,"type": qt['type'],"resolver": qt['rr'],"protocol": "udp",
      "status": "TIMEOUT", "timestamp": str(datetime.datetime.now()), "timestamp_sent": str(ts_sent)}
  
  # Resolver returns NOERROR but does not provide an answer
  except dns.resolver.NoAnswer:
    return {"name": name,"type": qt['type'],"resolver": qt['rr'],"protocol": "udp",
      "status": "NOANSWER", "timestamp": str(datetime.datetime.now()), "timestamp_sent": str(ts_sent)}
  
  # Resolver returned SRVFAIL
  except dns.resolver.NoNameservers:
    return {"name": name,"type": qt['type'],"resolver": qt['rr'],"protocol": "udp",
      "status": "SRVFAIL", "timestamp": str(datetime.datetime.now()), "timestamp_sent": str(ts_sent)}


""" Run one querytask / measurement """
async def run_querytask(querytask:dict) -> list:
  assert('queries' in querytask.keys())

  results = []

  for qt in querytask['queries']:

    assert qt['vp'] == LOCALHOST, f"FATAL: Query task for vantage point {qt['vp']} is being run on {LOCALHOST}"

    if qt['concurrent']:
      # Run asynchronously
      assert False, "Concurrent execution not tested"
      results = asyncio.run(run_async(qt, TIMEOUT))
      num_queries_sent = len(results)
      
    else:
      # Create and configure stub resolver
      stub = dns.asyncresolver.Resolver()
      stub.nameservers = [qt['rr']]
      stub.cache = None
      stub.retry_servfail = False # whether to retry on SRVFAIL
      stub.timeout = int(qt['timeout']) # seconds to wait on server
      stub.lifetime = int(qt['timeout']) # seconds for stub to try
      stub.use_search_by_default = False # make sure stub does not use system resolver

      if not qt['recursion_desired']:
        # default is None, which uses Message constructor default, which is only RD, QR bit needs to be 0 (query)
        stub.flags = 0
        #stub.flags ^= dns.flags.RD # flip recursion desired bit

      # Perform timed queries
      num_queries_sent = 0
        
      tracker = StatusTracker(qt, c.MAX_FAILS, c.WAIT_POLICY, c.ABORT_POLICY)

      for _ in range(int(qt['repeat'])):

        # Resolve single query
        res = await resolve_single(stub, qt, int(qt['timeout']))

        # TODO: assert timedelta between sent and received is more than sleep
        
        if tracker.should_abort(res): # Check whether to abort
          break

        if tracker.should_wait(res): # Check whether to wait
          await asyncio.sleep(int(qt['wait']))
        
        # Save result
        results.append(res)
        num_queries_sent += 1 # TODO: obsolete?
      
      if int(qt['wait_after']) > 0:
        await asyncio.sleep(int(qt['wait_after']))



    # Compile full task results
    task_results = {
      "pattern": querytask['pattern'],
      "queries": querytask['queries'],
      "nameservers": querytask['nameservers'],
      "responses": results,
    }
    
  return task_results

""" Get the public IP of the container using an EchoIP service"""
def get_public_ip() -> str:
  cmd = ["curl", c.ECHOIP_URL]
  try:
    r = subprocess.run(cmd, capture_output=True)
    r.check_returncode()
    return r.stdout.decode('ascii')
  except:
    print("Checking public IP failed, is 'curl' installed in the container?")
    exit(1)

"""Assert expected public_ip equals the observed public IP"""
def check_public_ip(public_ip: str) -> None:
  observed_ip = None
  try:
    cmd = ["curl", c.ECHOIP_URL]
    r = subprocess.run(cmd, capture_output=True)
    r.check_returncode()
    # If IP does not match, wait and retry
    if public_ip != r.stdout.decode('ascii'):
      time.sleep(5)
      r = subprocess.run(cmd, capture_output=True)
      r.check_returncode()
    # Extract observed public IP
    observed_ip = r.stdout.decode('ascii')
  except:
    print("Checking public IP failed, is 'curl' installed in the container?")
    exit(1)
  if public_ip != observed_ip:
    print(f"VPN for vantage point {public_ip} does not seem to work..")
    exit(1)

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

""" Check if all workers are still running, if not, exit with error"""
def check_workers(workers:list, log_writer) -> None:
  for w in workers:
    try:
      e = w.exception()
      if e == None: # Worker terminated without exception
        log_writer.write(f"Worker terminated early\n")
        log_writer.flush()
        exit(1)
      else: # Worker terminated with exception
        log_writer.write(f"Worker failed with exception: {e}\n")
        log_writer.flush()
        exit(1)
    except asyncio.CancelledError: # Worker was cancelled
      log_writer.write(f"Worker cancelled\n")
      log_writer.flush()
      exit(1)
    except asyncio.InvalidStateError as e: # Worker is still running
      continue

""" Print status to log file"""
def print_status(t_start, tasks_done, num_tasks, log_writer):
  time_since_start = time.time() - t_start
  rate = tasks_done / (time_since_start)
  if rate > 0:
    time_left = (num_tasks - tasks_done) / rate
  else:
    time_left = 0
  time_format = lambda x: time.strftime('%H:%M:%S', time.gmtime(x))
  status = f"{time_format(time_since_start)}: {tasks_done} out of {num_tasks}, {tasks_done / num_tasks * 100} % done, left: {time_format(time_left)}\n"
  log_writer.write(status)
  log_writer.flush()

""" Coroutine worker that repeatedly takes a query task from the queue and runs it"""
async def querytask_worker(task_queue:asyncio.Queue, result_queue:asyncio.Queue):
  while True:
    task = await task_queue.get()

    # Process task
    result = await run_querytask(task)

    await result_queue.put(result)
    # Confirm task is done
    task_queue.task_done()


""" Coroutine manager that puts all query tasks in a queue and runs them concurrently"""
async def execute_tasks(task_file:str, outfile:str):
  
  task_queue = asyncio.Queue(maxsize=2*c.NUM_WORKERS)
  result_queue = asyncio.Queue(maxsize=2*c.NUM_WORKERS)
  tasks_issued = 0
  tasks_done = 0

  # Count tasks beforehand, used to terminate loop
  num_tasks = 0
  with open(f"{c.QUERY_TASK_DIR}/{args.infile}", 'r') as f:
    while True:
      line = f.readline()
      if line == "\n": # empty line
        continue
      if line == "": # end of file
        break
      num_tasks += 1
  
  
  log_file = ip_to_fn('log', LOCALHOST) 
  log_writer = open(f"{c.QUERY_TASK_DIR}/{log_file}", "w")
  out_writer = open(f"{c.QUERY_TASK_DIR}/{outfile}", "w")
  task_reader = open(f"{c.QUERY_TASK_DIR}/{task_file}", "r")

  
  while True: # Fill queue initially
    if not task_queue.full(): # Check for space before reading task from file
      line = task_reader.readline()
      if line == "\n": # empty line
        continue
      if line == "": # end of file
        break
      qt = json.loads(line)
      
      try: # Put new task in queue
        task_queue.put_nowait(qt)
        tasks_issued += 1
        # Go to top of loop
      except asyncio.QueueFull: # Should never happen
        log_writer.write(f"Something is messed up with queuing\n")
        exit(1)

    else: # Task queue full
      break

  # Start timer
  t_start = time.time()

  # Start workers
  workers = []
  for _ in range(c.NUM_WORKERS):
    workers.append(asyncio.create_task(querytask_worker(task_queue, result_queue)))

  # Periodically check status, retrieve results, issue new tasks
  while tasks_done < num_tasks:

    await asyncio.sleep(10)
    
    if c.DEBUG:
      check_workers(workers, log_writer) # Check if workers are still running

    print_status(t_start, tasks_done, num_tasks, log_writer) # Compute metadata, print status
    
    while True: # Retrieve finished tasks
      try:
        # Check if any tasks are done
        result = result_queue.get_nowait()
        tasks_done += 1
        # Write result to output file
        out_writer.write(json.dumps(result) + '\n')
      except asyncio.QueueEmpty:
        # If no tasks are done, break out of this loop
        break
    
    while True: # Issue as many new tasks as possible
      if tasks_issued == num_tasks: # If all tasks have been issued, break out of this loop
        break
      
      if not task_queue.full(): # Check for space before reading task from file
        line = task_reader.readline()
        if line == "\n": # empty line
          continue
        if line == "": # end of file
          break
        qt = json.loads(line)

        try: # Put new task in queue
          task_queue.put_nowait(qt)
          tasks_issued += 1
        except asyncio.QueueFull: # Should not happen due to check above
          log_writer.write(f"Something is messed up with queuing\n")
          exit(1)

      else: # Task queue full
        break

  # All tasks are done, cancel workers
  log_writer.write("All tasks done, cancelling workers\n")
  log_writer.flush()
  for w in workers:
    w.cancel()

  # Wait for workers to finish
  log_writer.write("Waiting for workers to finish\n")
  log_writer.flush()
  await asyncio.gather(*workers, return_exceptions=True)
  log_writer.write("Done\n")
  log_writer.flush()

  log_writer.close()
  out_writer.close()
  task_reader.close()
  
LOCALHOST = None

if __name__ == "__main__":
  
  # This file runs inside a docker container
  #
  # Working directory: /measurement
  # VPN config directory: mounted under /measurement/configs
  # Task file directory: mounted under /measurement/tasks
  #
  # it is responsible for opening the VPN connection and issueing the queries
  # so far: assume each query task is performed entirely from one vantage point


  # Parse arguments
  import argparse
  parser = argparse.ArgumentParser(description="Run single vantage point in docker container and store result to file")
  parser.add_argument("infile", 
    help="json file containing a list of query tasks")
  parser.add_argument("outfile", 
    help="json file containing client responses")
  args = parser.parse_args()

  
  # Check dependencies
  from shutil import which
  for p in ["openvpn", "curl"]:
    if which(p) is None:
      print(f"{p} is not installed in the container, has the Dockerfile been modified?")

  # Check container environment is correct
  assert os.getcwd() == "/measurement", "cwd in the container is wrong, has the Dockerfile been modified?"
  assert c.VPN_CONFIG_DIR in os.listdir(os.getcwd()), f"{c.VPN_CONFIG_DIR} has not been found. Is the directory mounted correctly?"
  assert c.QUERY_TASK_DIR in os.listdir(os.getcwd()), f"{c.QUERY_TASK_DIR} has not been found. Is the directory mounted correctly?"

  LOCALHOST = get_public_ip()

  ## Gather all vantage point IPs, make sure there is only one
  #vp = list()
  #for q in queries:
  #  # Collect vantage points for query task q
  #  vp_per_task = [e['vp'] for e in q['queries']]
  #  assert len(vp_per_task) == 1, "Multiple vantage points within single query task is not supported!"
  #  vp += vp_per_task
  ## Collect unique vantage points across all query tasks
  #vp = list(set(vp))
  #assert len(vp) == 1, "One container can only run one vantage point at a time"
  #vp = vp[0]

  ## Check if VPN is required
  #if vp != args.localhost:
  #  
  #  # Load VPN configurations
  #  vpn_configs = [fn_to_ip(fn) for fn in os.listdir(VPN_CONFIG_DIR)]
  #  if vp not in vpn_configs:
  #    print(f"No VPN config for vantage point {vp} found..")
  #    exit(1)

  #  # Start VPN
  #  config_file = ip_to_fn('tun', vp)
  #  cmd = f"openvpn --config {VPN_CONFIG_DIR}/{config_file} --auth-user-pass creds.txt --data-ciphers AES-128-CBC --daemon"
  #  try:
  #    r = subprocess.run(cmd.split(' '))
  #    r.check_returncode()
  #  except:
  #    print(f"Starting the VPN daemon failed, something must be wrong with the config file {config_file}")
  #    exit(1)

  ## Make sure the expected vantage point IP matches externally observed public IP
  #check_public_ip(vp)
  
  # Perform query tasks
  results = asyncio.run(execute_tasks(args.infile, args.outfile))
  
  # Remove task file if finished successfully
  os.remove(f"{c.QUERY_TASK_DIR}/{args.infile}")

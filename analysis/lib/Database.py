
import os
import json
import csv
import lib.BasicMeasurement as basic
from lib.ZoneConf import ZoneConf
from lib.ResolverMeasurement import ResolverMeasurement

class Database:
  
  """ Class to handle a database of measurements. db_path should be the root directory of the database."""
  def __init__(self, db_path):
    
    # Root directory of the database
    self.db_path = f"{db_path[:-1]}" if db_path.endswith("/") else f"{db_path}"

    # Check if database directory exists, if not, create it
    if os.path.exists(self.db_path):
      assert os.path.exists(f"{self.db_path}/data"), f"Database path {self.db_path} does not contain a 'data' folder!"
      assert os.path.exists(f"{self.db_path}/settings"), f"Database path {self.db_path} does not contain a 'settings' folder!"
      assert os.path.exists(f"{self.db_path}/zoneconf"), f"Database path {self.db_path} does not contain a 'zoneconf' folder!"
    else:
      os.makedirs(self.db_path)
      os.makedirs(f"{self.db_path}/data")
      os.makedirs(f"{self.db_path}/settings")
      os.makedirs(f"{self.db_path}/zoneconf")

    self.data_dir = f"{self.db_path}/data"
    self.LOG = open(f"{self.db_path}/errorlog", 'w')

  def __del__(self):
    self.LOG.close()
  

  """ Take a resolver IP (ns) and returns the path to the folder containing the measurements of that resolver.
  Args:
    rr: resolver IP
  Returns:
    path to the folder containing the measurements of that resolver"""
  def ns_folder(self, rr):
    folder = ".".join(rr.split(".")[0:2])
    return os.path.join(self.data_dir, folder, rr)

  """ Traverse directory and yield lowest level dirs of resolvers with format x.x.x.x.
  Args:
    full_path: default=False, whether to yield the full path to the resolver directory or just the resolver IP
  Returns:
    resolver IP if full_path=False 
    or 
    path to the resolver directory if full_path=True
  """
  def traverse_resolvers(self, full_path=False):
    for root, dirs, files in os.walk(self.data_dir):
      for dir in dirs:
        if len(dir.split(".")) == 4:
          yield os.path.join(root, dir) if full_path else dir

  def traverse_files(self, prefix="", suffix=""):
    for root, dirs, files in os.walk(self.data_dir):
      for file in files:
        if file.startswith(prefix) and file.endswith(suffix):
          yield os.path.join(root, file)


  """ Process any datasets of a single resolver. 
  Used to evaluate any number of measurement files of a single resolver (e.g. data/1.2/1.2.3.4/enum and data/1.2/1.2.3.4/qmin)
  Args:
    rr: resolver IP
    funcs: dict of dataset->{"process": proc_func, "filter": filter_func}, 
    zoneconf: ZoneConf object belonging to the measurements. Only required if process_function needs it and zoneconfiguration is not embedded in BasicMeasurement
    group_by_rr: default=False, whether to produce one dict for the file (grouped) or one dict for each line in the file (i.e. per (rr,vp) tuple)
  Returns:
    dict of vantage point -> result if group_by_rr=False
    or
    dict of result if group_by_rr=True
  """
  def process_resolver(self, rr, funcs:dict, zoneconf=None, group_by_rr=False):
    dir = self.ns_folder(rr)
    patterns = os.listdir(dir)
    r = {}
    for p in patterns:
      if p not in funcs:
        continue
      file = os.path.join(dir, p)
      r = self.process_file(file, funcs[p]['process'], funcs[p]['filter'], zoneconf, group_by_rr)
    return r

  """ Process single dataset file. Used to evaluate a single measurement file (e.g. data/1.2/1.2.3.4/enum)
  Args:
    file: filepath of measurement file to be processed
    process_func: agg_xxx() function that takes a BasicMeasurement and returns a dict
    filter_func: function of BasicMeasurement to decide whether to discard a certain BasicMeasurement
    zone_conf: ZoneConf object belonging to the measurements. Only required if process_function needs it and zoneconfiguration is not embedded in BasicMeasurement
    group_by_rr: default=False, whether to produce one dict for the file (grouped) or one dict for each line in the file (i.e. per (rr,vp) tuple)
  Returns:
    dict of vantage point -> result if group_by_rr=False
    or
    dict of result if group_by_rr=True
    """
  def process_file(self, file, process_func, filter_func, zoneconf=None, group_by_rr=False):
    try:
      with open(file, 'r') as f:
        # Load
        data = []
        for i, l in enumerate(f):
          try:
            measurement = json.loads(l)
            bm = basic.BasicMeasurement(measurement, zoneconf=zoneconf)
            data.append(bm)
            #data.append(basic.BasicMeasurement(json.loads(l), zoneconf=zoneconf))
          except json.JSONDecodeError as e:
            self.LOG.write(f"Error processing line {i} in file {file}: {e}\n")
            continue
          except Exception as e:
            self.LOG.write(f"Error instantiating BasicMeasurement on line {i} in file {file}: {e}\n")
            continue
        #data = [basic.BasicMeasurement(json.loads(l), zoneconf=zoneconf) for l in f]
        data = [d for d in data if filter_func(d)]

        if len(data) == 0: # If no valid measurement, return None
          return None

        # Process
        if group_by_rr:   # Return one dict for recursive resolver
          rr_measurement = ResolverMeasurement(data)
          r = process_func(rr_measurement)
        else:
          # Return dict of vantage point -> result
          r = {}
          for d in data:
            a = process_func(d)
            if a is None:
              continue
            r[d.get_vantagepoint()] = process_func(d)

        return r
    except Exception as e:
      self.LOG.write(f"Error opening file {file}: {e}\n")
      return None


  """ Traverse database directory and process some dataset files according to 'funcs'. Write results to out_file.
  Args:
    out_file: output file
    funcs: dict of dataset->agg.Process object
    group_by_rr: default=False, whether to produce one dict for the file (grouped) or one dict for each line in the file (i.e. per (rr,vp) tuple)
    filetype: default='csv', output file type
  Returns:
    None
  """
  def process_multiple_datasets(self, out_file, funcs:dict, group_by_rr=False, filetype='csv'):

    with open(out_file, 'w') as of:

      # Initialize writer
      writer = None
      if filetype == "csv":
        # Retrieve field names for writing csv header
        #fields = [field for dataset in funcs for field in funcs[dataset]['process'](None, get_fields=True)]
        fields = [f for p in funcs.values() for f in p.get_fields()]
        writer = csv.DictWriter(of, fieldnames=["resolver", "vantagepoint"] + fields)
        writer.writeheader()
      elif filetype == 'json':
        writer = of
      else:
        assert False, f"Unknown filetype: {filetype}"

      for dir in self.traverse_resolvers(full_path=True):
        # 'dir' is the path to the recursive resolver directory whose name is the IP of the rr
        datasets = os.listdir(dir) # List of datasets in the resolver directory (no full path)

        agg = {} # Dict of vp->aggregated_ results, one entry corresponds to one line in the output file
        for p in datasets:
          
          if p not in funcs:  # if pattern p was not declared to be processed, skip
            continue

          # Otherwise, process resolver measurement file of pattern p
          file = os.path.join(dir, p)
          #r = self.process_file(file, funcs[p]['process'], funcs[p]['filter'], group_by_rr=group_by_rr)
          r = self.process_file(file, funcs[p].process, funcs[p].filter, group_by_rr=group_by_rr)

          if r is None: # Case if no vantage point of this rr measurement produced a valid result (can happen due to filter)
            continue # to next pattern

          # Case of group_by_ns = False
          if group_by_rr == False:
            # r is a dict of vp-> results
            for k, v in r.items(): # merge r with agg
              agg[k] = {**agg[k], **v} if k in agg else v
          else:
            # r is a dict of results
            for k, v in r.items():
              assert k not in agg, f"Duplicate aggregate key detected: {k}!"
              agg[k] = v


        if agg is None: # Case if no pattern from any vantage point produced a valid result for their respective analysis functions
          continue

        # Write
        if filetype == 'csv':
          for k, v in agg.items():
            # agg is a dict vp->results 
            # dir is the path to the recursive resolver directory whose name is the IP of the rr
            row = {
              "resolver": dir.split("/")[-1],
              "vantagepoint": k,
              **v
            }

            writer.writerow(row)
        elif filetype == 'json':
          if agg == {}: # Do not print empty results
            continue
          writer.write(json.dumps(agg) + "\n")
        else:
          assert False, "Unknown filetype"

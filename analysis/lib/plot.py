#! /usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib.dates as pltdates
import numpy as np
from collections import Counter
from lib.BasicMeasurement import BasicMeasurement
from lib.ResolverMeasurement import ResolverMeasurement as NameserverMeasurement
import datetime

# Type aliases
from typing import List, Dict

BasicMeasurementList = List[BasicMeasurement]
NameserverMeasurementList = List[NameserverMeasurement]

""" This function takes a list of measurements and creates a subplot for each of those measurements"""
def plot_subplot(data:list(), subplot_func:callable, sub_x=4, sub_y=3):
  # Create a subplot for each nameserver
  fig, ax = plt.subplots(ncols=sub_x, nrows=sub_y)
  fig.subplots_adjust(hspace=0.2)
  #assert sub_x*sub_y <= len(data)
  for i in range(sub_x):
    for j in range(sub_y):
      ind = i*sub_y + j
      if ind >= len(data):
        break
      subplot_func(data[ind], ax[j,i])
  plt.show()

""" This function takes a list of basic measurements and creates a basic egress resolver subplot for each measurement"""
def subplot_egress_basic(data:BasicMeasurement, ax):
  counter = Counter(data.get_egress_ips())
  names = counter.keys()
  frequencies = counter.values()
  
  x_coordinates = np.arange(len(counter))
  ax.bar(x_coordinates, frequencies, align='center')

  ax.xaxis.set_major_locator(plt.FixedLocator(x_coordinates))
  ax.xaxis.set_major_formatter(plt.FixedFormatter(list(names)))
  #ax.hist(d.get_egress_ips(), d.get_unique_egress_ips())
  #counts, bins = np.histogram(d.get_egress_ips())
  #ax[i,j].hist(counts)
  ax.set_title(data.get_resolver())
  ax.tick_params(labelrotation=30)
  return ax

def subplot_response_latency(data:BasicMeasurement, ax):

  resp = data.d['responses']

  x = []
  y = []

  for r in resp:
    x.append(r['timestamp'])
    y.append((r['timestamp'] - r['timestamp_sent']).total_seconds())

  ax.scatter(x, y)

  ax.set_title(f"Response Latency for {'-'.join(data.get_resolvers())}")
  ax.tick_params(labelrotation=30)
  return ax

""" This function takes a basic measurement and creates a plot with timestamps on the x-axis and logentry indicator on the y-axis"""
def subplot_order_rd0based(data:BasicMeasurement, ax):

  # Make sure basic measurement follows the structure required for this function
  assert data.cs_order_rd0based(), "Measurement not eligible for 'order' functions"
  
  # A flatten pattern has 4 stages
  # 1. Cache filling of ns0
  # 2. Probing ns1
  # 3. Cache filling of ns1
  # 4. Probing ns0
  # Consequently, index 0 and 3 concern ns0 and index 1 and 2 concern ns1
  queryplan = data.d['queries']
  ns0 = queryplan[0]['rr']
  ns1 = data.d['queries'][1]['rr']
  
  ns0_color = "blue"
  ns1_color = "red"
  response_label = "Responses"
  logentry_label = "Logentries"
  marker = "x"

  # Plot responses
  delta = data.get_ts_delta() # used to align response and logentry timestamps
  
  # Plot ns0 responses
  ns0_ts = [r['timestamp_sent'] for r in data.d['responses'] if r['resolver'] == ns0] # get timestamps of ns0 responses
  ns0_ts = [t-delta for t in ns0_ts] # normalize response timestamps
  ax.scatter(ns0_ts, [response_label]*len(ns0_ts), marker=marker, color=ns0_color, label=ns0)

  # Plot cache filling of ns0
  num_cache_filling = queryplan[0]['repeat'] # num queries in cache filling stage of ns0
  num_probing = queryplan[3]['repeat'] # num queries in probing stage of ns0
  assert len(ns0_ts) == num_cache_filling + num_probing, "Number of responses does not match number of queries"
  wait_after_first = datetime.timedelta(seconds=queryplan[0]['wait_after']) # padding time after cache filling of ns0
  # Cache filling stage of ns0 is from first query sent to last query sent (should be received!) plus padding time
  ax.axvspan(ns0_ts[0], ns0_ts[num_cache_filling-1]+wait_after_first, alpha=0.5, color=ns0_color, label=f"Cache filling {ns0}")

  # Plot ns1 responses
  ns1_ts = [r['timestamp_sent'] for r in data.d['responses'] if r['resolver'] == ns1] # get timestamps of ns1 responses
  ns1_ts = [t-delta for t in ns1_ts] # normalize response timestamps
  ax.scatter(ns1_ts, [response_label]*len(ns1_ts), marker=marker, color=ns1_color, label=ns1)
  
  # Plot cache filling of ns1
  num_probing = queryplan[1]['repeat']
  num_cache_filling = queryplan[2]['repeat']
  assert len(ns1_ts) == num_cache_filling + num_probing, "Number of responses does not match number of queries"
  wait_after_second = datetime.timedelta(seconds=queryplan[2]['wait_after'])
  ax.axvspan(ns1_ts[num_probing], ns1_ts[-1]+wait_after_second, alpha=0.5, color=ns1_color, label=f"Cache filling {ns1}")

  # Plot Buffer time
  buffer_time = datetime.timedelta(seconds=queryplan[1]['wait_after'])
  # Buffertime is 'buffer_time' seconds before first probing query of ns1
  ax.axvspan(ns1_ts[num_probing]-buffer_time, ns1_ts[num_probing], alpha=0.5, color='green', label="Buffer time")

  # Plot Logentries
  stages = data.order_group_logentries()
  
  # Plotting log entries to first nameserver
  assert stages[0]['rr'] == stages[3]['rr']
  ns0_ts = [e['timestamp'] for e in stages[0]['logentries']] + [e['timestamp'] for e in stages[3]['logentries']]
  ax.scatter(ns0_ts, [logentry_label]*len(ns0_ts), marker=marker, color=ns0_color)

  # Plotting log entries to second nameserver
  assert stages[1]['rr'] == stages[2]['rr']
  ns1_ts = [e['timestamp'] for e in stages[1]['logentries']] + [e['timestamp'] for e in stages[2]['logentries']]
  ax.scatter(ns1_ts, [logentry_label]*len(ns1_ts), marker=marker, color=ns1_color)

  result = data.order_rd0based() 
  result = result if result != None else ["None"]
  ax.legend()
  ax.set_title(f"{'->'.join(result)}")
  #ax.tick_params(labelrotation=30)
  return ax


""" This function takes a basic measurement and creates a plot with timestamps on the x-axis and logentry indicator on the y-axis"""
def subplot_order_cachebased(data:BasicMeasurement, ax):

  # Make sure basic measurement follows the structure required for this function
  assert data.cs_order_cachebased(), "Measurement not eligible for 'flatten' functions"
  
  # A flatten pattern has 4 stages
  # 1. Cache filling of ns0
  # 2. Probing ns1
  # 3. Cache filling of ns1
  # 4. Probing ns0
  # Consequently, index 0 and 3 concern ns0 and index 1 and 2 concern ns1
  queryplan = data.d['queries']
  ns0 = queryplan[0]['rr']
  ns1 = data.d['queries'][1]['rr']
  
  ns0_color = "blue"
  ns1_color = "red"
  response_label = "Responses"
  logentry_label = "Logentries"
  marker = "x"

  # Plot responses
  delta = data.get_ts_delta() # used to align response and logentry timestamps
  
  # Plot ns0 responses
  ns0_ts = [r['timestamp_sent'] for r in data.d['responses'] if r['resolver'] == ns0] # get timestamps of ns0 responses
  ns0_ts = [t-delta for t in ns0_ts] # normalize response timestamps
  ax.scatter(ns0_ts, [response_label]*len(ns0_ts), marker=marker, color=ns0_color, label=ns0)

  # Plot cache filling of ns0
  num_cache_filling = queryplan[0]['repeat'] # num queries in cache filling stage of ns0
  num_probing = queryplan[3]['repeat'] # num queries in probing stage of ns0
  assert len(ns0_ts) == num_cache_filling + num_probing, "Number of responses does not match number of queries"
  wait_after_first = datetime.timedelta(seconds=queryplan[0]['wait_after']) # padding time after cache filling of ns0
  # Cache filling stage of ns0 is from first query sent to last query sent (should be received!) plus padding time
  ax.axvspan(ns0_ts[0], ns0_ts[num_cache_filling-1]+wait_after_first, alpha=0.5, color=ns0_color, label=f"Cache filling {ns0}")

  # Plot ns1 responses
  ns1_ts = [r['timestamp_sent'] for r in data.d['responses'] if r['resolver'] == ns1] # get timestamps of ns1 responses
  ns1_ts = [t-delta for t in ns1_ts] # normalize response timestamps
  ax.scatter(ns1_ts, [response_label]*len(ns1_ts), marker=marker, color=ns1_color, label=ns1)
  
  # Plot cache filling of ns1
  num_probing = queryplan[1]['repeat']
  num_cache_filling = queryplan[2]['repeat']
  assert len(ns1_ts) == num_cache_filling + num_probing, "Number of responses does not match number of queries"
  wait_after_second = datetime.timedelta(seconds=queryplan[2]['wait_after'])
  ax.axvspan(ns1_ts[num_probing], ns1_ts[-1]+wait_after_second, alpha=0.5, color=ns1_color, label=f"Cache filling {ns1}")

  # Plot Buffer time
  buffer_time = datetime.timedelta(seconds=queryplan[1]['wait_after'])
  # Buffertime is 'buffer_time' seconds before first probing query of ns1
  ax.axvspan(ns1_ts[num_probing]-buffer_time, ns1_ts[num_probing], alpha=0.5, color='green', label="Buffer time")

  # Plot Logentries
  stages = data.order_group_logentries()
  
  # Plotting log entries to first nameserver
  assert stages[0]['rr'] == stages[3]['rr']
  ns0_ts = [e['timestamp'] for e in stages[0]['logentries']] + [e['timestamp'] for e in stages[3]['logentries']]
  ax.scatter(ns0_ts, [logentry_label]*len(ns0_ts), marker=marker, color=ns0_color)

  # Plotting log entries to second nameserver
  assert stages[1]['rr'] == stages[2]['rr']
  ns1_ts = [e['timestamp'] for e in stages[1]['logentries']] + [e['timestamp'] for e in stages[2]['logentries']]
  ax.scatter(ns1_ts, [logentry_label]*len(ns1_ts), marker=marker, color=ns1_color)

  result = data.order_cachebased() 
  result = result if result != None else ["None"]
  ax.legend()
  ax.set_title(f"{'->'.join(result)}")
  #ax.tick_params(labelrotation=30)
  return ax



""" This function takes a NameserverMeasurement object and creates a vantage point per egress ip subplot"""
def subplot_vp_per_egress(data:NameserverMeasurement, ax):
  #assert isinstance(data, NameserverMeasurement), "Data must be a NameserverMeasurement object"
  
  # Constants
  BAR_WIDTH = 0.5
  
  unique_egress_all = data.get_unique_egress_ips()
  num_unique_egress = len(unique_egress_all)
  vps = data.get_vantagepoints()

  # Create a dict of vantage point to list of counts of egress ips
  vp_to_egress_count = dict(zip(vps, [np.zeros(num_unique_egress) for _ in range(len(vps))]))

  for vp in vps:
    counter = Counter(data.get_egress_ips(vp))
    for i, egressIP in enumerate(unique_egress_all, 0):
      vp_to_egress_count[vp][i] = counter[egressIP]

  # Height for stacking the bars
  bottom = np.zeros(num_unique_egress)

  # Plot all egress resolver bars for each vantage point
  for vp, counts in vp_to_egress_count.items():
      p = ax.bar(unique_egress_all, counts, BAR_WIDTH, label=vp, bottom=bottom)
      bottom += counts

  ax.set_title(f"Nameserver at {data.get_resolver()}")
  ax.legend(loc="upper right")
  return ax

def subplot_ttl_line(data:BasicMeasurement, ax):
  assert data.cs_ttl_line(), "Measurement not eligible for 'shared' functions"

  # For each response, plot timestamp on x axis and ttl on y axis
  # Extract timestamps and ttls from responses
  timestamps = [r['timestamp_sent'] for r in data.d['responses'] if r['status'] == 'NOERROR']
  ttls = [int(r['data'][0]['ttl']) for r in data.d['responses'] if r['status'] == 'NOERROR']
  #ax.invert_yaxis()
  #ax.plot(timestamps, ttls, marker='x', linestyle='')
  ax.scatter(timestamps, ttls, marker='x')
  # Plot a vertical line for each logentry, normalized to the timestamp of the first response
  delta = data.get_ts_delta()
  for e in data.d['logentries']:
    ax.axvline(e['timestamp']-delta, color='red', linestyle='dashed')
  # draw a diagonal line for each logentry with slope -1, from top to bottom of plot
  max_ttl = int(data.d['zone'][0]['ttl'])
  for e in data.d['logentries']:
     ax.plot([e['timestamp']-delta, e['timestamp']-delta+datetime.timedelta(seconds=max_ttl)], [max_ttl, 0], color='green', linestyle='dashed')

  ax.set_title(f"{data.get_resolvers()} Shared Frontend: {data.cs_ttl_line()}")
  ax.tick_params(labelrotation=30)

  return ax

def subplot_logentry_timing(data:BasicMeasurement, ax):
  #assert data.cs_ttl_line(), "Measurement not eligible for 'shared' functions"

  # For each response, plot timestamp on x axis and ttl on y axis
  # Extract timestamps and ttls from responses
  #timestamps = [r['timestamp_sent'] for r in data.d['responses'] if r['status'] == 'NOERROR']
  #ttls = [int(r['data'][0]['ttl']) for r in data.d['responses'] if r['status'] == 'NOERROR']
  #ax.invert_yaxis()
  #ax.plot(timestamps, ttls, marker='x', linestyle='')
  #ax.scatter(timestamps, ttls, marker='x')
  # Plot a vertical line for each logentry, normalized to the timestamp of the first response
  delta = data.get_ts_delta()
  for e in data.d['logentries']:
    t = e['timestamp']-delta
    #print(t.second)
    #print(t.microsecond / 10**6)
    t = t.second + t.microsecond / 10**6
    ax.axvline(t, color='red', linestyle='dashed')

  ax.set_title(f"{data.get_resolver()}")
  ax.tick_params(labelrotation=30)
  ax.xaxis.set_major_formatter(pltdates.DateFormatter("%S.%f"))

  return ax

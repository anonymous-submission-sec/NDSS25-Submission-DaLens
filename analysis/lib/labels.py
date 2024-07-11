# /usr/bin/env python3

import os, sys
import csv

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

#from common import jsonline as io

class Labeler():

  """ Initialize Labeler with csv files in 'labeldir'"""
  def __init__(self, labeldir):
    
    KEY_LABEL = "organization"
    KEY_MATCH = "ip"

    label_files = os.listdir(labeldir)
    assert all([f.endswith(".csv") for f in label_files]), f"Labeldir '{labeldir}' contains other filetypes than .csv"

    # Initialize KEY_MATCH -> KEY_LABEL mapping
    self.labels = {}

    for f in label_files:
      # Process one label file
      with open(f"{labeldir}/{f}", "r") as f:
        reader = csv.DictReader(f)
        for d in reader:
          assert KEY_LABEL in d.keys(), f"Labelfile '{f}' in folder '{labeldir}' does not have a field '{KEY_LABEL}'"
          assert KEY_MATCH in d.keys(), f"Labelfile '{f}' in folder '{labeldir}' does not have a field '{KEY_MATCH}'"

          # Add label to mapping self.labels
          if d['ip'] not in self.labels.keys():
            self.labels[d[KEY_MATCH]] = d[KEY_LABEL]
          else:
            print(f"Warning: multiple labels for {d['ip']}.. skipping")

  """ Label a list of dictionaries. 
    - 'labelfield' is the dict key where the label should be placed
    - 'matchfield' is the dict key that should be looked up in the database
    - 'default_label' is the string that should be used if no match is found
    Returns None (processes dict list in-situ)
  """
  def label(self, dictlist:list, labelfield:str, matchfield:str, default_label="") -> None:
    
    # Print warning if labelfield not already present in dictionary  
    assert len(dictlist) > 0, "List of dictionaries is empty"
    if labelfield not in dictlist[0].keys():
        print(f"Warning: Dictionaries are missing labelfield '{labelfield}'. Add it to control key order.")

    # Process all dictionaries 
    for d in dictlist:
      assert matchfield in d.keys(), f"One dictionary does not have the matchfield '{matchfield}'"

      # Try to match, if successful, use label from self.labels, otherwise use default_label
      if d[matchfield] in self.labels.keys():
        label = self.labels[d[matchfield]]
      else:
        label = default_label

      d[labelfield] = label

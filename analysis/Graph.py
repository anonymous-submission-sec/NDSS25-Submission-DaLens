#! /usr/bin/env python3

import csv
from dash import Dash, html, dcc
import dash_cytoscape as cyto
import plotly.graph_objects as go
import random

source_file = "public1000-3/aggregated/ordering_2.csv"

limit = 1000
#VP = "138.68.96.43"
VP= "157.230.97.126"
# Load ordering data
nodes = set()
edges = set()
with open(source_file, 'r') as f:
  reader = csv.DictReader(f)
  for row in reader:
    if limit == 0:
      break
    if row['vantagepoint'] != VP:
      continue
    if row['order_A'] != "" and row['order_B'] != "":
      nodes.add(row['order_A'])
      nodes.add(row['order_B'])
      edges.add((row['order_A'], row['order_B']))
      #limit -= 1

#obsolete_edges = set()
#keep_edges = set()
#for n1 in nodes:
#  for n2 in nodes:
#    for n3 in nodes:
#        if (n1, n2) in edges and (n2, n3) in edges:
#            obsolete_edges.add((n1, n3))
#edges -= obsolete_edges

# Separate nodes into sink and non-sink nodes
nodes_sink = set()
for node in nodes:
  # If node has only outgoing edges add it do nodes_sink
  if len([e for e in edges if e[0] == node]) == 0:
    nodes_sink.add(node)
nodes_non_sink = nodes - nodes_sink

# Create graph elements
nodes_done = [
    {
        'data': {'id': node, 'label': node},
        'position': {'x': random.uniform(0, 1), 'y': random.uniform(0, 1)},
        'classes': 'sink'
    }
    for node in nodes_sink
] + [
    {
        'data': {'id': node, 'label': node},
        'position': {'x': random.uniform(0, 1), 'y': random.uniform(0, 1)},
        'classes': 'non-sink'
    }
    for node in nodes_non_sink
]

edges_done = [
    {'data': {'source': source, 'target': target}}
    for source, target in edges
]

app = Dash(__name__)

cyto.load_extra_layouts()

# Good layouts: klay, dagre, cose-bilkent, cose

elements = nodes_done + edges_done

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-layout-1',
        elements=elements,
        style={'width': '100%', 'height': '800px'},
        layout={
            'name': 'klay',
            'directed': True
        },
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle'
                }
            },
            {
                'selector': '.sink',
                'style': {
                    'background-color': 'red',
                    'line-color': 'red'
                }
            },
        ]
    )
])

app.run(debug=True)
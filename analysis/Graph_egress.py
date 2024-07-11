#! /usr/bin/env python3

import json
from dash import Dash, html, dcc
import dash_cytoscape as cyto
import plotly.graph_objects as go
import random


source_file = "public1000-3/aggregated/egress.json"


limit = 100

# Load ordering data
ingress_nodes = set()
egress_nodes = set()
edges = set()
with open(source_file, 'r') as f:
  for line in f:
    if limit == 0:
      break
    
    row = json.loads(line)
    if row['unique_egress'] < 3:
      continue
    ingress_nodes.add(row['ns'])
    #for vp in row['vps']:
    k = list(row['vps'].keys())[0]
    for egress in row['vps'][k]:
      #n = ".".join(egress.split(".")[:3])
      n = ".".join(egress.split(".")[:4])
      egress_nodes.add(n)

      edges.add((row['ns'], n))
    limit -= 1

print(len(egress_nodes))


# Create graph elements
nodes_done = [
    {
        'data': {'id': node, 'label': node},
        'position': {'x': random.uniform(0, 1), 'y': random.uniform(0, 1)},
        'classes': 'ingress'
    }
    for node in ingress_nodes
] + [
    {
        'data': {'id': node, 'label': node},
        'position': {'x': random.uniform(0, 1), 'y': random.uniform(0, 1)},
        'classes': 'egress'
    }
    for node in egress_nodes
]

edges_done = [
    {'data': {'source': source, 'target': target}}
    for source, target in edges
]

app = Dash(__name__)

cyto.load_extra_layouts()

elements = nodes_done + edges_done

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-layout-1',
        elements=elements,
        style={'width': '100%', 'height': '800px'},
        layout={
            'name': 'klay',
            #'circle': True,
            'grid': True,
            'animate': True,
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
                'selector': '.ingress',
                'style': {
                    'background-color': 'red',
                    'line-color': 'red'
                }
            },
        ]
    )
])

app.run(debug=True)
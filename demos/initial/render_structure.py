"""Draw the structural layer built from sidecars.

Usage: python render_structure.py SIDECAR [SIDECAR ...]

Each node is labeled with its name, Biolink category and RDDC class.
has_member edges are unlabeled.
"""

import sys

import graphviz
from dglink import EdgeSet, NodeSet

from rddc_kg.schema import EDGE_ATTRIBUTES, NODE_ATTRIBUTES
from rddc_kg.sidecar import add_sidecar, load_sidecar

# One row per category, from the contributor at the top to the subjects
COLORS = {
    "biolink:Agent": "#e7f1fb",
    "biolink:DatasetVersion": "#efedff",
    "biolink:Dataset": "#f9eeda",
    "biolink:DatasetDistribution": "#e5f4e4",
    "biolink:Case": "#fbebeb",
}

nodes = NodeSet(attributes=NODE_ATTRIBUTES)
edges = EdgeSet(attributes=EDGE_ATTRIBUTES)
for path in sys.argv[1:]:
    add_sidecar(load_sidecar(path), nodes, edges)

g = graphviz.Digraph(format="png")
g.attr(rankdir="LR", dpi="200", fontname="Helvetica", nodesep="0.02",
       ranksep="0.25")
g.attr("node", shape="box", style="rounded,filled", fontname="Helvetica",
       fontsize="10", margin="0.06,0.01", color="#888888")
g.attr("edge", fontname="Helvetica", fontsize="8", color="#888888",
       fontcolor="#555555")
# Graphviz reads a colon in a node id as a port separator
ids = {curie: f"n{i}" for i, curie in enumerate(nodes.nodes)}
for curie, node in nodes.nodes.items():
    category = node[":LABEL"]
    label = (f"{node['name']}\n{category.removeprefix('biolink:')}"
             f"\n({node['raw_label']})")
    g.node(ids[curie], label, fillcolor=COLORS[category])
for category in COLORS:
    with g.subgraph() as row:
        row.attr(rank="same")
        for curie, node in nodes.nodes.items():
            if node[":LABEL"] == category:
                row.node(ids[curie])
order = list(COLORS)
for edge in edges.edges.values():
    start, end = ids[edge[":START_ID"]], ids[edge[":END_ID"]]
    label = edge[":TYPE"].removeprefix("biolink:")
    if label == "has_member":
        label = ""
    rows = [order.index(nodes.nodes[c][":LABEL"])
            for c in (edge[":START_ID"], edge[":END_ID"])]
    # Upward edges are laid out reversed, edges within a row are ignored
    if rows[0] > rows[1]:
        g.edge(end, start, label, dir="back")
    else:
        g.edge(start, end, label, constraint=str(rows[0] < rows[1]).lower())
g.render("structural_layer", cleanup=True)

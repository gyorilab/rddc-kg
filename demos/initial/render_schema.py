"""Draw the node and edge types in the graph loaded in Neo4j.

Nodes are drawn in three rows, files, subjects and concepts, and edges are
colored by where they come from.
"""

import graphviz
from neo4j import GraphDatabase

from rddc_kg.schema import EXTERNAL_TRIPLES, MAPPING_PREDICATES

BOLT = "bolt://localhost:7697"
COLORS = {
    "Agent": "#D9C8AE",
    "DatasetVersion": "#C990C0",
    "Dataset": "#FFC454",
    "DatasetDistribution": "#8DCC93",
    "Case": "#F16667",
    "Disease": "#F79767",
    "PhenotypicFeature": "#ECB5C9",
    "Gene": "#57C7E3",
    "SmallMolecule": "#FFE081",
    "Pathway": "#569480",
}
ROWS = [["Agent", "DatasetVersion", "Dataset", "DatasetDistribution"],
        ["SmallMolecule", "Case"],
        ["Pathway", "Gene", "Disease", "PhenotypicFeature"]]
# Self-loops above or below their node, away from the edges in its row
LOOP_PORTS = {"Dataset": "n", "Gene": "s", "Disease": "s",
              "PhenotypicFeature": "s"}
ONTOLOGY_PREDICATES = {"biolink:subclass_of", *MAPPING_PREDICATES}
STYLES = {
    "rddc": {"color": "#666666", "fontcolor": "#444444"},
    "ontology": {"color": "#2f6fb5", "fontcolor": "#2f6fb5"},
    "external": {"color": "#d9822b", "fontcolor": "#b5651d",
                 "style": "dashed", "penwidth": "1.5"},
}
TRIPLES = """
MATCH (a)-[r]->(b)
RETURN DISTINCT labels(a)[0] AS s, type(r) AS p, labels(b)[0] AS o"""

driver = GraphDatabase.driver(BOLT, auth=None)
triples = [tuple(r) for r in driver.execute_query(TRIPLES).records]
g = graphviz.Digraph(format="png")
g.attr(rankdir="TB", newrank="true", dpi="200", fontname="Helvetica",
       ranksep="0.3", nodesep="0.35")
g.attr("node", shape="box", style="rounded,filled", fontname="Helvetica",
       fontsize="11", color="#888888")
g.attr("edge", fontname="Helvetica", fontsize="9")
for row in ROWS:
    with g.subgraph() as s:
        s.attr(rank="same")
        for label in row:
            s.node(label, fillcolor=COLORS[label])
        # Invisible edges keep the nodes of a row in order
        for a, b in zip(row, row[1:]):
            s.edge(a, b, style="invis")
for s, p, o in triples:
    if (s, p, o) in EXTERNAL_TRIPLES:
        kind = "external"
    elif p in ONTOLOGY_PREDICATES:
        kind = "ontology"
    else:
        kind = "rddc"
    # Graphviz reads a colon in a node id as a port separator
    s, o = s.removeprefix("biolink:"), o.removeprefix("biolink:")
    ports = {}
    if s == o and s in LOOP_PORTS:
        ports = {"tailport": LOOP_PORTS[s], "headport": LOOP_PORTS[s]}
    g.edge(s, o, p.removeprefix("biolink:"), **STYLES[kind], **ports)
g.render("schema_graph", cleanup=True)

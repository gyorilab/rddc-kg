"""Build the demo graph from example sidecars, demo records and CoGEx.

Usage: python build_graph.py SIDECAR [SIDECAR ...]

The node and edge files are written to neo4j_import/ for Neo4j's bulk
importer.
"""

import json
import os
import sys

import obonet
from dglink import EdgeSet, NodeSet
from dglink.core.validate_biolink import validate_graph
from indra_cogex.client import Neo4jClient

from rddc_kg.grounder import OBO_RELEASES, get_obo_path
from rddc_kg.mappings import get_mondo_mappings
from rddc_kg.schema import (ALLOWED_TRIPLES, EDGE_ATTRIBUTES,
                            EXTERNAL_TRIPLES, NODE_ATTRIBUTES)
from rddc_kg.sidecar import add_sidecar, load_sidecar, subject_curie

# Synthetic clinical records added for the subjects in the sidecars, which
# contain none: (subject, predicate, concept, raw_type)
RECORDS = [
    ("P0001", "biolink:associated_with", "mondo:0018975", "diagnosis"),
    ("P0001", "biolink:has_phenotype", "hp:0001250", None),
    ("P0001", "biolink:has_phenotype", "hp:0009732", None),
    ("P0001", "biolink:associated_with", "hgnc:7765", "variant"),
    ("P0002", "biolink:associated_with", "mondo:0018997", "diagnosis"),
    ("P0002", "biolink:has_phenotype", "hp:0007359", None),
    ("P0002", "biolink:has_phenotype", "hp:0001639", None),
    ("P0002", "biolink:associated_with", "hgnc:9644", "variant"),
    ("P0003", "biolink:has_phenotype", "hp:0001250", None),
]
ASSOCIATIONS = {
    "mondo": "biolink:CaseToDiseaseAssociation",
    "hp": "biolink:CaseToPhenotypicFeatureAssociation",
    "hgnc": "biolink:CaseToGeneAssociation",
}
CATEGORIES = {
    "mondo": "biolink:Disease",
    "mesh": "biolink:Disease",
    "hp": "biolink:PhenotypicFeature",
    "hgnc": "biolink:Gene",
    "chebi": "biolink:SmallMolecule",
    "wikipathways": "biolink:Pathway",
}
# WikiPathways Ras signaling
PATHWAY = "wikipathways:WP4223"
# Sources of curated drug-target statements in INDRA
TARGET_SOURCES = ["tas", "drugbank", "chembl"]

MEMBERS = """
MATCH (:BioEntity {id: $pathway})-[:haspart]->(g:BioEntity) RETURN g.id"""
TRIALS = """
MATCH (d:BioEntity)-[i:has_indication]->(m:BioEntity) WHERE m.id IN $diseases
MATCH (d)-[r:indra_rel {stmt_type: 'Inhibition'}]->(t:BioEntity)
WHERE t.id STARTS WITH 'hgnc:'
  AND any(s IN $sources WHERE r.source_counts CONTAINS ('"' + s + '"'))
RETURN d.id, m.id, i.version, t.id, max(r.belief)"""
# The statement type with the most evidence for each pair of genes
REGULATION = """
MATCH (a:BioEntity)-[r:indra_rel]->(b:BioEntity)
WHERE a.id IN $genes AND b.id IN $genes AND a <> b
  AND r.stmt_type IN ['Activation', 'Inhibition']
WITH a.id AS a, b.id AS b, r.stmt_type AS t, sum(r.evidence_count) AS ev,
     max(r.belief) AS belief
WHERE ev >= $min_evidence
WITH a, b, t, belief ORDER BY ev DESC
WITH a, b, collect([t, belief])[0] AS top
RETURN a, b, top[0], top[1]"""
NAMES = "MATCH (n:BioEntity) WHERE n.id IN $ids RETURN n.id, n.name"

nodes = NodeSet(attributes=NODE_ATTRIBUTES)
edges = EdgeSet(attributes=EDGE_ATTRIBUTES)
sidecars = [load_sidecar(path) for path in sys.argv[1:]]
for sidecar in sidecars:
    add_sidecar(sidecar, nodes, edges)
source = sidecars[0]["sourceId"]


def add_edge(subj, pred, obj, source, level, agent, **attrs):
    edges.update_edges({
        ":START_ID": subj, ":END_ID": obj, ":TYPE": pred,
        "primary_knowledge_source": source, "knowledge_level": level,
        "agent_type": agent, "access": "open", **attrs,
    })


for subject, pred, concept, raw_type in RECORDS:
    # The source marks the edge as added for this demo, not from a batch
    add_edge(subject_curie(source, subject), pred, concept,
             "rddc:example", "observation", "manual_agent",
             category=ASSOCIATIONS[concept.split(":")[0]],
             raw_type=raw_type or "", access="controlled")

# MeSH equivalents of the diagnoses, for drug indications from ChEMBL
diagnoses = {c for _, _, c, t in RECORDS if t == "diagnosis"}
mesh = set()
for m in get_mondo_mappings():
    if (m.subject in diagnoses and m.predicate == "biolink:exact_match"
            and m.object.startswith("mesh:")):
        mesh.add(m.object)
        add_edge(m.subject, m.predicate, m.object, "infores:mondo",
                 "knowledge_assertion", "manual_agent",
                 source_version=OBO_RELEASES["mondo"],
                 mapping_justification="semapv:ManualMappingCuration")

# Direct is_a relations between the phenotypes in the graph
hp = obonet.read_obo(get_obo_path("hp"))
phenotypes = {c for *_, c, _ in RECORDS if c.startswith("hp:")}
for child in phenotypes:
    for parent in hp.successors(child.upper()):
        if parent.lower() in phenotypes:
            add_edge(child, "biolink:subclass_of", parent.lower(),
                     "infores:hpo", "knowledge_assertion", "manual_agent",
                     source_version=OBO_RELEASES["hp"])

client = Neo4jClient()
members = {r[0] for r in client.query_tx(MEMBERS, pathway=PATHWAY)}
targets = set()
for drug, disease, version, target, belief in client.query_tx(
        TRIALS, diseases=list(mesh), sources=TARGET_SOURCES):
    targets.add(target)
    add_edge(drug, "biolink:in_clinical_trials_for", disease,
             "infores:chembl", "knowledge_assertion", "manual_agent",
             source_version=version)
    add_edge(drug, "biolink:affects", target, "infores:indra",
             "knowledge_assertion", "automated_agent",
             raw_type="Inhibition", **{"score:float": belief})
for a, b, stmt_type, belief in client.query_tx(
        REGULATION, genes=list(members | targets), min_evidence=20):
    add_edge(a, "biolink:regulates", b, "infores:indra",
             "knowledge_assertion", "automated_agent",
             raw_type=stmt_type, **{"score:float": belief})
genes = {c for *_, c, _ in RECORDS if c.startswith("hgnc:")}
for gene in genes & members:
    add_edge(gene, "biolink:actively_involved_in", PATHWAY,
             "infores:wikipathways", "knowledge_assertion", "manual_agent")

# Concept nodes for every edge end that is not yet in the graph
concepts = {e[k] for e in edges.edges.values()
            for k in (":START_ID", ":END_ID")}
concepts -= set(nodes.nodes)
names = dict(client.query_tx(NAMES, ids=list(concepts)))
for curie in concepts:
    nodes.update_nodes({
        "curie:ID": curie, ":LABEL": CATEGORIES[curie.split(":")[0]],
        "name": names.get(curie) or curie, "access": "open",
    })

report = validate_graph(nodes, edges, ALLOWED_TRIPLES | EXTERNAL_TRIPLES)
print(json.dumps(report, indent=1))
os.makedirs("neo4j_import", exist_ok=True)
nodes.write_node_set("neo4j_import/nodes.tsv")
edges.write_edge_set("neo4j_import/edges.tsv")

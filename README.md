# rddc-kg

Code to build a Biolink-conformant knowledge graph (KG) from data deposited in
the Rare Disease Data Commons (RDDC). General-purpose parts, such as graph
validation and grounding, are in [DGLink](https://github.com/gyorilab/dglink),
and this package contains the RDDC-specific schema and readers.

The graph has four layers:

- structural: contributors, batches, file sets, files and the subjects they
  list, read from RDDC sidecars
- instance: each subject's phenotypes, diagnoses, variants and medications
- semantic: ontology concepts linked from files and subjects, with their
  hierarchy and mappings across vocabularies
- external: edges from external knowledge bases such as INDRA CoGEx

## Modules

- `schema.py`: node categories, allowed (subject, predicate, object) triples
  for each layer, preferred vocabularies, and node and edge properties
- `sidecar.py`: reading a sidecar into the structural layer
- `grounder.py`: a Gilda grounder over pinned MONDO and HPO releases and the
  HGNC, ChEBI and GO terms distributed with Gilda
- `mappings.py`: MONDO's typed cross-references to other vocabularies

## Installation

```
pip install -e .
```

The pinned MONDO and HPO releases are downloaded to `~/.data/rddc_kg` on
first use.

## Example

```python
from dglink import EdgeSet, NodeSet
from dglink.core.validate_biolink import validate_graph
from rddc_kg.schema import ALLOWED_TRIPLES, EDGE_ATTRIBUTES, NODE_ATTRIBUTES
from rddc_kg.sidecar import add_sidecar, load_sidecar

nodes = NodeSet(attributes=NODE_ATTRIBUTES)
edges = EdgeSet(attributes=EDGE_ATTRIBUTES)
add_sidecar(load_sidecar("sidecar.json"), nodes, edges)
print(validate_graph(nodes, edges, ALLOWED_TRIPLES))
nodes.write_node_set("nodes.tsv")
edges.write_edge_set("edges.tsv")
```

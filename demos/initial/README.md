# Initial demo

A demo graph built from the two example sidecars in the rddc-model
repository, clinical records added for this demo, and knowledge from INDRA
CoGEx, MONDO and HPO.

## Synthetic data

All data in the demo are synthetic. Part of the graph comes from the example
sidecars as they are, and the clinical records are added for this demo as a
proof of principle.

| Part of the graph | Source |
|---|---|
| Contributor, batches, file sets, files and subjects | The example sidecars, as they are |
| Subjects' diagnoses, phenotypes and variant genes | Added for this demo, in `RECORDS` in `build_graph.py` |
| MONDO to MeSH `exact_match` edges | MONDO 2026-11-03 cross-references |
| HPO `subclass_of` edges | HPO 2026-09-01 |
| Pathway membership | WikiPathways, through CoGEx |
| Drug indications | ChEMBL, through CoGEx |
| Drug targets and gene regulation | INDRA statements, through CoGEx |

The edges added for this demo have `primary_knowledge_source`
`rddc:example`, and the CoGEx edges `infores:wikipathways`, `infores:chembl`
or `infores:indra`. In this demo the external edges are copied into the graph.

## Requirements

- rddc-kg and DGLink's `schema-validation` branch
- `indra_cogex`, configured with access to the CoGEx Neo4j database
- Docker, for Neo4j
- Graphviz, for the figures
- Playwright with Chrome, for the Neo4j Browser screenshot

## Steps

Set `RDDC_MODEL` to a local checkout of rddc-model at commit 4d1426d, which
has the example sidecars in `examples/`.

Build the graph, which prints the validation report and writes
`neo4j_import/nodes.tsv` and `neo4j_import/edges.tsv`:

```
python build_graph.py $RDDC_MODEL/examples/deposit_fhir_omop.json \
    $RDDC_MODEL/examples/ccda_document_set.json
```

Load the files into a new Neo4j database and start it, with Neo4j Browser on
port 7495 and Bolt on port 7697:

```
docker run --rm -v rddc-kg-neo4j-data:/data -v "$PWD/neo4j_import":/import \
    neo4j:5.26-community neo4j-admin database import full --delimiter=TAB \
    --nodes=/import/nodes.tsv --relationships=/import/edges.tsv \
    --overwrite-destination neo4j
docker run -d --name rddc-kg-neo4j -p 7495:7474 -p 7697:7687 \
    -e NEO4J_AUTH=none -v rddc-kg-neo4j-data:/data neo4j:5.26-community
```

Run the demo queries and print their results:

```
python queries.py
```

Draw the figures, `schema_graph.png` from the loaded graph and
`structural_layer.png` from the sidecars:

```
python render_schema.py
python render_structure.py $RDDC_MODEL/examples/deposit_fhir_omop.json \
    $RDDC_MODEL/examples/ccda_document_set.json
```

Take the Neo4j Browser screenshot of the subgraph that links P0002 to
sirolimus:

```
python screenshot.py subgraph.cypher subgraph.png 36
```

# rddc-kg

Builds a Biolink-conformant knowledge graph from data deposited in the Rare Disease
Data Commons (RDDC), using [DGLink](https://github.com/gyorilab/dglink).

The graph has three layers:

- structural: sources, batches, file sets and files, as described by RDDC sidecars
- instance: subjects and their phenotypes, diagnoses, variants and medications
- semantic: ontology concepts linked from files and subjects, with their hierarchy
  and mappings across vocabularies

`src/rddc_kg/schema.py` defines the categories, allowed edges and properties.

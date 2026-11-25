"""
Knowledge graph schema for data described by RDDC sidecars.

The graph has four layers:

- structural: contributors, batches, file sets, files and the subjects
  (biolink:Case) they list, as declared in the sidecar
- instance: each subject's phenotypes, diagnoses, variants and medications,
  which are access-controlled
- semantic: ontology concepts that files and subjects link to, with their
  hierarchy and mappings across vocabularies
- external: edges from external knowledge bases, typed in EXTERNAL_EDGES and
  not included in ALLOWED_TRIPLES
"""

# RDDC sidecar element -> Biolink category. The RDDC class is kept in `raw_label`.
RDDC_CLASS_TO_BIOLINK = {
    "Contributor": "biolink:Agent",
    "Batch": "biolink:DatasetVersion",
    "FileSet": "biolink:Dataset",
    "DataFile": "biolink:DatasetDistribution",
    "Subject": "biolink:Case",
}

CONCEPT_CATEGORIES = [
    "biolink:Disease",
    "biolink:PhenotypicFeature",
    "biolink:Gene",
    "biolink:Protein",
    "biolink:SequenceVariant",
    "biolink:SmallMolecule",
    "biolink:Drug",
    "biolink:BiologicalProcess",
    "biolink:CellularComponent",
    "biolink:GrossAnatomicalStructure",
    "biolink:OrganismTaxon",
    "biolink:RNAProduct",
    "biolink:MacromolecularComplex",
    "biolink:Pathway",
    "biolink:NamedThing",
]

# Bioregistry prefixes per category, most preferred first. A concept is identified
# by the first prefix it has an identifier in, other identifiers go in `xref`.
PREFERRED_PREFIXES = {
    "biolink:Disease": ["mondo", "orpha", "omim", "doid", "mesh"],
    "biolink:PhenotypicFeature": ["hp"],
    "biolink:Gene": ["hgnc", "ncbigene", "ensembl"],
    "biolink:Protein": ["uniprot"],
    "biolink:SequenceVariant": ["clinvar.variation", "dbsnp"],
    "biolink:Drug": ["rxnorm", "chebi", "chembl.compound", "drugbank"],
    "biolink:SmallMolecule": ["chebi", "chembl.compound", "drugbank", "mesh"],
    "biolink:Pathway": ["wikipathways", "reactome"],
}

# (subject category, predicate, object category, Biolink association) for each
# allowed edge
STRUCTURAL_EDGES = [
    ("biolink:DatasetVersion", "biolink:has_contributor", "biolink:Agent", None),
    ("biolink:DatasetVersion", "biolink:has_member", "biolink:Dataset", None),
    ("biolink:DatasetVersion", "biolink:has_member",
     "biolink:DatasetDistribution", None),
    ("biolink:Dataset", "biolink:has_member", "biolink:DatasetDistribution", None),
    ("biolink:Dataset", "biolink:derives_from", "biolink:Dataset", None),
    ("biolink:DatasetDistribution", "biolink:derives_from",
     "biolink:DatasetDistribution", None),
    ("biolink:DatasetVersion", "biolink:mentions", "biolink:Case", None),
    ("biolink:DatasetDistribution", "biolink:mentions", "biolink:Case", None),
]

# raw_type distinguishes edges that share a generic predicate, e.g. a confirmed
# diagnosis, a candidate diagnosis and a family history of a disease
INSTANCE_EDGES = [
    ("biolink:Case", "biolink:has_phenotype", "biolink:PhenotypicFeature",
     "biolink:CaseToPhenotypicFeatureAssociation"),
    ("biolink:Case", "biolink:associated_with", "biolink:Disease",
     "biolink:CaseToDiseaseAssociation"),
    ("biolink:Case", "biolink:associated_with", "biolink:SequenceVariant",
     "biolink:CaseToVariantAssociation"),
    ("biolink:Case", "biolink:associated_with", "biolink:Gene",
     "biolink:CaseToGeneAssociation"),
    ("biolink:Case", "biolink:associated_with", "biolink:Drug",
     "biolink:Association"),
    ("biolink:SequenceVariant", "biolink:is_sequence_variant_of", "biolink:Gene",
     "biolink:VariantToGeneAssociation"),
]

# Categories whose vocabularies have a hierarchy (MONDO, HPO, ChEBI, GO, Uberon)
HIERARCHY_CATEGORIES = [
    "biolink:Disease",
    "biolink:PhenotypicFeature",
    "biolink:SmallMolecule",
    "biolink:BiologicalProcess",
    "biolink:CellularComponent",
    "biolink:GrossAnatomicalStructure",
]

MAPPING_PREDICATES = [
    "biolink:exact_match",
    "biolink:close_match",
    "biolink:broad_match",
    "biolink:narrow_match",
]

# Edges from external knowledge bases, which are either stored in the graph or
# queried in the knowledge base's own graph. raw_type stores the knowledge
# base's own relation, for example an INDRA statement type.
EXTERNAL_EDGES = [
    ("biolink:Gene", "biolink:regulates", "biolink:Gene", None),
    ("biolink:Gene", "biolink:actively_involved_in", "biolink:Pathway", None),
    ("biolink:SmallMolecule", "biolink:affects", "biolink:Gene", None),
    ("biolink:SmallMolecule", "biolink:in_clinical_trials_for",
     "biolink:Disease", None),
]

SEMANTIC_EDGES = (
    [("biolink:DatasetDistribution", "biolink:mentions", c, None)
     for c in CONCEPT_CATEGORIES]
    + [(c, "biolink:subclass_of", c, None) for c in HIERARCHY_CATEGORIES]
    + [(c, p, c, None) for c in CONCEPT_CATEGORIES for p in MAPPING_PREDICATES]
)

EDGES = STRUCTURAL_EDGES + INSTANCE_EDGES + SEMANTIC_EDGES
ALLOWED_TRIPLES = {(s, p, o) for s, p, o, _ in EDGES}
EXTERNAL_TRIPLES = {(s, p, o) for s, p, o, _ in EXTERNAL_EDGES}

NODE_ATTRIBUTES = [
    "curie:ID",
    ":LABEL",
    "raw_label",
    "name",
    "iri",
    "xref:string[]",
    "grounded:boolean",
    "source:string[]",
    # "controlled" for anything deposited, "open" for ontology concepts
    "access",
    "conforms_to:string[]",
    "encoding_format",
    "id_system:string[]",
]

EDGE_ATTRIBUTES = [
    ":START_ID",
    ":END_ID",
    ":TYPE",
    "raw_type",
    "category",
    # Biolink provenance, on every edge
    "primary_knowledge_source",
    "knowledge_level",
    "agent_type",
    # Instance and mentions edges, one edge per supporting record
    "file_id",
    # Table column and row, OMOP table and record id, or text offsets
    "location",
    "raw_text",
    # source_identifier, harmonization_mapping, gilda or llm
    "method",
    "score:float",
    # subclass_of and mapping edges
    "source_version",
    # SSSOM mapping justification, e.g. semapv:LexicalMatching
    "mapping_justification",
    "negated:boolean",
    "onset",
    "zygosity",
    "interpretation",
    "access",
]

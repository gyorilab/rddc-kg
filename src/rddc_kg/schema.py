"""
Knowledge graph schema for data described by RDDC sidecars.

The graph has three layers:

- structural: Contributor -> Batch -> FileSet -> DataFile, as declared in the sidecar
- instance: subjects (biolink:Case) and their phenotypes, diagnoses, variants and
  medications, which are access-controlled
- semantic: ontology concepts that files and subjects link to, with their hierarchy
  and mappings across vocabularies
"""

## RDDC sidecar element -> Biolink category. The RDDC class is kept in `raw_label`.
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
    "biolink:NamedThing",
]

## Bioregistry prefixes per category, most preferred first. A concept is identified
## by the first prefix it has an identifier in, other identifiers go in `xref`.
PREFERRED_PREFIXES = {
    "biolink:Disease": ["mondo", "orpha", "omim", "doid", "mesh"],
    "biolink:PhenotypicFeature": ["hp"],
    "biolink:Gene": ["hgnc", "ncbigene", "ensembl"],
    "biolink:Protein": ["uniprot"],
    "biolink:SequenceVariant": ["clinvar.variation", "dbsnp"],
    "biolink:Drug": ["rxnorm", "chebi", "chembl.compound", "drugbank"],
    "biolink:SmallMolecule": ["chebi", "chembl.compound", "drugbank", "mesh"],
}

## (subject category, predicate, object category, Biolink association) for each
## allowed edge
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

## raw_type distinguishes edges that share a generic predicate, e.g. a confirmed
## diagnosis, a candidate diagnosis and a family history of a disease
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

## Categories whose vocabularies have a hierarchy (MONDO, HPO, ChEBI, GO, Uberon)
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

SEMANTIC_EDGES = (
    [("biolink:DatasetDistribution", "biolink:mentions", c, None)
     for c in CONCEPT_CATEGORIES]
    + [(c, "biolink:subclass_of", c, None) for c in HIERARCHY_CATEGORIES]
    + [(c, p, c, None) for c in CONCEPT_CATEGORIES for p in MAPPING_PREDICATES]
)

EDGES = STRUCTURAL_EDGES + INSTANCE_EDGES + SEMANTIC_EDGES
ALLOWED_TRIPLES = {(s, p, o) for s, p, o, _ in EDGES}

NODE_ATTRIBUTES = [
    "curie:ID",
    ":LABEL",
    "raw_label",
    "name",
    "iri",
    "xref:string[]",
    "grounded:boolean",
    "source:string[]",
    ## "controlled" for anything deposited, "open" for ontology concepts
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
    "source:string[]",
    "file_id:string[]",
    ## How the edge was made: sidecar, source_identifier,
    ## harmonization_mapping, gilda or llm
    "method",
    "score:float",
    "raw_texts:string[]",
    "columns:string[]",
    "negated:boolean",
    "onset",
    "zygosity",
    "interpretation",
    "access",
]

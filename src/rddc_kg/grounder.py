"""Gilda grounder over the vocabularies preferred in the RDDC knowledge graph."""

import gilda
import pystow
from gilda.generate_terms import terms_from_obo_url

## Pinned ontology releases, loaded from their OBO files
OBO_RELEASES = {
    "mondo": "2026-11-03",
    "hp": "2026-09-01",
}

## Namespaces taken from Gilda's built-in terms, versioned by the Gilda release
GILDA_NAMESPACES = {"HGNC", "CHEBI", "GO"}


def get_vocabulary_versions() -> dict:
    """Return the version of each vocabulary the grounder is built from."""
    return {**OBO_RELEASES, "gilda": gilda.__version__}


def get_obo_path(prefix: str) -> str:
    """Return the path of a pinned OBO release, downloading it if needed."""
    version = OBO_RELEASES[prefix]
    url = (f"http://purl.obolibrary.org/obo/{prefix}/releases/{version}/"
           f"{prefix}.obo")
    return str(pystow.ensure("rddc_kg", prefix, version, url=url))


def make_grounder() -> gilda.Grounder:
    """Return a Gilda grounder over the pinned vocabularies."""
    terms = [
        term
        for entries in gilda.get_grounder().entries.values()
        for term in entries
        if term.db in GILDA_NAMESPACES
    ]
    for prefix in OBO_RELEASES:
        ## Keep source identifiers instead of remapping them to MeSH or DOID
        terms += terms_from_obo_url(
            get_obo_path(prefix), prefix, ignore_mappings=True,
            map_to_ns=set()
        )
    return gilda.make_grounder(terms)

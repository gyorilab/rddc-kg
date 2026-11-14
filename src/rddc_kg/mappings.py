"""Map concepts from other vocabularies to the preferred vocabularies."""

from collections import defaultdict

import pystow
from dglink.core.mappings import read_obo_mappings

from rddc_kg.grounder import OBO_RELEASES

## MONDO's cross-reference qualifiers. "MONDO is narrower than the source" means
## the source term is broader, so MONDO broad_match source.
MONDO_QUALIFIER_PREDICATES = {
    "MONDO:equivalentTo": "biolink:exact_match",
    "MONDO:mondoIsNarrowerThanSource": "biolink:broad_match",
    "MONDO:mondoIsBroaderThanSource": "biolink:narrow_match",
}


def get_mondo_mappings() -> list:
    """Return MONDO's typed cross-references from the pinned MONDO release."""
    path = pystow.join("rddc_kg", "mondo", OBO_RELEASES["mondo"],
                       name="mondo.obo")
    return read_obo_mappings(str(path), MONDO_QUALIFIER_PREDICATES)


def exact_match_index(mappings: list) -> dict:
    """Return a dict from each mapped CURIE to its exactly matching CURIEs."""
    index = defaultdict(set)
    for m in mappings:
        if m.predicate == "biolink:exact_match":
            index[m.object].add(m.subject)
    return dict(index)

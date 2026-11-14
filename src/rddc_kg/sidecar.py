"""Build the structural layer of the graph from RDDC sidecars."""

import json
from fnmatch import fnmatch

from dglink import EdgeSet, NodeSet

from rddc_kg.schema import RDDC_CLASS_TO_BIOLINK

## Placeholder prefix until RDDC identifiers are registered in Bioregistry
PREFIX = "rddc"


def _as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _refs(value) -> list:
    return [ref["@id"] for ref in _as_list(value)]


def _item_id(item: dict, source_id: str, batch_id: str) -> str:
    kind = "fileset" if item["@type"] == "cr:FileSet" else "file"
    local = item["@id"]
    if local.startswith("urn:uuid:"):
        return f"{PREFIX}:{kind}/{local.removeprefix('urn:uuid:')}"
    ## Local ids are only unique within one sidecar
    return f"{PREFIX}:{kind}/{source_id}/{batch_id}/{local}"


def subject_curie(source_id: str, subject_id: str) -> str:
    """Return the node id of a subject, which is unique within a source."""
    return f"{PREFIX}:subject/{source_id}/{subject_id}"


def add_sidecar(sidecar: dict, node_set: NodeSet, edge_set: EdgeSet) -> str:
    """Add the batch a sidecar describes to the graph and return the batch id."""
    source_id, batch_id = sidecar["sourceId"], sidecar["batchId"]
    batch = f"{PREFIX}:batch/{source_id}/{batch_id}"
    contributor = f"{PREFIX}:contributor/{sidecar['contributorId']}"

    def add_node(curie, rddc_class, raw_label, name, **attrs):
        node_set.update_nodes(
            {
                "curie:ID": curie,
                ":LABEL": RDDC_CLASS_TO_BIOLINK[rddc_class],
                "raw_label": raw_label,
                "name": name,
                "source:string[]": batch,
                "access": "controlled",
                **attrs,
            }
        )

    def add_edge(subj, pred, obj, raw_type):
        edge_set.update_edges(
            {
                ":START_ID": subj,
                ":END_ID": obj,
                ":TYPE": pred,
                "raw_type": raw_type,
                "source:string[]": batch,
                "method": "sidecar",
                "access": "controlled",
            }
        )

    add_node(contributor, "Contributor", "Contributor", sidecar["contributorId"])
    add_node(batch, "Batch", "Batch", sidecar["name"],
             **{"conforms_to:string[]": set(_as_list(sidecar.get("conformsTo")))})
    add_edge(batch, "biolink:has_contributor", contributor, "contributorId")

    for subject in sidecar.get("subjects", []):
        case = subject_curie(source_id, subject["subjectId"])
        add_node(case, "Subject", "Subject", subject["subjectId"],
                 **{"id_system:string[]": subject["idSystem"]})
        add_edge(batch, "biolink:mentions", case, "subjects")

    items = sidecar.get("distribution", [])
    ids = {item["@id"]: _item_id(item, source_id, batch_id) for item in items}
    file_sets = [item for item in items if item["@type"] == "cr:FileSet"]
    files = [item for item in items if item["@type"] == "cr:FileObject"]

    for item in items:
        is_set = item["@type"] == "cr:FileSet"
        add_node(
            ids[item["@id"]],
            "FileSet" if is_set else "DataFile",
            item.get("additionalType", item["@type"]).split(":")[-1],
            item.get("name", item["@id"]),
            encoding_format=item.get("encodingFormat", ""),
            **{"conforms_to:string[]": set(_as_list(item.get("conformsTo")))},
        )
        for ref in _refs(item.get("wasDerivedFrom")):
            add_edge(ids[item["@id"]], "biolink:derives_from", ids[ref],
                     "wasDerivedFrom")
        for subject_id in item.get("subjectIds", []):
            add_edge(ids[item["@id"]], "biolink:mentions",
                     subject_curie(source_id, subject_id), "subjectIds")

    ## A file set lists its files in hasPart, or selects them with includes globs
    in_set = set()
    for file_set in file_sets:
        members = set(_refs(file_set.get("hasPart")))
        patterns = _as_list(file_set.get("includes"))
        excludes = _as_list(file_set.get("excludes"))
        for f in files:
            path = f.get("contentUrl", "")
            if any(fnmatch(path, p) for p in patterns) and not any(
                fnmatch(path, p) for p in excludes
            ):
                members.add(f["@id"])
        for member in members:
            add_edge(ids[file_set["@id"]], "biolink:has_member", ids[member],
                     "hasPart")
        in_set |= members
        add_edge(batch, "biolink:has_member", ids[file_set["@id"]], "distribution")
    for f in files:
        if f["@id"] not in in_set:
            add_edge(batch, "biolink:has_member", ids[f["@id"]], "distribution")
    return batch


def load_sidecar(path: str) -> dict:
    """Load a sidecar JSON file."""
    with open(path) as fh:
        return json.load(fh)

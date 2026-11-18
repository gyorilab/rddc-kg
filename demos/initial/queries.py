"""Run the demo queries on the graph loaded in Neo4j and print the results."""

from neo4j import GraphDatabase

BOLT = "bolt://localhost:7697"

QUERIES = {
    "Batches and files that list subject P0001": """
MATCH (s:`biolink:Case` {name: 'P0001'})<-[:`biolink:mentions`]-(x)
OPTIONAL MATCH (b:`biolink:DatasetVersion`)-[:`biolink:has_member`*1..2]->(x)
RETURN x.name AS mentioned_by, x.raw_label AS rddc_class,
       coalesce(b.name, x.name) AS batch, s.id_system AS id_systems""",
    "Subjects listed in more than one batch": """
MATCH (b:`biolink:DatasetVersion`)-[:`biolink:mentions`]->(s:`biolink:Case`)
WITH s, collect(b.name) AS batches WHERE size(batches) > 1
RETURN s.name AS subject, batches""",
    "Source file set of the OMOP tables": """
MATCH (o:`biolink:Dataset`)-[:`biolink:derives_from`]->(f:`biolink:Dataset`)
MATCH (f)-[:`biolink:has_member`]->(file)
RETURN o.name AS derived, f.name AS source,
       collect(file.name) AS source_files""",
    ## Drugs in trials for another subject's diagnosis that inhibit a gene
    ## that P0002's variant gene regulates, with the path's INDRA belief
    "Drugs linked to P0002 through external knowledge": """
MATCH (s:`biolink:Case` {name: 'P0002'})
      -[:`biolink:associated_with` {raw_type: 'variant'}]->(g:`biolink:Gene`)
MATCH (o:`biolink:Case`)-[:`biolink:associated_with` {raw_type: 'diagnosis'}]
      ->(dx)-[:`biolink:exact_match`]->()
      <-[:`biolink:in_clinical_trials_for`]-(drug)-[:`biolink:affects`]->(t)
WHERE o <> s
MATCH p = (g)-[:`biolink:regulates`*1..3]->(t)
WITH drug, dx, o, p,
     reduce(b = 1.0, r IN relationships(p) | b * r.score) AS belief
ORDER BY belief DESC
WITH drug, dx, o, collect(p)[0] AS p, max(belief) AS belief
RETURN drug.name AS drug,
       [r IN relationships(p) | startNode(r).name + ' ' + r.raw_type + ' '
        + endNode(r).name] AS mechanism,
       round(belief, 2) AS belief, dx.name AS trials_for, o.name AS subject
ORDER BY belief DESC""",
}

driver = GraphDatabase.driver(BOLT, auth=None)
for title, query in QUERIES.items():
    print(f"== {title}")
    for record in driver.execute_query(query).records:
        print(dict(record))
    print()

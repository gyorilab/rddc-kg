MATCH p1 = (s:`biolink:Case` {name: 'P0002'})
      -[:`biolink:associated_with`]->(g:`biolink:Gene`)
      -[:`biolink:regulates`]->(m:`biolink:Gene` {name: 'MTOR'})
      <-[:`biolink:affects`]-(:`biolink:SmallMolecule` {name: 'sirolimus'})
      -[:`biolink:in_clinical_trials_for`]->()<-[:`biolink:exact_match`]-()
      <-[:`biolink:associated_with`]-(o:`biolink:Case`)
MATCH p2 = (s)-[:`biolink:has_phenotype`|`biolink:associated_with`]->()
MATCH p3 = (o)-[:`biolink:has_phenotype`|`biolink:associated_with`]->()
MATCH p4 = (g)-[:`biolink:actively_involved_in`]->(w)
MATCH p5 = (o)-[:`biolink:associated_with`]->(:`biolink:Gene`)
      -[:`biolink:regulates`|`biolink:actively_involved_in`]->(y)
WHERE y = m OR y = w
RETURN p1, p2, p3, p4, p5

from typing import cast

from datetime import datetime, timezone

import requests
from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper

# --- CONFIGURATION ---
ENDPOINT_URL = "http://metadata.validation/api/v0/graph"
UPDATE_URL = "http://metadata.validation/api/v0/graph/update"
GRAPH_PREFIX = "https://glaciation-project.eu/uc/2/"
ETL_AGENT_URI = "https://glaciation-project.eu/prov/ETLAgent"
INGEST_PROCESS_URI = "https://glaciation-project.eu/prov/IngestProcess"

# --- QUERY METADATA SUBJECTS ---
sparql = SPARQLWrapper(ENDPOINT_URL)
sparql.setReturnFormat(JSON)
sparql.setQuery(
    f"""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?g ?s
WHERE {{
    GRAPH ?g {{
        ?s ?p ?o .
        FILTER(isIRI(?s))  # Only IRIs
        FILTER(!STRSTARTS(STR(?s), "https://w3id.org/dpv#"))
    }}
    FILTER (STRSTARTS(STR(?g), "{GRAPH_PREFIX}"))
}}
LIMIT 10
"""
)


# function to execute provenence query
def run_query():
    try:
        raw_results = sparql.query().convert()
    except Exception as e:
        print("SPARQL query failed:", e)
        exit()

    if not isinstance(raw_results, dict):
        print("SPARQL query returned unexpected format.")
        exit()

    results = cast(dict[str, dict[str, list[dict[str, dict[str, str]]]]], raw_results)

    # --- GENERATE INSERT DATA ---
    timestamp = datetime.now(timezone.utc).isoformat()
    insert_data = ""
    print(results)
    for result in results["results"]["bindings"]:
        g = result["g"]["value"]
        s = result["s"]["value"]
        insert_data += (
            f"GRAPH <{g}> {{\n"
            f"<{s}> "
            f"<http://www.w3.org/ns/prov#wasGeneratedBy> "
            f"<{INGEST_PROCESS_URI}> ;\n"
            f"           <http://www.w3.org/ns/prov#generatedAtTime> "
            f'"{timestamp}"^^<http://www.w3.org/2001/XMLSchema#dateTime> ;\n'
            f"<http://www.w3.org/ns/prov#wasAttributedTo> <{ETL_AGENT_URI}> .\n"
            f"}}\n"
        )

    if not insert_data.strip():
        print("No entities found. Nothing to insert.")
        exit()

    # --- PREPARE & PRINT SPARQL UPDATE ---
    sparql_update_query = f"""
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#dateTime>

    INSERT DATA {{
    {insert_data}
    }}
    """

    print("==== SPARQL UPDATE QUERY ====")
    print(sparql_update_query)

    # --- EXECUTE UPDATE ---
    update = SPARQLWrapper(UPDATE_URL)
    update.setMethod(POST)
    update.setRequestMethod(POSTDIRECTLY)
    update.setQuery(sparql_update_query)

    try:
        update.query()
        print("PROV metadata inserted successfully.")
    except Exception as e:
        print("SPARQL insert failed:", e)

    headers = {"Content-Type": "application/json"}
    payload = {"query": sparql_update_query}

    response = requests.post(UPDATE_URL, json=payload, headers=headers)

    if response.status_code == 200:
        print("PROV metadata inserted successfully.")
    else:
        print("SPARQL insert failed.")
        print("Status:", response.status_code)
        print("Response:", response.text)


# MAIN function
if __name__ == "__main__":
    run_query()

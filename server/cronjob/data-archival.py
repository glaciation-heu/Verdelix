import csv
import datetime
import re

from SPARQLWrapper import JSON, SPARQLWrapper  # type: ignore

# mention integration/validation metadata endpiunt
SPARQL_ENDPOINT = "http://metadata.validation/api/v0/graph"

# SPARQL Query to get all triples
QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX glc: <https://glaciation-project.eu/MetadataReferenceModel#>
PREFIX saref: <https://saref.etsi.org/core/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?g ?s ?p ?o
WHERE {
    GRAPH ?g {
        ?s ?p ?o .
    }
    FILTER (STRSTARTS(STR(?g), "https://glaciation-project.eu/uc/2"))
}
LIMIT 50  # Adjust limit as needed
"""

# Initialize SPARQL Wrapper
sparql = SPARQLWrapper(SPARQL_ENDPOINT)
sparql.setQuery(QUERY)
sparql.setReturnFormat(JSON)

# Execute query
results = sparql.query().convert()
today = datetime.datetime.now(datetime.timezone.utc)

filtered_triples = []

timestamp_pattern = re.compile(r"timestamp:(\d+)")

for result in results["results"]["bindings"]:
    graph_name = result["g"]["value"]
    match = timestamp_pattern.search(graph_name)

    if match:
        timestamp_ms = int(match.group(1))
        timestamp_dt = datetime.datetime.utcfromtimestamp(timestamp_ms / 1000).replace(
            tzinfo=datetime.timezone.utc
        )
        age_days = (today - timestamp_dt).days

        if age_days > 30:
            subject = result["s"]["value"]
            predicate = result["p"]["value"]
            obj = result["o"]["value"]
            filtered_triples.append((subject, predicate, obj, timestamp_dt, age_days))

if filtered_triples:
    print("\n Data Older than 30 days:")
    for s, p, o, ts, days in filtered_triples:
        print(
            (
                f" Subject: {s}\n"
                f"   Predicate: {p}\n"
                f"   Object: {o}\n"
                f"   Timestamp: {ts} ({days} days old)\n"
            )
        )

else:
    print("No data older than 30 days found.")

# Save to a CSV file
with open("filtered_data.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Subject", "Predicate", "Object", "Timestamp", "Age (days)"])
    writer.writerows(filtered_triples)

print("\n Filtered data saved to 'filtered_data.csv'")

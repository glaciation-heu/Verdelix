from typing import cast

import datetime
import os
import re
import subprocess

import requests
from SPARQLWrapper import JSON, SPARQLWrapper

# mention integration/validation metadata endpiunt
SPARQL_ENDPOINT = "http://metadata.validation/api/v0/graph"

QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX glc: <https://glaciation-project.eu/MetadataReferenceModel#>
PREFIX saref: <https://saref.etsi.org/core/>

SELECT DISTINCT (STRBEFORE(STRAFTER(STR(?g), "/uc/2/"), "/timestamp") AS ?uuid) ?g
 WHERE {
  { GRAPH ?g
    {
      ?s ?p ?o
    }
  }
  FILTER (STRSTARTS(STR(?g), 'https://glaciation-project.eu/uc/2/'))
}
# ORDER BY DESC(?g)
LIMIT 10
"""

# Initialize SPARQL Wrapper
sparql = SPARQLWrapper(SPARQL_ENDPOINT)
sparql.setQuery(QUERY)
sparql.setReturnFormat(JSON)

# Execute query
raw_results = sparql.query().convert()
# Check it's a dictionary (as expected with JSON return format)
if not isinstance(raw_results, dict):
    raise ValueError("Unexpected SPARQL result format")

# Inform MyPy: this is a nested JSON result
results = cast(dict[str, dict[str, list[dict[str, dict[str, str]]]]], raw_results)

# List to store UUIDs older than 30 days
old_uuids = []
# lists to store file_id (uuid) and corresponding timestamps
file_id = []
file_timestamp = []


# Current time (UTC)
now = datetime.datetime.now(datetime.timezone.utc)

# Regex to extract timestamp
timestamp_pattern = re.compile(r"timestamp:(\d+)")

# Iterate over each binding
for item in results["results"]["bindings"]:
    uuid = item["uuid"]["value"]
    graph_uri = item["g"]["value"]

    # Extract timestamp using regex
    match = timestamp_pattern.search(graph_uri)
    if match:
        timestamp_ms = int(match.group(1))
        timestamp_dt = datetime.datetime.utcfromtimestamp(timestamp_ms / 1000).replace(
            tzinfo=datetime.timezone.utc
        )
        age_days = (now - timestamp_dt).days

        if age_days > 10:
            old_uuids.append(uuid)
            file_id.append(uuid)
            file_timestamp.append(timestamp_ms)

file_metadata = list(zip(file_id, file_timestamp))
# Output list of old UUIDs
print("UUIDs older than 10 days:")
for u in old_uuids:
    print(f"🔹 {u}")

# --- CONFIGURATION for storing/moving data in a local folder ---
NAMESPACE = "semantification"
LABEL_SELECTOR = "app.kubernetes.io/name=semantification-service"
REMOTE_PATH = "/opt/nifi/nifi-current/output"
LOCAL_BACKUP_BASE = "./longhorn-data-backup"


def run(cmd, check=True, capture_output=False):
    print(f"Running: {cmd}")
    return subprocess.run(
        cmd, shell=True, check=check, capture_output=capture_output, text=True
    )


def get_pod_name():
    # cmd = f"kubectl get pods -n {NAMESPACE} -l '{LABEL_SELECTOR}' -o jsonpath='{{.items[0].metadata.name}}'"
    cmd = (
    f"kubectl get pods -n {NAMESPACE} "
    f"-l '{LABEL_SELECTOR}' "
    f"-o jsonpath='{{.items[0].metadata.name}}'"
    )
    result = run(cmd, capture_output=True)
    pod_name = result.stdout.strip()
    if not pod_name:
        raise RuntimeError("Could not find a matching pod.")
    print(f"Found pod: {pod_name}")
    return pod_name


def copy_selected_files(pod_name, file_list):
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    target_dir = os.path.join(LOCAL_BACKUP_BASE, f"uc2-pvc-flatfiles-{timestamp}")
    os.makedirs(target_dir, exist_ok=True)

    # Create string of space-separated file names only
    file_names = " ".join(file_list)
    print(file_names)
    # Tar files from inside output dir to avoid full path in archive
    tar_cmd = (
        f"kubectl exec -n {NAMESPACE} {pod_name} -- "
        f"sh -c 'cd {REMOTE_PATH} && tar -cf - {file_names}'"
    )

    untar_cmd = f"tar -xf - -C {target_dir}"

    print(f"Copying {len(file_list)} files from PVC to: {target_dir}")
    full_cmd = f"{tar_cmd} | {untar_cmd}"
    run(full_cmd)

    print(f"\n Done! Files are copied to: {target_dir}")
    return target_dir


# --- MAIN ---
if __name__ == "__main__":
    pod_name = get_pod_name()
    copy_selected_files(pod_name, old_uuids)


# updating file location in KG


def ms_to_iso8601(ms):
    """Convert a millisecond timestamp to ISO 8601 UTC string"""
    dt = datetime.datetime.fromtimestamp(int(ms) / 1000, tz=datetime.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def insert_dna_archive_metadata(
    fuseki_url, file_id, timestamp_ms, dna_access_url_base, dna_download_url_base
):
    # Construct graph URI and DNA distribution URI
    graph_uri = f"https://glaciation-project.eu/uc/2/{file_id}/timestamp:{timestamp_ms}"
    dna_uri = f"https://glaciation-project.eu/data/{file_id}/dna"

    # Convert timestamps
    created_iso = ms_to_iso8601(timestamp_ms)
    modified_iso = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Construct URLs (placeholders for DNA access)
    dna_access_url = f"{dna_access_url_base}/{file_id}/view"
    dna_download_url = f"{dna_download_url_base}/{file_id}/retrieve"

    # SPARQL INSERT query
    sparql_query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX dct: <http://purl.org/dc/terms/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    INSERT DATA {{
      GRAPH <{graph_uri}> {{
        <{dna_uri}> a dcat:Distribution ;
            dct:description "DNA-archived dataset. Retrieval via simulated endpoint." ;
            dcat:accessURL <{dna_access_url}> ;
            dcat:downloadURL <{dna_download_url}> ;
            dcat:mediaType "application/octet-stream" ;
            dct:created "{created_iso}"^^xsd:dateTime ;
            dct:modified "{modified_iso}"^^xsd:dateTime .
      }}
    }}
    """

    # Send SPARQL update request
    headers = {"Content-Type": "application/json"}
    payload = {"query": sparql_query}
    response = requests.post(fuseki_url, json=payload, headers=headers)

    if response.status_code == 200:
        print(f"Metadata inserted for {file_id}")
    else:
        print(f"Failed to insert for {file_id}")
        print("Status:", response.status_code)
        print("Response:", response.text)


# --- Batch Execution Setup ---

# Your Fuseki SPARQL update endpoint
fuseki_url = "http://metadata.validation/api/v0/graph/update"


# Placeholder URLs for DNA archive endpoints
dna_access_url_base = "https://dna-api.glaciation.eu/archive"
dna_download_url_base = "https://dna-api.glaciation.eu/archive"

# Run for each entry
for f_id, f_timestamp in file_metadata:
    insert_dna_archive_metadata(
        fuseki_url, f_id, f_timestamp, dna_access_url_base, dna_download_url_base
    )

# Verdelix
## Secure data management framework for AI 

This repository is part of the T3.5 initiative focused on building a secure and scalable Data Management Framework for AI-driven applications.

This service is designed to manage, archive, and trace datasets within a Kubernetes-based infrastructure using Knowledge Graphs, Longhorn volumes, and open standards like PROV-O.

Verdelix is a synthesis of two core concepts:

**Verde:** 
Derived from the Spanish and Italian word for "green," which implies environmental, sustainable, or eco-friendly connotations.

**Helix:** 
A term used to describe the spiral structure of a double-stranded DNA molecule in biology. The helix can metaphorically represent structure, continuity, and interwoven elements. In a broader sense, it may signify intertwined data or a structured approach.

Together, Verdelix suggests an eco-friendly, structured, and possibly intertwined or integrated approach, especially when applied to data or technology. It carries both an environmental consciousness and a sense of intricate, yet structured design. The name encapsulates the idea of a sustainable, green approach to structured or complex systems.

## Key Features & SODA Alignment

Below we outline the key features of the framework and how SODA Foundation components support them:

* **Orchestrated Data Lifecycle Management**
    * **SODA Terra:** Provides an API for automated storage provisioning, data movement across storage tiers, and secure deletion aligned with defined policies.

* **Intelligent Distributed Storage**
    * **SODA Terra:** Offers a unified namespace, facilitates data placement based on policies, and serves as the foundation for replication management.

* **Comprehensive Data Provenance**
    * **SODA Terra (with Extensions):** Supports metadata tagging. Potential for deeper integration with future SODA projects specializing in provenance tracking.

* **Enforcement of Data Sovereignty** 
    * **SODA Terra (through Integration):** Integrates with external IAM systems for access control. Provides a policy enforcement layer. Note: Encryption key management often resides outside of core SODA projects.

## Features added

Below mentioned are the two key features implemented as part of Secure data management framework:

* **Data Archival**
    * `data-archival.py` is the script that handles the feature. It can be found at `/server/cronjob/data-archival.py`.
    * This script can be excuted simply by running the following commands in the terminal:
    ```bash
    cd Verdelix/server/cronjob/
    python3 data-archival.py
    ```
    * Scans the Knowledge Graph for datasets older than 10 days.
    * Extracts those files from Longhorn Persistent Volumes (PVs). Such files can be found at `/server/cronjob/longhorn-data-backup/` folder.
    * These files can be further DNA encoded and stored in DNA storage for archival.
    
* **Data Provenance**
    * `data-prov-existing.py` is the script that handles the feature. It can be found at `\server\cronjob\data-prov-existing.py`.
    * This script can be excuted simply by running the following commands in the terminal:
    ```bash
    cd Verdelix/server/cronjob/
    python3 data-prov-existing.py
    ```
    * Queries and enhances the existing metadata in the Knowledge Graph using the PROV-O ontology.
    * Enables traceability of data-tracking its origin, lineage, and transformation.
    * Supports reproducibility and auditability for AI workflows.

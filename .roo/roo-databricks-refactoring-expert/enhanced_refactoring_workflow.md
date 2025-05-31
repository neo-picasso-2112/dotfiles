# Enhanced Databricks Refactoring Workflow

This document outlines the comprehensive workflow for the "Databricks Refactoring Expert" mode. It includes refactoring a user-provided Databricks notebook, synchronizing it, and critically, performing pre-flight validation of source objects and preparation (cloning) of target tables within the `wb_velocityanalytics_prd` Unity Catalog *before* submitting an ephemeral job.

## Goal:
To refactor a user-provided Databricks notebook, synchronize it, and before submitting the ephemeral job, perform comprehensive pre-flight validation of source objects and preparation (cloning) of target tables within the `wb_velocityanalytics_prd` Unity Catalog.

## Key Information Sources:

1.  **User-Provided Databricks Notebook:** The specific notebook to be refactored (path provided dynamically by the user at the start of the task).
2.  **`.roomodes` File:** Contains "Databricks SQL Refactoring Conventions" and references to existing helper scripts and workflows.
3.  **`data_source_validation_protocol.md`:** Details the comprehensive protocol for validating all source objects, including checks for data freshness, producer job verification, and consolidated pre-run reporting.
4.  **`target_table_cloning.md`:** Details procedures for cloning target tables from their original Hive location (e.g., `foreign_edp_prd_hive.velocity_analytics_foundation`) to `wb_velocityanalytics_prd` using `CREATE OR REPLACE TABLE ... DEEP CLONE ...`.

## Workflow Diagram:

```mermaid
graph TD
    A[User provides Databricks Notebook path] --> B{Start Refactoring Workflow};
    B --> C[1. Refactor Notebook: Apply conventions from .roomodes];
    C --> D[2. Pre-flight Validation & Data Preparation];
    D --> E[2a. Parse Refactored Notebook: Identify all DB objects];
    E --> F[2b. Create Object Mapping: original_3_level | uc_refactored_3_level (using .roomodes rules)];
    F --> G{For each SOURCE object in mapping (wb_velocityanalytics_prd)};
    G -- Yes --> H[2c. Validate Source Object (using data_source_validation_protocol.md)];
    H --> I{Validation OK?};
    I -- No --> J[Alert User & Halt];
    I -- Yes --> G;
    G -- No more source objects --> K{For each TARGET table in mapping};
    K -- Yes --> K_hist[2d.i. Check Original Hive Target Table History (DESCRIBE HISTORY foreign_edp_prd_hive...)];
    K_hist --> K_alert{Multiple writers on original?};
    K_alert -- Yes --> K_warn[Alert User: Potential reconciliation issues for original];
    K_warn --> L[2d.ii. Clone Target Table (using target_table_cloning.md)];
    K_alert -- No --> L;
    L --> M{Cloning OK?};
    M -- No --> J;
    M -- Yes --> K;
    K -- No more target tables --> Q[3. All Validations & Cloning Successful?];
    Q -- Yes --> R[4. Submit Ephemeral Job (using existing workflow from .roomodes)];
    R --> S[End Workflow];
    Q -- No --> J;
```

## Detailed Workflow Steps:

1.  **Initialization & Notebook Input:**
    *   The user initiates the "Databricks Refactoring Expert" mode and provides the path to the Databricks notebook that requires refactoring.

2.  **Refactoring Phase:**
    *   Apply the "Databricks SQL Refactoring Conventions" (found in `.roomodes`) to the provided notebook. This includes syntax changes, widget creation, schema/table reference migration, performance optimizations (e.g., `ROW_NUMBER` to `QUALIFY`, `TRUNCATE+INSERT` to `MERGE`), and code cleanup.

3.  **Pre-flight Validation & Data Preparation Phase:**
    *   **3a. Parse Refactored Notebook:**
        *   Parse the refactored notebook code (SQL and/or Python) to identify all unique database object references (tables, views, functions).
    *   **3b. Create Object Mapping:**
        *   Generate a two-column mapping: `original_object_name_3_level | refactored_object_in_unity_catalog_3_level`.
        *   Derive this mapping by applying the "Table Reference Transformation Guide" and "Schema and Table Reference Migration" rules from `.roomodes`.
    *   **3c. Source Object Validation (Iterative):**
        *   For every `refactored_object_in_unity_catalog_3_level` in the mapping identified as a *source* object:
            *   Follow the comprehensive "Data Source Validation" protocol detailed in `data_source_validation_protocol.md`. This includes Source Object Analysis, Migrated Producer Job Verification (if applicable), Data Up-to-Dateness Checks, and generation of a Consolidated Pre-Run Report.
            *   If critical alerts arise from the protocol (e.g., potential stale data), present these prominently to the user and halt if necessary before proceeding to target table cloning or job submission.
    *   **3d. Target Table Identification, Provenance Check & Cloning (Iterative):**
        *   Identify all target tables in the refactored notebook.
        *   For each target table:
            *   Determine `original_target_table_name`, `refactored_target_table_name`, and `<schema>` from the mapping.
            *   **Provenance Check (on original Hive table *and* current UC jobs *before* cloning):**
                *   **Hive History:** Execute: `dbsqlcli -e "DESCRIBE HISTORY foreign_edp_prd_hive.velocity_analytics_foundation.<original_target_table_name>" --table-format ascii`
                    *   Identify unique job names and user names from the Hive history.
                *   **UC Job Check:** For each significant job name identified from Hive history:
                    *   Execute: `databricks jobs list --profile default --output JSON | grep -E '"(<job_name_from_hive_history>)"'`
                *   **Alert User with Combined Analysis:**
                    *   Report which Hive-history jobs *are* found in the current UC workspace (e.g., "Job 'model_score' which historically wrote to the Hive source also exists in the current workspace."). This can provide confidence for proceeding.
                    *   Report which Hive-history jobs *are not* found in the current UC workspace, explaining potential implications (e.g., "Job 'legacy_job_X' which historically wrote to the Hive source was not found in the current workspace. The refactored notebook 'current_notebook.py' may be its replacement, or this indicates a change in data flow that could affect reconciliation if not all logic is covered.").
                    *   If multiple distinct write operations or unmigrated legacy jobs are found, reiterate the potential for reconciliation complexities for the cloned table.
            *   **Cloning Operation:**
                *   Execute cloning as per `target_table_cloning.md`:
                    `dbsqlcli -e "CREATE OR REPLACE TABLE wb_velocityanalytics_prd.<schema>.<refactored_target_table_name> DEEP CLONE foreign_edp_prd_hive.velocity_analytics_foundation.<original_target_table_name>"`
                *   If cloning fails, halt and alert the user.

4.  **Ephemeral Job Submission:**
    *   Only if all source object validations have passed and all necessary target tables have been successfully cloned:
        *   Proceed with submitting and executing the ephemeral job using the refactored notebook, following the existing "Post-Refactoring Validation" workflow referenced in `.roomodes` (e.g., using `databricks_job_runner.sh`).

5.  **Completion/Reporting:**
    *   Report the outcome of the job submission and execution to the user.

This enhanced workflow ensures greater data integrity and preparedness before executing refactored Databricks notebooks.
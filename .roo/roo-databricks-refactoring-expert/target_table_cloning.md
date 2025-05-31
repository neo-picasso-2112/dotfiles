# Target Table Cloning Instructions

This document outlines the steps and commands for cloning target tables identified in a refactored Databricks notebook. The cloning process prepares these tables in the `wb_velocityanalytics_prd` Unity Catalog *before* the ephemeral job submission. This ensures that the job writes to a fresh, controlled copy of the original production table.

## Cloning Steps for Each Target Table:

For every table identified as a *target* for write operations (e.g., `INSERT`, `MERGE`, `CREATE TABLE AS SELECT`, `DataFrame.write.saveAsTable`) in the refactored notebook:

1.  **Identify Source and Destination:**
    *   **Source Table for Cloning:** The original production table, typically located in the Hive metastore. Based on current conventions, this will be:
        `foreign_edp_prd_hive.velocity_analytics_foundation.<original_target_table_name>`
    *   **Destination Table in Unity Catalog:** The refactored table name within the `wb_velocityanalytics_prd` catalog. This will be:
        `wb_velocityanalytics_prd.<schema>.<refactored_target_table_name>`
    *   The `<original_target_table_name>`, `<schema>`, and `<refactored_target_table_name>` will be derived from the object mapping created during the pre-flight validation phase.

2.  **Execute Deep Clone Operation:**
    *   **Purpose:** To create an independent, full copy of the source table at the destination. Using `CREATE OR REPLACE TABLE` ensures the operation is idempotent.
    *   **Command:**
        ```bash
        dbsqlcli -e "CREATE OR REPLACE TABLE wb_velocityanalytics_prd.<schema>.<refactored_target_table_name> DEEP CLONE foreign_edp_prd_hive.velocity_analytics_foundation.<original_target_table_name>" --table-format ascii
        ```
    *   **Action:** If the command fails, report this as a critical error and halt the pre-flight validation process.

**Important Considerations:**

*   Replace `<original_target_table_name>`, `<schema>`, and `<refactored_target_table_name>` with the actual names.
*   Ensure that the service principal or user executing the `dbsqlcli` command has the necessary permissions to read from the source Hive table and create/replace tables in the target Unity Catalog schema.
*   Deep cloning can be resource-intensive for very large tables. This process assumes that the tables are of a manageable size for cloning within the job execution window or that appropriate cluster resources are available.
*   The `DEEP CLONE` operation copies the data as well as the table metadata.
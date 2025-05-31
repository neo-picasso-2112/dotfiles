# General Instructions for Databricks Reconciliation Expert Mode

This document outlines the general workflow and key considerations when using the Databricks Reconciliation Expert mode.

## Core Objective
To systematically compare data between a newly created/refactored Unity Catalog (UC) table and its original Hive metastore counterpart, identify discrepancies, diagnose root causes, and suggest fixes.

## Workflow
1.  **Identify Tables:** Clearly define the UC target table and the Hive source/comparison table.
2.  **Initial Checks (using `dbsqlcli` via `execute_command` tool):**
    *   **Row Count Comparison:** Verify if the number of rows matches.
    *   **Schema Comparison:** Ensure data types, column names, and column order are consistent or intentionally changed.
3.  **Data Content Comparison (using `dbsqlcli`):**
    *   Perform an `EXCEPT` query (e.g., `SELECT * FROM uc_table EXCEPT SELECT * FROM hive_table` and vice-versa) to find differing rows.
4.  **Investigate Discrepancies:**
    *   If discrepancies exist, analyze the refactored notebook's logic.
    *   Examine source tables used by the notebook:
        *   Compare source tables in UC vs. Hive if they were also migrated.
        *   Use `DESCRIBE HISTORY source_table_name` to check for recent modifications or concurrent writes that might affect the data.
    *   Look for common refactoring pitfalls (e.g., incorrect join conditions, flawed filtering logic, issues with data type conversions).
5.  **Root Cause Analysis:** Based on the investigation, determine the most likely cause of the data mismatch.
6.  **Suggest Fixes:**
    *   If the issue is in the refactored notebook, provide specific code suggestions to correct the logic.
    *   If the issue is with source data, highlight the problematic source.
7.  **Iteration:** After fixes are applied and the Databricks job is re-run, repeat the reconciliation process.

## Key `dbsqlcli` Usage
*   This mode will heavily rely on the `execute_command` tool to run `dbsqlcli` commands.
*   Ensure `dbsqlcli` is configured correctly to connect to the appropriate Databricks SQL warehouse.
*   Refer to `sql_templates.md` for common query patterns.
*   Refer to `dbsqlcli_commands.md` for command structures.
*   Refer to `catalog_paths.md` for common catalog and schema names.

## Important Considerations
*   **Permissions:** Ensure the credentials used by `dbsqlcli` have the necessary read permissions on both UC and Hive tables, as well as `USAGE` on catalogs and schemas.
*   **Data Volume:** For very large tables, full data comparison (`EXCEPT *`) can be resource-intensive. Consider sampling or comparing specific problematic subsets if performance is an issue.
*   **Data Skew:** Be mindful of data skew when analyzing discrepancies, as it might point to issues in partitioning or join logic.
*   **Transformation Logic:** Pay close attention to complex transformations, UDFs, and window functions in the refactored notebook, as these are common sources of errors.
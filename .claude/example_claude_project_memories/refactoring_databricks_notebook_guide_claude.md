# Folder Structure

analytical-data-model - Stores all Databricks notebook that have been refactored
analytical-data-model/to_be_refactored - Stores legacy Databricks notebook that use to run in hive Databricks workspace to be refactored.
tests/ - Contains pytest scripts to run data reconciliation tests
scripts/ - Contains adhoc scripts for developers to run to submit jobs such as pytest data reconciliation tests, or submitting refactored notebooks to be executed in an ephemeral job run (unit-testing).

## Commonly Used Commands

We typically use the CLI tool `dbsqlcli` quite often to submit SQL queries against our Databricks SQL Warehouse and get the returned results via our terminal in table format - very useful for debugging
data mismatches between migrated Unity catalog table produced by refactored notebooks against the same data assets in Hive catalog (foreign_edp_prd_hive.velocity_analytics_foundation catalog schema)

# Databricks SQL Refactoring Conventions

## Purpose
This document provides comprehensive guidelines for refactoring Databricks notebooks (SQL and Python) to make them Unity Catalog compatible. These conventions ensure consistent, performant, and maintainable code across all refactored notebooks.

## Critical Requirements

### Session Configuration
**ALWAYS** begin each notebook with these configuration statements:
```sql
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT delta_days DEFAULT '3'; 
```

Add additional widgets as needed for specific use cases:
```sql
-- Add when working with staging tables
CREATE WIDGET TEXT stage_source_schema DEFAULT 'staging';
-- Add when working with ALMS data
CREATE WIDGET TEXT edp_catalogue_name DEFAULT 'edp_prd';
CREATE WIDGET TEXT edp_source_schema DEFAULT 'silver_alms';
```

### Schema and Table Reference Migration

#### Core Schema Migration Rules
- **NEVER** source or target schema "velocity_analytics_foundation"
- **ALWAYS** use "loyalty" schema for standard tables
- **ALWAYS** use "staging" schema for staging tables
- **ALWAYS** use "reporting_loyalty" schema for tables with "rpt_" prefix
- **ALWAYS** change references from `va_alms_prd` schema to `edp_prd` database catalogue with schema `silver_alms`
- **ALWAYS** remove `stage_` prefix on staging tables when updating references

#### Table Reference Transformation Guide

| Original Reference Pattern | Transformed Reference Pattern | Notes |
|---------------------------|------------------------------|-------|
| `velocity_analytics_foundation.table_name` | `wb_velocityanalytics_prd.loyalty.table_name` | Keep table name unchanged |
| `velocity_analytics_foundation.staging_table_name` | `wb_velocityanalytics_prd.staging.table_name` | Remove `staging_` prefix |
| `va_alms_prd.table_name` | `edp_prd.silver_alms.table_name` | Change catalog and schema |
| `${base_schema}.table_name` | `IDENTIFIER(:catalogue_name || '.' || :source_schema || '.table_name')` | Replace variable syntax with parameter markers |
| Table with `rpt_` prefix | Target schema should be `reporting_loyalty` | For reporting tables |

#### Reference Examples

```sql
-- BEFORE: Legacy references
SELECT * FROM velocity_analytics_foundation.customer_table;
SELECT * FROM velocity_analytics_foundation.staging_partner_data;
SELECT * FROM va_alms_prd.member_history;

-- AFTER: Unity Catalog compatible references
SELECT * FROM wb_velocityanalytics_prd.loyalty.customer_table;
SELECT * FROM wb_velocityanalytics_prd.staging.partner_data;
SELECT * FROM edp_prd.silver_alms.member_history;

-- BEFORE: Variable syntax
SELECT * FROM ${base_schema}.table_name;

-- AFTER: Parameter markers
SELECT * FROM IDENTIFIER(:catalogue_name || '.' || :source_schema || '.table_name');
```

### Parameter Markers & Identifiers
- **ALWAYS** use parameter markers with IDENTIFIER clause for table references:
  ```sql
  -- Correct
  CREATE OR REPLACE TABLE IDENTIFIER(:catalogue_name || '.' || :target_schema || '.table_name') AS
  SELECT * FROM IDENTIFIER(:catalogue_name || '.' || :source_schema || '.source_table')
  ```

- **NEVER** use `${variable}` syntax - this is a critical anti-pattern:
  ```sql
  -- INCORRECT - DO NOT USE
  SELECT * FROM ${base_schema}.table
  ```

- **EXCEPTION**: Parameter markers CANNOT be used inside temporary view definitions - use explicit 3-level namespace:
  ```sql
  -- Inside temporary views, use explicit namespace
  CREATE OR REPLACE TEMPORARY VIEW temp_view AS
  SELECT * FROM wb_velocityanalytics_prd.loyalty.table
  ```
    - Additionally, Parameter markers are typically not directly used within the definition of a temporary view itself, especially in the DDL statement (e.g., CREATE VIEW temp_view_name AS ...). 
    - Can't use parameter markers to refer to widgets such as `:delta_days` within views/temporary views.


- **ALMS Data References**: When referencing ALMS data, use the appropriate widgets:
  ```sql
  -- Correct
  SELECT * FROM IDENTIFIER(:edp_catalogue_name || '.' || :edp_source_schema || '.partners_hist');
  
  -- Inside temporary views
  SELECT * FROM edp_prd.silver_alms.partners_hist;
  ```

## SQL Performance Optimizations

### ROW_NUMBER() Refactoring (CRITICAL)
**ALWAYS** replace nested ROW_NUMBER() queries with QUALIFY - this is a top priority:

```sql
-- BEFORE: Nested query with ROW_NUMBER() filter (ANTI-PATTERN)
WITH cte AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY col1, col2 ORDER BY date DESC) AS rn 
    FROM table
)
SELECT * FROM cte
WHERE rn = 1

-- AFTER: Single query with QUALIFY (REQUIRED)
SELECT * FROM table
QUALIFY ROW_NUMBER() OVER (PARTITION BY col1, col2 ORDER BY date DESC) = 1 
```

### TRUNCATE + INSERT Refactoring
**ALWAYS** replace TRUNCATE followed by INSERT with a single MERGE operation:

```sql
-- BEFORE: Two separate operations (ANTI-PATTERN)
TRUNCATE TABLE schema.target_table;
INSERT INTO schema.target_table
SELECT * FROM source_table;

-- AFTER: Single MERGE operation (REQUIRED)
MERGE INTO IDENTIFIER(:catalogue_name || '.' || :target_schema || '.target_table') AS target
USING source_table AS source
ON FALSE -- Replace all rows
WHEN NOT MATCHED THEN
  INSERT *
WHEN MATCHED THEN
  DELETE
```

### Other SQL Optimizations
1. **ALWAYS** replace numeric column positions with explicit column names:
   ```sql
   -- INCORRECT
   SELECT col1, col2 FROM table ORDER BY 1, 2
   
   -- CORRECT
   SELECT col1, col2 FROM table ORDER BY col1, col2
   ```

2. **ALWAYS** use table aliases when joining multiple tables
3. **ALWAYS** push predicates early in queries
4. **AVOID** `SELECT *` - specify required columns
5. Only cache tables used > 2 times in a notebook

## Code Cleanup Requirements

### Remove Unnecessary Code
- **REMOVE** any standalone SELECT queries that return results (except assertions)
- **REMOVE** all commented-out code blocks
- **REMOVE** all `OPTIMIZE` statements
- **REMOVE** all `ANALYZE` statements
- **REMOVE** all `TABLE PARTITION BY` statements

### Assertion Requirements
- **ENSURE** all assertions have the alias CHECKSUM:
  ```sql
  SELECT ASSERT_TRUE(condition) AS checksum
  ```

### Replacing Dynamic Date/Timestamp Variables

**ALWAYS** replace dynamic date/timestamp variables set via `spark.conf.set` and accessed with `${...}` syntax with built-in SQL functions. This avoids unnecessary cross-language
variable passing for standard values.

*   **Anti-Pattern:** Setting current date via Python and Spark Conf.
    ```python
    # In Python cell
    current_sql_date = datetime.now().strftime('%Y-%m-%d')
    spark.conf.set('env_var.current_sql_date', "'" + current_sql_date + "'")
    ```
    ```sql
    -- In SQL cell
    SELECT * FROM my_table WHERE event_date = ${env_var.current_sql_date};
    ```

*   **Required Pattern:** Using built-in SQL functions directly.
    ```sql
    -- In SQL cell
    -- Ensure TIME ZONE is set appropriately at the start of the notebook
    SELECT * FROM IDENTIFIER(:catalogue_name || '.' || :source_schema || '.my_table')
    WHERE event_date = current_date();
    -- Or use current_timestamp() if timestamp precision is needed
    ```

## Examples of Complete Refactoring

### Example 1: Basic Table Creation
```sql
-- BEFORE
CREATE OR REPLACE TABLE ${base_schema}.vel_activity_accrual_afm_link AS
SELECT * FROM velocity_analytics_foundation.vel_catalogue_ref_snapshot
WHERE col = "5";

-- AFTER
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';

CREATE OR REPLACE TABLE IDENTIFIER(:catalogue_name || '.' || :target_schema || '.vel_activity_accrual_afm_link') AS
SELECT col1, col2, col3 FROM IDENTIFIER(:catalogue_name || '.' || :source_schema || '.vel_catalogue_ref_snapshot')
WHERE col = '5';
```

### Example 2: ROW_NUMBER() Refactoring with Delta Days
```sql
-- BEFORE
SET TIME ZONE 'Australia/Sydney';
WITH ranked_data AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY activity_date DESC) AS rn
  FROM velocity_analytics_foundation.customer_activity
  WHERE activity_date >= current_date - INTERVAL '5' DAY
)
SELECT customer_id, activity_type, points 
FROM ranked_data
WHERE rn = 1;

-- AFTER
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT delta_days DEFAULT '5';

SELECT customer_id, activity_type, points
FROM IDENTIFIER(:catalogue_name || '.' || :source_schema || '.customer_activity')
WHERE activity_date >= DATE_SUB(current_date, :delta_days) -- We don't use INTERVAL days here, this is nicer.
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY activity_date DESC) = 1;
```

### Example 3: Complete Refactoring with Multiple Patterns
```sql
-- BEFORE
-- Some commented out code
-- SELECT * FROM old_table;
SET TIME ZONE 'Australia/Sydney';
TRUNCATE TABLE velocity_analytics_foundation.vel_classification_code_ref_snapshot;
INSERT INTO velocity_analytics_foundation.vel_classification_code_ref_snapshot
(col1, col2, col3) 
SELECT DISTINCT col1, col2, col3 
FROM va_alms_prd.stage_source_table
WHERE col1 IN (SELECT id FROM velocity_analytics_foundation.lookup_table WHERE rn = 1);
OPTIMIZE velocity_analytics_foundation.vel_classification_code_ref_snapshot ZORDER BY (col1);
SELECT * FROM velocity_analytics_foundation.vel_classification_code_ref_snapshot LIMIT 10;

-- AFTER
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT stage_source_schema DEFAULT 'staging';
CREATE WIDGET TEXT edp_catalogue_name DEFAULT 'edp_prd';
CREATE WIDGET TEXT edp_source_schema DEFAULT 'silver_alms';

MERGE INTO IDENTIFIER(:catalogue_name || '.' || :target_schema || '.vel_classification_code_ref_snapshot') AS target
USING (
  SELECT DISTINCT col1, col2, col3 
  FROM IDENTIFIER(:edp_catalogue_name || '.' || :edp_source_schema || '.source_table')
  WHERE col1 IN (
    SELECT id 
    FROM IDENTIFIER(:catalogue_name || '.' || :source_schema || '.lookup_table')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) = 1
  )
) AS source
ON FALSE
WHEN NOT MATCHED THEN
  INSERT (col1, col2, col3)
  VALUES (source.col1, source.col2, source.col3)
WHEN MATCHED THEN
  DELETE;
```

### Example 4: Staging Table Reference Refactoring
```sql
-- BEFORE
SELECT * FROM velocity_analytics_foundation.staging_partner_data;
INSERT INTO velocity_analytics_foundation.staging_transaction_history
SELECT * FROM va_alms_prd.transaction_source;

-- AFTER
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT stage_source_schema DEFAULT 'staging';
CREATE WIDGET TEXT edp_catalogue_name DEFAULT 'edp_prd';
CREATE WIDGET TEXT edp_source_schema DEFAULT 'silver_alms';

SELECT * FROM IDENTIFIER(:catalogue_name || '.' || :stage_source_schema || '.partner_data');
INSERT INTO IDENTIFIER(:catalogue_name || '.' || :stage_source_schema || '.transaction_history')
SELECT * FROM IDENTIFIER(:edp_catalogue_name || '.' || :edp_source_schema || '.transaction_source');
```

### Example 5: Reporting Table Refactoring
```sql
-- BEFORE
CREATE OR REPLACE TABLE velocity_analytics_foundation.rpt_member_summary AS
SELECT member_id, SUM(points) as total_points
FROM velocity_analytics_foundation.member_activity
GROUP BY member_id;

-- AFTER
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT target_schema DEFAULT 'reporting_loyalty';

CREATE OR REPLACE TABLE IDENTIFIER(:catalogue_name || '.' || :target_schema || '.rpt_member_summary') AS
SELECT member_id, SUM(points) as total_points
FROM IDENTIFIER(:catalogue_name || '.' || :source_schema || '.member_activity')
GROUP BY member_id;
```

## Common Pitfalls to Avoid
1. Forgetting to set the timezone to 'Australia/Brisbane'
2. Using `${variable}` syntax instead of parameter markers. Instead create a widget for that variable and refer as parameter marker if possible.
3. Leaving nested ROW_NUMBER() queries instead of using QUALIFY
4. Using TRUNCATE + INSERT instead of MERGE
5. Forgetting to remove OPTIMIZE, ANALYZE, or PARTITION BY statements
6. Using numeric column positions in ORDER BY/GROUP BY
7. Leaving standalone SELECT queries that return results

Remember: The goal is minimal, focused changes that improve code quality while ensuring Unity Catalog compatibility.

## Custom Instruction: Refactor File Saving to Databricks Volumes

When a Databricks notebook contains logic for saving files to `dbfs` (e.g., using `/dbfs/...` paths) and then copying them to S3 (often using `dbutils.fs.cp`), or directly writing to S3 paths that should now be Volumes, perform the following refactoring steps:

1.  **Identify Legacy File Saving:** Detect patterns like `df.to_csv("/dbfs/...")` followed by `dbutils.fs.cp("dbfs:/...", "s3://...")` or direct writes to S3 paths intended for Volume migration.
2.  **Confirm Original S3 Path:** State the current S3 destination path identified in the notebook (e.g., `s3://original-bucket/original-prefix/file.csv`).
3.  **Query for Volume Schema:** Ask the user to provide the target Unity Catalog `catalog.schema` where Databricks Volumes are managed (e.g., `wb_velocityanalytics_prd.wb_velocityanalytics_portal`).
4.  **List Available Volumes:**
    *   Execute the command: `dbsqlcli -e "SHOW VOLUMES IN <catalog.schema_from_user>"` --table-format ascii
    *   Present the list of available volumes to the user.
5.  **Propose Volume Path:**
    *   Based on the original S3 bucket name and path structure, and the list of available Volumes, propose a target Volume and a file prefix within that Volume.
    *   Example: If original S3 was `s3://va-edp-prd-outbound-analytics/velocity-analytics/ACM/model-purge/` and a `adobe_campaign_outbound` Volume exists, propose `/Volumes/<catalog>/<schema>/adobe_campaign_outbound/velocity-analytics/ACM/model-purge/`.
6.  **Confirm Full Volume Path:** Ask the user to confirm the proposed full Volume path or provide the correct one. Iterate if necessary, ensuring the file prefix matches the S3 path structure after the bucket name, as per user preference.
7.  **Refactor Code:**
    *   Modify the file writing command (e.g., `pandas.to_csv()`, `spark.write.format().save()`) to use the confirmed full Databricks Volume path (e.g., `/Volumes/catalog/schema/volume_name/prefix/filename`).
    *   Remove any subsequent `dbutils.fs.cp` commands related to the refactored file operation.
    *   If applicable, replace any direct S3 path writes with the new Volume path.
    *   Add a markdown comment indicating the change and the removal of the `dbutils.fs.cp` step, referencing the new Volume path.
8.  **Proceed with Workflow:** After successfully refactoring the file saving mechanism, continue with the standard refactoring workflow (e.g., source object validation).

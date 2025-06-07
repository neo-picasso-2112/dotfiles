# Common Catalog and Schema Paths for Data Reconciliation

This file lists common catalog and schema names that are frequently used during data reconciliation between Hive metastore and Unity Catalog (UC). These are placeholders and should be confirmed or updated based on the specific environment.

## Unity Catalog (UC) Paths

*   **Default Target Catalog for Refactored Tables:**
    *   `{uc_catalog_prod}`: e.g., `main`, `prod`, `gold_catalog`
    *   `{uc_catalog_dev}`: e.g., `dev`, `sandbox_catalog`

*   **Common UC Schemas:**
    *   `{uc_schema_gold}`: e.g., `gold`, `curated`, `analytics`
    *   `{uc_schema_silver}`: e.g., `silver`, `transformed`
    *   `{uc_schema_bronze}`: e.g., `bronze`, `raw` (less common for direct comparison against Hive production tables, but might be relevant for source tracing)

**Example UC Table Path:** `{uc_catalog_prod}.{uc_schema_gold}.{table_name}`

## Hive Metastore Paths

*   **Default Hive Catalog (often implicit or a standard name like `hive_metastore` if explicitly referenced in UC via foreign catalogs):**
    *   `{hive_catalog_legacy}`: e.g., `hive_metastore`, `legacy_db` (or sometimes not specified if queries are run in a context where it's the default)

*   **Common Hive Schemas (Databases):**
    *   `{hive_schema_prod}`: e.g., `default`, `production`, `app_db`
    *   `{hive_schema_staging}`: e.g., `staging`

**Example Hive Table Path (if accessed via UC foreign catalog):** `{hive_catalog_legacy}.{hive_schema_prod}.{table_name}`
**Example Hive Table Path (if `dbsqlcli` context is set to Hive):** `{hive_schema_prod}.{table_name}`

## Placeholders to be Replaced in SQL Templates:

*   `{uc_catalog}`: The target Unity Catalog name.
*   `{uc_schema}`: The target schema within the UC catalog.
*   `{uc_table}`: The target table name in UC.

*   `{hive_catalog}`: The Hive catalog name (often `hive_metastore` when accessed from UC, or might be omitted if `dbsqlcli` is configured for a Hive context).
*   `{hive_schema}`: The Hive schema (database) name.
*   `{hive_table}`: The Hive table name.

*   `{uc_source_schema}`: Schema for a source table in UC.
*   `{hive_source_schema}`: Schema for a source table in Hive.
*   `{source_table}`: Name of a source table.

*   `{catalog_name}`: Generic placeholder for a catalog, use specific UC or Hive one.
*   `{schema_name}`: Generic placeholder for a schema.
*   `{table_name}`: Generic placeholder for a table.


**Note:** The user should be prompted to confirm these paths or provide the correct ones for their environment at the beginning of a reconciliation task if they are not already known or configured.
# `dbsqlcli` Command Structures

This file provides common command structures for using `dbsqlcli` to execute SQL queries for data reconciliation. These commands will be used with the `execute_command` tool.

## Basic Query Execution

The fundamental command to execute a SQL query from a string:
```bash
dbsqlcli -e "YOUR_SQL_QUERY_HERE"
```

**Example:**
```bash
dbsqlcli -e "SELECT COUNT(*) FROM my_catalog.my_schema.my_table;"
```

## Executing a SQL Query from a File

If a complex query is saved in a `.sql` file (e.g., `query.sql`):
```bash
dbsqlcli -f /path/to/your/query.sql
```
*Note: The path to the SQL file should be accessible from where `dbsqlcli` is executed.*

## Specifying Connection Parameters (If not using default configuration)

`dbsqlcli` typically uses a default connection configuration (e.g., from `~/.dbsqlcli/dbsqlclirc` or environment variables). If you need to override or specify connection parameters:

*   **Host:** `--host YOUR_DATABRICKS_HOST` (e.g., `adb-xxxx.azuredatabricks.net`)
*   **HTTP Path:** `--http-path YOUR_SQL_WAREHOUSE_HTTP_PATH` (e.g., `/sql/1.0/warehouses/xxxx`)
*   **Token:** `--token YOUR_DATABRICKS_PAT_TOKEN` (Personal Access Token)

**Example with connection parameters:**
```bash
dbsqlcli --host myhost.databricks.com --http-path /sql/1.0/warehouses/abcdef1234567890 --token dapiXXXXXXXXXXXXXXXX \
-e "SELECT COUNT(*) FROM my_catalog.my_schema.my_table;"
```
*For security, it's generally better to configure these in the `dbsqlclirc` file or use environment variables rather than passing tokens directly in commands, especially if these commands are logged.*

## Output Formatting

`dbsqlcli` offers various output formats. The default is usually `tabular`.
*   `--format csv` for CSV output
*   `--format tsv` for TSV output
*   `--format json` for JSON output
*   `--format vertical` for a vertical display, useful for wide tables.

**Example (CSV output):**
```bash
dbsqlcli --format csv -e "SELECT * FROM my_catalog.my_schema.my_table LIMIT 10;" > output.csv
```
*This redirects the CSV output to a file named `output.csv`.*

## Using with `execute_command` Tool

When constructing the command for the `execute_command` tool:
1.  Replace placeholders in SQL templates (from `sql_templates.md`) with actual table/schema/catalog names.
2.  Embed the finalized SQL query within the `dbsqlcli -e "..."` structure.
3.  Ensure any special characters within the SQL query (like quotes) are handled correctly if the command is complex, though `dbsqlcli -e` is generally robust.

**Example for `execute_command`:**
```xml
<execute_command>
  <command>dbsqlcli -e "SELECT COUNT(*) AS uc_row_count FROM prod_uc_catalog.gold_schema.fact_sales;"</command>
</execute_command>
```

## Important Notes:
*   **Configuration:** It's assumed that `dbsqlcli` is installed and configured to connect to the target Databricks SQL warehouse. If not, the user will need to set this up first. This mode might need to remind the user about this prerequisite.
*   **Error Handling:** The output of `dbsqlcli` (stdout/stderr) should be reviewed after each command execution to check for errors or unexpected results.
*   **Long Queries:** For very long or complex SQL queries, writing them to a temporary `.sql` file and executing with `dbsqlcli -f` might be more manageable than a long `-e` string.
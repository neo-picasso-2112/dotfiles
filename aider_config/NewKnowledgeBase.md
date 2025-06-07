## New Knowledge Base

1. Widget Creation:
   - Always ensure that widgets are created for all catalogues and schemas used in the SQL scripts, such as edp_source_schema, to facilitate parameterization.

2. Temporary View Limitations:
   - When creating temporary views in Databricks, parameter markers and the IDENTIFIER
 function cannot be used. Instead, use the full 3-level namespace directly in the SQL
 statement.

3. Parameterization:
   - Avoid using ${} syntax for variable references. Instead, use the IDENTIFIER function with parameter markers for safe and consistent SQL injection prevention.

4. QUALIFY Usage:
   - When refactoring ROW_NUMBER() queries, ensure that the QUALIFY clause is used correctly to replace filtering conditions, and remove redundant lines.

5. Attention to Detail:
   - Ensure that all search/replace operations match the exact content, including whitespace and indentation, to avoid mismatches.

6. Consistent Namespace Usage:
   - Always use 3-level namespaces for table references, especially when refactoring from older schemas like va_alms_prd to edp_prd.silver_alms.

7. Using MERGE INTO for Inserts Only:
   - When refactoring to use `MERGE INTO` statements, if the original logic only involve
 inserting new records without updating existing ones, ensure that the `MERGE INTO`
 statement only includes the `WHEN NOT MATCHED THEN INSERT` clause. This maintains the
 original behavior and ensures backward compatibility.

8. Emphasizing the Use of Widgets for All Schema and Catalogue References:
   - Consistently use widgets for all schema and catalogue references to ensure parameterization and flexibility across different environments.

9. Notebooks might initially use Python cells to fetch widget values (e.g., `dbutils.widgets.get('base_schema')`) and set them as Spark session variables (e.g., `spark.conf.set('env_var.base_schema', ...)`), which are then used in SQL with `${env_var.variable}` syntax. While refactoring, standard SQL widgets (`CREATE WIDGET TEXT catalogue_name ...`) should be introduced as a first step. A subsequent step will be to refactor the SQL to use these new SQL widgets directly with `IDENTIFIER(:widget_name)` syntax and remove the Python-based Spark variable pattern for schema/catalogue names.

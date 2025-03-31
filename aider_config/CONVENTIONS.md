# Coding Conventions

The goal of these coding conventions is to refactor Databrick's notebooks written in SQL and sometimes Python
because we need to update these notebooks to be unity catalog compatible.

## General Guidance
- Modify files as minimally as possible to accomplish the task. Don't make superfluous changes, whitespace changes or changes to code that don't relate to goal.

## Conventions

1. At the beginning of workbook - Configure session & Parameterise Catalogue name, Schema name, Delta days always.
```sql
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT delta_days DEFAULT '3'; 
```
- If the SQL queries are selecting from a source schema that isn't loyalty,create another widget text for that source schema to reference that widget in the code as a parameter marker (use identifier function to form relation names for tables, views, functions etc.)
- If `delta_days` value is used or called within the code, then update the default value. For example, if 'INTERVAL 5 DAYS' is mentioned in the code, then change the default value for delta_days and reference this widget within the code.
- Use parameter markers (by creating widgets first) where necessary when creating target tables/functions/views (not possible to use this in temporary views). Our target tables will always be `loyalty` schema unless otherwise specified.

#### Usage Example
- Bad example code
```sql
CREATE WIDGET TEXT delta_days DEFAULT '3'; 
CREATE WIDGET TEXT table_ref DEFAULT "[TODO]";
SET TIME ZONE 'Australia/Sydney';
create or replace table velocity_foundations.table as
select * from stage.stage_dim_customer
where activity_date >= current_date - interval '5' day;
```
- Good code (refactored)
```sql
# bad code
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT stage_source_schema DEFAULT 'stage';

CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT delta_days DEFAULT '3'; 
create or replace table identifier(:catalogue_name || '.' || :target_schema || '.table_name') as
select * from identifier(:catalogue_name || '.' || :stage_source_schema || '.dim_customer')
where activity_date >= current_date - interval :delta_days day;
```

2. Update SQL references using parameter markers when selecting from tables, views, functions etc along with the IDENTIFIER clause to enable SQL injection safe parametrization of SQL statements. 
- If current code only references 2 level namespace, update to use 3 level namespace.
- Note: IDENTIFIER clause and parameter markers cannot be used inside temporary view queries, instead refer to 3 level namespaces directly `wb_velocityanalytics_prd.loyalty.<table>`.
- For temporary functions, and views - we do not need to explicitly mention the 3 level namespace and can leave as is.

#### Usage Example
- Bad code
```sql
-- Never ever refer to variables/widgets like ${var} since this is bad
-- Remove any code that creates variables like this ${base_schema} e.g. and use widgets as parameter markers.

CREATE OR REPLACE TABLE ${base_schema}.vel_activity_accrual_afm_link AS
select * from velocity_analytics_foundation.vel_catalogue_ref_snapshot
where col = "5";
```

- Good refactored code.
```sql
CREATE OR REPLACE TABLE IDENTIFIER(:catalogue_name || '.' || :target_schema|| '.vel_activity_accrual_afm_link') AS
select * from IDENTIFIER(:catalogue_name || '.' || :source_schema|| '.vel_catalogue_ref_snapshot')
where col = :delta_days ;
```

3. Remove unnecessary code:
- Any select queries that will return a result except for assertion checks. We only want queries that return no results such as CREATE TABLE or MERGE INTO statements. Any other select queries that produce results, including those used for eye checks or printing results in Databricks notebooks, should be removed.
- NOTE: Please ensure to remove any unnecessary blocks of commented-out code as per the coding conventions.                                                                           
- Remove any `OPTIMIZE` SQL statements.
- Remove any `ANALYSE` sql statements.
- Remove any `TABLE PARTITION BY` statements, we do not want table partitioning statements within our code.

#### Usage Example
- Bad code
```sql
-- SOME commented out block of sql query
-- Select (* from table);
OPTIMIZE ${base_schema}.vel_activity_accrual_afm_link ZORDER BY (reservation_hash, document_hash, coupon_sequence_number);
ANALYZE TABLE ${base_schema}.afm_document_coupon_proration --[ PARTITION clause ]
    COMPUTE STATISTICS FOR COLUMNS reservation_hash, document_hash, distance_proration_factor_gcd;

INSERT INTO velocity_analytics_foundation.vel_classification_code_ref_snapshot
(col1, col2, col3) select distinct col1, col2, col3 from velocity_analytics_foundation.table
select * from final_result;
```

- Good refactored code
```sql
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT delta_days DEFAULT '3'; 
INSERT INTO IDENTIFIER(:catalogue_name || '.' || :target_schema || '.vel_classification_code_ref_snapshot')
(col1, col2, col3) select distinct col1, col2, col3 from 
IDENTIFIER(:catalogue_name || '.' || :source_schema || '.vel_classification_code_ref_snapshot')
```

4. Replace ROW_NUMBER() inner query with QUALIFY ROW_NUMBER() … = 1

5. Avoid SELECT * - specify required columns in SELECT statement.
- If you do not know the required select columns, then leaving it as SELECT * should suffice.

6. Ensure assertions must have alias CHECKSUM. For e.g. `SELECT ASSERT_TRUE(...) AS checksum`

7. Use table qualifier/alias when more than 1 tables are used in a query

8. Only cache tables if it is used > 2 times within the code notebook/script.

9. Do not format the code, and change identation. Leave long lines as is, and only delete and change necessary lines of code to follow coding standards.

10. Push predicates early within the SQL query.

## Table Naming Conventions

As you go an update the Databrick's notebooks, you will notice some tables referenced has **staging_** prefix in the table name itself.
- When you update this table reference to use 3 level namespace, remove the `staging_` prefix from the table name.
- Next, Ensure you create a widget `source_staging_schema` with value `staging`.
- Lastly, refer to this widget within the code as a parameter marker or the values directly.
- Note: Tables with prefix `staging_` is always found within the `staging` schema within the catalogue `wb_velocityanalytics_prd`. Just remember to remove `staging_` prefix in the table name as you update the code.

Otherwise, you can assume the source tables we are selecting from (tables without `staging_` prefix in its table name), assume you can always source the data from:
- `wb_velocityanalytics_prd` catalogue and `loyalty` schema.
- Table names will remain the same.
- Use parameter markers with IDENTIFIER clause or without IDENTIFIER clause, or use the values directly to select from 3 level namespace tables.

Lastly, most code will select tables from a schema named `va_alms_prd.<table>`. Again, you must update this reference to `edp_prd.silver_alms.<table>` since the same tables from `va_alms_prd` schema can also be found within the unity catalog `edp_prd.silver_alms` schema.

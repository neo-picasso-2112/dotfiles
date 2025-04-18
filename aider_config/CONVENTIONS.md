# Coding Conventions

The goal of these coding conventions is to refactor Databrick's notebooks written in SQL and sometimes Python
because we need to update these notebooks to be unity catalog compatible.

## General Guidance
- Modify files as minimally as possible to accomplish the task. Don't make superfluous changes, whitespace changes or changes to code that don't relate to goal.
- Do not use IDENTIFIER clause with parameter markers inside temporary views, use 3 level namespace to refer to views/tables/functions inside temporary view statements e.g. `select * from catalogue.schema.table`
- We will never source or target schema "velocity_analytics_foundation" in our catalogue, it will always be "loyalty" schema for tables and "stage" schema for staging tables.
- Change select references to `va_alms_prd` schema to `edp_prd` database catalogue, and schema `silver_alms` always.
- Always remove `stage_` prefix on tables for staging tables when refactoring code, and the target schema should be updated to "staging".

## SQL Coding Rules for Refactoring
1. Always replace ROW_NUMBER() inner queries with the QUALIFY ROW_NUMBER() function for better readability and performance.
```sql
# bad example
with cte as (
    select *, row_number() over partition by (col1, col2 order by date desc) as rn from table
)
select * from cte
where rn = 1

# refactored good code
select * from table
qualify row_number() over partition by (col1, col2 order by date desc) = 1 
```

2. Remove any mentions of `${<variable>}` in the code and replace with `identifier` clause with parameter markers.

```sql
-- Bad code example
Select * from ${base_schema}.table

-- Refactor above line to be as below
select * from wb_velocityanalytics_prd.loyalty.table
```
3. Ensure assertions must have alias CHECKSUM. For e.g. `SELECT ASSERT_TRUE(...) AS checksum`
4. Use table qualifier/alias when more than 1 tables are used in a query.
5. Refactor any `ORDER BY` and `GROUP BY` SQL clauses that uses numeric column positions to use explicit column names instead to enforce clarity.
```sql
# bad example
select col1,col2 from table order by 1,2

# good refactored code
select col1,col2 from table order by col1,col2
```

3. At the beginning of workbook - Configure session & Parameterise Catalogue name, Schema name, Delta days always.
```sql
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT delta_days DEFAULT '3'; 
```
- If the SQL queries are selecting from a source schema that isn't loyalty, create another widget text for that source schema to reference that widget in the code as a parameter marker (use identifier function to form relation names for tables, views, functions etc.)
- If `delta_days` value is used or called within the code, then update the default value. For example, if 'INTERVAL 5 DAYS' is mentioned in the code, then change the default value for delta_days and reference this widget within the code.
- Use parameter markers (by creating widgets first) where necessary when creating target tables/functions/views (not possible to use this in temporary views). Our target tables will always be `loyalty` schema unless otherwise specified.
- Below are usage examples when refactoring the code:
```sql
-- Bad example code
CREATE WIDGET TEXT delta_days DEFAULT '3'; 
CREATE WIDGET TEXT table_ref DEFAULT "[TODO]";
SET TIME ZONE 'Australia/Sydney';
create or replace table velocity_foundations.table as
select * from staging.stage_dim_customer
where activity_date >= current_date - interval '5' day;
```

The above should be refactored to:
```sql
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT stage_source_schema DEFAULT 'staging';
CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT delta_days DEFAULT '5'; 

create or replace table identifier(:catalogue_name || '.' || :target_schema || '.table_name') as
select * from identifier(:catalogue_name || '.' || :stage_source_schema || '.dim_customer')
where activity_date >= current_date - interval :delta_days day;
```

4. Update SQL references using parameter markers when selecting from tables, views, functions etc along with the IDENTIFIER clause to enable SQL injection safe parametrization of SQL statements. 
- If current code only references 2 level namespace, update table references to use 3 level namespace.
- Note: IDENTIFIER clause and parameter markers cannot be used inside temporary view queries, instead refer to 3 level namespaces directly `wb_velocityanalytics_prd.loyalty.<table>`.
- For temporary functions, and views - we do not need to explicitly mention the 3 level namespace and can leave as is.
- Example usage:
```sql
-- Bad code example:
-- Never ever refer to variables/widgets like ${var} since this is bad
-- Remove any code that creates variables like this ${base_schema} e.g. and use widgets as parameter markers.
CREATE OR REPLACE TABLE ${base_schema}.vel_activity_accrual_afm_link AS
select * from velocity_analytics_foundation.vel_catalogue_ref_snapshot
where col = "5";
```

- Below is a refactored code example
```sql
CREATE OR REPLACE TABLE IDENTIFIER(:catalogue_name || '.' || :target_schema|| '.vel_activity_accrual_afm_link') AS
select * from IDENTIFIER(:catalogue_name || '.' || :source_schema|| '.vel_catalogue_ref_snapshot')
where col = :delta_days ;
```

5. Remove unnecessary code:
- Any select queries that will return a result except for assertion checks. We only want queries that return no results such as CREATE TABLE or MERGE INTO statements. Any other select queries that produce results, including those used for eye checks or printing results in Databricks notebooks, should be removed.
- NOTE: Please ensure to remove any unnecessary blocks of commented-out code as per the coding conventions.                                                                           
- Remove any `OPTIMIZE` SQL statements.
- Remove any `ANALYSE` sql statements.
- Remove any `TABLE PARTITION BY` statements, we do not want table partitioning statements within our code.

- Below is an example bad code you will find when refactoring the notebooks
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

- Below is what refactored good code looks like based on above example:
```sql
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';
INSERT INTO IDENTIFIER(:catalogue_name || '.' || :target_schema || '.vel_classification_code_ref_snapshot')
(col1, col2, col3) select distinct col1, col2, col3 from 
IDENTIFIER(:catalogue_name || '.' || :source_schema || '.vel_classification_code_ref_snapshot')
```

4. Avoid SELECT * - specify required columns in SELECT statement.
5. Only cache tables if it is used > 2 times within the code notebook/script.
6. Push predicates early within the SQL query.

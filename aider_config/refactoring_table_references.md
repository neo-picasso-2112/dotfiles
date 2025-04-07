## Table Naming Conventions

### General Guide on Refactoring Existing Code Table References
The source catalog to select tables from will always be **wb_velocityanalytics_prd** which contains `loyalty` and `staging` schemas. Below is a general guide on how to update table references.


#### Case 1: Code that selects from staging tables
As you go an update the Databrick's notebooks, you will notice some tables names referenced has **staging_** prefix in the table name itself.
- When you update this table reference to use 3 level namespace, remove the `staging_` prefix from the table name.
- Next, Ensure you create a widget `source_staging_schema` with value `staging`.
- Lastly, refer to this widget within the code as a parameter marker or the values directly.

#### Case 3: Code that selects from velocity_analytics_foundation schema
If code is selecting from schema `velocity_analytics_foundation`, remove all mentions of this schema and use `loyalty` schema instead when selecting from table.
- The table name will remain the same when selecting from source catalogue and `loyalty` schema, so no changes to table names, only catalogue and schema should be changed when selecting from this table.

#### Case 2: Code that selects from `va_alms_prd` schema. 

Our existing code has lines where we select from `va_alms_prd.<table` schema. Remove all mentions of this schema `va_alms_prd` when refactoring the code. Instead:
- Update table reference to be `edp_prd.silver_alms.<table>` where `edp_prd` is another catalogue and `silver_alms` is a schema within that catalogue.
- No changes to table names, only update this table references to 3 level namespace where `edp_prd` is the catalogue, and `silver_alms` is the schema.


#### Usage Examples
- Bad code example
```sql
select * from va_alms_prd.partners_hist;
select * from velocity_foundations_analytics.staging_partners_hist.stage_table;
```

- Good refactored code:
```sql
CREATE WIDGET TEXT edp_catalogue_name DEFAULT 'edp_prd';
CREATE WIDGET TEXT edp_source_schema DEFAULT 'silver_alms';
CREATE WIDGET TEXT stage_source_schema DEFAULT 'staging';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';

select * from IDENTIFIER(:edp_catalogue_name || '.' || :edp_source_schema || '.partners_hist');
-- Or select * from edp_prd.silver_alms.partners_hist when referring to tables in temporary views.
select * from IDENTIFIER(:catalogue_name || '.' || :source_schema || '.table');
-- Note `stage_` prefix is removed from table name.
-- Or select * from wb_velocityanalytics_prd.staging.table when referring to tables in temporary views.
```

## Existing Code Table References

Most existing code will reference this schema table `velocity_analytics_foundation.<table>`, when you refactor the code: please be sure to remove all references of `velocity_analytics_foundation`.

For example:
- `SELECT * FROM velocity_analytics_foundation.example_table` should be changed to:
- `SELECT * FROM wb_velocityanalytics_prd.loyalty.example_table`.

Another example:
- `SELECT * FROM velocity_analytics_foundation.staging_example_table` should be changed to:
- `SELECT * FROM wb_velocityanalytics_prd.staging.example_table`: take note to remove `stage_` prefix from table name as you refactor table references and select from `staging` schema for these staging tables.
- Note: Tables with prefix `staging_` is always found within the `staging` schema within the catalogue `wb_velocityanalytics_prd`. Just remember to remove `staging_` prefix in the table name as you update the code.



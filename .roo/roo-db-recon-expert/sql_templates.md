# SQL Templates for Data Reconciliation

This file provides template SQL queries to be executed via `dbsqlcli` for common data reconciliation tasks. Replace placeholders like `{uc_catalog}`, `{uc_schema}`, `{uc_table}`, `{hive_catalog}`, `{hive_schema}`, and `{hive_table}` with actual values.

## 1. Row Count Comparison

### UC Table Row Count
```sql
SELECT COUNT(*) AS uc_row_count FROM {uc_catalog}.{uc_schema}.{uc_table};
```

### Hive Table Row Count
```sql
SELECT COUNT(*) AS hive_row_count FROM {hive_catalog}.{hive_schema}.{hive_table};
```

## 2. Schema Comparison

### Describe UC Table Schema
```sql
DESCRIBE TABLE EXTENDED {uc_catalog}.{uc_schema}.{uc_table};
```
*Review column names, data types, nullability, and comments.*

### Describe Hive Table Schema
```sql
DESCRIBE TABLE EXTENDED {hive_catalog}.{hive_schema}.{hive_table};
```
*Review column names, data types, nullability, and comments.*

*Note: Manual comparison of the output from these two `DESCRIBE` commands is often needed.*

## 3. Data Content Comparison (Full)

### Rows in UC Table but not in Hive Table
```sql
SELECT * FROM {uc_catalog}.{uc_schema}.{uc_table}
EXCEPT
SELECT * FROM {hive_catalog}.{hive_schema}.{hive_table};
```
*If this returns rows, it indicates data present in the new UC table that's missing from the Hive table.*

### Rows in Hive Table but not in UC Table
```sql
SELECT * FROM {hive_catalog}.{hive_schema}.{hive_table}
EXCEPT
SELECT * FROM {uc_catalog}.{uc_schema}.{uc_table};
```
*If this returns rows, it indicates data present in the old Hive table that's missing from the UC table.*

### Count of Mismatched Rows (Alternative to full EXCEPT)
To get just the count of differing rows, which can be faster for very large tables:

#### Count of Rows in UC not in Hive
```sql
SELECT COUNT(*) AS rows_in_uc_not_in_hive
FROM (
    SELECT * FROM {uc_catalog}.{uc_schema}.{uc_table}
    EXCEPT
    SELECT * FROM {hive_catalog}.{hive_schema}.{hive_table}
);
```

#### Count of Rows in Hive not in UC
```sql
SELECT COUNT(*) AS rows_in_hive_not_in_uc
FROM (
    SELECT * FROM {hive_catalog}.{hive_schema}.{hive_table}
    EXCEPT
    SELECT * FROM {uc_catalog}.{uc_schema}.{uc_table}
);
```

## 4. Data Content Comparison (Specific Columns)
If tables have many columns and only a few are expected to match, or if you want to compare specific keys:

### UC Table - Specific Columns
```sql
SELECT {column1}, {column2}, {column3} FROM {uc_catalog}.{uc_schema}.{uc_table}
EXCEPT
SELECT {column1}, {column2}, {column3} FROM {hive_catalog}.{hive_schema}.{hive_table};
```

## 5. Table History

### Describe History of a Table (UC or Hive)
```sql
DESCRIBE HISTORY {catalog_name}.{schema_name}.{table_name};
```
*This helps understand recent operations on the table (writes, updates, deletes, merges) and which jobs/users performed them. Useful for both target and source tables.*

## 6. Investigating Source Data
If a target table discrepancy is suspected to be due to source data issues:

### Compare a Source Table (UC vs. Hive version if applicable)
```sql
-- Row count for UC version of source
SELECT COUNT(*) FROM {uc_catalog}.{uc_source_schema}.{source_table};

-- Row count for Hive version of source
SELECT COUNT(*) FROM {hive_catalog}.{hive_source_schema}.{source_table};

-- Data diff for source tables
SELECT * FROM {uc_catalog}.{uc_source_schema}.{source_table}
EXCEPT
SELECT * FROM {hive_catalog}.{hive_source_schema}.{source_table};
```

## 7. Check for NULLs or Specific Values in a Column
```sql
-- Count NULLs in a specific column
SELECT COUNT(*) AS null_count
FROM {catalog_name}.{schema_name}.{table_name}
WHERE {column_name} IS NULL;

-- Count rows with a specific value in a column
SELECT COUNT(*) AS specific_value_count
FROM {catalog_name}.{schema_name}.{table_name}
WHERE {column_name} = 'some_value';
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Virgin Australia Velocity Analytics Engineering** repository focused on:
- **Unity Catalog migration** - Refactoring legacy Hive-based Databricks notebooks to Unity Catalog
- **Loyalty program analytics** for Virgin Australia's Velocity frequent flyer program
- **Data reconciliation and testing** to ensure data integrity during migrations
- **SQL-first architecture** with Python support for specific data processing tasks

## Technology Stack

- **Databricks** (primary data platform with Unity Catalog)
- **Spark SQL** (main query engine)
- **Python** (data processing, PGP encryption, testing)
- **Jupyter Notebooks** (*.ipynb files for interactive development)
- **pytest** (testing framework for data reconciliation)

## Common Commands

- **`dbsqlcli`** - CLI tool for querying Databricks SQL Warehouse (commonly used for debugging data mismatches)
- **`databricks`** - Databricks CLI for workspace, job, and Unity Catalog management
- **`pytest tests/`** - Run data reconciliation tests between legacy Hive and Unity Catalog tables
- **`pip install -r requirements.txt`** - Install Python dependencies

## Databricks CLI & dbsqlcli Usage

### Environment Configuration
- **Primary Catalog**: `wb_velocityanalytics_prd`
- **Key Schemas**: `loyalty`, `staging`, `reporting_loyalty`, `wb_velocityanalytics_portal`
- **Authentication**: Pre-configured via environment variables/profiles

### dbsqlcli Common Patterns
```bash
# Query Unity Catalog objects
dbsqlcli -e "SHOW VOLUMES IN wb_velocityanalytics_prd.wb_velocityanalytics_portal" --table-format ascii
dbsqlcli -e "SHOW TABLES IN wb_velocityanalytics_prd.loyalty" --table-format ascii
dbsqlcli -e "DESCRIBE VOLUME wb_velocityanalytics_prd.wb_velocityanalytics_portal.adobe_campaign_outbound" --table-format ascii

# Data validation and reconciliation
dbsqlcli -e "SELECT COUNT(*) FROM wb_velocityanalytics_prd.loyalty.vel_member" --table-format ascii
dbsqlcli -e "DESCRIBE TABLE wb_velocityanalytics_prd.loyalty.vel_activity" --table-format ascii

# Schema comparison (legacy vs Unity Catalog)
dbsqlcli -e "SELECT COUNT(*) FROM foreign_edp_prd_hive.velocity_analytics_foundation.table_name" --table-format ascii
```

### Databricks CLI Common Patterns
```bash
# Workspace management
databricks workspace list /analytical-data-model --output json
databricks workspace export /analytical-data-model/activity/vel_activity-build --format SOURCE
databricks workspace import /path/to/notebook.py /analytical-data-model/new-notebook --format AUTO

# Job management
databricks jobs list --output json
databricks jobs run-now --job-id 123
databricks jobs get-run --run-id 456 --output json

# Unity Catalog operations
databricks catalogs list
databricks schemas list wb_velocityanalytics_prd
databricks tables list wb_velocityanalytics_prd.loyalty
databricks volumes list wb_velocityanalytics_prd.wb_velocityanalytics_portal

# Cluster operations
databricks clusters list --output json
databricks clusters get --cluster-id abc-123-def --output json
```

### Available Databricks Volumes
Key volumes in `wb_velocityanalytics_prd.wb_velocityanalytics_portal`:
- `adobe_analytics_inbound` / `adobe_analytics_outbound`
- `adobe_campaign_inbound` / `adobe_campaign_outbound` 
- `tealium_inbound` / `tealium_outbound`
- `velocityanalytics_inbound` / `velocityanalytics_outbound`
- `virgin_money_inbound`
- `auditlog`
- `velocityanalytics_config`

Volume path pattern: `/Volumes/wb_velocityanalytics_prd/wb_velocityanalytics_portal/{volume_name}/{prefix}/`

### Troubleshooting Commands
```bash
# Check authentication status
databricks auth profiles
databricks current-user me

# Debug job failures
databricks jobs get-run --run-id <run-id> --output json
databricks clusters get --cluster-id <cluster-id> --output json

# Validate table access
dbsqlcli -e "SELECT 1 FROM wb_velocityanalytics_prd.loyalty.vel_member LIMIT 1"
```

## Key Directory Structure

- **`analytical-data-model/`** - Refactored Unity Catalog compatible notebooks
  - `activity/` - Activity and transaction data (vel_activity* tables)
  - `billing/` - Billing and financial data
  - `member/` - Member profiles and tiers
  - `reference/` - Reference/lookup tables
  - `staging/` - Staging tables for data ingestion
  - `view-definition/` - SQL views (many in .ipynb format)
  - `tealium_profile_data_extract/` - Customer profile exports with PGP encryption
  - `to_be_refactored/` - Legacy notebooks awaiting migration
- **`tests/`** - Data validation and testing framework

## File Naming Conventions

### SQL Files
- `*-build.sql` - Table creation/schema definition scripts
- `*-load.sql` - Data loading and transformation scripts
- `*-increment.sql` - Incremental data update scripts
- `*-build-and-load.sql` - Combined build and load operations

### Jupyter Notebooks
- `*-create-table.ipynb` - Table creation notebooks
- `*-autoloader.ipynb` - Data streaming/ingestion notebooks
- `*-create-view.ipynb` - View definition notebooks

### Table Naming
- `vel_*` - Velocity program related tables
- `rpt_*` - Reporting tables (target schema: `reporting_loyalty`)
- `staging_*` - Staging tables (target schema: `staging`)

## Critical Unity Catalog Refactoring Rules

### Required Session Configuration
Every refactored SQL file must start with:
```sql
SET TIME ZONE 'Australia/Brisbane';
CREATE WIDGET TEXT catalogue_name DEFAULT 'wb_velocityanalytics_prd';
CREATE WIDGET TEXT source_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT target_schema DEFAULT 'loyalty';
CREATE WIDGET TEXT delta_days DEFAULT '3';
```

### Schema Migration Patterns
| Legacy Pattern | Unity Catalog Pattern | Notes |
|---------------|----------------------|-------|
| `velocity_analytics_foundation.table` | `wb_velocityanalytics_prd.loyalty.table` | Standard tables |
| `velocity_analytics_foundation.staging_table` | `wb_velocityanalytics_prd.staging.table` | Remove `staging_` prefix |
| `va_alms_prd.table` | `edp_prd.silver_alms.table` | ALMS data source |
| `${variable}` syntax | `:parameter` with IDENTIFIER() | Parameter markers |

### Required Performance Optimizations
1. **ROW_NUMBER() refactoring** - Replace nested queries with `QUALIFY` clause
2. **TRUNCATE + INSERT** - Replace with single `MERGE` operations
3. **Remove** - `OPTIMIZE`, `ANALYZE`, `PARTITION BY` statements

### Parameter Marker Usage
- **Always use**: `IDENTIFIER(:catalogue_name || '.' || :schema || '.table')`
- **Never use**: `${variable}` syntax
- **Exception**: Inside temporary views, use explicit 3-level namespace

## Unity Catalog ANSI SQL Type Compatibility (CRITICAL)

### CASE Statement Type Consistency
Unity Catalog enforces strict type checking in CASE statements. All branches must return compatible types.

**ANTI-PATTERN (Causes DateTimeException):**
```sql
-- This FAILS with CAST_INVALID_INPUT error
CASE WHEN condition THEN 'NULL' ELSE date_column END  -- STRING vs DATE = FAIL
```

**CORRECT PATTERN:**
```sql
-- Use actual NULL values instead of string 'NULL'
CASE WHEN condition THEN NULL ELSE date_column END    -- NULL is type-agnostic
```

**Common Error:** `DateTimeException: CAST_INVALID_INPUT` when Unity Catalog attempts to cast string 'NULL' to DATE type.

**Root Cause:** Unity Catalog's ANSI SQL compliance requires type consistency. When materialized, it tries to find a common supertype and fails on invalid string-to-date conversions.

### Widget Access Patterns
**ALWAYS use getArgument() in temporary views** instead of legacy ${} syntax:

```sql
-- CORRECT: Modern approach
WHEN getArgument('extract_type') = 'base' THEN TRUE

-- LEGACY: Still works but not recommended  
WHEN '${extract_type}' = 'base' THEN TRUE
```

**IMPORTANT:** Parameter markers (:parameter) CANNOT be used in CREATE VIEW statements. Use explicit 3-level namespace or getArgument() instead.

### Table Reference Migration - Alias Verification
When changing table references, ALWAYS verify column aliases remain consistent:

**Example Issue:**
```sql
-- BEFORE
FROM velocity_analytics_foundation.staging_table_name
WHERE staging_table_name.column = value

-- AFTER (INCORRECT - broken alias)
FROM wb_velocityanalytics_prd.staging.table_name  -- removed staging_ prefix
WHERE staging_table_name.column = value           -- OLD alias still used!

-- AFTER (CORRECT)
FROM wb_velocityanalytics_prd.staging.table_name
WHERE table_name.column = value                   -- Updated alias
```

**Verification Steps:**
1. Change table reference
2. Search for ALL column references using old table name/alias
3. Update column references to match new alias

### NULL Handling Best Practices
**ALWAYS use actual NULL values** instead of string representations:

```sql
-- CORRECT: Semantic NULL
CASE WHEN is_purged THEN NULL ELSE actual_value END

-- INCORRECT: String representation (causes type issues)
CASE WHEN is_purged THEN 'NULL' ELSE actual_value END
```

**Exception:** Keep `ARRAY('NULL')` for JSON string building in external system extracts.

### Volume Path Function Patterns
When migrating S3 to Volumes, update function signatures consistently:

```python
# BEFORE: S3 pattern
def encrypt_and_write_s3_file(df, bucket_name: str, prefix: str, filename: str)

# AFTER: Volume pattern  
def encrypt_and_write_file_to_volume(df, volume_name: str, prefix: str, filename: str)
```

**Standard Volume Path Construction:**
```python
volumes_path = "/Volumes/wb_velocityanalytics_prd/wb_velocityanalytics_portal/"
full_path = f"{volumes_path}/{volume_name}/{prefix}/{filename}"
```

### Common Unity Catalog Pitfalls
1. **Mixed Type CASE Statements**: Use NULL instead of 'NULL' strings
2. **Parameter Markers in Views**: Use getArgument() or explicit namespace
3. **Alias Consistency**: Update ALL column references when changing table names
4. **Widget Access**: Prefer getArgument() over ${} syntax in views
5. **Volume Function Names**: Update helper function signatures for Volume patterns

## Data Architecture

### Source Systems
- **ALMS** → `edp_prd.silver_alms.*`
- **Legacy Hive** → `foreign_edp_prd_hive.velocity_analytics_foundation.*`
- **API Sources** → Staging tables in `wb_velocityanalytics_prd.staging.*`

### Target Schemas
- **`loyalty`** - Core loyalty program data
- **`staging`** - Data ingestion and temporary tables
- **`reporting_loyalty`** - Reporting and analytics tables

## Testing Framework

### Data Reconciliation Tests
- Located in `tests/test_data_reconciliation.py`
- Compares schema and data between legacy Hive and Unity Catalog tables
- Configured in `tests/asset_config.py` with table-specific exclusions
- Uses Databricks Connect for local development

### Running Tests
```bash
pytest tests/test_data_reconciliation.py -v
```

## Databricks Volumes Migration

When refactoring file operations from `dbfs://` to Databricks Volumes:
1. Identify legacy S3 paths and `dbutils.fs.cp` operations
2. Query available volumes with: `dbsqlcli -e "SHOW VOLUMES IN <catalog.schema>"`
3. Replace with Volume paths: `/Volumes/catalog/schema/volume_name/prefix/filename`
4. Remove `dbutils.fs.cp` operations

## Development Workflow

### Git Commit Standards
**ALWAYS use Conventional Commits specification** for all commits in this repository.

**Format**: `<type>[optional scope]: <description>`

**Required Types**:
- `feat:` - New features or functionality
- `fix:` - Bug fixes
- `refactor:` - Code restructuring without functionality changes
- `docs:` - Documentation updates
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks (dependencies, build config)
- `perf:` - Performance improvements
- `style:` - Code formatting changes

**Examples**:
```bash
feat(member-profile): add PGP encryption for customer data exports
fix(unity-catalog): resolve IDENTIFIER() parameter marker syntax
refactor(vel-activity): migrate table references to Unity Catalog format
docs(readme): update development workflow section
test(reconciliation): add data validation tests for vel_member table
```

**Best Practices**:
- Use descriptive scopes (table names, component names)
- Keep descriptions concise but clear
- Use present tense ("add" not "added")
- Reference ticket numbers in commit body when applicable
- Make atomic commits (one logical change per commit)

**Reference**: https://www.conventionalcommits.org/

### Current Migration Focus
- Migrating Tealium profile extraction jobs to Workbench
- Converting `dbfs://` file operations to Databricks Volumes
- Ensuring PGP encryption for customer data exports

### Code Quality Requirements
- Follow Unity Catalog compatibility patterns
- Maintain data reconciliation test coverage
- Use consistent parameter marker syntax
- Remove all legacy optimization statements
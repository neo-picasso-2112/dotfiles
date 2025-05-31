# Common Databricks CLI Commands

This document lists commonly used Databricks CLI commands and their correct syntax for frequent operations within the "Databricks Refactoring Expert" mode.

## File System Operations

### Listing Files in Unity Catalog Volumes

When listing files or directories within a Unity Catalog Volume using `databricks fs ls`, always prefix the Volume path with `dbfs:`.

**Correct Syntax:**
```bash
databricks fs ls dbfs:/Volumes/<catalog_name>/<schema_name>/<volume_name>/<path_within_volume> --profile default
```

**Example:**
```bash
databricks fs ls dbfs:/Volumes/wb_velocityanalytics_prd/wb_velocityanalytics_portal/adobe_campaign_outbound/velocity-analytics/ACM/model-purge/ --profile default
```

**Incorrect Syntax (will likely result in "no such directory"):**
```bash
databricks fs ls /Volumes/<catalog_name>/<schema_name>/<volume_name>/<path_within_volume> --profile default
## Job Operations

### Listing Jobs
To list all jobs in the workspace:
```bash
databricks jobs list --profile default --output JSON
```

To filter the job list (e.g., for jobs containing "my_job_name" or "another_name"):
```bash
databricks jobs list --profile default --output JSON | grep -E '"(my_job_name|another_name)"'
```

## Workspace Operations

### Creating Directories
To create directories in the Databricks workspace (necessary before importing files if parent folders don't exist):
```bash
databricks workspace mkdirs "/Users/<your_user@example.com>/<path_to_directory>" --profile default
```
**Example:**
```bash
databricks workspace mkdirs "/Users/william.nguyen@virginaustralia.com/local-sync/model-score" --profile default
```

### Importing Files (Notebooks)
To import a local file (e.g., a notebook) into the Databricks workspace, overwriting if it exists:
```bash
databricks workspace import "/Users/<your_user@example.com>/<path_to_notebook_in_workspace>" --file "<local_path_to_notebook>" --language <LANGUAGE> --format <FORMAT> --overwrite --profile default
```
**Parameters:**
*   `<LANGUAGE>`: e.g., `PYTHON`, `SQL`, `SCALA`, `R`
*   `<FORMAT>`: e.g., `SOURCE` (for .py, .sql files), `AUTO`, `DBC`, `HTML`, `JUPYTER`

**Example (Python notebook):**
```bash
databricks workspace import "/Users/william.nguyen@virginaustralia.com/local-sync/model-score/extract_model_purge.py" --file "model-score/extract_model_purge.py" --language PYTHON --format SOURCE --overwrite --profile default
```

### Verifying Imported/Uploaded Files
After importing a file, or if a notebook creates files in a workspace directory (not a Volume), you can list the contents of the workspace directory to verify:
```bash
databricks workspace ls "/Users/<your_user@example.com>/<path_to_directory>" --profile default
```
**Example:**
```bash
databricks workspace ls "/Users/william.nguyen@virginaustralia.com/local-sync/model-score/" --profile default
```
Note: For files in Unity Catalog Volumes, use the `databricks fs ls dbfs:/Volumes/...` command documented under "File System Operations".
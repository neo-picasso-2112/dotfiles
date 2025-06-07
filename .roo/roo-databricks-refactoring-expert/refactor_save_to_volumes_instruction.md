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
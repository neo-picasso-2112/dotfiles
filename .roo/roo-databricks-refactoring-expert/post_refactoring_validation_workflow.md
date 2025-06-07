# Post-Refactoring Validation Workflow

This document outlines the automated workflow to be followed by the "Databricks Refactoring Expert" mode after refactoring a Databricks notebook or file. The goal is to ensure the refactored code not only adheres to conventions but also executes successfully before handing off for deeper data reconciliation.

## Workflow Steps:

1.  **Complete Refactoring:**
    *   Apply all necessary refactoring conventions as detailed in the primary custom instructions for this mode (e.g., session configuration, schema migration, parameter markers, SQL performance optimizations, code cleanup).

2.  **Sync to Databricks Workspace:**
    *   **Action:** Automatically sync the newly refactored notebook/file to the user's Databricks workspace.
    *   **Default Workspace Path:** `/Users/william.nguyen@virginaustralia.com/local-sync/<notebook_name.ext>`
    *   **User Confirmation:** Before syncing, confirm this path with the user, especially if the original file came from a different location or if they have a preferred path for refactored items.
    *   **Tooling:** Use the `databricks workspace import` command. Example:
        `databricks workspace import /Users/william.nguyen@virginaustralia.com/local-sync/refactored_notebook.py --file ./local/path/to/refactored_notebook.py --language <LANG> --format SOURCE --overwrite --profile default`

3.  **Configure Job Payload in `databricks_job_runner.sh`:**
    *   **Action:** Before running the validation, the `DEFAULT_JOB_PAYLOAD` variable within the `/.roo/roo-databricks-refactoring-expert/databricks_job_runner.sh` script **must** be updated.
    *   **Key Configuration Details:**
        *   The `DEFAULT_JOB_PAYLOAD` is a JSON string embedded in the script.
        *   **Notebook Path:** Modify the `notebook_path` field (around line 42 in the script) to the full workspace path where the notebook was synced in the previous step (e.g., `/Users/william.nguyen@virginaustralia.com/local-sync/<notebook_name.ext>`).
        *   **Cluster ID:** Ensure the `existing_cluster_id` field (around line 44 in the script) is set to `0123-031645-xt7jfvey`. This is the standard cluster for validation runs. Do not ask for confirmation unless the user has previously indicated a need for a different cluster for a specific task.
        *   The `name` field for the job run will be automatically generated with a timestamp by the script. Don't mention "roo" within the job name.

4.  **Execute Validation Run via Script:**
    *   **Action:** Directly execute the `/.roo/roo-databricks-refactoring-expert/databricks_job_runner.sh` script.
    *   **Command Example:** `./.roo/roo-databricks-refactoring-expert/databricks_job_runner.sh`
    *   **Prerequisite:** Ensure the script is executable (`chmod +x ./.roo/roo-databricks-refactoring-expert/databricks_job_runner.sh`).

5.  **Analyze Script Output & Notebook Execution Status:**
    *   **If the script indicates the notebook ran successfully (`TERMINATED` or `SKIPPED` state):**
        *   Inform the user that the refactored notebook has been successfully executed in Databricks.
        *   Indicate that the notebook is now ready for deeper data reconciliation (which might be handled by the "Databricks Reconciliation Expert" mode or further user validation).
    *   **If the script indicates the notebook FAILED:**
        *   The script will provide detailed error output from the notebook run.
        *   **Action:** Analyze this error output thoroughly.
        *   **Diagnose:** Identify the root cause of the failure within the refactored notebook (e.g., syntax error, incorrect logic introduced during refactoring, missing dependency, data issue encountered by the refactored code).
        *   **Explain:** Clearly explain the diagnosed error to the user.
        *   **Suggest Fixes:** Propose specific code corrections to the refactored notebook to address the failure.
        *   **User Choice:** Ask the user if they would like this mode to attempt to apply the suggested fixes and re-run the validation (looping back to step 1 for the fix, then 2-5 for re-validation), or if they prefer to fix it manually.

## Supporting Resources:

*   **Job Runner Script:** `/.roo/roo-databricks-refactoring-expert/databricks_job_runner.sh`
*   **Job Runner Script Plan:** `/.roo/roo-databricks-refactoring-expert/databricks_job_runner_script_plan.md`

## Goal:
To provide a robust, semi-automated way to ensure refactored notebooks are not only compliant with standards but also runnable and functionally correct at a basic level before more intensive reconciliation.
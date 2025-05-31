# Bash Script Plan for Databricks One-Time Job Runner

This document outlines the plan for a bash script designed to automate the submission, monitoring, and result retrieval for one-time Databricks jobs.

## 1. Objective of the Bash Script

The script will automate the following:
1.  Accept a Databricks job definition as a JSON payload via standard input.
2.  Submit this payload as a one-time job to Databricks using the `databricks jobs submit` command with the `--no-wait` flag.
3.  Capture the `run_id` from the submission command's output.
4.  Periodically poll the status of the job run using this `run_id`.
5.  Continue polling until the job run reaches a terminal state (`TERMINATED`, `FAILED`, or `SKIPPED`).
6.  If the job run `FAILED`, the script will then automatically fetch and display the detailed run output.
7.  Provide a clear overall success or failure message based on the job's outcome.

## 2. Key Components & Considerations

*   **Databricks CLI Commands Used:**
    *   `databricks jobs submit --json <payload_or_@file> --no-wait --output JSON`: To submit the job and get JSON output.
    *   `databricks jobs get-run --run-id <run_id> --output JSON`: To poll the run status.
    *   `databricks jobs get-run-output --run-id <run_id>`: To retrieve detailed logs on failure.
*   **JSON Parsing:** The script will use the `jq` command-line utility to parse JSON output from the Databricks CLI (e.g., to extract `run_id` and `life_cycle_state`).
*   **Polling Logic:**
    *   A loop that calls `databricks jobs get-run`.
    *   A configurable sleep interval between polls.
    *   A configurable maximum number of polling attempts or a total timeout.
*   **Error Handling:** The script will include checks for:
    *   `jq` installation.
    *   Empty JSON input.
    *   Failures in the initial job submission.
    *   Inability to extract `run_id`.
    *   Polling timeouts.
*   **Input Method:** The script will read the JSON job payload from standard input. It will attempt to pass this directly to the CLI. If the CLI requires a file for the `--json` flag, the script will transparently create, use, and then delete a temporary file.

## 3. User-Defined Parameters & Defaults

*   **`jq` Availability:** Assumed to be installed (script will check).
*   **Polling Interval:** 20 seconds.
*   **Polling Timeout:** 20 minutes (which is 60 polling attempts at a 20-second interval).

## 4. Visual Flow (Mermaid Diagram)

```mermaid
graph TD
    A[Start Script] --> A1[Read JSON from stdin into variable JSON_PAYLOAD];
    A1 --> B{JSON_PAYLOAD is not empty?};
    B -- Yes --> C{jq Installed?};
    B -- No --> X1[Exit: No JSON provided via stdin or read error];
    C -- Yes --> D[Attempt: databricks jobs submit --json "\$JSON_PAYLOAD" --no-wait --output JSON];
    C -- No --> X2[Exit: jq Not Installed];
    D --> D1{Submission with inline JSON OK?};
    D1 -- No --> D2[Create Temp File with JSON_PAYLOAD];
    D2 --> D3[Submit Job: databricks jobs submit --json @temp_file --no-wait --output JSON];
    D3 --> D4[Delete Temp File];
    D4 --> E;
    D1 -- Yes --> E;
    E{Submission Successful (captured output)?};
    E -- Yes --> F[Extract run_id from submission output using jq];
    E -- No --> X3[Exit: Job Submission Failed];
    F --> G{run_id Extracted?};
    G -- Yes --> H[Initialize Polling Loop (20s interval, 20min timeout / 60 attempts)];
    G -- No --> X6[Exit: Could not extract run_id];
    H --> I{Polling Attempts < 60 AND Elapsed Time < 20min?};
    I -- Yes --> J[Get Run Status: databricks jobs get-run --run-id \$run_id --output JSON];
    I -- No --> X4[Exit: Polling Timeout or Max Attempts Reached];
    J --> K[Extract life_cycle_state from status output using jq];
    K --> L{life_cycle_state is TERMINATED, FAILED, or SKIPPED?};
    L -- No --> M[Sleep for 20 Seconds];
    M --> H;
    L -- Yes --> N{life_cycle_state is FAILED?};
    N -- Yes --> O[Fetch Run Output: databricks jobs get-run-output --run-id \$run_id];
    O --> P[Display Run Output & Failure Message];
    N -- No --> Q[Display Success/Skipped Message (life_cycle_state)];
    P --> Z[End Script];
    Q --> Z[End Script];
    X1 --> Z;
    X2 --> Z;
    X3 --> Z;
    X4 --> Z;
    X6 --> Z;
```

## 5. Notes

*   The script will prioritize passing JSON directly. The temporary file mechanism is a fallback if the Databricks CLI's `--json` flag strictly requires a file path even for content that could be inline.
*   The script should be made executable (`chmod +x script_name.sh`).
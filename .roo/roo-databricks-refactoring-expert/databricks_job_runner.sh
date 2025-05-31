#!/bin/bash

# Script to submit a one-time Databricks job, monitor it, and retrieve logs on failure.
# Reads JSON job payload from stdin.

# --- Configuration ---
POLLING_INTERVAL_SECONDS=20
MAX_POLLING_ATTEMPTS=60 # (20 minutes / 20 seconds = 60 attempts)
INITIAL_POLL_DELAY_SECONDS=5
interrupted=0 # Flag to indicate if Ctrl+C was pressed

# --- Databricks URL Configuration ---
# IMPORTANT: Update these with your Databricks host and workspace ID
DATABRICKS_HOST="va-edp-wbprd.cloud.databricks.com"
DATABRICKS_WORKSPACE_ID="3449363190214202" # The 'o=' parameter in the URL

# --- Color Definitions ---
RESET='\033[0m'
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'

# --- Default Job Payload ---
# Define your Databricks job payload as a JSON string here.
# This will be used to submit the job.
# Example:
# DEFAULT_JOB_PAYLOAD='{
#   "name": "My Scripted Job",
#   "tasks": [
#     {
#       "task_key": "notebook_task_1",
#       "notebook_task": {
#         "notebook_path": "/Users/your_user@example.com/YourNotebookName"
#       },
#       "existing_cluster_id": "your_cluster_id_here"
#     }
#   ],
#   "timeout_seconds": 3600
# }'
DEFAULT_JOB_PAYLOAD='{
  "run_name": "Validation Run - extract_model_score.py - '"$(date +'%Y%m%d-%H%M%S')"'",
  "tasks": [
    {
      "task_key": "validation_task_extract_model_score",
      "notebook_task": {
        "notebook_path": "/Users/william.nguyen@virginaustralia.com/local-sync/model-score/extract_model_score.py"
      },
      "existing_cluster_id": "0123-031645-xt7jfvey"
    }
  ],
  "timeout_seconds": 3600
}'


# --- Helper Functions ---
log_info() { # For successful operations or positive outcomes
    echo -e "${GREEN}[INFO] $(date +'%Y-%m-%d %H:%M:%S') - $1${RESET}"
}

log_error() { # For errors or failures
    echo -e "${RED}${BOLD}[ERROR] $(date +'%Y-%m-%d %H:%M:%S') - $1${RESET}" >&2
}

log_warning() { # For potential issues or non-critical problems
    echo -e "${YELLOW}[WARN] $(date +'%Y-%m-%d %H:%M:%S') - $1${RESET}"
}

log_status() { # For general script progress messages, polling, etc.
    echo -e "${CYAN}[STATUS] $(date +'%Y-%m-%d %H:%M:%S') - $1${RESET}"
}

cleanup_temp_file() {
    if [[ -n "$TEMP_JSON_FILE" && -f "$TEMP_JSON_FILE" ]]; then
        log_status "Cleaning up temporary file: $TEMP_JSON_FILE"
        rm -f "$TEMP_JSON_FILE"
    fi
}

handle_sigint() {
    log_warning "SIGINT (Ctrl+C) received. Setting interrupt flag. Script will attempt to exit gracefully."
    interrupted=1
}

# Ensure cleanup on exit and handle SIGINT
trap cleanup_temp_file EXIT SIGTERM
trap handle_sigint SIGINT

# --- Pre-flight Checks ---
log_status "Checking for dependencies..."
if ! command -v jq &> /dev/null; then
    log_error "jq is not installed. Please install jq to use this script."
    exit 1
fi
log_info "jq found."

if ! command -v databricks &> /dev/null; then
    log_error "Databricks CLI is not installed or not in PATH. Please install and configure it."
    exit 1
fi
log_info "Databricks CLI found."

# --- Load JSON Payload ---
JSON_PAYLOAD="$DEFAULT_JOB_PAYLOAD"
log_status "Using default JSON payload defined in script."

if [[ -z "$JSON_PAYLOAD" ]]; then
    log_error "DEFAULT_JOB_PAYLOAD is empty. Please define it in the script."
    exit 1
fi

# Validate JSON (optional but good practice)
if ! echo "$JSON_PAYLOAD" | jq -e . > /dev/null; then
    log_error "DEFAULT_JOB_PAYLOAD is not valid JSON. Please check the syntax."
    exit 1
fi
log_status "JSON payload loaded and validated."

# --- Submit Job ---
RUN_ID=""
TEMP_JSON_FILE=""

log_status "Attempting to submit job..."

TEMP_JSON_FILE=$(mktemp "/tmp/databricks_job_payload.XXXXXX.json")
if [[ $? -ne 0 ]]; then
    log_error "Failed to create temporary file for JSON payload."
    exit 1
fi
echo "$JSON_PAYLOAD" > "$TEMP_JSON_FILE"
log_status "JSON payload written to temporary file: $TEMP_JSON_FILE"

SUBMIT_OUTPUT=$(databricks --profile default jobs submit --json "@$TEMP_JSON_FILE" --no-wait --output JSON 2>&1)
SUBMIT_EXIT_CODE=$?

if [[ $SUBMIT_EXIT_CODE -ne 0 ]]; then
    log_error "Failed to submit Databricks job. CLI Error:"
    log_error "$SUBMIT_OUTPUT"
    exit 1
fi

RUN_ID=$(echo "$SUBMIT_OUTPUT" | jq -r '.run_id // empty')

if [[ -z "$RUN_ID" ]]; then
    log_error "Failed to extract run_id from submission output. Output was:"
    log_error "$SUBMIT_OUTPUT"
    exit 1
fi
log_info "Job submitted successfully. Run ID: $RUN_ID"

cleanup_temp_file
TEMP_JSON_FILE=""

# --- Poll Job Status ---
log_status "Waiting $INITIAL_POLL_DELAY_SECONDS seconds before initial poll..."
sleep "$INITIAL_POLL_DELAY_SECONDS"

log_status "Polling job status for Run ID: $RUN_ID (Interval: ${POLLING_INTERVAL_SECONDS}s, Max Attempts: ${MAX_POLLING_ATTEMPTS})"
CURRENT_ATTEMPT=0
LIFE_CYCLE_STATE=""
STATE_MESSAGE=""
# GET_RUN_OUTPUT will store the JSON from `databricks jobs get-run` for later log parsing
GET_RUN_OUTPUT=""
JOB_ID="" # To store the job_id for the URL
JOB_URL_LOGGED=0 # Flag to ensure URL is logged only once

while [[ $CURRENT_ATTEMPT -lt $MAX_POLLING_ATTEMPTS && $interrupted -eq 0 ]]; do
    ((CURRENT_ATTEMPT++))
    
    GET_RUN_OUTPUT=$(databricks --profile default jobs get-run "$RUN_ID" --output JSON 2>&1)
    GET_RUN_EXIT_CODE=$?

    if [[ $interrupted -ne 0 ]]; then
        log_warning "Interrupt detected during 'get-run' call. Breaking poll loop."
        break
    fi

    if [[ $GET_RUN_EXIT_CODE -ne 0 ]]; then
        log_error "Failed to get run status for Run ID: $RUN_ID. Attempt $CURRENT_ATTEMPT/$MAX_POLLING_ATTEMPTS. CLI Error:"
        log_error "$GET_RUN_OUTPUT"
    else
        LIFE_CYCLE_STATE=$(echo "$GET_RUN_OUTPUT" | jq -r '.state.life_cycle_state // empty')
        STATE_MESSAGE=$(echo "$GET_RUN_OUTPUT" | jq -r '.state.state_message // "No state message."')
        
        if [[ -z "$JOB_ID" ]]; then # Try to get job_id if not already fetched
            JOB_ID=$(echo "$GET_RUN_OUTPUT" | jq -r '.job_id // empty')
        fi

        if [[ -n "$JOB_ID" && "$JOB_URL_LOGGED" -eq 0 && -n "$DATABRICKS_HOST" && -n "$DATABRICKS_WORKSPACE_ID" ]]; then
            JOB_RUN_URL="https://${DATABRICKS_HOST}/jobs/${JOB_ID}/runs/${RUN_ID}?o=${DATABRICKS_WORKSPACE_ID}"
            log_info "Databricks Job Run URL: ${BOLD}${BLUE}${JOB_RUN_URL}${RESET}"
log_status "Attempting to open job run URL in browser..."
            # Attempt to open the URL in the default browser
            # Use 'open' for macOS, 'xdg-open' for Linux, and provide a fallback message
            if command -v open &> /dev/null && [[ "$(uname)" == "Darwin" ]]; then
                open "${JOB_RUN_URL}" || log_warning "Failed to automatically open URL with 'open'. Please open it manually: ${JOB_RUN_URL}"
            elif command -v xdg-open &> /dev/null && [[ "$(uname)" == "Linux" ]]; then
                xdg-open "${JOB_RUN_URL}" || log_warning "Failed to automatically open URL with 'xdg-open'. Please open it manually: ${JOB_RUN_URL}"
            else
                log_warning "Could not find a command to automatically open the URL ('open' for macOS, 'xdg-open' for Linux). Please open it manually: ${JOB_RUN_URL}"
            fi
            JOB_URL_LOGGED=1
        fi

        log_status "Poll $CURRENT_ATTEMPT/$MAX_POLLING_ATTEMPTS: Run ID $RUN_ID - LifeCycleState: $LIFE_CYCLE_STATE"

        if [[ "$LIFE_CYCLE_STATE" == "TERMINATED" || "$LIFE_CYCLE_STATE" == "FAILED" || "$LIFE_CYCLE_STATE" == "SKIPPED" || "$LIFE_CYCLE_STATE" == "INTERNAL_ERROR" ]]; then
            break
        fi
    fi
    
    log_status "Sleeping for $POLLING_INTERVAL_SECONDS seconds..."
    sleep "$POLLING_INTERVAL_SECONDS"
    if [[ $interrupted -ne 0 ]]; then
        log_warning "Interrupt detected after sleep. Breaking poll loop."
        break
    fi
done

# --- Process Final Status ---
if [[ $interrupted -ne 0 ]]; then
    log_error "Script was interrupted by user (Ctrl+C)."
    exit 130
fi

if [[ "$LIFE_CYCLE_STATE" == "TERMINATED" ]]; then
    log_info "Job run $RUN_ID completed successfully (TERMINATED)."
    log_info "State Message: $STATE_MESSAGE"
    log_status "Fetching detailed run output for tasks in successful Run ID: $RUN_ID..."

    NUM_TASKS=$(echo "$GET_RUN_OUTPUT" | jq '.tasks | length')

    if [[ -z "$GET_RUN_OUTPUT" || "$GET_RUN_OUTPUT" == "null" || -z "$NUM_TASKS" || "$NUM_TASKS" -eq 0 ]]; then
        log_warning "No tasks found or GET_RUN_OUTPUT is empty for Run ID $RUN_ID. Cannot fetch individual task logs for successful run."
    else
        log_status "Found $NUM_TASKS task(s). Fetching output for each..."
        echo "$GET_RUN_OUTPUT" | jq -c '.tasks[]' | while IFS= read -r task_json; do
            TASK_KEY=$(echo "$task_json" | jq -r '.task_key')
            TASK_RUN_ID=$(echo "$task_json" | jq -r '.run_id')
            TASK_LIFE_CYCLE_STATE=$(echo "$task_json" | jq -r '.state.life_cycle_state') # Should be TERMINATED

            log_status "Fetching output for Task Key: '${BOLD}${TASK_KEY}${RESET}' (Task Run ID: ${BOLD}$TASK_RUN_ID${RESET}, State: $TASK_LIFE_CYCLE_STATE)..."
            
            if [[ -n "$TASK_RUN_ID" && "$TASK_RUN_ID" != "null" ]]; then
                TASK_RUN_OUTPUT_RAW=$(databricks --profile default jobs get-run-output "$TASK_RUN_ID" 2>&1)
                GET_TASK_OUTPUT_EXIT_CODE=$?
                
                echo -e "${BLUE}${BOLD}---------- TASK OUTPUT (SUCCESS): '$TASK_KEY' (Run ID: $TASK_RUN_ID) ----------${RESET}"
                if [[ $GET_TASK_OUTPUT_EXIT_CODE -ne 0 ]]; then
                    log_error "Failed to fetch output for successful task '$TASK_KEY' (Run ID: $TASK_RUN_ID). CLI Error:"
                    # Attempt to print as JSON if it is, otherwise raw
                    if echo "$TASK_RUN_OUTPUT_RAW" | jq -e . > /dev/null 2>&1; then
                        echo "$TASK_RUN_OUTPUT_RAW" | jq .
                    else
                        echo -e "${RED}$TASK_RUN_OUTPUT_RAW${RESET}"
                    fi
                else
                    # Attempt to parse as JSON
                    if echo "$TASK_RUN_OUTPUT_RAW" | jq -e . > /dev/null 2>&1; then
                        TASK_RUN_OUTPUT_JSON="$TASK_RUN_OUTPUT_RAW"
                        NOTEBOOK_RESULT=$(echo "$TASK_RUN_OUTPUT_JSON" | jq -r '.notebook_output.result // empty')
                        LOGS_OUTPUT=$(echo "$TASK_RUN_OUTPUT_JSON" | jq -r '.logs // empty')

                        if [[ -n "$NOTEBOOK_RESULT" ]]; then
                            log_info "Notebook Result for task '$TASK_KEY':"
                            echo "$NOTEBOOK_RESULT"
                        fi
                        if [[ -n "$LOGS_OUTPUT" && "$LOGS_OUTPUT" != "null" ]]; then
                            log_status "Logs for task '$TASK_KEY' (may be base64 encoded):"
                            if echo "$LOGS_OUTPUT" | base64 --decode > /dev/null 2>&1; then
                                echo "$LOGS_OUTPUT" | base64 --decode
                            else
                                echo "$LOGS_OUTPUT"
                            fi
                        fi
                        if [[ -z "$NOTEBOOK_RESULT" && (-z "$LOGS_OUTPUT" || "$LOGS_OUTPUT" == "null") ]]; then
                            # Attempt to parse specific metadata fields for a cleaner success message
                            TASK_RESULT_STATE=$(echo "$TASK_RUN_OUTPUT_JSON" | jq -r '.metadata.state.result_state // "UNKNOWN"')
                            TASK_EXEC_DURATION_MS=$(echo "$TASK_RUN_OUTPUT_JSON" | jq -r '.metadata.execution_duration // "N/A"')
                            TASK_RUN_PAGE_URL=$(echo "$TASK_RUN_OUTPUT_JSON" | jq -r '.metadata.run_page_url // empty')

                            log_info "Task '$TASK_KEY' (Run ID: $TASK_RUN_ID) completed."
                            log_info "  Result State: ${BOLD}${GREEN}$TASK_RESULT_STATE${RESET}"
                            if [[ "$TASK_EXEC_DURATION_MS" != "N/A" && "$TASK_EXEC_DURATION_MS" =~ ^[0-9]+$ ]]; then
                                log_info "  Execution Duration: $(($TASK_EXEC_DURATION_MS / 1000))s"
                            elif [[ "$TASK_EXEC_DURATION_MS" != "N/A" ]]; then # Corrected typo: TASK_EXEC_DURATIONS_MS -> TASK_EXEC_DURATION_MS
                                log_info "  Execution Duration: $TASK_EXEC_DURATION_MS"
                            fi
                            if [[ -n "$TASK_RUN_PAGE_URL" ]]; then
                                log_info "  Task Run Page URL: ${BOLD}${BLUE}${TASK_RUN_PAGE_URL}${RESET}"
                            fi
                            log_info "  NOTE: The direct API response for 'get-run-output' did not contain 'notebook_output.result' or 'logs'."
                            log_info "  For detailed cell-by-cell output (e.g., print statements), please use the Databricks UI via the run URL(s) provided."
                        fi
                    else
                        # Output was not JSON, print raw
                        log_status "Raw output for successful task '$TASK_KEY':"
                        echo "$TASK_RUN_OUTPUT_RAW"
                    fi
                fi
                echo -e "${BLUE}${BOLD}--------------------------------------------------------------------------${RESET}"
            else
                log_warning "Skipping output fetch for task '$TASK_KEY'; its Task Run ID is missing or null."
            fi
        done
    fi
    exit 0
elif [[ "$LIFE_CYCLE_STATE" == "SKIPPED" ]]; then
    log_warning "Job run $RUN_ID was SKIPPED."
    log_warning "State Message: $STATE_MESSAGE"
    exit 0
elif [[ "$LIFE_CYCLE_STATE" == "FAILED" || "$LIFE_CYCLE_STATE" == "INTERNAL_ERROR" ]]; then
    if [[ "$LIFE_CYCLE_STATE" == "FAILED" ]]; then
        log_error "Job run $RUN_ID FAILED."
    else
        log_error "Job run $RUN_ID resulted in INTERNAL_ERROR."
    fi
    log_error "State Message: $STATE_MESSAGE"
    log_status "Fetching detailed run output for tasks in Run ID: $RUN_ID..."

    NUM_TASKS=$(echo "$GET_RUN_OUTPUT" | jq '.tasks | length')

    if [[ -z "$GET_RUN_OUTPUT" || "$GET_RUN_OUTPUT" == "null" || -z "$NUM_TASKS" || "$NUM_TASKS" -eq 0 ]]; then
        log_warning "No tasks found or GET_RUN_OUTPUT is empty for Run ID $RUN_ID. Cannot fetch individual task logs."
        log_warning "This might happen if the job submission failed very early or the job definition was invalid."
    else
        log_status "Found $NUM_TASKS task(s). Fetching output for each..."
        echo "$GET_RUN_OUTPUT" | jq -c '.tasks[]' | while IFS= read -r task_json; do
            TASK_KEY=$(echo "$task_json" | jq -r '.task_key')
            TASK_RUN_ID=$(echo "$task_json" | jq -r '.run_id')
            TASK_LIFE_CYCLE_STATE=$(echo "$task_json" | jq -r '.state.life_cycle_state')

            log_status "Fetching output for Task Key: '${BOLD}${TASK_KEY}${RESET}' (Task Run ID: ${BOLD}$TASK_RUN_ID${RESET}, State: $TASK_LIFE_CYCLE_STATE)..."
            
            if [[ -n "$TASK_RUN_ID" && "$TASK_RUN_ID" != "null" ]]; then
                # Use `databricks jobs get-run-output` for individual task runs
                TASK_RUN_OUTPUT_JSON=$(databricks --profile default jobs get-run-output "$TASK_RUN_ID" 2>&1) # Attempt to get raw output first
                GET_TASK_OUTPUT_EXIT_CODE=$?
                # Try to parse as JSON, but be robust if it's not
                if ! echo "$TASK_RUN_OUTPUT_JSON" | jq -e . > /dev/null 2>&1 && [[ $GET_TASK_OUTPUT_EXIT_CODE -eq 0 ]]; then
                    # If not JSON and successful, wrap it to look like the expected JSON structure for logs
                    # This is a heuristic; actual non-JSON output might need different handling
                    LOGS_CONTENT_ESCAPED=$(echo "$TASK_RUN_OUTPUT_JSON" | jq -s -R .)
                    TASK_RUN_OUTPUT_JSON="{\"logs\": $LOGS_CONTENT_ESCAPED}"
                elif [[ $GET_TASK_OUTPUT_EXIT_CODE -ne 0 ]]; then
                     # If CLI errored, ensure TASK_RUN_OUTPUT_JSON contains the error message for display
                     : # TASK_RUN_OUTPUT_JSON already holds the error output from the CLI
                fi
                
                echo -e "${MAGENTA}${BOLD}---------- TASK OUTPUT: '$TASK_KEY' (Run ID: $TASK_RUN_ID) ----------${RESET}"
                if [[ $GET_TASK_OUTPUT_EXIT_CODE -ne 0 ]]; then
                    log_error "Failed to fetch output for task '$TASK_KEY' (Run ID: $TASK_RUN_ID). CLI Error:"
                    if echo "$TASK_RUN_OUTPUT_JSON" | jq -e . > /dev/null 2>&1; then
                        echo "$TASK_RUN_OUTPUT_JSON" | jq . # Pretty print if JSON error
                    else
                        echo -e "${RED}$TASK_RUN_OUTPUT_JSON${RESET}"
                    fi
                else
                    # Extract and display relevant parts of the task output JSON
                    NOTEBOOK_RESULT=$(echo "$TASK_RUN_OUTPUT_JSON" | jq -r '.notebook_output.result // empty')
                    ERROR_DETAILS=$(echo "$TASK_RUN_OUTPUT_JSON" | jq -r '.error // empty')
                    ERROR_TRACE=$(echo "$TASK_RUN_OUTPUT_JSON" | jq -r '.error_trace // empty')
                    LOGS_OUTPUT=$(echo "$TASK_RUN_OUTPUT_JSON" | jq -r '.logs // empty') # Often base64

                    if [[ -n "$NOTEBOOK_RESULT" ]]; then
                        log_info "Notebook Result for task '$TASK_KEY':"
                        echo "$NOTEBOOK_RESULT"
                    fi
                    if [[ -n "$ERROR_DETAILS" ]]; then
                        log_error "Error Details for task '$TASK_KEY':"
                        echo -e "${RED}$ERROR_DETAILS${RESET}"
                    fi
                    if [[ -n "$ERROR_TRACE" ]]; then
                        log_error "Error Trace for task '$TASK_KEY':"
                        echo -e "${RED}$ERROR_TRACE${RESET}"
                    fi
                     if [[ -n "$LOGS_OUTPUT" && "$LOGS_OUTPUT" != "null" ]]; then
                        log_status "Logs for task '$TASK_KEY' (may be base64 encoded):"
                        # Attempt to decode if it looks like base64, otherwise print as is
                        if echo "$LOGS_OUTPUT" | base64 --decode > /dev/null 2>&1; then
                            echo "$LOGS_OUTPUT" | base64 --decode
                        else
                            echo "$LOGS_OUTPUT"
                        fi
                    fi
                    
                    # If no specific fields were prominent, show the full JSON for debugging.
                    if [[ -z "$NOTEBOOK_RESULT" && -z "$ERROR_DETAILS" && -z "$ERROR_TRACE" && -z "$LOGS_OUTPUT" ]]; then
                        log_warning "No specific result/error/logs fields found in output for task '$TASK_KEY'. Displaying full JSON output:"
                        echo "$TASK_RUN_OUTPUT_JSON" | jq .
                    fi
                fi
                echo -e "${MAGENTA}${BOLD}-------------------------------------------------------------------${RESET}"
            else
                log_warning "Skipping output fetch for task '$TASK_KEY'; its Task Run ID is missing or null."
            fi
        done
    fi
    exit 1
else
    log_error "Job run $RUN_ID did not reach a terminal state recognized by the script after $MAX_POLLING_ATTEMPTS attempts."
    log_error "Last known LifeCycleState: $LIFE_CYCLE_STATE. State Message: $STATE_MESSAGE"
    exit 1
fi
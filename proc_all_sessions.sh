#!/bin/bash

# Get the logging level from the first command-line argument
logging_level=$1

# Get the prompt delete decision from the third command-line argument, or use the default if not provided
prompt_user_decision=${2:-false}

# Get the source path from the second command-line argument, or use the default if not provided
source_path=${3:-/Volumes/large/simon/nas_vrdata}

directories=$(ls -ld $source_path/*/)


for dir in $(ls -dr $source_path/*/); do
  if [ -d "$dir" ]; then
    if [ "$prompt_user_decision" = "true" ]; then
      python session_processing/process_session.py --logging_dir "../logs" --logging_name "session_proc.log" --logging_level "$logging_level" --session_dir "$dir" --prompt_user_decision
    else
      python session_processing/process_session.py --logging_dir "../logs" --logging_name "session_proc.log" --logging_level "$logging_level" --session_dir "$dir"
    fi
  fi
done
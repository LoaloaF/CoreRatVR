#!/bin/bash

# Get the logging level from the first command-line argument
logging_level=$1

for dir in /Volumes/large/simon/nas_vrdata/*; do
  if [ -d "$dir" ]; then
    python process_session.py --logging_dir "../logs" --logging_name "session_proc.log" --logging_level "$logging_level" --session_dir "$dir"
  fi
done
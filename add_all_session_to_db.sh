#!/bin/bash

# Get the logging level from the first command-line argument
logging_level=$1

# Get the source path from the second command-line argument, or use the default if not provided
source_path=${2:-/mnt/NTnas/nas_vrdata/000_rYL001_P0200}

database_name=${3:-ratvr}

# echo $directories
for dir in $(ls -ld $source_path/*/); do
  if [ -d "$dir" ]; then
    python session_processing/db_mysqlz/session2db.py --logging_dir "../logs" --logging_name "add_db.log" --logging_level "$logging_level" --session_dir "$dir" --database_name "$database_name" 
  fi
done
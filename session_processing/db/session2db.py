import pandas as pd
import json
import sqlite3
import os
from session_processing.db.db_session import db_session, db_session_parameters
from session_processing.db.db_camera import db_camera
from session_processing.db.db_variable import db_variable
from session_processing.db.db_utils import *
from datetime import datetime
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..', '..')) # project dir

from CustomLogger import CustomLogger as Logger


def _clear_tables(L, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # clear each column of the table
    for table in tables:
        table_name = table[0]
        cursor.execute(f"DELETE FROM {table_name};")
    
    conn.commit()
    L.logger.info("------------------------------------------")
    L.logger.info("Test table cleared.")


def add_data(L, session_dir, fname, database_location, database_name):
    db_fpath = os.path.join(database_location, database_name)
    conn = sqlite3.connect(db_fpath)
    cursor = conn.cursor()
    
    # read the session json file and convert it into a dataframe
    df_session = read_file_from_hdf5(L, session_dir, fname, "metadata")
    df_session['session_path'] = session_dir

    for column_name in df_session.columns:
        df_session = df_session.rename(columns={column_name: camel_to_snake(column_name)})

    
    # get session meatada back, or write to final hdf5 file
    try:
        db_session(L, conn, cursor, df_session)
        db_session_parameters(L, conn, cursor, df_session)
        add_file_from_hdf5_to_db(L, conn, cursor, session_dir, fname, 'unity_frame')
        add_file_from_hdf5_to_db(L, conn, cursor, session_dir, fname, 'unity_trial')
    except Exception as e:
        raise ValueError(f"Failed to add session data with error {e}")

    try:
        db_camera(L, conn, cursor, session_dir, fname, 'face')
    except Exception as e:
        L.logger.error(f"Failed to add face camera data with error {e}")

    try:
        db_camera(L, conn, cursor, session_dir, fname, 'body')
    except Exception as e:
        L.logger.error(f"Failed to add body camera data with error {e}")
    
    try:
        db_camera(L, conn, cursor, session_dir, fname, 'unity')
    except Exception as e:
        L.logger.error(f"Failed to add unity camera data with error {e}")
    
    try:
        add_file_from_hdf5_to_db(L, conn, cursor, session_dir, fname, 'ballvelocity')
    except Exception as e:
        L.logger.error(f"Failed to add ballvelocity data with error {e}")
    
    try:
        add_file_from_hdf5_to_db(L, conn, cursor, session_dir, fname, 'event')
    except Exception as e:
        L.logger.error(f"Failed to add event data with error {e}")
    
    try:
        db_variable(L, conn, cursor, session_dir, fname, df_session)
    except Exception as e:
        L.logger.error(f"Failed to add variable data with error {e}")

    L.logger.info(f"Data added successfully for path: {session_dir} into database {db_fpath}")

    conn.commit()
    conn.close()

def session2db(session_dir, fname, database_location, database_name):

    L = Logger()
    conn = None

    # if any error occurs when writing to rat_vr_test.db, the data will not be added to rat_vr.db
    # and the rat_vr_test.db will be cleared anyway
    try:
        add_data(L, session_dir, fname, database_location, database_name + '_test.db')
        L.logger.info("------------------------------------------")
        add_data(L, session_dir, fname, database_location, database_name + '.db')
    except Exception as e:
        L.logger.error(f"Failed to add data from: {session_dir} with error {e}")
    finally:
        if conn is not None:
            conn.close()
        conn = sqlite3.connect('rat_vr_test.db')
        _clear_tables(L, conn)
        conn.close()


# -S- 
# I added the overhead archetecture for this procedure. Here is what i changed:
# I added a file called process_session.py to the Core root dir. This is the 
# file that will be exectued by the user. It import the session2DB function from
# this module and calls it. In the future, more things will be called from there 
# (like validation). I also added the API endpoints for calling process_session.py
# You can run the vr server, and then testapi.py to initiate then run the process_session.py
# This will create a new session directory and put the log file of process_session in it.

# if you want to directly see the logs in the terminal, you can also run it explicitly,
# but you need to pass the logger arugments. Excample below:
#   python process_session.py --logging_dir "../logs" --logging_name "sesion_proc.log" --logging_level "DEBUG"

# We will handle the exact path handling later. For now you can expect to get 
# the directory passed to the session2DB function.

# I won't check all add_* files in detail, but I think you got my points;)
# Add logging where necessary (you can just pass L around or recreate, it will
# reference the same logger object, so no overhead) Then, add # comments where 
# things are maybe not so clear, cleanup imports, limit line length to 80 chars

# But it really looks very nice, thanks a lot!!
# -S- 


if __name__ == "__main__":

    session2db("/mnt/smbshare/vrdata/2024-06-13_12-59-52_goodone_Thursday_1/",
               'behavior_2024-06-13_11-04_rYL001_P0200_GoalDirectedMovement_11min.hdf5',
               '../', 'rat_vr')
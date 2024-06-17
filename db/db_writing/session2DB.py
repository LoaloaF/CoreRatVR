import pandas as pd
import json
import sqlite3
import os
from add_session import add_session
from add_unity_output import add_unity_output, extract_trial_package
from add_camera import add_camera
from add_portenta import add_ball_velocity, add_event
from add_variable import add_variable
from add_utils import *
from datetime import datetime
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..', '..')) # project dir

from CustomLogger import CustomLogger as Logger


def read_session_json_file(cursor, session_dir):

    session_folder_name = session_dir.split('/')[-1]  # get the last part of the path
    session_info = session_folder_name.split('_')  # split into time_time_sessionName

    session_json_path = os.path.join(session_dir, 'session_parameters.json')
    with open(session_json_path, 'r') as file:
        session_json = json.load(file)

    # check if the animal and paradigm already exist in the database
    paradigm_name = session_json["paradigm_name"]
    cursor.execute("SELECT paradigm_id FROM paradigm WHERE paradigm_name=?", (paradigm_name,))
    fetch_result = cursor.fetchall()
    if len(fetch_result) == 0:
        cursor.execute("INSERT INTO paradigm (paradigm_name) VALUES (?)", (paradigm_name,))
        paradigm_id = cursor.lastrowid
    else:
        paradigm_id = fetch_result[0][0]

    animal_name = session_json["animal"]
    cursor.execute("SELECT animal_id FROM animal WHERE animal_name=?", (animal_name,))
    fetch_result = cursor.fetchall()
    if len(fetch_result) == 0:
        cursor.execute("INSERT INTO animal (animal_name) VALUES (?)", (animal_name,))
        animal_id = cursor.lastrowid
    else:
        animal_id = fetch_result[0][0]

    # convert the json into a dataframe
    df_session = pd.DataFrame([session_json])

    # convert the column names from camel case to snake case
    for each_column in df_session.columns:
        df_session.rename(columns={each_column: camel_to_snake(each_column)}, inplace=True)

    # add the session time, name, path, paradigm_id, and animal_id
    session_time_ori_format = datetime.strptime((session_info[0] + '_' + session_info[1]), "%Y-%m-%d_%H-%M-%S")
    session_time_reformat = session_time_ori_format.strftime("%Y-%m-%d %H:%M:%S")
    df_session['session_time'] = session_time_reformat
    df_session['session_name'] = session_info[2]
    df_session['session_path'] = session_dir
    df_session['paradigm_id'] = paradigm_id
    df_session['animal_id'] = animal_id

    df_session.drop(columns=['session_id', 'animal', 'paradigm_name'], inplace=True)

    return df_session   


def clear_tables(L, conn):
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


def add_data(L, session_dir, db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    
    # all of this should be indepdant of the DB/ cursor  - unless there is a big mismatch 

    # read the session json file and convert it into a dataframe
    df_session = read_session_json_file(cursor, session_dir)
    
    # get session meatada back, or write to final hdf5 file
    df_session_parameters = add_session(L, df_session, conn, cursor)

    # extract the trial package from the unity output hdf5 file
    df_trialPackage = extract_trial_package(cursor, session_dir, 
                                            df_session, use_frame_for_trial_time=True)
    
    add_unity_output(L, conn, cursor, session_dir, df_trialPackage)
    add_camera(L, conn, cursor, session_dir, df_trialPackage, 'face')
    add_camera(L, conn, cursor, session_dir, df_trialPackage, 'body')
    add_camera(L, conn, cursor, session_dir, df_trialPackage, 'unity')
    add_ball_velocity(L, conn, cursor, session_dir, df_trialPackage)
    add_event(L, conn, cursor, session_dir, df_trialPackage)
    add_variable(L, conn, cursor, session_dir, df_session)

    L.logger.info(f"Data added successfully for path: {session_dir} into database {db_name}")

    conn.commit()
    conn.close()

def session2DB(session_dir):
    # -S-
    # Use session_dir everywhere instead of folder_path etc
    # -S-

    L = Logger()
    conn = None

    # if any error occurs when writing to rat_vr_test.db, the data will not be added to rat_vr.db
    # and the rat_vr_test.db will be cleared anyway
    try:
        # -S-
        # Add logging statements at INFO level
        # -S-
        # add_data(session_dir, '/mnt/smbshare/vrdata/rat_vr_test.db')
        # add_data(session_dir, '/mnt/smbshare/vrdata/rat_vr.db')

        add_data(L, session_dir, 'rat_vr_test.db')
        L.logger.info("------------------------------------------")
        add_data(L, session_dir, 'rat_vr.db')

    except Exception as e:
        L.logger.error(f"Failed to add data from: {session_dir} with error {e}")
    finally:
        if conn is not None:
            conn.close()
        conn = sqlite3.connect('rat_vr_test.db')
        clear_tables(L, conn)
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

    session2DB("/mnt/smbshare/vrdata/2024-05-29_17-15-57_goodoneWedndesday2")
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

def read_session_json_file(cursor, parent_folder_path, session_folder_name):

    session_info = session_folder_name.split('_')  
    session_json_path = os.path.join(parent_folder_path, session_folder_name, 'session_parameters.json')

    with open(session_json_path, 'r') as file:
        session_json = json.load(file)

    paradigm_name = session_json["paradigm_name"]
    cursor.execute("SELECT paradigm_id FROM paradigm WHERE paradigm_name=?", (paradigm_name,))
    fetch_result = cursor.fetchall()
    if len(fetch_result) == 0:
        raise ValueError(f"Paradigm {paradigm_name} does not exist in the paradigm table.")
    else:
        paradigm_id = fetch_result[0]

    animal_name = session_json["animal"]
    cursor.execute("SELECT animal_id FROM animal WHERE animal_name=?", (animal_name,))
    fetch_result = cursor.fetchall()
    if len(fetch_result) == 0:
        raise ValueError(f"Animal {animal_name} does not exist in the animal table.")
    else:
        animal_id = fetch_result[0]

    df_session = pd.DataFrame([session_json])

    for each_column in df_session.columns:
        df_session.rename(columns={each_column: camel_to_snake(each_column)}, inplace=True)

    df_session['session_time'] = datetime.strptime((session_info[0] + '_' + session_info[1]), "%Y-%m-%d_%H-%M-%S").strftime("%Y-%m-%d %H:%M:%S")
    df_session['session_name'] = session_info[2]
    df_session['session_path'] = os.path.join(parent_folder_path, session_folder_name)
    df_session['paradigm_id'] = paradigm_id
    df_session['animal_id'] = animal_id

    df_session.drop(columns=['session_id', 'animal', 'paradigm_name'], inplace=True)

    return df_session   


def clear_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        if table_name == 'paradigm' or table_name == 'animal':
            continue
        cursor.execute(f"DELETE FROM {table_name};")
    
    conn.commit()
    print("Test database cleared.")


def add_data(parent_folder_path, session_folder_name, db_name):
    folder_path = os.path.join(parent_folder_path, session_folder_name)
    conn = sqlite3.connect(db_name)

    cursor = conn.cursor()
    df_session = read_session_json_file(cursor, parent_folder_path, session_folder_name)
    add_session(df_session, conn, cursor)
    df_trialPackage = extract_trial_package(cursor, folder_path, df_session, use_frame_for_trial_time=True)
    
    add_unity_output(conn, cursor, folder_path, df_trialPackage)
    # add_camera(conn, cursor, folder_path, df_trialPackage, 'face')
    # add_camera(conn, cursor, folder_path, df_trialPackage, 'body')
    # add_camera(conn, cursor, folder_path, df_trialPackage, 'unity')
    add_ball_velocity(conn, cursor, folder_path, df_trialPackage)
    add_event(conn, cursor, folder_path, df_trialPackage)
    add_variable(conn, cursor, folder_path, df_session)

    print("Data added successfully for path: ", folder_path, " into database: ", db_name)
    print("-----------------------------------------")

    conn.commit()
    conn.close()

def session2DB(session_dir):
    # -S-
    # Use session_dir everywhere instead of folder_path etc
    # -S-
    print(session_dir)
    print()
    
    parent_folder_path = '/home/ntgroup/Project/DBRatVR/SQLite/TestData'
    session_folder_name = '2024-06-04_12-06-04_goodone_Tuesday_1'
    folder_path = os.path.join(parent_folder_path, session_folder_name)
    
    conn = None

    try:
        # -S-
        # Add logging statements at INFO level
        # -S-
        add_data(parent_folder_path, session_folder_name, 'rat_vr_test.db')
        conn = sqlite3.connect('rat_vr_test.db')
        clear_tables(conn)
        conn.close()
        add_data(parent_folder_path, session_folder_name, 'rat_vr.db')

    except Exception as e:
        print("-----------------------------------------")
        print("Failed to add data in folder: ", folder_path)
        print(e)
        print("-----------------------------------------")

    finally:
        if conn is not None:
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

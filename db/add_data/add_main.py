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
    add_camera(conn, cursor, folder_path, df_trialPackage, 'face')
    add_camera(conn, cursor, folder_path, df_trialPackage, 'body')
    add_camera(conn, cursor, folder_path, df_trialPackage, 'unity')
    add_ball_velocity(conn, cursor, folder_path, df_trialPackage)
    add_event(conn, cursor, folder_path, df_trialPackage)
    add_variable(conn, cursor, folder_path, df_session)

    print("Data added successfully for path: ", folder_path, " into database: ", db_name)
    print("-----------------------------------------")

    conn.commit()
    conn.close()


if __name__ == "__main__":


    parent_folder_path = '/home/vrmaster/projects/ratvr/VirtualReality/data'
    session_folder_name = '2024-06-05_18-09-34_goodone_wednes2'
    folder_path = os.path.join(parent_folder_path, session_folder_name)
    
    conn = None

    try:
        add_data(parent_folder_path, session_folder_name, '/home/vrmaster/projects/ratvr/VirtualReality/data/rat_vr_test.db')

        add_data(parent_folder_path, session_folder_name, '/home/vrmaster/projects/ratvr/VirtualReality/data/rat_vr.db')

    except Exception as e:
        print("-----------------------------------------")
        print("Failed to add data in folder: ", folder_path)
        print(e)
        print("-----------------------------------------")

    finally:
        if conn is not None:
            conn.close()
        conn = sqlite3.connect('/home/vrmaster/projects/ratvr/VirtualReality/data/rat_vr_test.db')
        clear_tables(conn)
        conn.close()

        
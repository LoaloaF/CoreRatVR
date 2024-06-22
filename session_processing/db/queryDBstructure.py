import sqlite3
import os

def get_table_names(db_path=None):
    if db_path:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [table[0] for table in cursor.fetchall()]
        conn.close()
    else:
        table_names = ['animal', 'paradigm', 'session', 'session_parameter', 'ball_velocity', 'event', 'unity_frame', 'unity_trial', 'face_cam', 'body_cam', 'unity_cam', 'paradigm_P0200']
    return table_names

def get_table_structure(table_name, db_fullfname=None):
    if db_fullfname and os.exists(db_fullfname):
        conn = sqlite3.connect(db_fullfname)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        conn.close()
        return columns
    
    else:
        # Hardcoded structure based on createDB.py - careful this may not always be up to date
        print("No database file found or path provided. Returning hardcoded DB structure.")
        
        structures = {
            'animal': [('animal_id', 'INTEGER'), ('animal_name', 'TEXT'), ('animal_gender', 'TEXT'), ('animal_description', 'TEXT')],
            'paradigm': [('paradigm_id', 'INTEGER'), ('paradigm_name', 'TEXT'), ('paradigm_description', 'TEXT')],
            'session': [('session_id', 'INTEGER'), ('session_name', 'TEXT'), ('session_time', 'DATE'), ('session_path', 'TEXT'), ('paradigm_id', 'INT'), ('animal_id', 'INT'), ('animal_weight', 'DOUBLE'), ('start_time', 'DATE'), ('end_time', 'DATE'), ('duration', 'DOUBLE'), ('notes', 'TEXT')],
            'session_parameter': [('session_parameter_id', 'INTEGER'), ('session_id', 'INT'), ('parameter_name', 'TEXT'), ('parameter_value', 'TEXT'), ('parameter_type', 'TEXT')],
            'ball_velocity': [('ball_velocity_id', 'INTEGER'), ('session_id', 'INT'), ('ball_velocity_timestamp', 'BIGINT'), ('ball_velocity_ttl', 'BIGINT'), ('ball_velocity_data', 'BLOB')],
            'event': [('event_id', 'INTEGER'), ('session_id', 'INT'), ('event_timestamp', 'BIGINT'), ('event_ttl', 'BIGINT'), ('event_data', 'BLOB')],
            'unity_frame': [('unity_frame_id', 'INTEGER'), ('session_id', 'INT'), ('unity_frame_timestamp', 'BIGINT'), ('unity_frame_ttl', 'BIGINT'), ('unity_frame_data', 'BLOB')],
            'unity_trial': [('unity_trial_id', 'INTEGER'), ('session_id', 'INT'), ('unity_trial_timestamp', 'BIGINT'), ('unity_trial_ttl', 'BIGINT'), ('unity_trial_data', 'BLOB')],
            'face_cam': [('face_cam_id', 'INTEGER'), ('session_id', 'INT'), ('face_cam_timestamp', 'BIGINT'), ('face_cam_ttl', 'BIGINT'), ('face_cam_data', 'BLOB')],
            'body_cam': [('body_cam_id', 'INTEGER'), ('session_id', 'INT'), ('body_cam_timestamp', 'BIGINT'), ('body_cam_ttl', 'BIGINT'), ('body_cam_data', 'BLOB')],
            'unity_cam': [('unity_cam_id', 'INTEGER'), ('session_id', 'INT'), ('unity_cam_timestamp', 'BIGINT'), ('unity_cam_ttl', 'BIGINT'), ('unity_cam_data', 'BLOB')],
            'paradigm_P0200': [('paradigm_P0200_id', 'INTEGER'), ('session_id', 'INT'), ('trial_id', 'BIGINT'), ('pd', 'DOUBLE'), ('pa', 'DOUBLE')]
        }
        return structures.get(table_name, [])
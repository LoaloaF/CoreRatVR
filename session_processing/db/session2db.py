import os
import sqlite3

from CustomLogger import CustomLogger as Logger

from session_processing.db.db_writing import write_session2db
from session_processing.db.db_writing import write_session_params2db
from session_processing.db.db_writing import write_paradigmVariable2db
from session_processing.db.db_writing import write_camera2db

from session_processing.db.db_utils import read_file_from_hdf5
from session_processing.db.db_utils import camel_to_snake
from session_processing.db.db_utils import add_file_from_hdf5_to_db

def _clear_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # clear each column of the table
    for table in tables:
        table_name = table[0]
        cursor.execute(f"DELETE FROM {table_name};")
    
    conn.commit()
    Logger().logger.spacer()
    Logger().logger.info("Test table cleared.")


def add_data(session_dir, fname, database_location, database_name):
    L = Logger()
    db_fpath = os.path.join(database_location, database_name)
    conn = sqlite3.connect(db_fpath)
    cursor = conn.cursor()
    
    # read the session json file and convert it into a dataframe
    df_session = read_file_from_hdf5(session_dir, fname, "metadata")
    df_session['session_path'] = session_dir

    for column_name in df_session.columns:
        df_session = df_session.rename(columns={column_name: camel_to_snake(column_name)})
    
    # get session meatada back, or write to final hdf5 file
    try:
        write_session2db(conn, cursor, df_session)
        write_session_params2db(conn, cursor, df_session)
        add_file_from_hdf5_to_db(conn, cursor, session_dir, fname, 'unity_frame')
        add_file_from_hdf5_to_db(conn, cursor, session_dir, fname, 'unity_trial')
    except Exception as e:
        raise ValueError(f"Failed to add session data with error {e}")

    try:
        write_camera2db(conn, cursor, session_dir, fname, 'face')
    except Exception as e:
        L.logger.error(f"Failed to add face camera data with error {e}")

    try:
        write_camera2db(conn, cursor, session_dir, fname, 'body')
    except Exception as e:
        L.logger.error(f"Failed to add body camera data with error {e}")
    
    try:
        write_camera2db(conn, cursor, session_dir, fname, 'unity')
    except Exception as e:
        L.logger.error(f"Failed to add unity camera data with error {e}")
    
    try:
        add_file_from_hdf5_to_db(conn, cursor, session_dir, fname, 'ballvelocity')
    except Exception as e:
        L.logger.error(f"Failed to add ballvelocity data with error {e}")
    
    try:
        add_file_from_hdf5_to_db(conn, cursor, session_dir, fname, 'event')
    except Exception as e:
        L.logger.error(f"Failed to add event data with error {e}")
    
    try:
        write_paradigmVariable2db(conn, cursor, session_dir, fname, df_session)
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
        test_database_name = database_name.replace(".db", "_test.db")
        add_data(session_dir, fname, database_location, test_database_name)
        L.spacer()
        add_data(session_dir, fname, database_location, database_name)
    except Exception as e:
        L.logger.error(f"Failed to add data from: {session_dir} with error {e}")
    finally:
        if conn is not None:
            conn.close()
            
        conn = sqlite3.connect(os.path.join(database_location, test_database_name))
        _clear_tables(conn)
        conn.close()
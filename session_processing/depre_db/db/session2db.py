import os
import sqlite3
import argparse
import sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
from CustomLogger import CustomLogger as Logger

from session_processing.db.db_writing import write_session2db
from session_processing.db.db_writing import write_session_params2db
from session_processing.db.db_writing import write_paradigmVariable2db
from session_processing.db.db_writing import write_camera2db

from session_processing.db.db_utils import read_file_from_hdf5
from session_processing.db.db_utils import camel_to_snake
from session_processing.db.db_utils import add_file_from_hdf5_to_db
from session_processing.db.createDB import create_ratvr_db

def _clear_tables(database_location, database_name):

    os.remove(os.path.join(database_location, database_name))
    create_ratvr_db(os.path.join(database_location, database_name))

    Logger().spacer()
    Logger().logger.info("Test table cleared.")


def write_data2db(session_dir, fname, database_location, database_name):
    L = Logger()
    db_fpath = os.path.join(database_location, database_name)
    conn = sqlite3.connect(db_fpath)
    cursor = conn.cursor()
    
    # read the session json file and convert it into a dataframe
    df_session = read_file_from_hdf5(session_dir, fname, "metadata")

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
        L.logger.warning(f"Failed to add face camera data with error {e}")

    try:
        write_camera2db(conn, cursor, session_dir, fname, 'body')
    except Exception as e:
        L.logger.warning(f"Failed to add body camera data with error {e}")
    
    try:
        write_camera2db(conn, cursor, session_dir, fname, 'unity')
    except Exception as e:
        L.logger.warning(f"Failed to add unity camera data with error {e}")
    
    try:
        add_file_from_hdf5_to_db(conn, cursor, session_dir, fname, 'ballvelocity')
    except Exception as e:
        L.logger.warning(f"Failed to add ballvelocity data with error {e}")
    
    try:
        add_file_from_hdf5_to_db(conn, cursor, session_dir, fname, 'event')
    except Exception as e:
        L.logger.warning(f"Failed to add event data with error {e}")
    
    try:
        write_paradigmVariable2db(conn, cursor, session_dir, fname, df_session)
    except Exception as e:
        L.logger.warning(f"Failed to add variable data with error {e}")

    L.logger.info(f"Data added successfully for path: {session_dir} into database {db_fpath}")

    conn.commit()
    conn.close()

def session2db(session_dir, fname, database_location, database_name):
    L = Logger()
    conn = None
    
    if fname is None:
        fname = 'behavior_' + session_dir.split('/')[-2] + '.hdf5'
    #TODO: add metadata["metadata"]["paradigms_states"] as a new table in the database

    # if any error occurs when writing to rat_vr_test.db, the data will not be added to rat_vr.db
    # and the rat_vr_test.db will be cleared anyway
    try:
        test_database_name = database_name.replace(".db", "_test.db")
        write_data2db(session_dir, fname, database_location, test_database_name)
        L.spacer()
        write_data2db(session_dir, fname, database_location, database_name)
    except Exception as e:
        L.logger.error(f"Failed to add data from: {session_dir} with error {e}")
    finally:
        if conn is not None:
            conn.close()
        _clear_tables(database_location, test_database_name)




if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Validate and add a finished session to DB")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level", default="INFO")
    argParser.add_argument("--session_dir", default="/mnt/NTnas/nas_vrdata/000_rYL001_P0200/2024-06-03_18-24_rYL001_P0200_GoalDirectedMovement_min")
    argParser.add_argument("--fname", default=None)
    # argParser.add_argument("--database_location", default='/run/media/ntgroup/2D2C888C340113CD/homedataXPS_080123/homedataXPS/projects/ratvr/database')
    argParser.add_argument("--database_location", default='/home/ntgroup/Project')
    argParser.add_argument("--database_name", default='rat_vr.db')

    kwargs = vars(argParser.parse_args())
    
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.spacer()
    L.logger.info("Subprocess started")
    L.logger.info(L.fmtmsg(kwargs))
            
    session2db(**kwargs)
    L.spacer()
    print("\n\n\n\n")
import os
import h5py

from CustomLogger import CustomLogger as Logger

from session_processing.db.db_utils import read_file_from_hdf5
from session_processing.db.db_utils import add_session_into_df

def write_session2db(conn, cursor, df_session):
    L = Logger()
    # extract the session info stored in the main session table
    paradigm_name = df_session["paradigm_name"][0]
    paradigm_id = int(paradigm_name[1:5])
    cursor.execute(f"SELECT paradigm_id FROM paradigm_meta WHERE paradigm_name=?", (paradigm_name,))
    fetch_result = cursor.fetchall()
    if len(fetch_result) == 0:
        cursor.execute("INSERT INTO paradigm_meta (paradigm_id, paradigm_name) VALUES (?,?)", (paradigm_id,paradigm_name,))

    animal_name = df_session["animal_name"][0]
    cursor.execute("SELECT animal_id FROM animal WHERE animal_name=?", (animal_name,))
    fetch_result = cursor.fetchall()
    if len(fetch_result) == 0:
        cursor.execute("INSERT INTO animal (animal_name) VALUES (?)", (animal_name,))

    cursor.execute(f"PRAGMA table_info(session)")
    columns_info = cursor.fetchall()
    column_names = [column[1] for column in columns_info]
    session_columns = column_names[1:]

    for each_column in session_columns:
        if each_column not in df_session.columns:
            df_session[each_column] = None
    
    # if the column is not in the desired column, drop it
    for each_column in df_session.columns:
        if each_column not in session_columns:
            df_session = df_session.drop(columns=each_column)

    # check if the session already exists
    # if exists, raise an error
    # if not, add the session and its parameters
    session_name = df_session['session_name'].values[0]
    cursor.execute(f"SELECT * from session WHERE session_name=?", (session_name,))
    if len(cursor.fetchall()) != 0:
        raise ValueError(f"Session {session_name} already exists.")
    else:
        df_session.to_sql('session', conn, if_exists='append', index=False)        
        L.logger.info(f"Session {session_name} added successfully.")


def write_session_params2db(conn, cursor, df_session):
    L = Logger()
    
    # extract the column names in the session_parameter table
    cursor.execute(f"PRAGMA table_info(session_parameter)")
    columns_info = cursor.fetchall()
    column_names = [column[1] for column in columns_info]
    parameters_full_column = column_names[1:]

    # if the required column in the table is not present in the df_session_parameters, add it
    for each_column in parameters_full_column:
        if each_column not in df_session.columns:
            df_session[each_column] = None
    
    # if the column is not in the desired column, drop it
    for each_column in df_session.columns:
        if each_column not in parameters_full_column:
            df_session = df_session.drop(columns=each_column)
    
    df_session.to_sql('session_parameter', conn, if_exists='append', index=False)
    L.logger.info(f"Session parameters added successfully.")


def write_camera2db(conn, cursor, session_dir, fname, camera_type):
    L = Logger()
    
    df_cam = read_file_from_hdf5(session_dir, fname, camera_type + 'cam_packages')

    if df_cam is None:
        return

    # add session info into df
    df_cam = add_session_into_df(cursor, df_cam)

    cam_name_prefix = camera_type + 'cam_'
    # prepare the space in df for the blob data
    df_cam[cam_name_prefix + 'data'] = None
    df_cam[cam_name_prefix + 'data'] = df_cam[cam_name_prefix + 'data'].astype(object)

    # read the blob data from hdf5 file
    cam_path = os.path.join(session_dir, fname)
    hdf_cam = h5py.File(cam_path, 'r')[cam_name_prefix + 'frames']

    for each_hdf in hdf_cam:
        package_id = int(each_hdf.split('_')[1])
        df_cam.loc[df_cam[cam_name_prefix + 'image_id'] == package_id, cam_name_prefix + 'data'] = hdf_cam[each_hdf][()]
    
    df_cam.to_sql(camera_type + 'cam', conn, if_exists='append', index=False)
    L.logger.info(f"{camera_type} camera added successfully.")
    

def write_paradigmVariable2db(conn, cursor, session_dir, fname, df_session):
    L = Logger()
    paradigm_name = df_session["paradigm_name"][0] 

    # check if the variable table already exists
    variable_table_name = "paradigm_" + paradigm_name.split('_')[0]
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (variable_table_name,))

    if (len(cursor.fetchall()) == 0):
        raise Exception(f"Variable table {variable_table_name} does not exist. "
                        f"Please add the paradigm first.")
    
    try:
        unity_output_path = os.path.join(session_dir, 'unity_output.hdf5')
        df_variable = read_file_from_hdf5(session_dir, fname, 'paradigm_variable')

        if df_variable is None:
            return

        df_variable = add_session_into_df(cursor, df_variable)

        df_variable.to_sql(variable_table_name, conn, if_exists='append', index=False)
        L.logger.info(f"Variable table {variable_table_name} added successfully.")

    except:
        L.logger.info(f"No trialPackages found in {unity_output_path}. "
                      f"Variable table {variable_table_name} not added.")
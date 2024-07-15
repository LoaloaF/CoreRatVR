import os
import h5py
from PIL import Image
import io
from CustomLogger import CustomLogger as Logger

from session_processing.db_mysql.db_utils import read_file_from_hdf5
from session_processing.db_mysql.db_utils import add_session_into_df

def write_session2db(conn, cursor, engine, df_session):
    L = Logger()
    # extract the session info stored in the main session table
    paradigm_name = df_session["paradigm_name"][0]
    # paradigm_id = int(paradigm_name[1:5])
    # TODO paradigm_id not always there by default, code below still needed?
    paradigm_id = int(df_session['paradigm_id'][0])
    cursor.execute(f"SELECT paradigm_id FROM paradigm_meta WHERE paradigm_name='{paradigm_name}'")
    fetch_result = cursor.fetchall()
    if len(fetch_result) == 0:
        cursor.execute(f"INSERT INTO paradigm_meta (paradigm_id, paradigm_name) VALUES ('{paradigm_id}','{paradigm_name}')")

    animal_name = df_session["animal_name"][0]
    cursor.execute(f"SELECT animal_id FROM animal WHERE animal_name='{animal_name}'")
    fetch_result = cursor.fetchall()
    if len(fetch_result) == 0:
        cursor.execute(f"INSERT INTO animal (animal_name) VALUES ('{animal_name}')")

    cursor.execute("DESCRIBE session")
    columns_info = cursor.fetchall()
    column_names = [column[0] for column in columns_info]
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
    cursor.execute(f"SELECT * from session WHERE session_name='{session_name}'")
    if len(cursor.fetchall()) != 0:
        raise ValueError(f"Session {session_name} already exists.")
    else:
        df_session.to_sql('session', con=engine, if_exists='append', index=False) 
        conn.commit()       
        L.logger.info(f"Session {session_name} added successfully.")


def write_session_params2db(conn, cursor, engine, df_session):
    L = Logger()
    
    # extract the column names in the session_parameter table
    cursor.execute("DESCRIBE session_parameter")
    columns_info = cursor.fetchall()
    column_names = [column[0] for column in columns_info]
    parameters_full_column = column_names[1:]

    # if the required column in the table is not present in the df_session_parameters, add it
    for each_column in parameters_full_column:
        if each_column not in df_session.columns:
            df_session[each_column] = None
    
    # if the column is not in the desired column, drop it
    for each_column in df_session.columns:
        if each_column not in parameters_full_column:
            df_session = df_session.drop(columns=each_column)
    
    df_session.to_sql('session_parameter', con=engine, if_exists='append', index=False)
    L.logger.info(f"Session parameters added successfully.")


def write_camera2db(conn, cursor, engine, session_dir, fname, camera_type):
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

    image_id = 0
    for each_hdf in hdf_cam:
        if (image_id % 10000) == 0:
            L.logger.info(f"{camera_type}cam: Processing {image_id}th image.")

        package_id = int(each_hdf.split('_')[1])
        image = Image.open(io.BytesIO(hdf_cam[each_hdf][()].item()))
        output_stream = io.BytesIO()
        image.save(output_stream, format='JPEG', quality=50)
        compressed_image_data = output_stream.getvalue()
        df_cam.loc[df_cam[cam_name_prefix + 'image_id'] == package_id, cam_name_prefix + 'data'] = compressed_image_data
        image_id += 1

    df_cam[f"{camera_type}cam_image_ephys_timestamp"] = None

    chunksize = 10000
    for i in range(0, len(df_cam), chunksize):
        L.logger.info(f"{camera_type} inserting from {i} to {i+chunksize}.")
        df_chunk = df_cam.iloc[i:i+chunksize]
    # # Iterate over chunks and write to SQL
    # for i in range(0, len(df_cam), chunksize):
    #     print(i, i+chunksize)
    #     df_chunk = df_cam.iloc[i:i+chunksize]
    #     # query = "INSERT INTO facecam (facecam_image_id, facecam_image_pc_timestamp, facecam_image_ephys_timestamp, trial_id, session_id, facecam_data) VALUES (%s, %s, %s, %s, %s, %s)"
    #     # data = [tuple(x) for x in df_chunk.to_numpy()]
    #     # cursor.executemany(query, data)
        df_chunk.to_sql(camera_type + 'cam', con=engine, if_exists='append', index=False)

    L.logger.info(f"{camera_type} camera added successfully.")
    

def write_paradigmVariable2db(conn, cursor, engine, session_dir, fname, df_session):
    L = Logger()
    paradigm_name = df_session["paradigm_name"][0] 

    # check if the variable table already exists
    variable_table_name = "paradigm_" + paradigm_name.split('_')[0]


    # Query the information_schema.tables table to check if the table exists
    query = """
        SELECT TABLE_NAME 
        FROM information_schema.tables 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
    """
    cursor.execute(query, (conn.database, variable_table_name))
    result = cursor.fetchone()

    if not result:
        raise Exception(f"Variable table {variable_table_name} does not exist. "
                        f"Please add the paradigm first.")
    
    try:
        unity_output_path = os.path.join(session_dir, 'unity_output.hdf5')
        df_variable = read_file_from_hdf5(session_dir, fname, 'paradigm_variable')

        if df_variable is None:
            return

        df_variable = add_session_into_df(cursor, df_variable)

        df_variable.to_sql(variable_table_name, con=engine, if_exists='append', index=False)
        L.logger.info(f"Variable table {variable_table_name} added successfully.")

    except:
        L.logger.info(f"No trialPackages found in {unity_output_path}. "
                      f"Variable table {variable_table_name} not added.")
from session_processing.db.db_utils import *
import os


def db_variable(L, conn, cursor, session_dir, fname, df_session):

    paradigm_name = df_session["paradigm_name"][0] 

    # check if the variable table already exists
    variable_table_name = "paradigm_" + paradigm_name.split('_')[0]
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (variable_table_name,))

    if (len(cursor.fetchall()) == 0):
        raise Exception(f"Variable table {variable_table_name} does not exist. Please add the paradigm first.")
    
    # TODO check integrity of the following code
    try:
        unity_output_path = os.path.join(session_dir, 'unity_output.hdf5')
        df_variable = read_file_from_hdf5(L, session_dir, fname, 'paradigm_variable')

        if df_variable is None:
            return

        df_variable = add_session_into_df(cursor, df_variable)

        df_variable.to_sql(variable_table_name, conn, if_exists='append', index=False)
        L.logger.info(f"Variable table {variable_table_name} added successfully.")

    except:
        L.logger.info(f"No trialPackages found in {unity_output_path}. Variable table {variable_table_name} not added.")
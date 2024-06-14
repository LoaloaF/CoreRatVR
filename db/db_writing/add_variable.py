import pandas as pd
from add_utils import *
import os


def add_variable(L, conn, cursor, folder_path, df_session):

    # read the dataframe of variable
    paradigm_id = df_session['paradigm_id'][0]
    cursor.execute(f"SELECT paradigm_name FROM paradigm WHERE paradigm_id={paradigm_id}")

    paradigm_name = cursor.fetchall()[0][0]

    # TODO: check if the variable table already exists
    variable_table_name = "paradigm_" + paradigm_name.split('_')[0]

    
    try:
        unity_output_path = os.path.join(folder_path, 'unity_output.hdf5')
        df_variable = pd.read_hdf(unity_output_path, key='trialPackages')
        df_variable = df_variable.reset_index(drop=True)
        df_variable.drop(columns=['N', 'SFID', 'SPCT', 'SPCT', 'EFID', 'EPCT', 'TD', 'O'], inplace=True)
        df_variable.rename(columns={'ID': 'trial_id'}, inplace=True)
        df_variable.columns = df_variable.columns.str.lower()
        df_variable = add_session_into_df(cursor, df_variable)

        df_variable.to_sql(variable_table_name, conn, if_exists='append', index=False)
        L.logger.info(f"Variable table {variable_table_name} added successfully.")

    except:
        L.logger.info(f"No trialPackages found in {unity_output_path}. Variable table {variable_table_name} not added.")
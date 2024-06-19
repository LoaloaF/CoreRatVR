import pandas as pd
import merge_utils as utils
import os


def merge_trial_variable_hdf5(L, session_dir):


    unity_output_path = os.path.join(session_dir, 'unity_output.hdf5')

    if not os.path.exists(unity_output_path):
        L.logger.error(f"Failed to find unity_output.hdf5 file: {unity_output_path}")
        return
    
    try:
        df_variable = pd.read_hdf(unity_output_path, key='trialPackages')
    except:
        L.logger.error(f"Failed to read trialPackages from unity_output.hdf5 file: {unity_output_path}")
        return
    
    df_variable = df_variable.reset_index(drop=True)
    df_variable.drop(columns=['N', 'SFID', 'SPCT', 'SPCT', 'EFID', 'EPCT', 'TD', 'O'], inplace=True)
    df_variable.rename(columns={'ID': 'trial_id'}, inplace=True)
    df_variable.columns = df_variable.columns.str.lower()

    utils.merge_into_hdf5(L, session_dir, df_variable, 'trial_variable')
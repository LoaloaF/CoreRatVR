import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'session_processing', 'merge_hdf5')) # project dir

from datetime import datetime
import json
import pandas as pd

from CustomLogger import CustomLogger as Logger

import merge_utils as utils
from merge_unity_output import merge_unity_output_hdf5, extract_trial_package
from merge_camera import merge_camera_hdf5
from merge_portenta import merge_ball_velocity_hdf5, merge_event_hdf5
from merge_trial_variable import merge_trial_variable_hdf5

def read_session_json_file(session_dir):
    session_folder_name = session_dir.split('/')[-1]  # get the last part of the path
    session_info = session_folder_name.split('_')  # split into time_time_sessionName


    session_json_path = os.path.join(session_dir, 'session_parameters.json')

    with open(session_json_path, 'r') as file:
        session_json = json.load(file)

    # convert the json into a dataframe
    df_session = pd.DataFrame([session_json])

    # convert the column names from camel case to snake case
    for each_column in df_session.columns:
        df_session.rename(columns={each_column: utils.camel_to_snake(each_column)}, inplace=True)

    # add the session time, name, path, paradigm_id, and animal_id
    session_time_ori_format = datetime.strptime((session_info[0] + '_' + session_info[1]), "%Y-%m-%d_%H-%M-%S")
    session_time_reformat = session_time_ori_format.strftime("%Y-%m-%d %H:%M:%S")
    df_session['session_time'] = session_time_reformat
    df_session['session_name'] = session_info[2]
    df_session['session_path'] = session_dir
    return df_session   

def init_hdf5(session_dir, merged_fname):
    hdf5_fname = os.path.join(session_dir, merged_fname)    
    
    with pd.HDFStore(hdf5_fname) as hdf:
        keys = ('session', 'unity_frame', 'unity_trial', 'face_cam', 'body_cam', 
                'unity_cam', 'ball_velocity', 'event', 'trial_variable')
        [hdf.put(key, pd.DataFrame(), format='table', append=False) for key in keys]

def session_data2single_hdf5(session_dir, filelist):
    L = Logger()
    
    # create the empty hdf5 file to write to
    merged_fname = 'behavior.hdf5'
    init_hdf5(session_dir, merged_fname)

    # read the session json file (excel metadata) and convert it into a dataframe
    if filelist["JSON-Files"]["session_parameters.json"] != "Missing!":
        df_session_metadata = read_session_json_file(session_dir)
    
        # read the session json file (excel metadata) and convert it into a dataframe
        if filelist["JSON-Files"]["parameters.json"] != "Missing!":
            # load json here and add it
            with open(os.path.join(session_dir, 'parameters.json'), 'r') as file:
                parameters_json = json.load(file)
                parameters_str = f'{parameters_json}'
                df_session_metadata['session_parameter'] = parameters_str
            # pass
        utils.merge_into_hdf5(L, session_dir, df_session_metadata, hdf5_key='session')
    
    # extract the trial package from the unity output hdf5 file
    if filelist["Data-Files"]["unity_output.hdf5"] != "Missing!":
        df_trialPackage = extract_trial_package(session_dir, df_session_metadata, 
                                                use_frame_for_trial_time=False)
        # process unity output and write to hdf5
        merge_unity_output_hdf5(L, session_dir, df_trialPackage)
    
    # merge_session_metadata_hdf5(L, session_dir, df_session_metadata)
    merge_camera_hdf5(L, session_dir, df_trialPackage, 'face')
    merge_camera_hdf5(L, session_dir, df_trialPackage, 'body')
    merge_camera_hdf5(L, session_dir, df_trialPackage, 'unity')
    merge_ball_velocity_hdf5(L, session_dir, df_trialPackage)
    merge_event_hdf5(L, session_dir, df_trialPackage)
    merge_trial_variable_hdf5(L, session_dir)

    L.logger.info(f"Data merged successfully for path: {session_dir} into 1 HDF5 file.")




if __name__ == "__main__":
    session_data2single_hdf5("/home/ntgroup/Project/data/2024-06-13_12-59-52_goodone_Thursday_1", [])
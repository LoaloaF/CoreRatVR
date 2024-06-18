import pandas as pd
import json
import os
from merge_session import merge_session_hdf5
from merge_unity_output import merge_unity_output_hdf5, extract_trial_package
from merge_camera import merge_camera_hdf5
from merge_portenta import merge_ball_velocity_hdf5, merge_event_hdf5
from merge_trial_variable import merge_trial_variable_hdf5
from merge_utils import *
from datetime import datetime
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..', '..')) # project dir

from CustomLogger import CustomLogger as Logger


def read_session_json_file(session_dir):

    session_folder_name = session_dir.split('/')[-1]  # get the last part of the path
    session_info = session_folder_name.split('_')  # split into time_time_sessionName


    session_json_path = os.path.join(session_dir, 'session_parameters.json')

    if not os.path.exists(session_json_path):
        raise FileNotFoundError(f"session_parameters.json file not found in {session_dir}")

    with open(session_json_path, 'r') as file:
        session_json = json.load(file)

    # convert the json into a dataframe
    df_session = pd.DataFrame([session_json])

    # convert the column names from camel case to snake case
    for each_column in df_session.columns:
        df_session.rename(columns={each_column: camel_to_snake(each_column)}, inplace=True)

    # add the session time, name, path, paradigm_id, and animal_id
    session_time_ori_format = datetime.strptime((session_info[0] + '_' + session_info[1]), "%Y-%m-%d_%H-%M-%S")
    session_time_reformat = session_time_ori_format.strftime("%Y-%m-%d %H:%M:%S")
    df_session['session_time'] = session_time_reformat
    df_session['session_name'] = session_info[2]
    df_session['session_path'] = session_dir


    return df_session   

def init_hdf5(L, session_dir):
    hdf5_fname = os.path.join(session_dir, 'behavior.hdf5')    
    
    with pd.HDFStore(hdf5_fname) as hdf:
        hdf.put('session', pd.DataFrame(), format='table', append=False)
        hdf.put('unity_frame', pd.DataFrame(), format='table', append=False)
        hdf.put('unity_trial', pd.DataFrame(), format='table', append=False)
        hdf.put('face_cam', pd.DataFrame(), format='table', append=False)
        hdf.put('body_cam', pd.DataFrame(), format='table', append=False)
        hdf.put('unity_cam', pd.DataFrame(), format='table', append=False)
        hdf.put('ball_velocity', pd.DataFrame(), format='table', append=False)
        hdf.put('event', pd.DataFrame(), format='table', append=False)
        hdf.put('trial_variable', pd.DataFrame(), format='table', append=False)



def merge_hdf5(L, session_dir):
    # all of this should be indepdant of the DB/ cursor  - unless there is a big mismatch 

    # read the session json file and convert it into a dataframe
    df_session = read_session_json_file(session_dir)
    # extract the trial package from the unity output hdf5 file
    df_trialPackage = extract_trial_package(session_dir, df_session, 
                                            use_frame_for_trial_time=False)
    
    merge_session_hdf5(L, session_dir, df_session)
    merge_unity_output_hdf5(L, session_dir, df_trialPackage)
    merge_camera_hdf5(L, session_dir, df_trialPackage, 'face')
    merge_camera_hdf5(L, session_dir, df_trialPackage, 'body')
    merge_camera_hdf5(L, session_dir, df_trialPackage, 'unity')
    merge_ball_velocity_hdf5(L, session_dir, df_trialPackage)
    merge_event_hdf5(L, session_dir, df_trialPackage)
    merge_trial_variable_hdf5(L, session_dir)

    L.logger.info(f"Data merged successfully for path: {session_dir} into 1 HDF5 file.")


def merge_main(session_dir):

    L = Logger()
    init_hdf5(L, session_dir)

    try:
        merge_hdf5(L, session_dir)
    except Exception as e:
        L.logger.error(f"Failed to merge data from: {session_dir} with error {e}")

            


if __name__ == "__main__":

    merge_main("/home/ntgroup/Project/data/2024-06-13_12-59-52_goodone_Thursday_1")
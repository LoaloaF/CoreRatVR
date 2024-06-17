import os
import pandas as pd
from add_utils import *

def add_unity_frame(L, cursor, conn, df_unity_frame, df_trialPackage):
    df_unity_frame.drop(columns=['N'], inplace=True)
    
    # add trial info into df
    df_unity_frame = add_trial_into_df(df_trialPackage, df_unity_frame)

    # rename columns to match the table
    df_unity_frame.rename(columns={"ID": "frame_id", 
                                   "PCT": "frame_timestamp", 
                                   "X": "x", "Z": "z", "A": "a", 
                                   "S": 's',"FB": "fb", 
                                   "BFP": "bfp", "BLP": 'blp'}, inplace=True)
    
    # add session info into df
    df_unity_frame = add_session_into_df(cursor, df_unity_frame)

    df_unity_frame.to_sql('unity_frame', conn, if_exists='append', index=False)
    L.logger.info("Unity frame added successfully.")


def generate_trial_package_from_frame(cursor, df_unity_frame, df_session):

    # extract the paradigm name from the session
    paradigm_id = df_session['paradigm_id'].values[0]
    cursor.execute(f"SELECT paradigm_name from paradigm WHERE paradigm_id={paradigm_id}")
    paradigm_name = cursor.fetchall()[0][0]
    start_state_id = -1

    # based on the paradigm name, set the start state id and inter trial state id
    # so we can extract the start and end frame of each trial
    if paradigm_name == 'P0000_AutoLickReward':
        start_state_id = -1
        inter_trial_state_id = -1
    elif paradigm_name == 'P0100_SpoutAssoc':
        start_state_id = 101
        inter_trial_state_id = 108
    elif paradigm_name == 'P0200_GoalDirectedMovement':
        start_state_id = 201
        inter_trial_state_id = 208
    else:
        raise ValueError(f"Paradigm {paradigm_name} is not supported.")
    
    # drop the inter trial state from the dataframe
    df_unity_frame.drop(df_unity_frame[df_unity_frame['S'] == inter_trial_state_id].index, 
                        inplace=True)
    df_unity_frame.reset_index(drop=True, inplace=True)

    # extract the start and end frame of each trial
    start_FID = df_unity_frame[df_unity_frame['S'] == start_state_id]['ID']

    # since we have removed the inter trial state, the end frame is one frame before 
    # the start frame of the next trial
    end_FID = df_unity_frame.loc[(start_FID[1:].index -1).to_list(), 'ID']

    if(len(start_FID) == len(end_FID) + 1):
        start_FID = start_FID[:-1]

    # extract the start and end frameID/timestamp of each trial
    start_FID = start_FID.reset_index(drop=True)
    start_PCT = df_unity_frame[df_unity_frame['ID'].isin(start_FID)]['PCT']
    start_PCT = start_PCT.reset_index(drop=True)
    end_FID = end_FID.reset_index(drop=True)
    end_PCT = df_unity_frame[df_unity_frame['ID'].isin(end_FID)]['PCT']
    end_PCT = end_PCT.reset_index(drop=True)

    df_trialPackage = pd.DataFrame({
        'trial_start_timestamp': start_PCT,
        'trial_start_frame': start_FID,
        'trial_end_timestamp': end_PCT,
        'trial_end_frame': end_FID
    })

    df_trialPackage.reset_index(inplace=True)
    df_trialPackage["index"] += 1  # let the trial id start from 1
    df_trialPackage.rename(columns={"index": "trial_id"}, inplace=True)  # rename the column
    df_trialPackage["trial_duration"] = df_trialPackage["trial_end_timestamp"] - df_trialPackage["trial_start_timestamp"]

    # if the session parameters do not have the maximum trial length, set it to 30s
    if 'maxium_trial_length' not in df_session.columns:
        maximum_trial_duration = 30
    else:
        maximum_trial_duration = df_session['maxium_trial_length'].values[0]
    
    # set the trial outcome based on the trial duration
    df_trialPackage.loc[df_trialPackage["trial_duration"] <  maximum_trial_duration * 10**6, "trial_outcome"] = 1
    df_trialPackage.loc[df_trialPackage["trial_duration"] >= maximum_trial_duration * 10**6, "trial_outcome"] = 0

    df_trialPackage["trial_outcome"] = df_trialPackage["trial_outcome"].astype(int)
    df_trialPackage = add_session_into_df(cursor, df_trialPackage)
    
    return df_trialPackage

def generate_trial_package_from_hdf5(cursor, unity_output_path):

    # read the trialPackage from the hdf5 file
    df_trialPackage = pd.read_hdf(unity_output_path, key='trialPackages')
    df_trialPackage = df_trialPackage.reset_index(drop=True)

    # only keep the columns we need in the trialPackage
    df_trialPackage = df_trialPackage[["ID", "SFID", "SPCT", "EFID", "EPCT", "TD", "O"]]

    # rename the columns
    df_trialPackage.rename(columns={"ID": "trial_id", 
                                    "SFID": "trial_start_frame", "SPCT": "trial_start_timestamp", 
                                    "EFID": "trial_end_frame", "EPCT": "trial_end_timestamp",
                                    "TD": "trial_duration", "O": "trial_outcome"}, inplace=True)

    df_trialPackage = add_session_into_df(cursor, df_trialPackage)

    return df_trialPackage


def extract_trial_package(cursor, folder_path, df_session, use_frame_for_trial_time):

    # read the dataframe of unity frames
    unity_output_path = os.path.join(folder_path, 'unity_output.hdf5')
    df_unity_frame = pd.read_hdf(unity_output_path, key='unityframes')
    df_unity_frame.reset_index(drop=True, inplace=True)
    df_unity_frame = df_unity_frame.reset_index(drop=True)

    # if the data in unity_output_path contains trialPackage, use it to generate the trial info
    # otherwise, use the frame data to generate the trial info 
    # Notice that for the 1st case, it should only applied to deprecated data (early version) and 
    # should be treated manually and carefully
    if use_frame_for_trial_time:
        df_trialPackage = generate_trial_package_from_frame(cursor, df_unity_frame, df_session)
    else:
        df_trialPackage = generate_trial_package_from_hdf5(cursor, unity_output_path)

    return df_trialPackage


def add_unity_output(L, conn, cursor, folder_path, df_trialPackage):

    unity_output_path = os.path.join(folder_path, 'unity_output.hdf5')

    df_unity_frame = pd.read_hdf(unity_output_path, key='unityframes')
    df_unity_frame.reset_index(drop=True, inplace=True)
    df_unity_frame = df_unity_frame.reset_index(drop=True)

    df_trialPackage.to_sql('unity_trial', conn, if_exists='append', index=False)
    L.logger.info("Unity trial added successfully.")

    add_unity_frame(L, cursor, conn, df_unity_frame, df_trialPackage)

    return df_trialPackage

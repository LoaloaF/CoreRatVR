from datetime import datetime
import os
import json
import pandas as pd
from CustomLogger import CustomLogger as Logger

def patch_metadata(session_metadata, session_dir):
    try:
        if 'animal' in session_metadata:
            session_metadata['animal_name'] = session_metadata.pop('animal')
        # if no animal information is found
        elif 'animal_name' not in session_metadata:
            session_metadata['animal_name'] = "rNA-NaN"
        session_metadata['animal_name'] = session_metadata['animal_name'].replace("_", "")
        
        if 'paradigm_name' not in session_metadata:
            session_metadata['paradigm_name'] = "PNaN-NaN"
            session_metadata['paradigm_id'] = -1
        
        if any([session_metadata.get(time_key) == None 
                for time_key in ('start_time', 'stop_time', 'duration')]):
            start_time, stop_time, duration = _infer_session_time(session_dir)   
            session_metadata['start_time'] = start_time
            session_metadata['stop_time'] = stop_time
            session_metadata['duration'] = duration

        return session_metadata
    
    except Exception as e:
        L = Logger()
        L.logger.error(L.fmtmsg(["Failed to patch incomplete metadata: ", str(e)]))
    return

def reorganize_metadata(session_metadata):
    session_metadata['metadata'] = {}

    separate_keys = ['session_name', 'paradigm_name', 'animal_name', 'start_time', 'stop_time', 
                     'duration', 'notes', 'rewardPostSoundDelay', 'rewardAmount', 'punishmentLength', 
                     'punishInactivationLength', 'interTrialIntervalLength', 'abortInterTrialIntervalLength',
                     'successSequenceLength', 'maxiumTrialLength', 'sessionDescription', 'configuration', 'metadata']

    for k in list(session_metadata.keys()):
        if k not in separate_keys:
            session_metadata['metadata'][k] = session_metadata.pop(k)

    session_metadata['metadata'] = json.dumps(session_metadata['metadata'])


    return pd.DataFrame(session_metadata, index=[0])

def _infer_session_time(session_dir):
    Logger().logger.debug(f"Inferring session time for {session_dir}")
    # infer session start and stop times from data files, try two
    from_fullfname = os.path.join(session_dir, 'unity_output.hdf5')
    if os.path.exists(from_fullfname) and os.path.getsize(from_fullfname) > 1e4:
        key = 'unityframes'
    else:
        from_fullfname = os.path.join(session_dir, 'portenta_output.hdf5')
        if os.path.exists(from_fullfname):
            key = 'ballvelocity'
        #TODO what if there is no ballvelocity

    Logger().logger.debug(f"Reading {from_fullfname} with key: {key}")
    
    # extract start and stop by readinf first and last rows
    first_row = pd.read_hdf(from_fullfname, key=key, start=0, stop=1)
    start_tstamps = first_row.iloc[0].loc["PCT"] / 10**6
    last_row = pd.read_hdf(from_fullfname, key=key, start=-1)
    stop_tstamps = last_row.iloc[0].loc["PCT"] / 10**6
    duration = stop_tstamps - start_tstamps
    
    # finally convert to str 
    start_tstamps = datetime.utcfromtimestamp(start_tstamps).strftime('%Y-%m-%d_%H-%M')
    stop_tstamps = datetime.utcfromtimestamp(stop_tstamps).strftime('%Y-%m-%d_%H-%M')
    duration = f"{int(duration / 60)}min"
    return start_tstamps, stop_tstamps, duration

def patch_paradigmVariable_data(paradigmVariable_trials_data):
    try:
        paradigmVariable_toDBnames_mapping_patch = {
            "PD": "pillar_distance",
            "PA": "pillar_angle",
            "MRN":"maximum_reward_number",
            'RN': "reward_number"
            # add more here
        }
        paradigmVariable_trials_data = paradigmVariable_trials_data.rename(columns=paradigmVariable_toDBnames_mapping_patch)
    except:
        Logger().logger.error("Failed to patch the paradigm-specific variables with "
                              "hardcoded mapping")

    if len(paradigmVariable_trials_data.columns) == 0:
        Logger().logger.error("No paradigm-specific variables found in the unity output file. Set it to None")
        paradigmVariable_trials_data = None  
    
    return paradigmVariable_trials_data


def patch_trial_packages(unity_trials_data_package, df_unity_frame, metadata):

    paradigm_name = metadata["paradigm_name"]

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
        if unity_trials_data_package is None:
            Logger().logger.error(f"Paradigm {paradigm_name} is not supported for trial package generation. And no trial package found.")
        else:
            return unity_trials_data_package
    
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
        'SPCT': start_PCT,
        'SFID': start_FID,
        'EPCT': end_PCT,
        'EFID': end_FID
    })

    df_trialPackage.reset_index(inplace=True)
    df_trialPackage["index"] += 1  # let the trial id start from 1
    df_trialPackage.rename(columns={"index": "ID"}, inplace=True)  # rename the column
    df_trialPackage["TD"] = df_trialPackage["EPCT"] - df_trialPackage["SPCT"]

    # if the session parameters do not have the maximum trial length, set it to 30s
    if 'maxiumTrialLength' not in metadata.keys():
        maximum_trial_duration = 30
    else:
        maximum_trial_duration = metadata['maxiumTrialLength']
    
    # set the trial outcome based on the trial duration
    df_trialPackage.loc[df_trialPackage["TD"] <  maximum_trial_duration * 10**6, "O"] = 1
    df_trialPackage.loc[df_trialPackage["TD"] >= maximum_trial_duration * 10**6, "O"] = 0

    df_trialPackage["O"] = df_trialPackage["O"].astype(int)
    
    if unity_trials_data_package is None:
        unity_trials_data = df_trialPackage
    elif len(unity_trials_data_package) != len(df_trialPackage):
        Logger().logger.error("Mismatch in number of trial packages and unityframe trials.")
        if len(unity_trials_data_package) >= len(df_trialPackage):
            unity_trials_data = unity_trials_data_package
        else:
            unity_trials_data = df_trialPackage
    else:
        unity_trials_data = unity_trials_data_package

    return unity_trials_data
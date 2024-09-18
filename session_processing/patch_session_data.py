import os
import sys
import h5py
import json
import pandas as pd
from CustomLogger import CustomLogger as Logger

def patch_metadata(session_metadata, session_dir):
    L = Logger()
    L.logger.info("Patching to patch metadata...")
    
    if "animal_name" not in session_metadata and 'animal' in session_metadata:
        session_metadata['animal_name'] = session_metadata.pop('animal')
    
    if 'animal_name' not in session_metadata:
        L.logger.error("Required metadata key animal_name missing.")
        raise ValueError("Required metadata key missing.")
    if 'paradigm_name' not in session_metadata:
        L.logger.error("Required metadata key paradigm_name missing.")
        raise ValueError("Required metadata key missing.")

    if "paradigm_id" not in session_metadata:
        paradigm_id = int(session_metadata["paradigm_name"][1:5])
        session_metadata["paradigm_id"] = paradigm_id
    
    # newest sessions have start, stop and duretion, older ones have none of these
    # infer start time from name, and set durutation to "min" to construct session_name
    if session_dir.endswith("/"):
        session_dir = session_dir[:-1]
    start_time_patch = os.path.split(session_dir)[1][:16]
    
    L.logger.info(f"Start time patched to {start_time_patch}")
    session_metadata['animal_name'] = session_metadata['animal_name'].replace("_", "")
    session_metadata['start_time'] = session_metadata.get('start_time', start_time_patch)
    session_metadata['duration'] = session_metadata.get('duration', "min")


    # convert JSON array list-like arguments to lists or floats or str
    for key, value in session_metadata.items():
        if (isinstance(value, str) and key != 'configuration'
            and len(list_like := value.split(",")) > 1):
            # floats or integers
            try:
                session_metadata[key] = list(map(float, list_like))
            except:
                session_metadata[key] = list_like # leave as str
    
    return session_metadata

def patch_paradigmVariable_data(paradigmVariable_trials_data):
    L = Logger()
    try:
        paradigmVariable_toDBnames_mapping_patch = {
            "PD": "pillar_distance",
            "PA": "pillar_angle",
            "MRN":"maximum_reward_number", # set at trial start
            "RN": "reward_number", # like an outcome
            "MT": "movement_time", # time required to move to straight move,
            "ST": "stay_time", # time required to stay in the reward zone,
            "MTH": "movement_threshold", # threshold to detect movement
            "STH": "stay_threshold", # threshold to detect stay
            "SSTH": "stay_stop_threshold", # threshold to detect stay stop
            "R": "raw", # raw movement enabled
            "Y": "yaw", # yaw movement enabled
            "P": "pitch", # pitch movement enabled
            "C": "cue", # cue number
            "LR": "lick_reward", # lick reward
            # add more here
        }
        paradigmVariable_trials_data = paradigmVariable_trials_data.rename(columns=paradigmVariable_toDBnames_mapping_patch)
    except:
        L.logger.error("Failed to patch the paradigm-specific variables with "
                              "hardcoded mapping")

    if len(paradigmVariable_trials_data.columns) == 0:
        L.logger.error("No paradigm-specific variables found in the unity output file. Set it to None")
        paradigmVariable_trials_data = None  
    
    L.logger.info("Paradigm variables patched as \n" + str(paradigmVariable_trials_data))
    return paradigmVariable_trials_data


def patch_trial_packages(unity_trials_data_package, df_unity_frame, metadata):
    Logger().logger.info("Attempting to patch trial packages...")
    paradigm_name = metadata["paradigm_name"]

    start_state_id = -1

    # based on the paradigm name, set the start state id and inter trial state id
    # so we can extract the start and end frame of each trial
    if paradigm_name == 'P0000_AutoLickReward':
        return unity_trials_data_package
    # elif paradigm_name == 'P0100_SpoutAssoc':
    #     start_state_id = 101
    #     inter_trial_state_id = 108
    elif paradigm_name == 'P0200_GoalDirectedMovement':
        start_state_id = 201
        inter_trial_state_id = 208
    else:
        if unity_trials_data_package is None:
            Logger().logger.error(f"Paradigm {paradigm_name} is not supported "
                                  "for trial package generation. And no trial "
                                  "package found.")
        else:
            Logger().logger.info("Data is ok, didn't even need patching.")
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

def convert_hdf5_fixed_to_table(session_fullfname, dummyrun=True, final_cleanup=False):
    # count how often the string _fixed is in the filename
    n_fixed = session_fullfname.count("_fixed")
    n_old = session_fullfname.count("_old")
    s = os.path.getsize(session_fullfname) / 1e6
    print(session_fullfname)
    print(n_fixed, n_old, s)
       
    
    idx = session_fullfname.rfind("_")
    session_fixed_fullfname = session_fullfname[:idx] + "_fixed" + session_fullfname[idx:]
    session_fixed_fullfname = session_fixed_fullfname.replace("/behavior_", "/")

    session_old_fullfname = session_fullfname[:idx] + "_old" + session_fullfname[idx:]
    print("Fixing:")
    print(os.path.basename(session_fullfname))
    print("->")
    print(os.path.basename(session_fixed_fullfname))
    
    # if os.path.basename(session_fullfname) != "2024-08-22_15-11_rYL008_P0800_LinearTrack_18min.hdf5":
    #     return

    if final_cleanup:
        print("Final cleanup")
        if "_old" in session_fullfname:
            # treat with care, maybe use send2trash?
            # os.remove(session_fullfname)
            return
        elif "_fixed" in session_fullfname:
            session_fixed_fullfname_rename = session_fixed_fullfname.replace("_fixed", "")
            os.rename(session_fixed_fullfname, session_fixed_fullfname_rename)
            return
        else:
            print("No cleanup needed")
    
    # print(f"Fixing {session_fullfname}\nNew name:\n{session_fixed_fullfname}")
    # Open the input HDF5 file
    try:
        with pd.HDFStore(session_fullfname, 'r') as source_pd_store:
            keys = source_pd_store.keys()  # Get all keys in the HDF5 file
            print(f"Keys in {session_fullfname}: {keys}")
            
            # Create a new HDF5 file to save the converted data
            with pd.HDFStore(session_fixed_fullfname, 'w') as new_pd_store:
                for key in keys:
                    # Get the storer for each key and check if it's in Fixed format
                    storer = source_pd_store.get_storer(key)
                    if not storer.is_table:
                        print(f"Converting Fixed format dataset '{key}' to Table format.")
                        
                        # Read the entire Fixed format dataset
                        data = source_pd_store[key]
                        
                        # fix metadata
                        if key == '/metadata':
                            # Ensure each element in 'notes' is a string
                            if 'notes' in data.columns:
                                data["notes"] = data["notes"].apply(lambda x: " ".join(x) if isinstance(x, list) else str(x))
                            
                            # split the metadata into two parts
                            nested_metadata = json.loads(data['metadata'].item())
                            data.drop(columns=['metadata'], inplace=True)
                            
                            pillar_keys = ["pillars","pillar_details","envX_size",
                                            "envY_size", "base_length","wallzone_size",
                                            "wallzone_collider_size",]
                            pillar_metadata = {k: nested_metadata.get(k) for k in pillar_keys}
                            fsm_keys = ["paradigms_states", "paradigms_transitions", 
                                        "paradigms_decisions", "paradigms_actions"]
                            fsm_metadata = {k: nested_metadata.get(k) for k in fsm_keys}
                            log_file_content = nested_metadata.get("log_files")
                            
                            data['env_metadata'] = [json.dumps(pillar_metadata)]
                            data['fsm_metadata'] = [json.dumps(fsm_metadata)]
                            data['log_file_content'] = [json.dumps(log_file_content)]

                        if not dummyrun:
                            # Write it to the new store in Table format
                            new_pd_store.put(key, data, format='table')
                    else:
                        print(f"'{key}' is already in Table format, copying as is.")
                        # If already Table format, just copy it over
                        if not dummyrun:
                            new_pd_store.put(key, new_pd_store[key], format='table')
                            
        # copy the camera data into the behavior file
        with h5py.File(session_fixed_fullfname, 'a') as output_file:
            with h5py.File(session_fullfname, 'r') as source_file:
                if "facecam_frames" in source_file.keys():
                    if not dummyrun:
                        source_file.copy(source_file["facecam_frames"], output_file, name="facecam_frames")
                    print("Facecam copied")
                if "bodycam_frames" in source_file.keys():
                    if not dummyrun:
                        source_file.copy(source_file["bodycam_frames"], output_file, name="bodycam_frames")
                    print("Bodycam copied")
                if "unitycam_frames" in source_file.keys():
                    if not dummyrun:
                        source_file.copy(source_file["unitycam_frames"], output_file, name="unitycam_frames")
                    print("Unitycam copied")
        print(f"Conversion complete! New HDF5 file saved as: {session_fixed_fullfname}")

        session_fullfname_rename = session_fullfname[:idx] + "_old" + session_fullfname[idx:]
        if not dummyrun:
            os.rename(session_fullfname, session_fullfname_rename)
        print(f"Old file renamed to {session_fullfname_rename}")
    
    except Exception as e:
        print(f"Error: {e} with {session_fullfname}")
        return 
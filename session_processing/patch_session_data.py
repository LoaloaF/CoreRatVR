from datetime import datetime
import os

import pandas as pd
from CustomLogger import CustomLogger as Logger

def patch_metadata(session_metadata, session_dir):
    try:
        # should we print the metadata here? - now no, we print it in load_session_metadata
        # print(session_metadata)
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
            # add more here
        }
        return paradigmVariable_trials_data.rename(columns=paradigmVariable_toDBnames_mapping_patch)
    except:
        Logger().logger.error("Failed to patch the paradigm-specific variables with "
                              "hardcoded mapping")
    return 


import os
import numpy as np
import pandas as pd
import h5py
import json

from CustomLogger import CustomLogger as Logger
from patch_session_data import patch_paradigmVariable_data
from patch_session_data import patch_metadata
from patch_session_data import patch_trial_packages

def load_session_metadata(session_dir, dbNames):
    L = Logger()
    
    # read the session json file (excel metadata)
    session_metadata = {}
    metadata_fullfname = os.path.join(session_dir, "session_parameters.json")
    if not os.path.exists(metadata_fullfname):
        L.logger.error("Session JSON file not found.")
        return
    else:
        with open(metadata_fullfname, 'r') as file:
            session_metadata = json.load(file)
            L.logger.debug(L.fmtmsg(["Found metadata JSON: ", session_metadata]))
    
    parameters_fullfname = os.path.join(session_dir, 'parameters.json')
    if os.path.exists(parameters_fullfname):
        with open(parameters_fullfname, 'r') as file:
            session_metadata['configuration'] = file.read()


    # patch the metadata with missing keys if possible/needed
    session_metadata = patch_metadata(session_metadata, session_dir)
    if session_metadata is None:
        return
    
    # this key is supposed to be constructed only in postprocessing
    name = (f'{session_metadata["start_time"]}_{session_metadata["animal_name"]}_'
            f'{session_metadata["paradigm_name"]:04}_{session_metadata["duration"]}')
    session_metadata['session_name'] = name
    
    # remove explicit keys from metadata and add them to metadata field
    # session_metadata['metadata'] = {}
    # [session_metadata['metadata'].update({k:session_metadata.pop(k)}) 
    #                               for k in list(session_metadata.keys()) if k not in dbNames]
    
    # rename a problematic key (typo)
    if "paradigms_transitions " in session_metadata:
        session_metadata["paradigms_transitions"] = session_metadata.pop("paradigms_transitions ")
     
    env_metadata = {k: session_metadata[k] for k in dbNames['env_metadata']}
    fsm_metadata = {k: session_metadata[k] for k in dbNames['fsm_metadata']}
    log_file_content = {}
    # Add log files to metadata
    for filename in os.listdir(session_dir):
        if filename.endswith('.log'):
            with open(os.path.join(session_dir, filename), 'r') as file:
                log_file_content[filename] = file.read()

    # convert to json 
    session_metadata['env_metadata'] = json.dumps(env_metadata, indent=2)
    session_metadata['fsm_metadata'] = json.dumps(fsm_metadata, indent=2)
    session_metadata['log_file_content'] = json.dumps(log_file_content, indent=2)
    # session_metadata['metadata'] = json.dumps(session_metadata['metadata'], indent=2)
    L.logger.debug(L.fmtmsg(["Metadata patched: ", session_metadata]))

    # simplify the log message, don't print deeply nested values
    metadata_to_print = session_metadata.copy()
    metadata_to_print['configuration'] = f"{metadata_to_print['configuration'][:50]}..."
    metadata_to_print['env_metadata'] = f"{metadata_to_print['env_metadata'][:50]}..."
    metadata_to_print['fsm_metadata'] = f"{metadata_to_print['fsm_metadata'][:50]}..."
    metadata_to_print.pop('log_file_content')
    L.logger.info(L.fmtmsg(["Metadata: ", metadata_to_print]))

    return session_metadata

def load_unity_frames_data(session_dir, toDBnames_mapping):
    unity_frame_data = _read_hdf5_data(session_dir, 'unity_output.hdf5', 'unityframes')
    unity_frame_data = _rename_columns('unity_frames', unity_frame_data, toDBnames_mapping)
    return unity_frame_data

def load_unity_trials_data(session_dir, metadata, toDBnames_mapping):
    unity_trials_data_package = _read_hdf5_data(session_dir, 'unity_output.hdf5', 'trialPackages')
    
    # TODO depr/ delte this once not needed anymore
    unity_frame_data = _read_hdf5_data(session_dir, 'unity_output.hdf5', 'unityframes')
    if unity_frame_data is None:
        raise Exception("Failed to read unityframes data.")
    unity_trials_data = patch_trial_packages(unity_trials_data_package, unity_frame_data, metadata)


    paradigmVariable_data = _handle_paradigm_specific_variables(unity_trials_data, 
                                                                toDBnames_mapping, 
                                                                metadata)
    unity_trials_data = _rename_columns('unity_trial', unity_trials_data, toDBnames_mapping)
    return unity_trials_data, paradigmVariable_data

def load_camera_data(session_dir, camera_fname, toDBnames_mapping):
    frame_packages = _read_hdf5_data(session_dir, camera_fname, 'frame_packages')
    frame_packages = _rename_columns(camera_fname, frame_packages, toDBnames_mapping)
    return frame_packages

def load_ballvelocity_data(session_dir, toDBnames_mapping):
    bv_data = _read_hdf5_data(session_dir, 'portenta_output.hdf5', 'ballvelocity')
    bv_data = _rename_columns('ball_velocity', bv_data, toDBnames_mapping)
    return bv_data

def load_portenta_event_data(session_dir, toDBnames_mapping):
    portenta_event_data = _read_hdf5_data(session_dir, 'portenta_output.hdf5', 
                                          'portentaoutput', drop_N_column=False)
    portenta_event_data = _rename_columns('portenta_event', portenta_event_data, toDBnames_mapping)
    return portenta_event_data

def _read_hdf5_data(session_dir, fname, key, drop_N_column=True):
    L = Logger()
    fullfname = os.path.join(session_dir, fname)
    if not os.path.exists(fullfname):
        L.logger.error(f"Cannot find {fullfname}")
        return
    
    with h5py.File(fullfname, 'r') as f:
        if key not in f.keys():
            L.logger.error(f"Failed to find {key} key in {fname}, trying with "
                           f"'packages' key...")
            if (key := 'packages') not in f.keys():
                L.logger.error(f"Failed to find {key} key in {fname}.")
            return
    try:
        data = pd.read_hdf(fullfname, key=key)
    except Exception as e:
        L.logger.error(f"Found the key {key} but failed to read the key {key} "
                       f"from {fullfname}.\n{e}")
        return
        
    data.reset_index(drop=True, inplace=True)
    if drop_N_column:
        data.drop(columns=['N'], inplace=True, errors='ignore')
    return data

def _insert_columns(data, new_columns):
    for col in new_columns:
        data[col] = np.nan
    return data

def _rename_columns(data_type, data, toDBnames_mapping):
    L = Logger()
    
    if data is None:
        L.logger.error(f"{data_type} is None. Cannot rename columns.")
        return

    new_columns = [toDBnames_mapping.pop(k) for k in list(toDBnames_mapping) 
                   if k.startswith("INSERT")]
    data = _insert_columns(data, new_columns)

    if any([k not in data.columns for k in toDBnames_mapping.keys()]):
        msg = ("Failed to find all expected columns:", toDBnames_mapping.keys(),
               "in data:", data.columns)
        L.logger.error(L.fmtmsg(msg))
        return
    
    msg = f"Slicing data columns", data.columns, "and renaming them using", toDBnames_mapping
    L.logger.debug(L.fmtmsg(msg))
    data = data[list(toDBnames_mapping.keys()) + new_columns].copy()
    data.rename(columns=toDBnames_mapping, inplace=True)
    return data

def _handle_paradigm_specific_variables(unity_trials_data, frames_toDBnames_mapping, 
                                        metadata):
    L = Logger()
    # drop_cols = [k for k in unity_trials_data.columns 
    #              if not (k.startswith("INSERT") or k == "ID")]
    drop_cols = ['SFID', 'SPCT', 'EFID', 'EPCT', 'TD', 'O']
    paradigmVariable_trials_data = unity_trials_data.drop(columns=drop_cols)
    paradigmVariable_trials_data.rename(columns={'ID': 'trial_id'}, inplace=True)
    
    # rename the columns to match DB format, using metadata if available
    try:
        trialVariables = json.loads(metadata.get('metadata')).get('trialPackageVariables')
        trialVariables_full_names = json.loads(metadata.get('metadata')).get('trialPackageVariablesFullNames')
        paradigmVariable_toDBnames_mapping = dict(zip(trialVariables, trialVariables_full_names))
        paradigmVariable_trials_data.rename(columns=paradigmVariable_toDBnames_mapping, 
                                             inplace=True)
        return paradigmVariable_trials_data
    except:
        L.logger.warning(L.fmtmsg(("Failed to find the paradigm-specific variables in metadata/excel. ",
                                   "Using hardcoded mapping instead.")))
        return patch_paradigmVariable_data(paradigmVariable_trials_data)

#add trialPackageVariablesFulllNames to excel sheet schema
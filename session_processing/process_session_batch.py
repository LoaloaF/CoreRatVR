import shutil
import traceback
import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..'))

import argparse
# from send2trash import send2trash
import pandas as pd
import h5py
from CustomLogger import CustomLogger as Logger
import json
from session_processing.db.session2db import *
from check_session_files import check_file_existence
from check_session_files import check_log_files
from load_session_data import load_session_metadata
from load_session_data import load_unity_frames_data
from load_session_data import load_unity_trials_data
from load_session_data import load_camera_data
from load_session_data import load_ballvelocity_data
from load_session_data import load_portenta_event_data
from polish_session_data import insert_trial_id
from polish_session_data import add_ephys_timestamps
from polish_session_data import hdf5_frames2mp4


def patch_metadata(fname):
    L = Logger()
    idx = fname.rfind("_")
    session_fixed_fullfname = fname[:idx] + "_fixed" + fname[idx:]
    session_fixed_fullfname = session_fixed_fullfname.replace("/behavior_", "/")
    session_fixed_fullfname = session_fixed_fullfname.replace(".xlsx", "")

    session_old_fullfname = fname[:idx] + "_old" + fname[idx:]
    L.logger.info("Fixing:")
    L.logger.info(os.path.basename(fname))
    L.logger.info("->")
    L.logger.info(os.path.basename(session_fixed_fullfname))
    
    
    try:
        with pd.HDFStore(fname, 'r') as source_pd_store:
            keys = source_pd_store.keys()  # Get all keys in the HDF5 file
            L.logger.info(f"Keys in {fname}: {keys}")
            
            # Create a new HDF5 file to save the converted data
            with pd.HDFStore(session_fixed_fullfname, 'w') as new_pd_store:
                for key in keys:
                    # Get the storer for each key and check if it's in Fixed format
                    storer = source_pd_store.get_storer(key)
                    if not storer.is_table:
                        L.logger.info(f"Converting Fixed format dataset '{key}' to Table format.")
                        
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
                            
                            log_file_content = {}
                            log_keys = [key for key in list(nested_metadata.keys()) if key.endswith('.log')]
                            for log_key in log_keys:
                                log_file_content[log_key] = nested_metadata[log_key]
                            log_file_content = str(log_file_content)
                            
                            data['env_metadata'] = [json.dumps(pillar_metadata)]
                            data['fsm_metadata'] = [json.dumps(fsm_metadata)]
                            # data['log_file_content'] = [json.dumps(log_file_content)]

                        new_pd_store.put(key, data, format='table')
                    else:
                        L.logger.info(f"'{key}' is already in Table format, copying as is.")
                        new_pd_store.put(key, new_pd_store[key], format='table')
                            
        # copy the camera data into the behavior file
        with h5py.File(session_fixed_fullfname, 'a') as output_file:
            if log_file_content is not None:
                output_file.create_dataset("log_file_content", data=log_file_content)
                L.logger.info("Log file content copied")
                
            with h5py.File(fname, 'r') as source_file:
                if "facecam_frames" in source_file.keys():
                    source_file.copy(source_file["facecam_frames"], output_file, name="facecam_frames")
                    L.logger.info("Facecam copied")
                if "bodycam_frames" in source_file.keys():
                    source_file.copy(source_file["bodycam_frames"], output_file, name="bodycam_frames")
                    L.logger.info("Bodycam copied")
                if "unitycam_frames" in source_file.keys():
                    source_file.copy(source_file["unitycam_frames"], output_file, name="unitycam_frames")
                    L.logger.info("Unitycam copied")
        L.logger.info(f"Conversion complete! New HDF5 file saved as: {session_fixed_fullfname}")

        session_fullfname_rename = fname[:idx] + "_old" + fname[idx:]
        os.rename(fname, session_fullfname_rename)
        L.logger.info(f"Old file renamed to {session_fullfname_rename}")

        session_fixed_fullfname_new = session_fixed_fullfname.replace("_fixed", "")
        os.rename(session_fixed_fullfname, session_fixed_fullfname_new)
        L.logger.info(f"Fixed file renamed to {session_fixed_fullfname_new}")
        
    except Exception as e:
        L.logger.error(f"Error: {e} with {fname}")
        return 



def _handle_logs(session_dir):
    fnames = os.listdir(session_dir)

    _, format_filelist_str = check_file_existence(session_dir, fnames.copy())
    L.logger.info(L.fmtmsg(format_filelist_str))
    logs_result = check_log_files(session_dir, [fn for fn in fnames if fn.endswith(".log")])
    L.logger.info(L.fmtmsg(logs_result))

def _handle_data(session_dir):
    L = Logger()
    L.logger.info(f"Loading metadata...")
    # first 4 keys are required
    dbNames = {"metadata": ['session_name', 'paradigm_name', 'animal_name', 'paradigm_id',
                            'start_time', 'stop_time', 'duration', 'notes', 'rewardPostSoundDelay', 
                            'rewardAmount', 'punishmentLength', 'punishInactivationLength', 
                            'interTrialIntervalLength', 'abortInterTrialIntervalLength',
                            'successSequenceLength', 'maxiumTrialLength', 'sessionDescription',
                            'configuration'],
               "env_metadata": ["pillars","pillar_details","envX_size",
                                "envY_size", "base_length","wallzone_size",
                                "wallzone_collider_size"],
               "fsm_metadata": ["paradigms_states", "paradigms_transitions", 
                                "paradigms_decisions", "paradigms_actions"],
               "log_files": []} # add whatever log files are present
    metadata = load_session_metadata(session_dir, dbNames)
    
    
    L.logger.info(f"Loading unity data...")
    toDBnames_mapping = {"ID": "trial_id", 
                         "INSERT1": "trial_start_ephys_timestamp",
                         "INSERT2": "trial_end_ephys_timestamp",
                         "SFID": "trial_start_frame", 
                         "SPCT": "trial_start_pc_timestamp", 
                         "EFID": "trial_end_frame", 
                         "EPCT": "trial_end_pc_timestamp",
                         "TD": "trial_pc_duration", 
                         "O": "trial_outcome"}
    # paradigmVariable_data has keys [ID, *metadata.fullParadgmVariableNames]
    unity_trials_data, paradigmVariable_data = load_unity_trials_data(session_dir, 
                                                                      metadata, 
                                                                      toDBnames_mapping)
    # load the unity frames and trials data
    toDBnames_mapping = {"ID": "frame_id", 
                         "PCT": "frame_pc_timestamp", 
                         "INSERT1": "frame_ephys_timestamp",
                         "INSERT2": "trial_id",
                         "X": "frame_x_position", 
                         "Z": "frame_z_position", 
                         "A": "frame_angle", 
                         "S": 'frame_state',
                         "FB": "frame_blinker", 
                         "BFP": "ballvelocity_first_package", 
                         "BLP": 'ballvelocity_last_package'}
    unity_frames_data = load_unity_frames_data(session_dir, toDBnames_mapping)
    
    L.logger.info(f"Loading portenta data...")
    # load portenta ballvelocity and event data
    toDBnames_mapping = {"ID": "ballvelocity_package_id", 
                         "T": "ballvelocity_portenta_timestamp", 
                         "PCT": "ballvelocity_pc_timestamp", 
                         "INSERT1": "ballvelocity_ephys_timestamp",
                         "INSERT2": "trial_id",
                         "Vr": "ballvelocity_raw", 
                         "Vy": "ballvelocity_yaw", 
                         "Vp":"ballvelocity_pitch"}
    # do all keys need the ball velocity prefix in DB?
    ballvel_data = load_ballvelocity_data(session_dir, toDBnames_mapping)
    toDBnames_mapping = {"ID": "event_package_id", 
                         "T": "event_portenta_timestamp", 
                         "PCT": "event_pc_timestamp", 
                         "INSERT1": "event_ephys_timestamp",
                         "INSERT2": "trial_id",
                         "V": "event_value", 
                         "N": "event_name"}
    event_data = load_portenta_event_data(session_dir, toDBnames_mapping)
    
    
    L.logger.info(f"Loading camera data...")
    # load the camera data
    toDBnames_mapping = {"ID": f"facecam_image_id", 
                         "PCT": f"facecam_image_pc_timestamp",
                         "INSERT1": "facecam_image_ephys_timestamp",
                         "INSERT2": "trial_id",}
    facecam_packages = load_camera_data(session_dir, 'facecam.hdf5', 
                                        toDBnames_mapping)
    toDBnames_mapping = {"ID": f"bodycam_image_id", 
                         "PCT": f"bodycam_image_pc_timestamp",
                         "INSERT1": "trial_id",}
    bodycam_packages = load_camera_data(session_dir, 'bodycam.hdf5', 
                                        toDBnames_mapping)
    toDBnames_mapping = {"ID": f"unitycam_image_id", 
                         "PCT": f"unitycam_image_pc_timestamp",
                         "INSERT1": "unitycam_image_ephys_timestamp",
                         "INSERT2": "trial_id",}
    unitycam_packages = load_camera_data(session_dir, 'unitycam.hdf5', 
                                         toDBnames_mapping)
    
    return (metadata, unity_trials_data, paradigmVariable_data, unity_frames_data,
            ballvel_data, event_data, facecam_packages, bodycam_packages,  
            unitycam_packages)

def _save_merged_hdf5_data(session_dir, fname, metadata, unity_trials_data, 
                           unity_frames_data, paradigmVariable_data, 
                           facecam_packages, bodycam_packages, 
                           unitycam_packages, ballvel_data, event_data):
    L.logger.info(f"Merging data into one hdf5 file: {fname}")
    full_fname = os.path.join(session_dir, fname)
    if os.path.exists(full_fname):
        L.logger.error(f"File {full_fname} already exists!")
        raise Exception(f"File {full_fname} already exists!")
        return
    
    metadata = {key: str(value) for key, value in metadata.items()}
    log_file_content = metadata.pop("log_file_content", None)
    
    with pd.HDFStore(full_fname, 'w') as store:
        L.logger.info(f"Merging metadata {metadata}...")
        store.put('metadata', pd.DataFrame([metadata], index=[0]), format='table')
    
        L.logger.info(f"Merging unity data...")
        store.put('unity_trial', unity_trials_data, format='table')
        store.put('unity_frame', unity_frames_data, format='table')
        if paradigmVariable_data is not None:
            store.put('paradigm_variable', paradigmVariable_data, format='table')

        L.logger.info(f"Merging portenta data...")
        if ballvel_data is not None:
            store.put('ballvelocity', ballvel_data, format='table')
        if event_data is not None:
            store.put('event', event_data, format='table')
        
        if facecam_packages is not None:
            store.put('facecam_packages', facecam_packages, format='table')    
        if bodycam_packages is not None:
            store.put('bodycam_packages', bodycam_packages, format='table')
        if unitycam_packages is not None:
            store.put('unitycam_packages', unitycam_packages, format='table')

    # copy the camera data into the behavior file
    with h5py.File(full_fname, 'a') as output_file:
        L.logger.info(f"Merging log file data...")
        output_file.create_dataset("log_file_content", data=log_file_content)
        
        L.logger.info(f"Merging facecam data...")
        if os.path.exists(os.path.join(session_dir, 'facecam.hdf5')):
            with h5py.File(os.path.join(session_dir, 'facecam.hdf5'), 'r') as source_file:
                source_file.copy(source_file["frames"], output_file, name="facecam_frames")
        else:
            L.logger.warning(f"Failed to find facecam data in {session_dir}")
        
        L.logger.info(f"Merging bodycam data...")
        if os.path.exists(os.path.join(session_dir, 'bodycam.hdf5')):
            with h5py.File(os.path.join(session_dir, 'bodycam.hdf5'), 'r') as source_file:
                source_file.copy(source_file["frames"], output_file, name="bodycam_frames")
        else:
            L.logger.warning(f"Failed to find bodycam data in {session_dir}")

        L.logger.info(f"Merging unitycam data...")

        if os.path.exists(os.path.join(session_dir, 'unitycam.hdf5')):
            with h5py.File(os.path.join(session_dir, 'unitycam.hdf5'), 'r') as source_file:
                source_file.copy(source_file["frames"], output_file, name="unitycam_frames")
        else:
            L.logger.warning(f"Failed to find unitycam data in {session_dir}")
    L.logger.info(f"Sucessfully merged and saved data to {full_fname}")

def _handle_ephys_integration(nas_dir, session_dir, unity_trials_data,
                              unity_frames_data, ballvel_data, event_data,
                              facecam_packages, unitycam_packages):
    # TODO
    # read the ephys file bits field
    # integrate with behavior data with extensive alignment chacking
    ephys_fname = [f for f in os.listdir(os.path.join(nas_dir, session_dir)) 
                if f.endswith(".raw.h5") and 'ephys' in f]
    if len(ephys_fname) != 1:
        L.logger.error(f"Failed to find ephys recording file in {nas_dir}/{session_dir}")
        return
    ephys_fname = ephys_fname[0]
    ephys_fullfname = os.path.join(nas_dir, session_dir, ephys_fname)
    # inplace insertation of ephys timestamps into all dataframes

    add_ephys_timestamps(ephys_fullfname, unity_trials_data, unity_frames_data,
                         ballvel_data, event_data, facecam_packages, unitycam_packages)
    
def _handle_move2nas(session_dir, nas_dir, merged_fname, animal, paradigm):
    L.logger.info(f"Copying files to the NAS")
    try:
        # create the dir on the NAS
        nas_dir_animal = os.path.join(nas_dir, f"RUN_{animal}")
        if not os.path.exists(nas_dir_animal):
            os.mkdir(nas_dir_animal)
            L.logger.info(f"Created directory {nas_dir_animal}")
        nas_dir_animal_paradigm = os.path.join(nas_dir_animal, f"{animal}_{paradigm[:5]}")
        # see if the paradigm dir exists
        if not os.path.exists(nas_dir_animal_paradigm):
            os.mkdir(nas_dir_animal_paradigm)
            L.logger.info(f"Created directory {nas_dir_animal_paradigm}")
        
        
        L.logger.info(f"Directory {nas_dir_animal_paradigm}")
        
        full_nas_dir = os.path.join(nas_dir_animal_paradigm, merged_fname[:-5])
        os.mkdir(full_nas_dir)
        L.logger.info(f"Created directory {full_nas_dir}")
        
        # copy only these selected files to NAS (merged file, log files, bodycam video)
        fnames = [fname for fname in os.listdir(session_dir) 
                if fname.endswith(".log") or fname in (merged_fname, "bodycam.mp4")]
        for fn in fnames:
            src = os.path.join(session_dir, fn)
            if os.path.exists(src):
                if fn == merged_fname:
                    L.logger.info(f"Copying {fn} ({os.path.getsize(src)/(1024**3):.1}GB)"
                                f" to NAS...")
                dst = os.path.join(full_nas_dir, fn)
                shutil.copyfile(src, dst)
    except Exception as e:
        L.logger.error(f"Failed to copy files to NAS: {e}")
        return
    
# def _handle_rename_nas_session_dirs(session_dir, nas_dir, new_dir_name):
#     print(nas_dir, session_dir, new_dir_name)
#     L.logger.info(f"Renaming session directory on NAS")
#     # old_dir_name = os.path.basename(session_dir)
#     # nas_session_dir = os.path.join(nas_dir, new_dir_name)
#     # TODO os.rename doesn't work for non-empty folders?
#     # os.rename(os.path.join(nas_dir, old_dir_name), nas_session_dir)
#     os.rename(session_dir, (os.path.join(os.path.split(session_dir[:-1])[0], new_dir_name)))
#     return session_dir

def process_session(session_dir, nas_dir, prompt_user_decision, integrate_ephys, 
                    copy_to_nas, write_to_db, database_location, database_name,
                    render_videos):
    L = Logger()
    L.logger.info(f"Processing session {session_dir}")
    
    if ".xlsx" in session_dir:
        session_dir_new = session_dir.replace(".xlsx", "")
        os.rename(session_dir, session_dir_new)
        session_dir = session_dir_new
    
    if prompt_user_decision:
        answer = input("\nSkip this session? [y/n]: ")
        if answer.lower() == 'y':
            return

    # check if files exsist and if .log files have warnings or erros
    _handle_logs(session_dir)

    # load the metadata, unity, camera, ballvelocity and event data
    try:
        data = _handle_data(session_dir)
    except Exception as e:
        L.logger.error(traceback.format_exc())  # Log the detailed stack trace
        L.spacer()
        L.logger.error(f"Failed to load data, check logs for details.\n{e}")

        if prompt_user_decision:
            answer = input("\nPermanently delete session? [y/n]: ")
            if answer.lower() == 'y':
                shutil.rmtree(session_dir)
                L.logger.info(f"Session {session_dir} deleted")
        return
    
    
    (metadata, unity_trials_data, paradigmVariable_data, unity_frames_data,
    ballvel_data, event_data, facecam_packages, bodycam_packages,  
    unitycam_packages) = data
    L.spacer()
    L.logger.info(f"{metadata['session_name']}\nData loaded without Exceptions! ")
    L.spacer()
    
    if integrate_ephys:
        _handle_ephys_integration(nas_dir, session_dir, unity_trials_data,
                                  unity_frames_data, ballvel_data, event_data,
                                  facecam_packages, unitycam_packages)
        
    # inplace insert trial id into every dataframe with a timestamp
    insert_trial_id(unity_trials_data, unity_frames_data,
                    ballvel_data, event_data, facecam_packages, bodycam_packages,
                    unitycam_packages, use_ephys_timestamps=integrate_ephys)
    
    if prompt_user_decision:
        answer = input("\nProceed with merging and renaming session dir? [y/n]: ")
        if answer.lower() != 'y':
            return
    
    # merge all data into a single hdf5 file and store in session_dir
    merged_fname = f"{metadata['session_name']}.hdf5"
    _save_merged_hdf5_data(session_dir, merged_fname, metadata, unity_trials_data, 
                           unity_frames_data, paradigmVariable_data, 
                           facecam_packages, bodycam_packages, 
                           unitycam_packages, ballvel_data, event_data)
    L.spacer()
    
    if render_videos:
        hdf5_frames2mp4(session_dir, merged_fname)
    L.spacer()
    
    # change the session dir name to the session_name
    # session_dir = _handle_rename_nas_session_dirs(session_dir, nas_dir, 
    #                                               metadata["session_name"])
    
    if copy_to_nas and os.path.exists(nas_dir):
        _handle_move2nas(session_dir, nas_dir, merged_fname, metadata['animal_name'], 
                         metadata['paradigm_name'])
    L.spacer()

    # read the moved data on the NAS, not local (faster in the future)
    if write_to_db:
        session2db(nas_dir, merged_fname, database_location, database_name)
    
    L.logger.info(f"Session processing finished sucessfully")
    #TODO run on all the available data with fast network connection to NAS, 
    #TODO test with a session that has ephys data

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Validate and add a finished session to DB")
    argParser.add_argument("--logging_dir", default="../logs")
    argParser.add_argument("--logging_name", default="process_session_batch.log")
    argParser.add_argument("--logging_level", default="INFO")
    # optional arguments
    argParser.add_argument("--prompt_user_decision", action="store_true")
    argParser.add_argument("--render_videos", action="store_true")
    argParser.add_argument("--integrate_ephys", action="store_true")
    argParser.add_argument("--copy_to_nas", action="store_true")
    argParser.add_argument("--nas_dir", default="/mnt/NTnas/nas_vrdata")
    argParser.add_argument("--write_to_db", action="store_true")
    argParser.add_argument("--database_location", default=None)
    argParser.add_argument("--database_name", default=None)
    kwargs = vars(argParser.parse_args())
    
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.spacer()
    L.logger.info("Subprocess started")
    L.logger.info(L.fmtmsg(kwargs))
            
    prompt_user_decision = kwargs.pop("prompt_user_decision")
    integrate_ephys = kwargs.pop("integrate_ephys")
    copy_to_nas = kwargs.pop("copy_to_nas")
    write_to_db = kwargs.pop("write_to_db")
    nas_dir = kwargs.pop("nas_dir")
    database_location = kwargs.pop("database_location")
    database_name = kwargs.pop("database_name")
    render_videos = kwargs.pop("render_videos")
    
    # animal_ids = [1,2,3,4,5,6,7,8,9]
    animal_ids = [1,2,3,4]
    
    parent_folder = "/mnt/SpatialSequenceLearning/"
    # TODO
    # 1. fix the post processing script with error on log file
    # 2. for all sessions, if there is unity_output.hdf5
    #   2.1 clear all the merged files
    #   2.2 post-process it again
    # 3. if there is no unity_output.hdf5
    #   3.1 patch the session based on the left file
    #   3.2 keep the old file for safety
    
    
    for animal_id in animal_ids:
        animal_dir = os.path.join(parent_folder, f"RUN_rYL00{animal_id}")
        for paradigm_name in os.listdir(animal_dir):
            if "rYL" not in paradigm_name:
                continue
            paradigm_dir = os.path.join(animal_dir, paradigm_name)
            
            for session in os.listdir(paradigm_dir):
                if "DS_Store" in session:
                    continue
                session_dir = os.path.join(paradigm_dir, session)
                # session_dir = "/mnt/SpatialSequenceLearning/RUN_rYL008/rYL008_P0800/2024-08-22_15-11_rYL008_P0800_LinearTrack_18min/"
                session_dir_new = session_dir.replace(".xlsx", "")
                os.rename(session_dir, session_dir_new)
                session_dir = session_dir_new
                fnames = [f for f in os.listdir(session_dir) if f.endswith("min.hdf5")]
                all_fnames = os.listdir(session_dir)
                
                if "unity_output.hdf5" in all_fnames:
                    for fname in fnames:
                        full_fname = os.path.join(session_dir, fname)
                        os.remove(full_fname)
                    
                    try:
                        process_session(session_dir, nas_dir, prompt_user_decision, 
                                        integrate_ephys, copy_to_nas, write_to_db,
                                        database_location, database_name, 
                                        render_videos)
                    except Exception as e:
                        L.logger.error(f"Failed to process session: {e}")
                    continue
                else:
                    for fname in fnames:
                        full_fname = os.path.join(session_dir, fname)
                        if "_old" in full_fname or '_fixed' in full_fname: 
                            # os.remove(full_fname)
                            continue
                        else:
                            patch_metadata(full_fname)
            L.spacer()
            print("\n\n\n\n")
            
    
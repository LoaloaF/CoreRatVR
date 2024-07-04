import shutil
import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..'))

import argparse
from send2trash import send2trash
import pandas as pd
import h5py
from CustomLogger import CustomLogger as Logger

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
    dbNames = ['session_name', 'paradigm_name', 'animal_name', 'paradigm_id',
               'start_time', 'stop_time', 'duration', 'notes', 'rewardPostSoundDelay', 
               'rewardAmount', 'punishmentLength', 'punishInactivationLength', 
               'interTrialIntervalLength', 'abortInterTrialIntervalLength',
               'successSequenceLength', 'maxiumTrialLength', 'sessionDescription',
               'configuration', 'metadata']
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
        return
    
    with pd.HDFStore(full_fname, 'w') as store:
        store.put('metadata', pd.DataFrame(metadata, index=[0]))
    
        L.logger.info(f"Merging unity data...")
        store.put('unity_trial', unity_trials_data)
        store.put('unity_frame', unity_frames_data)
        if paradigmVariable_data is not None:
            store.put('paradigm_variable', paradigmVariable_data)

        L.logger.info(f"Merging portenta data...")
        if ballvel_data is not None:
            store.put('ballvelocity', ballvel_data)
        if event_data is not None:
            store.put('event', event_data)
        
        if facecam_packages is not None:
            store.put('facecam_packages', facecam_packages)    
        if bodycam_packages is not None:
            store.put('bodycam_packages', bodycam_packages)
        if unitycam_packages is not None:
            store.put('unitycam_packages', unitycam_packages)

    # copy the camera data into the behavior file
    with h5py.File(full_fname, 'a') as output_file:
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
                if f.endswith(".h5.raw") and 'vr_ephys' in f]
    if len(ephys_fname) != 1:
        L.logger.error(f"Failed to find ephys recording file in {nas_dir}/{session_dir}")
        return
    ephys_fname = ephys_fname[0]
    ephys_fullfname = os.path.join(nas_dir, session_dir, ephys_fname)
    # inplace insertation of ephys timestamps into all dataframes

    add_ephys_timestamps(ephys_fullfname, unity_trials_data, unity_frames_data,
                         ballvel_data, event_data, facecam_packages, unitycam_packages)
    
def _handle_move2nas(session_dir, nas_dir, merged_fname):
    L.logger.info(f"Copying files to the NAS")
    # copy only these selected files to NAS (merged file, log files, bodycam video)
    fnames = [fname for fname in os.listdir(session_dir) 
              if fname.endswith(".log") or fname in (merged_fname, "bodycam.mp4")]
    for fn in fnames:
        src = os.path.join(session_dir, fn)
        if os.path.exists(src):
            if fn == merged_fname:
                L.logger.info(f"Copying {fn} ({os.path.getsize(src)/(1024**3):.1}GB)"
                              f" to NAS...")
            dst = os.path.join(nas_dir, os.path.basename(session_dir), fn)
            shutil.copy(src, dst)
    
def _handle_rename_nas_session_dirs(session_dir, nas_dir, new_dir_name):
    print(nas_dir, session_dir, new_dir_name)
    L.logger.info(f"Renaming session directory on NAS")
    old_dir_name = os.path.basename(session_dir)
    
    nas_session_dir = os.path.join(nas_dir, new_dir_name)
    # TODO os.rename doesn't work for non-empty folders?
    # os.rename(os.path.join(nas_dir, old_dir_name), nas_session_dir)
    os.rename(session_dir, (os.path.join(os.path.split(session_dir[:-1])[0], new_dir_name)))

    return nas_session_dir

def process_session(session_dir, nas_dir, prompt_user_decision, integrate_ephys, 
                    copy_to_nas, write_to_db, database_location, database_name,
                    render_videos):
    L = Logger()
    L.logger.info(f"Processing session {session_dir}")
    
    if prompt_user_decision:
        answer = input("\nSkip this session? [y/n]: ")
        if answer.lower() == 'y':
            return

    # check if files exsist and if .log files have warnings or erros
    _handle_logs(session_dir)

    # load the metadata, unity, camera, ballvelocity and event data
    data = _handle_data(session_dir)
    try:
        data = _handle_data(session_dir)
    except Exception as e:
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
    merged_fname = f"behavior_{metadata['session_name']}.hdf5"
    _save_merged_hdf5_data(session_dir, merged_fname, metadata, unity_trials_data, 
                           unity_frames_data, paradigmVariable_data, 
                           facecam_packages, bodycam_packages, 
                           unitycam_packages, ballvel_data, event_data)
    L.spacer()
    
    if render_videos:
        hdf5_frames2mp4(session_dir, merged_fname)
    L.spacer()
    
    if copy_to_nas and os.path.exists(nas_dir):
        L.logger.info(f"Copying session to NAS...")
        _handle_move2nas(session_dir, nas_dir, merged_fname)
        L.spacer()

    # change the session dir name to the session_name
    nas_session_dir = _handle_rename_nas_session_dirs(session_dir, nas_dir, 
                                                        metadata["session_name"])
    L.spacer()

    # read the moved data on the NAS, not local (faster in the future)
    if write_to_db:
        session2db(nas_session_dir, merged_fname, database_location, database_name)
    
    L.logger.info(f"Session processing finished")
    #TODO run on all the available data with fast network connection to NAS, 
    #TODO test with a session that has ephys data

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Validate and add a finished session to DB")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--session_dir")
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
            
    process_session(**kwargs)
    L.spacer()
    print("\n\n\n\n")
    
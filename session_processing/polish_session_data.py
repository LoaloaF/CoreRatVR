import os

import numpy as np
import pandas as pd
import h5py
import cv2

from CustomLogger import CustomLogger as Logger

def add_ephys_timestamps(ephys_fullfname, unity_trials_data, unity_frames_data,
                         ballvel_data, event_data, facecam_packages, unitycam_packages):
    pass

def insert_trial_id(unity_trials_data, unity_frames_data, ballvel_data, 
                    event_data, facecam_packages, bodycam_packages,
                    unitycam_packages, use_ephys_timestamps=False):
    
    trials_tstamp_col = 'trial_start_pc_timestamp' 
    frame_tstamp_col = 'frame_pc_timestamp' 
    ballvel_tstamp_col = "ballvelocity_pc_timestamp"
    event_tstamp_col = "event_pc_timestamp"
    facecam_tstamp_col = "facecam_image_pc_timestamp"
    bodycam_tstamp_col = "bodycam_image_pc_timestamp"
    unitycam_tstamp_col = "unitycam_image_pc_timestamp"
    if use_ephys_timestamps:
        trials_tstamp_col = trials_tstamp_col.replace('_pc_', '_ephys_')
        frame_tstamp_col = frame_tstamp_col.replace('_pc_', '_ephys_')
        ballvel_tstamp_col = ballvel_tstamp_col.replace('_pc_', '_ephys_')
        event_tstamp_col = event_tstamp_col.replace('_pc_', '_ephys_')
        facecam_tstamp_col = facecam_tstamp_col.replace('_pc_', '_ephys_')
        bodycam_tstamp_col = bodycam_tstamp_col.replace('_pc_', '_ephys_')
        unitycam_tstamp_col = unitycam_tstamp_col.replace('_pc_', '_ephys_')
    
    # if unity_trials_data is None, this will enter the catch block in main function
    # get the trial time boundaries and constuct an interval index from it

    import matplotlib.pyplot as plt
    for idx, trial in unity_trials_data.iterrows():
        start, stop = trial["trial_start_pc_timestamp"], trial["trial_end_pc_timestamp"]
        trial_id = trial["trial_id"]
        msg = f"Trial ID: {trial_id}"
        if start>stop: 
            col = 'red'
            msg += " - ERROR: Start > Stop"
        else:
            col = "green"
            
        if idx and start < unity_trials_data.loc[idx-1,"trial_end_pc_timestamp"]:
            col = 'red'
            msg += " - ERROR: Start < previous trial stop"
            
        # for checking the trial start and end times
        plt.scatter([start], [trial_id], edgecolors=col, s=60, zorder=2, color='none', marker='>')
        plt.scatter([stop], [trial_id], edgecolors=col, s=60, zorder=2, color='none', marker='o')
        plt.plot([start, stop], [trial_id, trial_id], color=col, linewidth=3)
        plt.text(start, trial_id+.3, f"{trial['trial_start_frame']:.0f}", fontsize=8)
        plt.text(stop, trial_id+.3, f"{trial['trial_end_frame']:.0f}", fontsize=8)
        print(msg)
        msg = ""
    plt.show()        
    
    trial_starts = unity_trials_data[trials_tstamp_col]
    trial_ends = unity_trials_data[trials_tstamp_col.replace('start', 'end')]
    # we append an additional mapping from -1 to nan, so that timestamps that 
    # are not within any trial are assined to nan (their index is -1 in the IntervalIndex)
    trial_ids = pd.concat((unity_trials_data['trial_id'], pd.Series({-1: np.nan})))
    trial_intervals = pd.IntervalIndex.from_arrays(trial_starts, trial_ends, 
                                                   closed='both')
    
    # vectorized function to assign trial IDs using the IntervalIndex
    def assign_trial_id(timestamps):
        # Find the positions of timestamps within the interval index
        idx = trial_intervals.get_indexer(timestamps)
        idx = idx.astype(int)
        # Handle cases where timestamp is not within any interval (ITI)
        return np.where(idx == -1, -1, trial_ids[idx].values)

    unity_frames_data['trial_id'] = assign_trial_id(unity_frames_data[frame_tstamp_col])

    if ballvel_data is not None:
        ballvel_data['trial_id'] = assign_trial_id(ballvel_data[ballvel_tstamp_col])
    if event_data is not None:
        event_data['trial_id'] = assign_trial_id(event_data[event_tstamp_col])
    if facecam_packages is not None:
        facecam_packages['trial_id'] = assign_trial_id(facecam_packages[facecam_tstamp_col])
    if bodycam_packages is not None:
        bodycam_packages['trial_id'] = assign_trial_id(bodycam_packages[bodycam_tstamp_col])
    if unitycam_packages is not None:
        unitycam_packages['trial_id'] = assign_trial_id(unitycam_packages[unitycam_tstamp_col])
    Logger().logger.info(f"Sucessfully added trial_id to dataframes.")
    
def hdf5_frames2mp4(session_dir, merged_fname):    
    def _calc_fps(packages, cam_name):
        timestamps = packages[f'{cam_name}_image_pc_timestamp']
        return np.round(1 / np.mean(np.diff(timestamps)) * 1e6, 0)

    def _create_video_writer(cam_name, fps, frame_shape):
        out_fullfname = os.path.join(session_dir, f'{cam_name}.mp4')
        out_dims = frame_shape[1], frame_shape[0] # flip dims for cv2
        isColor = True if len(frame_shape) == 3 else False
        return cv2.VideoWriter(out_fullfname, cv2.VideoWriter_fourcc(*'mp4v'), 
                               fps, out_dims, isColor=isColor)
    
    def render_video(cam_name):
        merged_fullfname = os.path.join(session_dir, merged_fname)
        with h5py.File(merged_fullfname, 'r') as merged_file:
            try:
                packages = pd.read_hdf(merged_fullfname, key=f'{cam_name}_packages')
                fps = _calc_fps(packages, cam_name)

                frame_keys = merged_file[f"{cam_name}_frames"].keys()
                L.logger.info(f"Rendering {cam_name} (n={len(frame_keys):,})...")
                for i, (frame_key, pack) in enumerate(zip(frame_keys, packages.iterrows())):
                    frame = merged_file[f"{cam_name}_frames"][frame_key][()]
                    frame = cv2.imdecode(np.frombuffer(frame.tobytes(), np.uint8), 
                                         cv2.IMREAD_COLOR) 
                    
                    pack_id = pack[1][f"{cam_name}_image_id"]
                    if i == 0:
                        writer = _create_video_writer(cam_name, fps, frame.shape)
                        prv_pack_id = pack_id-1
                    
                    # insert black frame if package ID is discontinuous
                    if pack_id != prv_pack_id+1:
                        L.logger.warning(f"Package ID discontinuous; gap was "
                                         f"{pack_id - prv_pack_id}.  Inserting"
                                         f" black frame.")
                        writer.write(np.zeros_like(frame))
                    else:
                        writer.write(frame)
                    prv_pack_id = pack_id
                    
                    # log progress
                    # if i % (len(frame_keys)//10) == 0:
                    #     print(f"{i/len(frame_keys)*100:.0f}% done...", end='\r')
                L.logger.info(f"Sucessfully rendered {cam_name} video!")
            # keys in hdf5 file may very well not exist
            except Exception as e:
                L.logger.error(f"Failed to render {cam_name} video: {e}")
                return
    L = Logger()
    L.logger.info(f"Rendering videos from hdf5 files in {session_dir}")
    render_video("facecam")
    render_video("bodycam")
    render_video("unitycam")
import os

import numpy as np
import pandas as pd
import h5py
import cv2
import matplotlib.pyplot as plt

# from CustomLogger import CustomLogger as Logger

def detect_edges(signal, signal_name):

    diff_val = np.diff(signal[signal_name])
    rising_edges_idx = np.where(diff_val == 1)[0] + 1
    falling_edges_idx = np.where(diff_val == -1)[0] + 1
    
    rising_edge_times = signal['time'].iloc[rising_edges_idx].values
    falling_edge_times = signal['time'].iloc[falling_edges_idx].values

    return rising_edge_times, falling_edge_times

def comparision_plot(ttl,pc_timestamp):
    fig, ax = plt.subplots()

    # Plot the dots
    ax.scatter(ttl, np.ones_like(ttl), color='blue', label='Rising TTL')
    ax.scatter(pc_timestamp, np.zeros_like(pc_timestamp), color='red', label='PC Timestamp')

    for i in range(len(ttl)):
        ax.plot([ttl[i], pc_timestamp[i]], [1, 0], color='gray', linestyle='--')
    
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['PC Timestamp', 'Rising TTL'])
    ax.legend()
    ax.set_xlabel('Time')
    ax.set_title('Comparison of Rising TTL and PC Timestamp')

    plt.show()

def clean_ttl_data(data, threshold=10):
    filtered_data = [data[0]]
    for i in range(1, len(data)):
        if data[i] - data[i - 1] >= threshold:
            filtered_data.append(data[i])
    return np.array(filtered_data)

def patch_ephys_time(ballvel_data, target_data, target_data_pc_name):
    ballvel_pc_time = ballvel_data["ballvelocity_pc_timestamp"].values
    ballvel_ephys_time = ballvel_data["ballvelocity_ephys_timestamp"].values

    target_data_ephys_time = np.empty(len(target_data), dtype=ballvel_ephys_time.dtype)

    for i, target_pc_time in enumerate(target_data[target_data_pc_name].values):
        closest_index = np.argmin(np.abs(ballvel_pc_time - target_pc_time))
        target_data_ephys_time[i] = ballvel_ephys_time[closest_index]

    return target_data_ephys_time


def add_ephys_timestamps(ephys_fullfname, unity_trials_data, unity_frames_data,
                         ballvel_data, event_data, facecam_packages, 
                         bodycam_packages, unitycam_packages):
    
    L = Logger()
     
    try:
        with h5py.File(ephys_fullfname, 'r') as file:
            ephys_bits = file['bits']["0000"][:]
    except:
        with h5py.File(ephys_fullfname, 'r') as file:
            ephys_bits = file['bits'][:]

    msg = np.array([(a[0],a[1]) for a in ephys_bits])

    ephys_data = pd.DataFrame(msg, columns=['time', 'value'])

    for column_id in range(8):
        ephys_data[f'bit{column_id}'] = (ephys_data['value'] & (1 << column_id))/2**column_id
        ephys_data[f'bit{column_id}'] = ephys_data[f'bit{column_id}'].astype(int)
    
    # Ball Velocity
    L.spacer()
    ball_ttl = ephys_data[['time', 'bit0']]
    ball_rising_ttl, ball_falling_ttl = detect_edges(ball_ttl, "bit0")

    if (ball_ttl["bit0"].iloc[0] == 1):
        ball_rising_ttl = np.insert(ball_rising_ttl, 0, ball_ttl["time"].iloc[0])
        
    ball_pc_timestamp = np.array(ballvel_data["ballvelocity_pc_timestamp"])

    ball_rising_ttl_norm = (ball_rising_ttl - ball_rising_ttl[0])*50
    ball_pc_timestamp_norm = ball_pc_timestamp - ball_pc_timestamp[0]

    L.logger.info(f"Ball TTL: {len(ball_rising_ttl_norm)}")
    L.logger.info(f"Ball PC: {len(ball_pc_timestamp_norm)}")
    
    if (len(ball_rising_ttl_norm) != len(ball_pc_timestamp_norm)):
        L.logger.warning("Ball TTL and PC Timestamp length mismatch. Add ephys timestamp failed.")
        return
    else:
        L.logger.info(f"Average diff: {np.mean(ball_rising_ttl_norm - ball_pc_timestamp_norm)}")
        plt.figure()
        plt.plot(ball_rising_ttl_norm - ball_pc_timestamp_norm)
        plt.title("Ball Vecocity: TTL - PC")
        ballvel_data["ballvelocity_ephys_timestamp"] = (ball_rising_ttl_norm/50 + ball_rising_ttl[0])*50
        L.logger.info("Ball Velocity TTL Timestamps added")

    # Frame
    L.spacer()
    ball_last_packages_ids = unity_frames_data.ballvelocity_last_package.values
    filtered_ball_data = ballvel_data[ballvel_data["ballvelocity_package_id"].isin(ball_last_packages_ids)]
    frame_ttl = filtered_ball_data.ballvelocity_ephys_timestamp.values
    
    frame_pc_timestamp = np.array(unity_frames_data["frame_pc_timestamp"])
    frame_pc_timestamp_norm = frame_pc_timestamp - frame_pc_timestamp[0]
    frame_ttl_norm = frame_ttl - frame_ttl[0]
   
    if (len(frame_pc_timestamp_norm) != len(frame_ttl_norm)):
        L.logger.warning("Frame TTL and PC Timestamp length mismatch")
    else:
        L.logger.info(f"Average diff: {np.mean(frame_ttl_norm - frame_pc_timestamp_norm)}")
        plt.figure()
        plt.plot(frame_ttl_norm - frame_pc_timestamp_norm)
        plt.title('Unity Frame: TTL - PC')
        plt.show() 
        
        unity_frames_data["frame_ephys_timestamp"] = frame_ttl
        
        # append unitycam ephys
        merged_data = pd.merge(
            unitycam_packages,
            unity_frames_data[['frame_id', 'frame_ephys_timestamp']],
            left_on='unitycam_image_id',
            right_on='frame_id',
            how='left'
        )
        unitycam_packages["unitycam_image_ephys_timestamp"] =  merged_data['frame_ephys_timestamp']
        
        # append trial start ephys
        merged_data = pd.merge(
            unity_trials_data,
            unity_frames_data[['frame_id', 'frame_ephys_timestamp']],
            left_on='trial_start_frame',
            right_on='frame_id',
            how='left'
        )
        unity_trials_data["trial_start_ephys_timestamp"] = merged_data['frame_ephys_timestamp']

        # append trial end ephys
        merged_data = pd.merge(
            unity_trials_data,
            unity_frames_data[['frame_id', 'frame_ephys_timestamp']],
            left_on='trial_end_frame',
            right_on='frame_id',
            how='left'
        )
        unity_trials_data["trial_end_ephys_timestamp"] = merged_data['frame_ephys_timestamp']

        ballvel_pc_time = ballvel_data["ballvelocity_pc_timestamp"].values
        ballvel_ephys_time = ballvel_data["ballvelocity_ephys_timestamp"].values

        # patch the first trial start and end ephys timestamps
        closest_index_trial_1_start = np.argmin(np.abs(ballvel_pc_time - unity_trials_data["trial_start_pc_timestamp"].values[0]))
        unity_trials_data.at[0, "trial_start_ephys_timestamp"] = ballvel_ephys_time[closest_index_trial_1_start]
        closest_index_trial_1_end= np.argmin(np.abs(ballvel_pc_time - unity_trials_data["trial_end_pc_timestamp"].values[0]))
        unity_trials_data.at[0, "trial_end_ephys_timestamp"] = ballvel_ephys_time[closest_index_trial_1_end]        
        
        L.logger.info("Unity Frame/Cam/Trials TTL Timestamps added")
    
    # Facecam
    L.spacer()
    if facecam_packages is None:
        L.logger.warning("No Facecam Data")
    else:
        facecam_ttl = ephys_data[['time', 'bit2']]
        facecam_rising_ttl, facecam_falling_ttl = detect_edges(facecam_ttl, "bit2")
        facecam_pc_timestamp = np.array(facecam_packages["facecam_image_pc_timestamp"])
        L.logger.info(f"Facecam TTL: {len(facecam_rising_ttl)}")
        L.logger.info(f"Facecam PC: {len(facecam_pc_timestamp)}")
            
        if (len(facecam_pc_timestamp) == 0):
            L.logger.warning("No Facecam TTL")
        elif (len(facecam_rising_ttl) != len(facecam_pc_timestamp)):
            L.logger.warning("Facecam TTL and PC Timestamp length mismatch. Start patching with Ballvel data...")
            facecam_packages["facecam_image_ephys_timestamp"] = patch_ephys_time(ballvel_data, facecam_packages, "facecam_image_pc_timestamp")
            L.logger.info("Facecam TTL Timestamps patched")
        else:
            facecam_rising_ttl_norm = (facecam_rising_ttl - facecam_rising_ttl[0])*50
            facecam_pc_timestamp_norm = facecam_pc_timestamp - facecam_pc_timestamp[0]
            L.logger.info(f"Average diff: {np.mean(facecam_rising_ttl_norm - facecam_pc_timestamp_norm)}")
            
            plt.figure()
            plt.plot(facecam_rising_ttl_norm - facecam_pc_timestamp_norm)
            plt.title('Facecam: TTL - PC')
            plt.show() 
            
            facecam_packages["facecam_image_ephys_timestamp"] = (facecam_rising_ttl_norm/50 + facecam_rising_ttl[0])*50
            L.logger.info("Facecam TTL Timestamps added")
    
    # Bodycam
    L.spacer()
    if bodycam_packages is None:
        L.logger.warning("No Bodycam Data")
    elif facecam_packages is None:
        L.logger.warning("No Facecam Data to reference for Bodycam")
    else:
        facecam_pc_time = facecam_packages["facecam_image_pc_timestamp"].values
        facecam_ephys_time = facecam_packages["facecam_image_ephys_timestamp"].values

        bodycam_ephys_time = np.empty(len(bodycam_packages), dtype=facecam_ephys_time.dtype)

        for i, bodycam_pc_time in enumerate(bodycam_packages["bodycam_image_pc_timestamp"].values):
            closest_index = np.argmin(np.abs(facecam_pc_time - bodycam_pc_time))
            bodycam_ephys_time[i] = facecam_ephys_time[closest_index]
        
        bodycam_packages["bodycam_image_ephys_timestamp"] = bodycam_ephys_time
        L.logger.info("Bodycam TTL Timestamps patched")
                     
    L.spacer()
    if event_data is None:
        L.logger.warning("No Event Data")
    else:
        lick_ttl = ephys_data[['time', 'bit7']]
        lick_rising_ttl, lick_falling_ttl = detect_edges(lick_ttl, "bit7")
        lick_pc_timestamp = np.array(event_data[event_data["event_name"]=="L"]["event_pc_timestamp"])
        lick_pc_value = np.array(event_data[event_data["event_name"]=="L"]["event_value"])
        lick_pc_timestamp = lick_pc_timestamp + lick_pc_value
        L.logger.info(f"Lick TTL: {len(lick_rising_ttl)}")
        L.logger.info(f"Lick PC: {len(lick_pc_timestamp)}")
        
        if (len(lick_pc_timestamp) == 0):
            L.logger.warning("No Lick Event.")
        elif (len(lick_rising_ttl) != len(lick_pc_timestamp)):
            L.logger.warning("Lick TTL and PC Timestamp length mismatch. Start patching with Ballvel data...")
            event_data.loc[event_data["event_name"]=="L", "event_ephys_timestamp"] = patch_ephys_time(ballvel_data, event_data[event_data["event_name"]=="L"], "event_pc_timestamp")
            L.logger.info("Lick TTL Timestamps patched")
        else:
            lick_rising_ttl_norm = (lick_rising_ttl - lick_rising_ttl[0])*50
            lick_pc_timestamp_norm = lick_pc_timestamp - lick_pc_timestamp[0]
            L.logger.info(f"Average diff: {np.mean(lick_rising_ttl_norm - lick_pc_timestamp_norm)}")
            
            plt.figure()
            plt.plot(lick_rising_ttl_norm - lick_pc_timestamp_norm)
            plt.title('Lick: TTL - PC')
            plt.show() 
            # comparision_plot(lick_rising_ttl_norm, lick_pc_timestamp_norm)
            event_data.loc[event_data["event_name"]=="L", "event_ephys_timestamp"] = (lick_rising_ttl_norm/50 + lick_rising_ttl[0])*50
            L.logger.info("Lick TTL Timestamps added")
        
        # Punishment
        L.spacer()
        punishment_ttl = ephys_data[['time', 'bit1']]
        punishment_rising_ttl, punishment_falling_ttl = detect_edges(punishment_ttl, "bit1")
        punishment_pc_timestamp = np.array(event_data[event_data["event_name"]=="V"]["event_pc_timestamp"])
        L.logger.info(f"Punishment TTL: {len(punishment_rising_ttl)}")
        L.logger.info(f"Punishment PC: {len(punishment_pc_timestamp)}")
        
        if (len(punishment_pc_timestamp) == 0):
            L.logger.warning("No Punishment Event.")
        elif len(punishment_rising_ttl) != len(punishment_pc_timestamp):
            L.logger.warning("Punishment TTL and PC Timestamp length mismatch. Start patching with Ballvel data...")
            event_data.loc[event_data["event_name"]=="V", "event_ephys_timestamp"] = patch_ephys_time(ballvel_data, event_data[event_data["event_name"]=="V"], "event_pc_timestamp")
            L.logger.info("Punishment TTL Timestamps patched")
        else:
            punishment_rising_ttl_norm = (punishment_rising_ttl - punishment_rising_ttl[0])*50
            punishment_pc_timestamp_norm = punishment_pc_timestamp - punishment_pc_timestamp[0]
            L.logger.info(f"Average diff: {np.mean(punishment_rising_ttl_norm - punishment_pc_timestamp_norm)}")
            
            plt.figure()
            plt.plot(punishment_rising_ttl_norm - punishment_pc_timestamp_norm)
            plt.title('Punishment: TTL - PC')
            plt.show()
            # comparision_plot(punishment_rising_ttl_norm, punishment_pc_timestamp_norm)
            event_data.loc[event_data["event_name"]=="V", "event_ephys_timestamp"] = (punishment_rising_ttl_norm/50 + punishment_rising_ttl[0])*50
            L.logger.info("Punishment TTL Timestamps added")
        
        # Reward
        L.spacer()
        reward_ttl = ephys_data[['time', 'bit6']]
        reward_rising_ttl, reward_falling_ttl = detect_edges(reward_ttl, "bit6")
        reward_pc_timestamp = np.array(event_data[event_data["event_name"]=="R"]["event_pc_timestamp"])
        
        L.logger.info(f"Reward TTL: {len(reward_rising_ttl)}")
        L.logger.info(f"Reward PC: {len(reward_pc_timestamp)}")
            
        if (len(reward_pc_timestamp) == 0):
            L.logger.warning("No Reward Event.")
        elif len(reward_rising_ttl) != len(reward_pc_timestamp):
            L.logger.warning("Reward TTL and PC Timestamp length mismatch. Start patching with Ballvel data...")
            event_data.loc[event_data["event_name"]=="R", "event_ephys_timestamp"] = patch_ephys_time(ballvel_data, event_data[event_data["event_name"]=="R"], "event_pc_timestamp")
            L.logger.info("Reward TTL Timestamps patched")
        else:
            reward_rising_ttl_norm = (reward_rising_ttl - reward_rising_ttl[0])*50
            reward_pc_timestamp_norm = reward_pc_timestamp - reward_pc_timestamp[0]
            L.logger.info(f"Average diff: {np.mean(reward_rising_ttl_norm - reward_pc_timestamp_norm)}")
            
            plt.figure()
            plt.plot(reward_rising_ttl_norm - reward_pc_timestamp_norm)
            plt.title('Reward: TTL - PC')
            plt.show()
            # comparision_plot(reward_rising_ttl_norm, reward_pc_timestamp_norm)
            event_data.loc[event_data["event_name"]=="R", "event_ephys_timestamp"] = (reward_rising_ttl_norm/50 + reward_rising_ttl[0])*50
            L.logger.info("Reward TTL Timestamps added")

        # Sound
        L.spacer()
        sound_ttl = ephys_data[['time', 'bit4']]
        sound_rising_ttl, sound_falling_ttl = detect_edges(sound_ttl, "bit4")
        sound_pc_timestamp = np.array(event_data[event_data["event_name"]=="S"]["event_pc_timestamp"])
        L.logger.info(f"Sound TTL: {len(sound_rising_ttl)}")
        L.logger.info(f"Sound PC: {len(sound_pc_timestamp)}")
        
        if (len(sound_pc_timestamp) == 0):
            L.logger.warning("No Sound Event.")
        elif len(sound_rising_ttl) != len(sound_pc_timestamp):
            L.logger.warning("Sound TTL and PC Timestamp length mismatch. Start patching with Ballvel data...")
            event_data.loc[event_data["event_name"]=="S", "event_ephys_timestamp"] = patch_ephys_time(ballvel_data, event_data[event_data["event_name"]=="S"], "event_pc_timestamp")
            L.logger.info("Sound TTL Timestamps patched")
        else:
            sound_rising_ttl_norm = (sound_rising_ttl - sound_rising_ttl[0])*50
            sound_pc_timestamp_norm = sound_pc_timestamp - sound_pc_timestamp[0]
            L.logger.info(f"Average diff: {np.mean(sound_rising_ttl_norm - sound_pc_timestamp_norm)}")
            
            plt.figure()
            plt.plot(sound_rising_ttl_norm - sound_pc_timestamp_norm)
            plt.title('Difference between TTL and PC Timestamp after patching: TTL - PC')
            plt.show()
            # comparision_plot(sound_rising_ttl_norm, sound_pc_timestamp_norm)
            event_data.loc[event_data["event_name"]=="S", "event_ephys_timestamp"] = (sound_rising_ttl_norm/50 + sound_rising_ttl[0])*50
            L.logger.info("Sound TTL Timestamps added")

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

    # import matplotlib.pyplot as plt
    # for idx, trial in unity_trials_data.iterrows():
    #     start, stop = trial["trial_start_pc_timestamp"], trial["trial_end_pc_timestamp"]
    #     trial_id = trial["trial_id"]
    #     msg = f"Trial ID: {trial_id}"
    #     if start>stop: 
    #         col = 'red'
    #         msg += " - ERROR: Start > Stop"
    #     else:
    #         col = "green"
            
    #     if idx and start < unity_trials_data.loc[idx-1,"trial_end_pc_timestamp"]:
    #         col = 'red'
    #         msg += " - ERROR: Start < previous trial stop"
            
    #     # for checking the trial start and end times
    #     plt.scatter([start], [trial_id], edgecolors=col, s=60, zorder=2, color='none', marker='>')
    #     plt.scatter([stop], [trial_id], edgecolors=col, s=60, zorder=2, color='none', marker='o')
    #     plt.plot([start, stop], [trial_id, trial_id], color=col, linewidth=3)
    #     plt.text(start, trial_id+.3, f"{trial['trial_start_frame']:.0f}", fontsize=8)
    #     plt.text(stop, trial_id+.3, f"{trial['trial_end_frame']:.0f}", fontsize=8)
    #     print(msg)
    #     msg = ""
    # plt.show()        
    
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
                # L.logger.info(f"Rendering {cam_name} (n={len(frame_keys):,})...")
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
                        # L.logger.warning(f"Package ID discontinuous; gap was "
                        #                  f"{pack_id - prv_pack_id}.  Inserting"
                        #                  f" black frame.")
                        writer.write(np.zeros_like(frame))
                    else:
                        writer.write(frame)
                    prv_pack_id = pack_id
                    
                    # log progress
                    # if i % (len(frame_keys)//10) == 0:
                    #     print(f"{i/len(frame_keys)*100:.0f}% done...", end='\r')
                # L.logger.info(f"Sucessfully rendered {cam_name} video!")
            # keys in hdf5 file may very well not exist
            except Exception as e:
                # L.logger.error(f"Failed to render {cam_name} video: {e}")
                return
    # L = Logger()
    # L.logger.info(f"Rendering videos from hdf5 files in {session_dir}")
    render_video("facecam")
    render_video("bodycam")
    render_video("unitycam")
    
    
if __name__ == '__main__':
    session_dir ="/Volumes/large/BMI/VirtualReality/SpatialSequenceLearning/RUN_rYL006/rYL006_P1000/2024-10-25_15-41_rYL006_P1000_MotorLearningStop_14min"
    session_dir ="/Volumes/large/BMI/VirtualReality/SpatialSequenceLearning/RUN_rYL006/rYL006_P0500/2024-11-12_17-14_rYL006_P0500_MotorLearning_0min"
    merged_fname = "2024-10-25_15-41_rYL006_P1000_MotorLearningStop_14min.hdf5"
    merged_fname = "2024-11-12_17-14_rYL006_P0500_MotorLearning_0min.hdf5"
    hdf5_frames2mp4(session_dir, merged_fname)
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def P200_wallzone_ratio():
    parent_dir = "/mnt/NTnas/nas_vrdata/000_rYL001_P0200"

    # Get a list of all items in the directory
    all_items = os.listdir(parent_dir)

    # Filter out non-directory items and sort the remaining directories alphabetically
    directories = sorted([item for item in all_items if os.path.isdir(os.path.join(parent_dir, item))])

    wall_zone_ratio = []
    for session_dir in directories:
        print("Now processing:" + session_dir)
        for file_name in os.listdir(os.path.join(parent_dir, session_dir)):
            if file_name.startswith("behavior_"):
                file_path = os.path.join(parent_dir, session_dir, file_name)
                df = pd.read_hdf(file_path, key='unity_frame')
                df_remove_intertrial = df[df["trial_id"] != -1]
                df_wallzone = df_remove_intertrial[df_remove_intertrial["frame_state"] == 203]
                wall_zone_ratio.append(len(df_wallzone)/len(df_remove_intertrial))
    print(wall_zone_ratio)
    plt.figure(1)
    plt.plot(wall_zone_ratio)
    plt.title("Wall zone ratio")
    plt.show()

def P200_success_ratio():
    parent_dir = "/mnt/NTnas/nas_vrdata/000_rYL001_P0200"

    # Get a list of all items in the directory
    all_items = os.listdir(parent_dir)

    # Filter out non-directory items and sort the remaining directories alphabetically
    directories = sorted([item for item in all_items if os.path.isdir(os.path.join(parent_dir, item))])

    success_ratio = []
    for session_dir in directories:
        print("Now processing:" + session_dir)
        for file_name in os.listdir(os.path.join(parent_dir, session_dir)):
            if file_name.startswith("behavior_"):
                file_path = os.path.join(parent_dir, session_dir, file_name)
                df = pd.read_hdf(file_path, key='unity_trial')
                df_success_trial = df[df["trial_outcome"] == 1]
                success_ratio.append(len(df_success_trial)/len(df))
    print(success_ratio)
    plt.figure(1)
    plt.plot(success_ratio)
    plt.title("Success ratio")
    plt.show()

def P200_trajectory():
    early_session_dir = "/mnt/NTnas/nas_vrdata/000_rYL001_P0200/2024-05-22_15-33_rYL001_P0200_GoalDirectedMovement_min"
    late_session_dir = "/mnt/NTnas/nas_vrdata/000_rYL001_P0200/2024-06-21_12-07_rYL001_P0200_GoalDirectedMovement_30min"

    early_session_file = 'behavior_' + os.path.basename(early_session_dir) + '.hdf5'
    late_session_file = 'behavior_' + os.path.basename(late_session_dir) + '.hdf5'

    df_early = pd.read_hdf(os.path.join(early_session_dir, early_session_file), key='unity_frame')
    df_late = pd.read_hdf(os.path.join(late_session_dir, late_session_file), key='unity_frame')

    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.plot(df_early["frame_x_position"], df_early["frame_z_position"])
    ax1.set_title("Early session")
    ax1.set_xlim(-100, 100)
    ax1.set_ylim(-100, 100)
    ax2.plot(df_late["frame_x_position"], df_late["frame_z_position"])
    ax2.set_title("Late session")
    ax2.set_xlim(-100, 100)
    ax2.set_ylim(-100, 100)
    plt.show()

def P400_ratio():
    parent_dir = "/mnt/NTnas/nas_vrdata/000_rYL001_P0400"

    # Get a list of all items in the directory
    all_items = os.listdir(parent_dir)

    # Filter out non-directory items and sort the remaining directories alphabetically
    directories = sorted([item for item in all_items if os.path.isdir(os.path.join(parent_dir, item))])

    wall_zone_ratio = []
    succeed_zone_ratio = []
    for session_dir in directories:
        print("Now processing:" + session_dir)
        for file_name in os.listdir(os.path.join(parent_dir, session_dir)):
            if file_name.startswith("behavior_"):
                file_path = os.path.join(parent_dir, session_dir, file_name)
                df = pd.read_hdf(file_path, key='unity_frame')
                df_remove_intertrial = df[df["trial_id"] != -1]
                df_wallzone = df_remove_intertrial[df_remove_intertrial["frame_state"] == 403]
                df_succeed = df_remove_intertrial[df_remove_intertrial["frame_state"] == 405]
                wall_zone_ratio.append(len(df_wallzone)/len(df_remove_intertrial))
                succeed_zone_ratio.append(len(df_succeed)/len(df_remove_intertrial))
    print(wall_zone_ratio)
    plt.figure(1)
    plt.plot(wall_zone_ratio)
    plt.title("Wall zone ratio")
    plt.show()


    print(succeed_zone_ratio)
    plt.figure(2)
    plt.plot(succeed_zone_ratio)
    plt.title("Succeed zone ratio")
    plt.show()

def P400_trajectory():
    early_session_dir = "/mnt/NTnas/nas_vrdata/000_rYL001_P0400/2024-06-26_17-51_rYL001_P0400_4PillarDirected_41min"
    late_session_dir = "/mnt/NTnas/nas_vrdata/000_rYL001_P0400/2024-07-09_15-00_rYL001_P0400_4PillarDirected_24min"

    early_session_file = 'behavior_' + os.path.basename(early_session_dir) + '.hdf5'
    late_session_file = 'behavior_' + os.path.basename(late_session_dir) + '.hdf5'
    df_early = pd.read_hdf(os.path.join(early_session_dir, early_session_file), key='unity_frame')
    df_late = pd.read_hdf(os.path.join(late_session_dir, late_session_file), key='unity_frame')

    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.plot(df_early["frame_x_position"], df_early["frame_z_position"])
    ax1.set_title("Early session")
    # ax1.set_xlim(-100, 100)
    # ax1.set_ylim(-100, 100)
    ax2.plot(df_late["frame_x_position"], df_late["frame_z_position"])
    ax2.set_title("Late session")
    # ax2.set_xlim(-100, 100)
    # ax2.set_ylim(-100, 100)
    plt.show()

def P500_ratio():
    parent_dir = "/mnt/NTnas/nas_vrdata/000_rYL003_P0500"

    # Get a list of all items in the directory
    all_items = os.listdir(parent_dir)

    # Filter out non-directory items and sort the remaining directories alphabetically
    directories = sorted([item for item in all_items if os.path.isdir(os.path.join(parent_dir, item))])

    inter_mean = []
    for session_dir in directories:
        print("Now processing:" + session_dir)
        for file_name in os.listdir(os.path.join(parent_dir, session_dir)):
            if file_name.startswith("behavior_"):
                file_path = os.path.join(parent_dir, session_dir, file_name)
                df = pd.read_hdf(file_path, key='unity_trial')
                inter_time = df["trial_start_pc_timestamp"].diff()
                inter_time = inter_time[1:]
                plt.plot(inter_time)
                plt.show()
                inter_mean.append(inter_time.mean())
    
    print(inter_mean)
    plt.figure(1)
    plt.plot(inter_mean)
    plt.title("Inter trial time")
    plt.show()

def P200_distance():
    parent_dir = "/mnt/NTnas/nas_vrdata/000_rYL001_P0200"

    # Get a list of all items in the directory
    all_items = os.listdir(parent_dir)

    # Filter out non-directory items and sort the remaining directories alphabetically
    directories = sorted([item for item in all_items if os.path.isdir(os.path.join(parent_dir, item))])

    for session_dir in directories:
        print("Now processing:" + session_dir)
        for file_name in os.listdir(os.path.join(parent_dir, session_dir)):
            if file_name.startswith("behavior_"):
                file_path = os.path.join(parent_dir, session_dir, file_name)
                df = pd.read_hdf(file_path, key='unity_frame')
                trial_set = df["trial_id"].unique()
                trial_set = trial_set[1:]
                plt.figure()
                plt.xlabel("Time (s)")
                plt.ylabel("Distance to center")
                plt.xlim(0, 30)
                plt.ylim(0, 15)
                for trial in trial_set:
                    trial_df = df[df["trial_id"] == trial]
                    distance_time = (trial_df["frame_pc_timestamp"] - trial_df["frame_pc_timestamp"].iloc[0])/1000000
                    distance_to_center = np.sqrt(((trial_df["frame_x_position"] - 0) ** 2 + (trial_df["frame_z_position"] - 0) ** 2) ** 0.5)
                    distance_to_center = np.array(distance_to_center)
                    distance_time = np.array(distance_time)
                    plt.plot(distance_time, distance_to_center)
                plt.show()

def live_movement():
    parent_dir = "/mnt/NTnas/nas_vrdata/000_rYL001_P0200"

    # Get a list of all items in the directory
    all_items = os.listdir(parent_dir)

    # Filter out non-directory items and sort the remaining directories alphabetically
    directories = sorted([item for item in all_items if os.path.isdir(os.path.join(parent_dir, item))])

    for session_dir in directories:
        print("Now processing:" + session_dir)
        for file_name in os.listdir(os.path.join(parent_dir, session_dir)):
            if file_name.startswith("behavior_"):
                file_path = os.path.join(parent_dir, session_dir, file_name)
                df = pd.read_hdf(file_path, key='unity_frame')
                trial_set = df["trial_id"].unique()
                trial_set = trial_set[1:]
                for trial in trial_set:
                    plt.figure()
                    trial_df = df[df["trial_id"] == trial][100:200]
                    trial_df[trial_df["frame_angle"]<0] = trial_df[trial_df["frame_angle"]<0] + 360
                    plt.plot(trial_df["frame_x_position"], trial_df["frame_z_position"])
                    for i, row in trial_df.iterrows():
                        x, y, angle = row['frame_x_position'], row['frame_z_position'], row['frame_angle']
                        dx, dy = angle_to_vector(angle)
                        plt.arrow(x, y, dx, dy, head_width=0.2, head_length=0.3, fc='r', ec='r')
                    plt.show()

def angle_to_vector(angle):
    radians = np.deg2rad(angle)
    return np.cos(radians), np.sin(radians)

if __name__ == "__main__":
    P200_distance()


    # fname = "/mnt/NTnas/nas_vrdata/000_rYL001_P0200/2024-06-20_18-52_rYL001_P0200_GoalDirectedMovement_32min/behavior_2024-06-20_18-52_rYL001_P0200_GoalDirectedMovement_32min.hdf5"
    

    # df = pd.read_hdf(fname, key='unity_frame')

    # trial_set = df["trial_id"].unique()
    # trial_set = trial_set[1:]

    # plt.figure()
    # for trial in trial_set:
    #     trial_df = df[df["trial_id"] == trial]
    #     plt.plot(trial_df["frame_x_position"], trial_df["frame_z_position"])
    # plt.title("Trajectory")
    # plt.show()
    



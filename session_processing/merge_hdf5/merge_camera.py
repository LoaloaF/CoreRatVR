import pandas as pd
import merge_utils as utils
import os
import h5py

def merge_camera_hdf5(L, session_dir, df_trialPackage, camera_type):
    cam_file = camera_type + 'cam.hdf5'
    cam_path = os.path.join(session_dir, cam_file)

    if not os.path.exists(cam_path):
        L.logger.error(f"Failed to find camera file: {cam_path}")
        return

    # read the dataframe of camera
    df_cam = pd.read_hdf(cam_path)
    df_cam.reset_index(drop=True, inplace=True)

    with h5py.File(cam_path, 'r') as cam_file:
        # Extract the group
        cam_group = cam_file["frames"]
        # Open the target HDF5 file
        with h5py.File(session_dir + "/behavior.hdf5", 'a') as behavior_file:
            # Copy the group from the source file to the target file
            cam_file.copy(cam_group, behavior_file, name = camera_type + "_cam_frames")

    
    # add trial info into df
    df_cam = utils.add_trial_into_df(df_trialPackage, df_cam)

    # rename the columns
    cam_name_prefix = camera_type + '_cam_'
    df_cam.rename(columns={"ID": cam_name_prefix + "package_id", 
                           "PCT": cam_name_prefix + "timestamp"}, inplace=True)

    utils.merge_into_hdf5(L, session_dir, df_cam, camera_type + '_cam')

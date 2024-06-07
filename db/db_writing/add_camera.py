import sqlite3
import pandas as pd
from add_utils import *
import os
import h5py
import cv2
import numpy as np

def add_camera(conn, cursor, folder_path, df_trialPackage, camera_type):
    cam_file = camera_type + 'cam.hdf5'
    cam_path = os.path.join(folder_path, cam_file)


    df_cam = pd.read_hdf(cam_path)
    df_cam.reset_index(drop=True, inplace=True)
    df_cam = add_session_into_df(cursor, df_cam)

    df_cam['data'] = None
    df_cam['data'] = df_cam['data'].astype(object)

    hdf_cam = h5py.File(cam_path, 'r')["frames"]

    for each_hdf in hdf_cam:
        package_id = int(each_hdf.split('_')[1])

        df_cam.loc[df_cam['ID'] == package_id, 'data'] = hdf_cam[each_hdf][()]
        
    df_cam = add_trial_into_df(df_trialPackage, df_cam)

    cam_name_prefix = camera_type + '_cam_'
    df_cam.rename(columns={"ID": cam_name_prefix + "package_id", "PCT": cam_name_prefix + "timestamp", "data": cam_name_prefix + 'data'}, inplace=True)

    df_cam.to_sql(camera_type + '_cam', conn, if_exists='append', index=False)

    print(f"{camera_type} camera added successfully.")
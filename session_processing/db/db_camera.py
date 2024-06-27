import pandas as pd
from session_processing.db.db_utils import *
import os
import h5py

def db_camera(L, conn, cursor, session_dir, fname, camera_type):
    df_cam = read_file_from_hdf5(L, session_dir, fname, camera_type + 'cam_packages')

    if df_cam is None:
        return

    cam_name_prefix = camera_type + 'cam_'

    # add session info into df
    df_cam = add_session_into_df(cursor, df_cam)

    # prepare the space in df for the blob data
    df_cam[cam_name_prefix + 'data'] = None
    df_cam[cam_name_prefix + 'data'] = df_cam[cam_name_prefix + 'data'].astype(object)

    # read the blob data from hdf5 file
    cam_path = os.path.join(session_dir, fname)
    hdf_cam = h5py.File(cam_path, 'r')[cam_name_prefix + 'frames']

    for each_hdf in hdf_cam:
        package_id = int(each_hdf.split('_')[1])
        df_cam.loc[df_cam[cam_name_prefix + 'image_id'] == package_id, cam_name_prefix + 'data'] = hdf_cam[each_hdf][()]
    
    # rename the columns

    df_cam.to_sql(camera_type + 'cam', conn, if_exists='append', index=False)

    L.logger.info(f"{camera_type} camera added successfully.")
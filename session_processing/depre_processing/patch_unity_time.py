from datetime import datetime
import os
import pandas as pd
import h5py
import matplotlib.pyplot as plt

def _read_hdf5(session_dir, fname, key, drop_N_column=True):
    fullfname = os.path.join(session_dir, fname)
    if not os.path.exists(fullfname):
        print(f"Cannot find {fullfname}")
        return
    
    with h5py.File(fullfname, 'r') as f:
        if key not in f.keys():
            print(f"Failed to find {key} key in {fname}, trying with "
                           f"'packages' key...")
            if (key := 'packages') not in f.keys():
                print(f"Failed to find {key} key in {fname}.")
            return
    try:
        data = pd.read_hdf(fullfname, key=key)
    except Exception as e:
        print(f"Found the key {key} but failed to read the key {key} "
                       f"from {fullfname}.\n{e}")
        return

    data.reset_index(drop=True, inplace=True)
    if drop_N_column:
        data.drop(columns=['N'], inplace=True, errors='ignore')

    return data


def patch_unity_time(df_PCT, fname):
    df_microseconds = df_PCT % 10**6
    df_fixed = df_PCT - df_microseconds/2
    df_fixed = df_fixed.astype(int)
    df_fixed_half = df_fixed.copy()


    df_diff = df_fixed.diff()
    df_diff_rise = df_diff[df_diff > 500000]

    for i in df_diff_rise.index:
        drop_index = 0
        while(True):
            # print(f"Fixing {i + drop_index}...")
            if (i + drop_index) >= len(df_fixed):
                break
            elif df_diff[i + drop_index] < 0:
                break
            else:
                df_fixed[i + drop_index] = df_fixed[i + drop_index] - 500000
                drop_index += 1

    plt.figure(1)
    plt.hist(df_PCT.diff())
    plt.hist(df_fixed.diff())
    plt.legend(["Original", "Fixed"])
    plt.title(fname)
    plt.show()

    plt.figure(2)
    show_start = 10000
    show_end = show_start + 1000
    plt.plot(df_PCT[show_start:show_end])
    plt.scatter(df_PCT[show_start:show_end].index, df_PCT[show_start:show_end])
    plt.plot(df_fixed_half[show_start:show_end])
    plt.scatter(df_fixed_half[show_start:show_end].index, df_fixed_half[show_start:show_end])
    plt.plot(df_fixed[show_start:show_end])
    plt.scatter(df_fixed[show_start:show_end].index, df_fixed[show_start:show_end])
    plt.show()
    return df_fixed

def patch_df(fname, key, full_fname):
    df = _read_hdf5(session_dir, fname, key)
    df["PCT"] = patch_unity_time(df["PCT"], full_fname)

    with h5py.File(full_fname, 'a') as hdf:
        del hdf[key]

    with pd.HDFStore(full_fname) as hdf:
        hdf.put(key, pd.DataFrame(), format='table', append=False)

    df.to_hdf(full_fname, key=key, mode='a', append=True, format="table")

if __name__ == "__main__":

    # parent_folder = '/mnt/NTnas/nas_vrdata/'

    # # Define the string to look for in folder names
    # search_string = 'GoalDirectedMovement'

    # # Loop through each item in the parent folder
    # for folder_name in os.listdir(parent_folder):
    #     # Construct the full path to the item
    #     folder_path = os.path.join(parent_folder, folder_name)
        
    #     # Check if the item is a directory and contains the search string
    #     if os.path.isdir(folder_path) and search_string in folder_name:
            
    session_dir = '/mnt/NTnas/nas_vrdata/2024-07-04_17-43-13_400'

    fname = 'unity_output.hdf5'
    key = 'unityframes'
    full_fname = os.path.join(session_dir, fname)
    patch_df(fname, key, full_fname)


    fname = 'unitycam.hdf5'
    key = 'frame_packages'
    full_fname = os.path.join(session_dir, fname)
    
    patch_df(fname, key, full_fname)

    print(f"Done with {session_dir}")



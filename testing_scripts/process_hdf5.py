import pandas as pd
import numpy as np
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from scipy.signal import find_peaks
import os
import warnings

# notice here to avoid mean of slice warning we ignore the runtimewarning
warnings.simplefilter(action='ignore', category=RuntimeWarning)

def load_hdf5_data(full_fname, key):
    # load data: full_fname should be the file type
    try:
        df = pd.read_hdf(full_fname, key=key)
    except KeyError:
        df = pd.read_hdf(full_fname)

    return df

def process_unity_file(df_unity, file_name):
    x_val = df_unity["X"]
    z_val = df_unity["Z"]
    a_val = df_unity["A"]

    plt.figure()
    plt.plot(np.array(z_val))
    plt.title(file_name + " X")

    # Peak value of x and z; difference between peak and valley of A
    x_peaks = find_all_peak_values(x_val)
    z_peaks = find_all_peak_values(z_val)
    a_diffs = rotation_diff(a_val)

    print("X RelativePeak: ", x_peaks.mean(), f"gain: {157.079632679/x_peaks.mean()}")
    print("Z RelativePeak: ", z_peaks.mean(), f"gain: {157.079632679/z_peaks.mean()}")
    print("A RelativePeak: ", a_diffs.mean(), f"gain: {360/a_diffs.mean()}")

    return x_peaks, z_peaks, a_diffs

def process_portenta_file(df_portenta, file_name):

    Vr_peaks = None
    Vy_peaks = None
    Vp_peaks = None

    # if something wrong with portenta_output.hdf5, return None
    try:
        Vr_val = df_portenta["Vr"]
        Vy_val = df_portenta["Vy"]
        Vp_val = df_portenta["Vp"]

        Vr_peaks = find_all_peak_values(Vr_val)
        Vy_peaks = find_all_peak_values(Vy_val)
        Vp_peaks = find_all_peak_values(Vp_val)

        print("Vr RelativePeak: ", Vr_peaks.mean())
        print("Vy RelativePeak: ", Vy_peaks.mean())
        print("Vp RelativePeak: ", Vp_peaks.mean())
    except:
        print("No Vr, Vy, Vp values found in portenta_output.hdf5")

    return Vr_peaks, Vy_peaks, Vp_peaks



def find_all_peak_values(df_value):
    value = np.array(df_value)
    diff = np.diff(value)
    peakVals = value[np.where(diff<-50)[0]]
    return peakVals


def rotation_diff(df_value):
    value = np.array(df_value)
    diff = np.diff(value)

    # peakVal should be the datapoint after a high gradient
    peakVals = value[np.where(diff>50)[0]+1]
    vallyVals = value[np.where(diff<-50)[0]]

    # to avoid dimension inconsistency, we caculate the minimum of the two
    min_shape = np.min([peakVals.shape[0], vallyVals.shape[0]])

    diffVal = peakVals[:min_shape] - vallyVals[:min_shape]
    return diffVal

if __name__ == "__main__":
    # load data
    unity_key = "packages"
    portenta_key = "portentaoutput"
    
    folder_path = "../data/"
    subfolders = []
    for subfolder in os.listdir(folder_path):
        if 'rotation' in subfolder or 'forward' in subfolder or 'sideways' in subfolder: 
            
            print("--------------------------------------------------------")
            print(subfolder)
            subfolder_path = os.path.join(folder_path, subfolder) 

            unity_file_path = os.path.join(subfolder_path, "unity_output.hdf5")
            df_unity = load_hdf5_data(unity_file_path, unity_key)
            x_peaks, z_peaks, a_diffs = process_unity_file(df_unity, subfolder)

            
            portenta_file_path = os.path.join(subfolder_path, "portenta_output.hdf5")
            df_portenta = load_hdf5_data(portenta_file_path, portenta_key)
            Vr_peaks, Vy_peaks, Vp_peaks = process_portenta_file(df_portenta, subfolder)
        
    
    # plt.show()

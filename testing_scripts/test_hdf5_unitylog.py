import pandas as pd
import numpy as np
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from scipy.signal import find_peaks


def load_hdf5_data(full_fname, key):
    # load data
    df = pd.read_hdf(full_fname, key=key)
    return df

def draw_hist(name, dat, ax, minmax):
    ax.hist(dat, bins=100, label=name, alpha=.8, range=minmax)
    ax.set_yscale('log')

    perc_99 = np.percentile(dat, 99)
    perc_90 = np.percentile(dat, 90)

    ax.axvline(x=perc_99, color='red', linestyle='--', label=f'99th perc: {perc_99:.3}')
    ax.axvline(x=perc_90, color='orange', linestyle='--', label=f'90th perc: {perc_90:.3}')
    ax.legend()
    
def setup_hist(n):
    fig, axes = plt.subplots(n, sharex=True)
    plt.xlabel("serial port buffer checks deltatime [ms]")
    plt.ticklabel_format(axis="x", useOffset=False, style='plain')
    return axes

def plot_package_deltatimes(df):
    min_dt = np.min(np.concatenate((df["PCT"], df["T"])))
    max_dt = np.max(np.concatenate((df["PCT"], df["T"])))
    max_dt = 10
    min_dt = 0

    hist_data = {
        "portenta_package_detatimes": df["T"],
        "fresh_package_PC_detatimes": df["PCT"][df["F"].astype(bool)],
        "old_package_PC_detatimes": df["PCT"][~df["F"].astype(bool)],
    }

    axes = setup_hist(len(hist_data))
    for i, (name, data) in enumerate(hist_data.items()):
        if not data.empty:
            draw_hist(name, data, axes[i], (min_dt,max_dt))

def plot_T_PCT_comparison(df):
    chunk = 1000
    nchunks = len(df)//1000 +1
    fig, axes = plt.subplots(nrows=nchunks, figsize=(18,2*nchunks))
    if nchunks == 1:
        axes = [axes]
    fig.subplots_adjust(left=.03, right=.995, bottom=.03, hspace=.2, top=.99)
    
    for i in range(nchunks):
        xmin = i*chunk
        xmax = (i+1)*chunk
        dat = df.iloc[xmin:xmax].reset_index(drop=True)
        axes[i].spines["top"].set_visible(False)
        axes[i].spines["right"].set_visible(False)
        # axes[i].set_xlim(xmin-20,xmax+20)

        axes[i].set_ylim(0,5)
        
        if i == 0:
            axes[i].set_ylabel("package deltatime [ms]")
            axes[i].set_xlabel("package ID", labelpad=-10)
        else:
            # axes[i].tick_params(bottom=False, labelleft=False)
            pass
        
        printPCT_fresh = dat["PCT"][dat["F"].astype(bool)]
        printPCT_old = dat["PCT"][~dat["F"].astype(bool)]
        axes[i].scatter(dat.index, dat["T"], s=5, alpha=.6)
        axes[i].scatter(printPCT_fresh.index, printPCT_fresh, s=5, color='orange', alpha=.6)
        axes[i].scatter(printPCT_old.index, printPCT_old, s=50, marker="|", color='orange', alpha=.4)
        
        S_df = dat[dat["N"] == "S"]
        R_df = dat[dat["N"] == "R"]
        axes[i].scatter(S_df.index, S_df["T"], s=50, marker="o", edgecolor="green", facecolor='None')
        axes[i].scatter(R_df.index, R_df["T"], s=50, marker="o", edgecolor="black", facecolor='None')


def printMaxValues(df_value):
    value = np.array(df_value)
    diff = np.diff(value)
    maxVals = value[np.where(diff<-50)[0]]
    print(maxVals)


if __name__ == "__main__":
    import os
    base_path = '../data/'
    all_dirs = sorted(os.listdir(base_path))
    # full_fname = os.path.join(base_path, all_dirs[-1], "unity_output.hdf5")

    full_fname = "/home/vrmaster/projects/ratvr/VirtualReality/data/2024-05-15_13-29-50_goodone_9th_session/portenta_output.hdf5"    
    df = pd.read_hdf(full_fname, key="portentaoutput")
    print(df.columns)



    # full_fname = "/home/ntgroup/Project/CoreRatVR/testing_scripts/Data/2024-05-02_17-19-56_forward_P10000/unity_output.hdf5"    
    
    # df = load_hdf5_data(full_fname, "packages")
    # z = df["Z"]

    # printMaxValues(z)




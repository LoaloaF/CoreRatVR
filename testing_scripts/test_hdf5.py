import pandas as pd
import numpy as np
key = "arduino_packages"
df = pd.read_hdf("../data/data.hdf5", key=key)
print(df)

ds = np.diff(df.index.values)
print([df.iloc[1:][ds!=1]])
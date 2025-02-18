

# import tables

# file_path = "/Volumes/large/BMI/VirtualReality/SpatialSequenceLearning/raw_raw_data/2025-01-22_17-59-02_active_ooStorageCorrupted/ephys_output.raw.h5"

# try:
#     with tables.open_file(file_path, "r") as f:
#         print("Opened successfully! Found nodes:", f.root._v_children.keys())
# except Exception as e:
#     print("PyTables could not open the file:", e)


import h5py
import shutil
import os

file_path = "/Volumes/large/BMI/VirtualReality/SpatialSequenceLearning/raw_raw_data/2025-01-22_17-59-02_active_ooStorageCorrupted/ephys_output.raw.h5"

temp_path = file_path + ".temp"

def is_h5_valid(path):
    """Try to open the HDF5 file and return True if successful, False otherwise."""
    try:
        with h5py.File(path, "r"):
            return True
    except Exception as e:
        return False

# Make a backup before modifying
# shutil.copy(file_path, temp_path)

# Get file size
file_size = os.path.getsize(temp_path)

print(f"Original file size: {file_size} bytes")

for i in range(1, min(1_000_000, file_size)):  # Try up to 100,000 bytes
    new_size = file_size - i
    os.truncate(temp_path, new_size)  # Remove i bytes
    
    if i % 1000 == 0:
        print(f"Trying to open the file after truncating {i} bytes...")

    if is_h5_valid(temp_path):
        print(f"✅ Successfully opened the file after truncating {i} bytes!")
        print(f"New file size: {new_size} bytes")
        os.rename(temp_path, file_path + "_fixed.h5")  # Save the fixed version
        break
else:
    print("❌ Could not recover the file by truncating bytes.")
    os.remove(temp_path)  # Clean up


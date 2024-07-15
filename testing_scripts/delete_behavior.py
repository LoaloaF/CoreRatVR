import os

# Define the parent directory
parent_folder = '/mnt/NTnas/nas_vrdata/'

# Define the prefix of the file name to delete
file_prefix = 'behavior_'

# Loop through each item in the parent folder
for folder_name in os.listdir(parent_folder):
    # Construct the full path to the item
    folder_path = os.path.join(parent_folder, folder_name)
    
    # Check if the item is a directory
    if os.path.isdir(folder_path):
        # Loop through each file in the directory
        for file_name in os.listdir(folder_path):
            # Check if the file name starts with the specified prefix
            if file_name.startswith(file_prefix):
                # Construct the full path to the file
                file_path = os.path.join(folder_path, file_name)
                try:
                    # Delete the file
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file: {file_path}, error: {e}")
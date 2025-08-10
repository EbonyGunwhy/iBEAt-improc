import os
import shutil

root_dir = "G:\Shared drives\iBEAt Build\dixon\stage_2_data\Patients\Turku"

for dirpath, dirnames, filenames in os.walk(root_dir):
    depth = dirpath[len(root_dir):].count(os.sep)
    
    if depth == 2:
        for dirname in dirnames:
            dir_to_remove = os.path.join(dirpath, dirname)
            print(f"Removing directory: {dir_to_remove}")
            shutil.rmtree(dir_to_remove)  # Deletes folder and all contents
        # Prevent os.walk from going deeper into removed dirs
        dirnames.clear()

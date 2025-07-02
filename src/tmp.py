import os


def rename_directories(root_folder):
    """
    Walks through the folder hierarchy starting from root_folder and renames each directory 
    by replacing old_substring with new_substring.

    Parameters:
        root_folder (str): The top-level directory to start renaming from.
        old_substring (str): The substring to replace.
        new_substring (str): The substring to replace with.
    """
    for dirpath, dirnames, _ in os.walk(root_folder, topdown=False):  # Bottom-up traversal
        for dirname in dirnames:
            if dirname[:8] == 'patient_':
                new_dirname = dirname.replace('patient_', 'Patient__')
            elif dirname[:6] == 'study_':
                new_dirname = dirname.replace('study_[', 'Study__')
                new_dirname = new_dirname.replace(']', '_')
            elif dirname[:7] == 'series_':
                new_dirname = dirname.replace('series_[', 'Series__')
                new_dirname = new_dirname.replace(']', '_')
            else:
                continue
            old_dir = os.path.join(dirpath, dirname)
            new_dir = os.path.join(dirpath, new_dirname)
            
            print(f"Renaming: {old_dir} -> {new_dir}")
            os.rename(old_dir, new_dir)

    print("✅ Renaming complete!")

# Example usage:
# rename_directories('/path/to/folder', 'old', 'new')


if __name__=='__main__':

    rename_directories("C:\\Users\\md1spsx\\Documents\\GitHub\\iBEAt-improc\\build")
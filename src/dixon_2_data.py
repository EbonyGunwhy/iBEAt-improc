import os
import zipfile
import shutil
import logging

import pydicom
import dbdicom as db

downloadpath = os.path.join(os.getcwd(), 'build', 'dixon_1_download')
datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')


# Set up logging
logging.basicConfig(
    filename=os.path.join(datapath, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def flatten_folder(root_folder):
    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=False):
        for filename in filenames:
            src_path = os.path.join(dirpath, filename)
            dst_path = os.path.join(root_folder, filename)
            
            # If file with same name exists, optionally rename or skip
            if os.path.exists(dst_path):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dst_path):
                    dst_path = os.path.join(root_folder, f"{base}_{counter}{ext}")
                    counter += 1

            shutil.move(src_path, dst_path)

        # Remove empty subdirectories (but skip the root folder)
        if dirpath != root_folder:
            try:
                os.rmdir(dirpath)
            except OSError:
                print(f"Could not remove {dirpath} — not empty or in use.")


def leeds_ibeat_patient_id(folder):
    if folder[:3]=='iBE':
        return folder[4:].replace('-', '_')
    else:
        return folder[:4] + '_' + folder[4:]

def bari_ibeat_patient_id(folder):
    if folder[:3]=='iBE':
        return folder[4:].replace('-', '_')
    else:
        return folder[:4] + '_' + folder[4:]
    

def leeds_rename_folder(folder):

    # If a series is among the first 20, assume it is precontrast
    name = os.path.basename(folder)
    series_nr = int(name[-2:])
    if series_nr < 20:
        folder_name = 'Dixon_1_'
    else:
        folder_name = 'Dixon_post_contrast_1_'

    # Add image type to the name
    file = os.listdir(folder)[0]
    ds = pydicom.dcmread(os.path.join(folder, file))
    image_type = ds['ImageType'].value
    props = image_type[3]
    if props == 'IN_PHASE':
        folder_name += 'in_phase'  
    elif props == 'OUT_PHASE':
        folder_name += 'out_phase'
    elif props == 'WATER':
        folder_name += 'water'
    elif props == 'FAT':
        folder_name += 'fat'
    else:
        folder_name += props
    new_folder = os.path.join(os.path.dirname(folder), folder_name)

    # If file with same name exists, increment the counter
    if os.path.exists(new_folder):
        counter = 2
        while os.path.exists(new_folder):
            new_folder = os.path.join(os.path.dirname(folder), folder_name.replace('_1_', f'_{counter}_'))
            counter += 1
    shutil.move(folder, new_folder)
    shutil.rmtree(folder, ignore_errors=True)


def bari_rename_folder(folder):

    # If a series is among the first 20, assume it is precontrast
    name = os.path.basename(folder)
    series_nr = int(name[7:])
    if series_nr < 1000:
        folder_name = 'Dixon_1'
    else:
        folder_name = 'Dixon_post_contrast_1'

    # Create a new folder
    new_folder = os.path.join(os.path.dirname(folder), folder_name)
    # If file with same name exists, increment the counter
    if os.path.exists(new_folder):
        counter = 2
        while os.path.exists(new_folder):
            new_folder = os.path.join(os.path.dirname(folder), folder_name.replace('_1_', f'_{counter}_'))
            counter += 1
    # Move data to the new folder and remove the old
    shutil.move(folder, new_folder)
    shutil.rmtree(folder, ignore_errors=True)
    return new_folder


def bari_split_series(folder):
    name = os.path.basename(folder)
    vol = db.volume(folder, 'EchoTime')
    vol = vol[0].separate()
    if vol.size==1: # nothing to split
        return
    ref = db.series(folder)[0]
    patient = os.path.basename(os.path.dirname(folder))
    for i, scan in enumerate(['_out_phase', '_in_phase']):
        path = os.path.join(os.path.dirname(folder), name + scan)
        db.write_volume(vol[i], [path, patient, name, name + scan], ref)
        os.remove(os.path.join(path, 'dbtree.json'))
        flatten_folder(path)
    shutil.rmtree(folder)


def leeds():
    # Clean Leeds patient data
    sitedownloadpath = os.path.join(downloadpath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients")
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients") 
    os.makedirs(sitedatapath, exist_ok=True)
    patients = [f.path for f in os.scandir(sitedownloadpath) if f.is_dir()]
    for pat in patients:
        pat_id = leeds_ibeat_patient_id(os.path.basename(pat))
        new_path = os.path.join(sitedatapath, pat_id)
        os.makedirs(new_path, exist_ok=True)
        for zip_series in os.scandir(pat):
            # Get the name of the zip file without extension
            zip_name = os.path.splitext(os.path.basename(zip_series.path))[0]
            # Create a subfolder using that name
            extract_to = os.path.join(new_path, zip_name)
            os.makedirs(extract_to, exist_ok=True)
            # Extract to the subfolder
            with zipfile.ZipFile(zip_series.path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            # Flatten the extracted folder
            flatten_folder(extract_to)
            # Rename the extracted folder
            leeds_rename_folder(extract_to)


def bari():
    # Clean Bari patient data
    sitedownloadpath = os.path.join(downloadpath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    os.makedirs(datapath, exist_ok=True)
    # Loop over all patients
    patients = [f.path for f in os.scandir(sitedownloadpath) if f.is_dir()]
    for pat in patients:
        # Get a standardized ID from the folder name
        pat_id = bari_ibeat_patient_id(os.path.basename(pat))
        # Create a folder with theat name in the database
        new_path = os.path.join(sitedatapath, pat_id)
        os.makedirs(new_path, exist_ok=True)
        # Loop over all series
        for zip_series in os.scandir(pat):
            # Get the name of the zip file without extension
            zip_name = os.path.splitext(os.path.basename(zip_series.path))[0]
            # Series with 'OT' in name are not images
            if 'OT' not in zip_name:
                # Create a subfolder using that name
                extract_to = os.path.join(new_path, zip_name)
                os.makedirs(extract_to, exist_ok=True)
                # Extract to the subfolder
                with zipfile.ZipFile(zip_series.path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                # Flatten the extracted folder
                flatten_folder(extract_to)
                # Rename the extracted folder
                new_extract_to = bari_rename_folder(extract_to)
                # Split series (In/Opp phase)
                try:
                    bari_split_series(new_extract_to)
                except Exception as e:
                    logging.error(
                        f"Error splitting Bari series {pat_id} "
                        f"{os.path.basename(new_extract_to)}."
                        f"The series is not included in the database."
                        f"Details of the error: {e}"
                    )
                    shutil.rmtree(new_extract_to)


def all():
    leeds()
    bari()


if __name__=='__main__':
    # TODO: keep pt, study, series hierarchy in Datbase (study='baseline', 'followup')
    # write with dbdicom to keep coherent database
    
    leeds()
    bari()
    

    


    
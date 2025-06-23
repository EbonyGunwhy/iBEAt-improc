"""
Create clean database
---------------------

Leeds
-----

62 cases in database & on XNAT.

Bari
----

72 cases in database, 74 on XNAT.

Not included in database:

Bari 1128_013: data on XNAT unusable/incomplete - check google drive, then with Bari if data are correct in archive.
Bari 1128_018: data on XNAT unusable/incomplete - check google drive, then with Bari if data are correct in archive.
"""

import os
import zipfile
import shutil
import logging

from tqdm import tqdm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import pydicom
import dbdicom as db


# These datasets are unusable and not included in the database.

BARI_UNUSABLE = [
    '1128_013', # Only one single image in DIXON series on XNAT. Other scans also incomplete - check with Bari.
]


downloadpath = os.path.join(os.getcwd(), 'build', 'dixon_1_download')
datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
os.makedirs(datapath, exist_ok=True)


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
        return folder[-7:-3] + '_' + folder[-3:]

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


def leeds_add_series_name(folder, all_series:list):

    # If a series is among the first 20, assume it is precontrast
    name = os.path.basename(folder)
    series_nr = int(name[-2:])
    if series_nr < 20:
        series_name = 'Dixon_1_'
    else:
        series_name = 'Dixon_post_contrast_1_'

    # Add image type to the name
    file = os.listdir(folder)[0]
    ds = pydicom.dcmread(os.path.join(folder, file))
    image_type = ds['ImageType'].value
    props = image_type[3]
    if props == 'IN_PHASE':
        series_name += 'in_phase'  
    elif props == 'OUT_PHASE':
        series_name += 'out_phase'
    elif props == 'WATER':
        series_name += 'water'
    elif props == 'FAT':
        series_name += 'fat'
    else:
        series_name += props
    
    # Add the appropriate number
    new_series_name = series_name
    counter = 2
    while new_series_name in all_series:
        new_series_name = series_name.replace('_1_', f'_{counter}_')
        counter += 1
    all_series.append(new_series_name)



def bari_add_series_name(name, all_series:list):

    # If a series is among the first 20, assume it is precontrast
    series_nr = int(name[7:])
    if series_nr < 1000:
        series_name = 'Dixon_1_'
    else:
        series_name = 'Dixon_post_contrast_1_'
    
    # Increment the number as appropriate
    new_series_name = series_name
    counter = 2
    while new_series_name in all_series:
        new_series_name = series_name.replace('_1_', f'_{counter}_')
        counter += 1
    all_series.append(new_series_name)


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


def leeds_check_fatwater_swap():

    # Set up folders
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients") 
    sitepngpath = os.path.join(datapath, "BEAt-DKD-WP4-Leeds")
    os.makedirs(sitepngpath, exist_ok=True)

    # If the file exists, dont build the figure
    file = os.path.join(sitepngpath, 'fat-water swap check.png')
    if os.path.exists(file):
        return

    # Get out phase series
    series = db.series(sitedatapath)
    series_fat = [s for s in series if s[-1][0][-3:]=='fat']

    # Build list of center slices
    center_slices = []
    for series in tqdm(series_fat, desc='Reading fat images'):
        vol = db.volume(series)
        center_slice = vol.values[:,:,round(vol.shape[-1]/2)]
        center_slices.append(center_slice)

    # Display center slices as mosaic
    ncols = int(np.ceil(np.sqrt(len(center_slices))))
    fig, ax = plt.subplots(nrows=ncols, ncols=ncols, gridspec_kw = {'wspace':0, 'hspace':0}, figsize=(10,10), dpi=300)

    i=0
    for row in tqdm(ax, desc='Building png'):
        for col in row:

            col.set_xticklabels([])
            col.set_yticklabels([])
            col.set_aspect('equal')
            col.axis("off")

            if i < len(center_slices):

                # Show center image
                col.imshow(
                    center_slices[i].T, 
                    cmap='gray', 
                    interpolation='none', 
                    vmin=0, 
                    vmax=np.mean(center_slices[i]) + 2 * np.std(center_slices[i])
                )
                # Add white text with black background in upper-left corner
                col.text(
                    0.01, 0.99,                   
                    f'{series_fat[i][1][0]} - {series_fat[i][-1]}',   
                    color='white',
                    fontsize=2,
                    ha='left',
                    va='top',
                    transform=col.transAxes,     # Use axes coordinates
                    bbox=dict(facecolor='black', alpha=0.7, boxstyle='round,pad=0.3')
                )

            i+=1 

    fig.suptitle('FatMaps', fontsize=14)
    fig.savefig(file)
    plt.close()


def leeds_054():

    # Clean Leeds patient 054
    pat = os.path.join(downloadpath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients", 'iBE-4128-054')
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients") 
    temp_folder = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", 'tmp')
    os.makedirs(sitedatapath, exist_ok=True)
    
    # Extract to a temporary folder
    os.makedirs(temp_folder, exist_ok=True)
    for zip_series in os.scandir(pat):
        with zipfile.ZipFile(zip_series.path, 'r') as zip_ref:
            zip_ref.extractall(temp_folder)
    flatten_folder(temp_folder)

    dixon = {
        4: 'Dixon_out_phase',
        5: 'Dixon_in_phase',
        6: 'Dixon_fat',
        7: 'Dixon_water',
        41: 'Dixon_post_contrast_out_phase',
        42: 'Dixon_post_contrast_in_phase',
        43: 'Dixon_post_contrast_fat',
        44: 'Dixon_post_contrast_water',
    }
    
    # Group the series
    for s in db.series(temp_folder):
        v = db.unique('SeriesNumber', s)[0]
        new_series = [sitedatapath, '4128_054', 'Baseline', dixon[v]]
        db.move(s, new_series)

    # delete tmp folder
    shutil.rmtree(temp_folder)

        


def leeds():

    # Clean Leeds patient data
    sitedownloadpath = os.path.join(downloadpath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients")
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients") 
    temp_folder = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", 'tmp')
    os.makedirs(sitedatapath, exist_ok=True)
    
    # Loop over all patients
    patients = [f.path for f in os.scandir(sitedownloadpath) if f.is_dir()]
    for pat in patients:

        # Get a standardized ID from the folder name
        pat_id = leeds_ibeat_patient_id(os.path.basename(pat))

        # If the dataset already exists, continue to the next
        subdirs = [d for d in os.listdir(sitedatapath)
           if os.path.isdir(os.path.join(sitedatapath, d))]
        if f'patient_{pat_id}' in subdirs: 
            continue

        # Exception with unique folder structure
        if pat_id == '4128_054':
            leeds_054()
            continue

        pat_series = []
        for zip_series in os.scandir(pat):

            # Get the name of the zip file without extension
            zip_name = os.path.splitext(os.path.basename(zip_series.path))[0]

            # Extract to a temporary folder and flatten
            os.makedirs(temp_folder, exist_ok=True)
            extract_to = os.path.join(temp_folder, zip_name)
            with zipfile.ZipFile(zip_series.path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            flatten_folder(extract_to)

            # Add new series name to the list
            try:
                leeds_add_series_name(extract_to, pat_series)
            except Exception as e:
                logging.error(f"Patient {pat_id} - error renaming {zip_name}: {e}")
                shutil.rmtree(extract_to)
                continue

            # Copy to the database using the harmonized names
            dixon = db.series(extract_to)[0]
            dixon_clean = [sitedatapath, pat_id, 'Baseline', pat_series[-1]]
            db.copy(dixon, dixon_clean)

            # Clean up tmp folder
            shutil.rmtree(temp_folder)

    # Build mosaic to check fat-water swap
    leeds_check_fatwater_swap()



def bari():

    # Define input and output folders
    sitedownloadpath = os.path.join(downloadpath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    temp_folder = os.path.join(sitedatapath, 'tmp')

    # Loop over all patients
    patients = [f.path for f in os.scandir(sitedownloadpath) if f.is_dir()]
    for pat in patients:

        # Get a standardized ID from the folder name
        pat_id = bari_ibeat_patient_id(os.path.basename(pat))

        # Corrupted data
        if pat_id in BARI_UNUSABLE:
            continue

        # If the dataset already exists, continue to the next
        subdirs = [d for d in os.listdir(sitedatapath)
           if os.path.isdir(os.path.join(sitedatapath, d))]
        if f'patient_{pat_id}' in subdirs:
            continue

        # Find all zip series, remove those with 'OT' in the name and sort by series number
        all_zip_series = [f for f in os.listdir(pat) if os.path.isfile(os.path.join(pat, f))]
        all_zip_series = [s for s in all_zip_series if 'OT' not in s]
        all_zip_series = sorted(all_zip_series, key=lambda x: int(x[7:-4]))

        # loop over all series
        pat_series = []
        for zip_series in all_zip_series:

            # Get the name of the zip file without extension
            zip_name = zip_series[:-4]

            # # Series with 'OT' in name are not images
            # if 'OT' in zip_name:
            #     continue

            # Extract to a temporary folder and flatten it
            os.makedirs(temp_folder, exist_ok=True)
            try:
                extract_to = os.path.join(temp_folder, zip_name)
                with zipfile.ZipFile(os.path.join(pat, zip_series), 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            except Exception as e:
                logging.error(f"Patient {pat_id} - error extracting {zip_name}: {e}")
                shutil.rmtree(temp_folder)
                continue

            flatten_folder(extract_to)

            # Get the harmonized series name 
            try:
                bari_add_series_name(zip_name, pat_series)
            except Exception as e:
                logging.error(f"Patient {pat_id} - error renaming {zip_name}: {e}")
                shutil.rmtree(temp_folder)
                continue

            # Split series into in- and opposed phase
            dixon = db.series(extract_to)[0]
            try:
                dixon_split = db.split_series(dixon, 'EchoTime')
            except Exception as e:
                logging.error(
                    f"Error splitting Bari series {pat_id} "
                    f"{os.path.basename(extract_to)}."
                    f"The series is not included in the database.\n"
                    f"--> Details of the error: {e}")
                shutil.rmtree(temp_folder)
                continue
            
            # Copy split series to the database using the harmonized names
            out_phase_clean = [sitedatapath, pat_id, 'Baseline', pat_series[-1] + 'out_phase']
            in_phase_clean = [sitedatapath, pat_id, 'Baseline', pat_series[-1] + 'in_phase']
            TE = list(dixon_split.keys())
            if len(TE) == 1:
                logging.error(
                    f"Bari patient {pat_id}, series "
                    f"{os.path.basename(extract_to)}: "
                    f"Only one echo time found. Excluded from database.")
                shutil.rmtree(temp_folder)
                continue               
            db.copy(dixon_split[TE[0]], out_phase_clean)
            db.copy(dixon_split[TE[1]], in_phase_clean)
            shutil.rmtree(temp_folder)

            # # Predict fat and water
            # # ---------------------
            # This works but the results are poor
            # Uncomment when the method has been improved

            # try:
            #     out_phase = db.volume(out_phase_clean)
            #     in_phase = db.volume(in_phase_clean)
            # except Exception as e:
            #     logging.error(
            #         f"Patient {pat_id}: error predicting fat-water separation. "
            #         f"Cannot read out-phase or in-phase volumes: {e}")
            #     continue
            # array = np.stack((out_phase.values, in_phase.values), axis=-1)
            # fw = miblab.kidney_dixon_fat_water(array)

            # # Save fat and water
            # fat = [sitedatapath, pat_id, 'Baseline', pat_series[-1] + 'fat']
            # water = [sitedatapath, pat_id, 'Baseline', pat_series[-1] + 'water']
            # ref = out_phase_clean
            # db.write_volume((fw['fat'], out_phase.affine), fat, ref)
            # db.write_volume((fw['water'], out_phase.affine), water, ref)






def all():
    leeds()
    bari()


if __name__=='__main__':

    leeds()
    bari()
    
    

    


    
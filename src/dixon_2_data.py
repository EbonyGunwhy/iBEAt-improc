"""
Create clean database
"""

import os
import zipfile
import shutil
import logging
import tempfile
import csv

from tqdm import tqdm
import numpy as np
import pydicom
import dbdicom as db
import vreg


EXCLUDE = [
    '7128_054', # TODO: (Passed on to Kevin). Post contrast outphase not complete (233/248 slices), water map missing. Looks like incomplete data transfer. 
    '7128_065', # TODO: (Passed on to Kevin). Missing post-contrast In-phase and Out-phase (fat and water are there) and precontrast Water (the others are there)
    '7128_148', # TODO: (Passed on to Kevin). Missing post-contrast out_phase (fat, in-phase and water are there). Missing precontrast water (fat, inphase, outphase are there)
    '7128_155', # TODO: (Passed on to Kevin). Precontrast missing in-phase. Post-contrast mssing in-phase, out-phase (fat/water are there)
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

def sheffield_ibeat_patient_id(folder):
    id = folder[3:]
    id = id[:4] + '_' + id[4:]
    if id == '2178_157': # Data entry error
        id = '7128_157'
    return id

def turku_ge_ibeat_patient_id(folder):
    id = folder[4:].replace('-', '_')
    if "followup" in id:
        id = id[:8] + "_followup"
    else:
        id = id[:8]

    return id

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


def sheffield_add_series_desc(folder, all_series:list):

    # Read series description from file
    file = os.listdir(folder)[0]
    ds = pydicom.dcmread(os.path.join(folder, file))
    original_series_desc = ds['SeriesDescription'].value
    
    # For Philips decide based on EchoTime - no fat-water included
    if ds['Manufacturer'].value == 'Philips Healthcare':
        if ds['EchoTime'].value < 2:
            if original_series_desc == 'T1w_abdomen_dixon_cor_bh':
                series_desc = 'Dixon_1_out_phase'
            else:
                series_desc = 'Dixon_post_contrast_1_out_phase'
        else:
            if original_series_desc == 'T1w_abdomen_dixon_cor_bh':
                series_desc = 'Dixon_1_in_phase'
            else:
                series_desc = 'Dixon_post_contrast_1_in_phase'

    # For GE translate descriptions to standard convention
    else:
        new_series_desc = {
            'WATER: T1_abdomen_dixon_cor_bh': 'Dixon_1_water',
            'FAT: T1_abdomen_dixon_cor_bh': 'Dixon_1_fat',
            'InPhase: T1_abdomen_dixon_cor_bh': 'Dixon_1_in_phase',
            'OutPhase: T1_abdomen_dixon_cor_bh': 'Dixon_1_out_phase',
            'WATER: T1_abdomen_post_contrast_dixon_cor_bh': 'Dixon_post_contrast_1_water',
            'FAT: T1_abdomen_post_contrast_dixon_cor_bh': 'Dixon_post_contrast_1_fat',
            'InPhase: T1_abdomen_post_contrast_dixon_cor_bh': 'Dixon_post_contrast_1_in_phase',
            'OutPhase: T1_abdomen_post_contrast_dixon_cor_bh': 'Dixon_post_contrast_1_out_phase',
        }
        series_desc = new_series_desc[original_series_desc]

    # Increment counter if needed
    new_series_desc = series_desc
    counter = 2
    while new_series_desc in all_series:
        new_series_desc = series_desc.replace('_1_', f'_{counter}_')
        counter += 1
    all_series.append(new_series_desc)

def turku_add_series_desc(folder, all_series:list):

    # Read series description from file
    file = os.listdir(folder)[0]
    ds = pydicom.dcmread(os.path.join(folder, file))
    original_series_desc = ds['SeriesDescription'].value
    
    # For Philips decide based on EchoTime - no fat-water included
    if ds['Manufacturer'].value == 'Philips Healthcare':
        if ds['EchoTime'].value < 2:
            if original_series_desc == 'T1w_abdomen_dixon_cor_bh':
                series_desc = 'Dixon_1_out_phase'
            else:
                series_desc = 'Dixon_post_contrast_1_out_phase'
        else:
            if original_series_desc == 'T1w_abdomen_dixon_cor_bh':
                series_desc = 'Dixon_1_in_phase'
            else:
                series_desc = 'Dixon_post_contrast_1_in_phase'

    # For GE translate descriptions to standard convention
    else:
        new_series_desc = {
            'WATER: T1_abdomen_dixon_cor_bh': 'Dixon_1_water',
            'FAT: T1_abdomen_dixon_cor_bh': 'Dixon_1_fat',
            'InPhase: T1_abdomen_dixon_cor_bh': 'Dixon_1_in_phase',
            'OutPhase: T1_abdomen_dixon_cor_bh': 'Dixon_1_out_phase',
            'WATER: T1_abdomen_post_contrast_dixon_cor_bh': 'Dixon_post_contrast_1_water',
            'FAT: T1_abdomen_post_contrast_dixon_cor_bh': 'Dixon_post_contrast_1_fat',
            'InPhase: T1_abdomen_post_contrast_dixon_cor_bh': 'Dixon_post_contrast_1_in_phase',
            'OutPhase: T1_abdomen_post_contrast_dixon_cor_bh': 'Dixon_post_contrast_1_out_phase',
        }
        series_desc = new_series_desc[original_series_desc]

    # Increment counter if needed
    new_series_desc = series_desc
    counter = 2
    while new_series_desc in all_series:
        new_series_desc = series_desc.replace('_1_', f'_{counter}_')
        counter += 1
    all_series.append(new_series_desc)

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


def swap_fat_water(record, dixon, series, image_type):
    for row in record:
        if row[1:4] == [dixon[1], dixon[2], series]:
            if row[4]=='1':
                # Swap fat and water
                if image_type=='fat':
                    return dixon[:3] + [f'{series}_water']
                if image_type=='water':
                    return dixon[:3] + [f'{series}_fat']
    return dixon


def leeds_054():

    # Clean Leeds patient 054
    # Problem: each image saved in a separate series with its own SeriesInstanceUID
    # Solution: group images by SeriesNumber 
    pat = os.path.join(downloadpath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients", 'iBE-4128-054')
    sitedatapath = os.path.join(datapath, "Leeds", "Patients") 
    os.makedirs(sitedatapath, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_folder:
    
        # Extract to a temporary folder
        temp_database_1 = os.path.join(temp_folder, 'data_1')
        os.makedirs(temp_database_1, exist_ok=True)
        for zip_series in os.scandir(pat):
            with zipfile.ZipFile(zip_series.path, 'r') as zip_ref:
                zip_ref.extractall(temp_database_1)
        flatten_folder(temp_database_1)

        dixon = {
            4: 'Dixon_1_out_phase',
            5: 'Dixon_1_in_phase',
            6: 'Dixon_1_fat',
            7: 'Dixon_1_water',
            41: 'Dixon_post_contrast_1_out_phase',
            42: 'Dixon_post_contrast_1_in_phase',
            43: 'Dixon_post_contrast_1_fat',
            44: 'Dixon_post_contrast_1_water',
        }
        
        # Group into series by series number in a temporary database 2
        temp_database_2 = os.path.join(temp_folder, 'data_2')
        for s in db.series(temp_database_1):
            v = db.unique('SeriesNumber', s)[0]
            new_series = [temp_database_2, '4128_054', 'Baseline', dixon[v]]
            db.move(s, new_series)    

        # Read as volume to ensure proper slice orders and write to final database.
        for s in db.series(temp_database_2): 
            try:
                dixon_vol = db.volume(s)
            except Exception as e:
                logging.error(f"Patient 4128_054 - {s[-1][0]}: {e}")
            else:
                new_series = [sitedatapath] + s[1:]
                db.write_volume(dixon_vol, new_series, ref=s)



def leeds():

    # Clean Leeds patient data
    sitedownloadpath = os.path.join(downloadpath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients")
    sitedatapath = os.path.join(datapath, "Leeds", "Patients") 
    os.makedirs(sitedatapath, exist_ok=True)
    
    # Loop over all patients
    patients = [f.path for f in os.scandir(sitedownloadpath) if f.is_dir()]
    for pat in tqdm(patients, desc='Building clean database..'):

        # Get a standardized ID from the folder name
        pat_id = leeds_ibeat_patient_id(os.path.basename(pat))


        # If the dataset already exists, continue to the next
        subdirs = [d for d in os.listdir(sitedatapath)
           if os.path.isdir(os.path.join(sitedatapath, d))]
        if f'Patient__{pat_id}' in subdirs: 
            continue

        # Exception with unique folder structure
        if pat_id == '4128_054':
            leeds_054()
            continue

        with tempfile.TemporaryDirectory() as temp_folder:

            pat_series = []
            for zip_series in os.scandir(pat):

                # Get the name of the zip file without extension
                zip_name = os.path.splitext(os.path.basename(zip_series.path))[0]

                # Extract to a temporary folder and flatten
                extract_to = os.path.join(temp_folder, zip_name)
                with zipfile.ZipFile(zip_series.path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                flatten_folder(extract_to)

                # Add new series name to the list
                try:
                    leeds_add_series_name(extract_to, pat_series)
                except Exception as e:
                    logging.error(f"Patient {pat_id} - error renaming {zip_name}: {e}")
                    continue

                # Copy to the database using the harmonized names
                dixon = db.series(extract_to)[0]
                dixon_clean = [sitedatapath, pat_id, 'Baseline', pat_series[-1]]
                # db.copy(dixon, dixon_clean)
                try:
                    dixon_vol = db.volume(dixon)
                except Exception as e:
                    logging.error(f"Patient {pat_id} - {pat_series[-1]}: {e}")
                else:
                    db.write_volume(dixon_vol, dixon_clean, ref=dixon)



def bari_030(dixon_split):

    # The precontrast dixon of this subject has missing slices in the 
    # middle. In out-phase is missing 2 consecutive slices at slice 
    # locations 13 and 14, and the in-phase is missing 1 slice at 
    # slice location 13. Solved by interpolating to recover the missing 
    # slices.

    sitedatapath = os.path.join(datapath, "Bari", "Patients")
    pat_id = '1128_030'
    series_desc = 'Dixon_1'

    # Need these values to build the affine
    aff = ['ImageOrientationPatient', 'ImagePositionPatient', 'PixelSpacing', 'SpacingBetweenSlices']

    # Interpolate missing slices - out-phase
    loc0 = 11.6357442880728 # last slice before the gap
    series = dixon_split[1.274]
    arr, crd, val = db.pixel_data(series, dims='SliceLocation', coords=True, attr=aff)
    i0 = np.where(crd[0,:] == loc0)[0][0]
    # Interpolate missing slices
    pixel_data = np.zeros(arr.shape[:2] + (arr.shape[2]+2, ))
    pixel_data[:,:,:i0+1] = arr[:,:,:i0+1]
    pixel_data[:,:,i0+1] = (1/3) * arr[:,:,i0] + (2/3) * arr[:,:,i0+1]
    pixel_data[:,:,i0+2] = (2/3) * arr[:,:,i0] + (1/3) * arr[:,:,i0+1]
    pixel_data[:,:,i0+3:] = arr[:,:,i0+1:]
    # Create volume and save
    affine = db.affine_matrix(
        val['ImageOrientationPatient'][0], 
        val['ImagePositionPatient'][0], 
        val['PixelSpacing'][0], 
        val['SpacingBetweenSlices'][0])
    in_phase_vol = vreg.volume(pixel_data, affine)
    in_phase_clean = [sitedatapath, pat_id, 'Baseline', series_desc + '_out_phase']
    db.write_volume(in_phase_vol, in_phase_clean, ref=series)

    # Interpolate missing slices - in_phase
    loc0 = 13.1357467355428 # last slice before the gap
    series = dixon_split[2.444]
    arr, crd = db.pixel_data(series, dims='SliceLocation', coords=True)
    i0 = np.where(crd[0,:] == loc0)[0][0]
    # Interpolate missing slices
    pixel_data = np.zeros(arr.shape[:2] + (arr.shape[2]+1, ))
    pixel_data[:,:,:i0+1] = arr[:,:,:i0+1]
    pixel_data[:,:,i0+1] = (1/2) * arr[:,:,i0] + (1/2) * arr[:,:,i0+1]
    pixel_data[:,:,i0+2:] = arr[:,:,i0+1:]
    # Create volume and save
    out_phase_vol = vreg.volume(pixel_data, affine)
    out_phase_clean = [sitedatapath, pat_id, 'Baseline', series_desc + '_in_phase']
    db.write_volume(out_phase_vol, out_phase_clean, ref=series)




def bari():

    # Define input and output folders
    sitedownloadpath = os.path.join(downloadpath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    sitedatapath = os.path.join(datapath, "Bari", "Patients")
    os.makedirs(sitedatapath, exist_ok=True)

    # Loop over all patients
    patients = [f.path for f in os.scandir(sitedownloadpath) if f.is_dir()]
    for pat in tqdm(patients, desc='Building clean database'):

        # Get a standardized ID from the folder name
        pat_id = bari_ibeat_patient_id(os.path.basename(pat))

        # Corrupted data
        if pat_id in EXCLUDE:
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

            # Get the harmonized series name 
            try:
                bari_add_series_name(zip_name, pat_series)
            except Exception as e:
                logging.error(f"Patient {pat_id} - error renaming {zip_name}: {e}")
                continue

            # Construct output series
            study = [sitedatapath, pat_id, ('Baseline', 0)]
            out_phase_clean = study + [(pat_series[-1] + 'out_phase', 0)]
            in_phase_clean = study + [(pat_series[-1] + 'in_phase', 0)]

            # If the series already exists, continue to the next
            if out_phase_clean in db.series(study):
                continue

            with tempfile.TemporaryDirectory() as temp_folder:

                # Extract to a temporary folder and flatten it
                os.makedirs(temp_folder, exist_ok=True)
                try:
                    extract_to = os.path.join(temp_folder, zip_name)
                    with zipfile.ZipFile(os.path.join(pat, zip_series), 'r') as zip_ref:
                        zip_ref.extractall(extract_to)
                except Exception as e:
                    logging.error(f"Patient {pat_id} - error extracting {zip_name}: {e}")
                    continue
                flatten_folder(extract_to)

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
                    continue
                
                # Check the echo times
                TE = list(dixon_split.keys())
                if len(TE) == 1:
                    logging.error(
                        f"Bari patient {pat_id}, series "
                        f"{os.path.basename(extract_to)}: "
                        f"Only one echo time found. Excluded from database.")
                    continue    

                # Special case
                if (pat_id == '1128_030') and (pat_series[-1] == 'Dixon_1_'):
                    bari_030(dixon_split)
                    continue

                # Write to the database using read/write volume to ensure proper slice order.
                try:
                    out_phase_vol = db.volume(dixon_split[TE[0]])
                    in_phase_vol = db.volume(dixon_split[TE[1]])
                except Exception as e:
                    logging.error(f"Patient {pat_id} - {pat_series[-1]}: {e}")
                else:
                    db.write_volume(out_phase_vol, out_phase_clean, ref=dixon_split[TE[0]])
                    db.write_volume(in_phase_vol, in_phase_clean, ref=dixon_split[TE[1]])

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



def sheffield():

    # Clean Leeds patient data
    sitedownloadpath = os.path.join(downloadpath, "BEAt-DKD-WP4-Sheffield")
    sitedatapath = os.path.join(datapath, "Sheffield", "Patients") 
    os.makedirs(sitedatapath, exist_ok=True)

    # Read fat-water swap record to avoid repeated reading at the end
    record = os.path.join(os.getcwd(), 'src', 'data', 'fat_water_swap_record.csv')
    with open(record, 'r') as file:
        reader = csv.reader(file)
        record = [row for row in reader]

    # Loop over all patients
    patients = [f.path for f in os.scandir(sitedownloadpath) if f.is_dir()]
    for patient in tqdm(patients, desc='Building clean database'):

        # Get a standardized ID from the folder name
        pat_id = sheffield_ibeat_patient_id(os.path.basename(patient))

        # Corrupted data
        if pat_id in EXCLUDE:
            continue

        # If the dataset already exists, continue to the next
        # This needs to check sequences not patients
        subdirs = [
            d for d in os.listdir(sitedatapath)
            if os.path.isdir(os.path.join(sitedatapath, d))]
        if f'Patient__{pat_id}' in subdirs:
            continue

        # Get the experiment directory
        experiment = [f for f in os.listdir(patient) if os.path.isdir(os.path.join(patient, f))][0]
        experiment_path = os.path.join(patient, experiment)

        # Find all zip series in the experiment and sort by series number
        all_zip_series = [f for f in os.listdir(experiment_path) if os.path.isfile(os.path.join(experiment_path, f))]
        all_zip_series = sorted(all_zip_series, key=lambda x: int(x[7:-4]))

        # Note:
        # In Sheffield XNAT the Dixon series are not saved in the proper order, which looks messy in the database.
        # So all series for a single patient are extracted first, then they are saved to the 
        # database in the proper order.

        # Extract all series of the patient
        with tempfile.TemporaryDirectory() as temp_folder:

            pat_series = []
            tmp_series_folder = {} # keep a list of folders for each series
    
            for zip_series in all_zip_series:

                # Get the name of the zip file without extension.
                zip_name = zip_series[:-4]

                # Extract to a temporary folder and flatten it
                try:
                    extract_to = os.path.join(temp_folder, zip_name)
                    with zipfile.ZipFile(os.path.join(experiment_path, zip_series), 'r') as zip_ref:
                        zip_ref.extractall(extract_to)
                except Exception as e:
                    logging.error(f"Patient {pat_id} - error extracting {zip_name}: {e}")
                    continue
                flatten_folder(extract_to)

                # Add new series to the list 
                try:
                    sheffield_add_series_desc(extract_to, pat_series)
                except Exception as e:
                    logging.error(f"Patient {pat_id} - error renaming {zip_name}: {e}")
                    continue

                # Save in dictionary
                tmp_series_folder[pat_series[-1]] = extract_to


            # Write the series to the database in the proper order
            for series in ['Dixon', 'Dixon_post_contrast']:
                for counter in [1,2,3]: # never more than 3 repetitions
                    for image_type in ['out_phase', 'in_phase', 'fat', 'water']:
                        series_desc = f'{series}_{counter}_{image_type}'
                        if series_desc in tmp_series_folder:
                            extract_to = tmp_series_folder[series_desc]
                            # Copy to the database using the harmonized names
                            dixon = db.series(extract_to)[0]
                            dixon_clean = [sitedatapath, pat_id, 'Baseline', series_desc]
                            # Perform fat-water swap if needed
                            dixon_clean = swap_fat_water(record, dixon_clean, f'{series}_{counter}', image_type)
                            # Write to database.
                            # db.copy(dixon, dixon_clean)
                            try:
                                dixon_vol = db.volume(dixon)
                            except Exception as e:
                                logging.error(f"Patient {pat_id} - {series_desc}: {e}")
                            else:
                                db.write_volume(dixon_vol, dixon_clean, ref=dixon)

def turku_ge():

    # Clean Leeds patient data
    sitedownloadpath = os.path.join(downloadpath, "BEAt-DKD-WP4-Turku","Turku_Patients")
    sitedatapath = os.path.join(datapath, "Turku", "Patients") 
    os.makedirs(sitedatapath, exist_ok=True)

    # Read fat-water swap record to avoid repeated reading at the end
    record = os.path.join(os.getcwd(), 'src', 'data', 'fat_water_swap_record.csv')
    with open(record, 'r') as file:
        reader = csv.reader(file)
        record = [row for row in reader]

    # Loop over all patients
    patients = [f.path for f in os.scandir(sitedownloadpath) if f.is_dir()]
    for patient in tqdm(patients, desc='Building clean database'):

        # Get a standardized ID from the folder name
        pat_id = turku_ge_ibeat_patient_id(os.path.basename(patient))

        # 5128_001

        if "_followup" in pat_id:
            time_point ="Followup"
            pat_id = pat_id[0:8]
        else:
            time_point ="Baseline"
            pat_id = pat_id[0:8]

        # Corrupted data
        if pat_id in EXCLUDE:
            continue

        # If the study
        dixon_clean_study = [sitedatapath, pat_id, time_point]
        if dixon_clean_study in db.studies(sitedatapath):
            continue

        # Get the experiment directory
        experiment_path = os.path.join(patient)

        # Find all zip series in the experiment and sort by series number
        all_zip_series = [f for f in os.listdir(experiment_path) if os.path.isfile(os.path.join(experiment_path, f))]
        all_zip_series = sorted(all_zip_series, key=lambda x: int(x[7:-4]))

        # Note:
        # In Sheffield XNAT the Dixon series are not saved in the proper order, which looks messy in the database.
        # So all series for a single patient are extracted first, then they are saved to the 
        # database in the proper order.

        # Extract all series of the patient
        with tempfile.TemporaryDirectory() as temp_folder:

            pat_series = []
            tmp_series_folder = {} # keep a list of folders for each series
    
            for zip_series in all_zip_series:

                # Get the name of the zip file without extension.
                zip_name = zip_series[:-4]

                # Extract to a temporary folder and flatten it
                try:
                    extract_to = os.path.join(temp_folder, zip_name)
                    with zipfile.ZipFile(os.path.join(experiment_path, zip_series), 'r') as zip_ref:
                        zip_ref.extractall(extract_to)
                except Exception as e:
                    logging.error(f"Patient {pat_id} - error extracting {zip_name}: {e}")
                    continue
                flatten_folder(extract_to)

                # Add new series to the list 
                try:
                    turku_add_series_desc(extract_to, pat_series)
                except Exception as e:
                    logging.error(f"Patient {pat_id} - error renaming {zip_name}: {e}")
                    continue

                # Save in dictionary
                tmp_series_folder[pat_series[-1]] = extract_to


            # Write the series to the database in the proper order
            for series in ['Dixon', 'Dixon_post_contrast']:
                for counter in [1,2,3]: # never more than 3 repetitions
                    for image_type in ['out_phase', 'in_phase', 'fat', 'water']:
                        series_desc = f'{series}_{counter}_{image_type}'
                        if series_desc in tmp_series_folder:
                            extract_to = tmp_series_folder[series_desc]
                            # Copy to the database using the harmonized names
                            dixon = db.series(extract_to)[0]

                            dixon_clean = dixon_clean_study + [series_desc]
                            # Perform fat-water swap if needed
                            #dixon_clean = swap_fat_water(record, dixon_clean, f'{series}_{counter}', image_type)
                            # Write to database.
                            # db.copy(dixon, dixon_clean)
                            try:
                                dixon_vol = db.volume(dixon)
                            except Exception as e:
                                logging.error(f"Patient {pat_id} - {series_desc}: {e}")
                            else:
                                db.write_volume(dixon_vol, dixon_clean, ref=dixon)



def all():
    # leeds()
    # bari()
    # sheffield()
    turku_ge()


if __name__=='__main__':
    
    # sheffield()
    # leeds()
    # bari()
    turku_ge()
    
    
    

    


    
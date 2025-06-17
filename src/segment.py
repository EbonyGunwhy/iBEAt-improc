import os
import logging

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm

import dbdicom as db
import miblab

import utils

datapath = os.path.join(os.getcwd(), 'build', 'Data') 
maskpath = os.path.join(os.getcwd(), 'build', 'Masks') 

# Set up logging
logging.basicConfig(
    filename=os.path.join(maskpath, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



def leeds():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients") 
    sitemaskpath = os.path.join(maskpath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients")
    os.makedirs(sitemaskpath, exist_ok=True)
    patients = [f.path for f in os.scandir(sitedatapath) if f.is_dir()]
    for pat in patients:
        series_folders = os.listdir(pat)
        patient_id = os.path.basename(pat)
        for scan in ['Dixon', 'Dixon_post_contrast']:
            i=1
            while f'{scan}_{i}_in_phase' in series_folders:

                ref_series = db.series(os.path.join(pat, f'{scan}_{i}_out_phase'))[0]
                op = db.volume(os.path.join(pat, f'{scan}_{i}_out_phase'))[0]
                ip = db.volume(os.path.join(pat, f'{scan}_{i}_in_phase'))[0]
                wi = db.volume(os.path.join(pat, f'{scan}_{i}_water'))[0]
                fi = db.volume(os.path.join(pat, f'{scan}_{i}_fat'))[0]
                
                # total segmentator
                try:
                    rois = miblab.totseg(wi, cutoff=0.01, task='total_mr', device='cpu')
                except Exception as e:
                    logging.error(f"Error processing {patient_id} {scan}_{i} with total segmentator: {e}")
                else:
                    print('Creating total segmentator .png')
                    png_file = os.path.join(sitemaskpath, f'{patient_id}_{scan}_{i}_totseg.png')
                    utils.total_masks_as_png(op.values, rois, png_file)
                    print('Creating total segmentator .dcm')
                    # Convert to single array
                    mask = np.zeros(rois['kidney_left'].values.shape, dtype=np.int16)
                    for i, roi in enumerate(rois):
                        mask += (i+1) * rois[roi].values.astype(np.int16)
                    # Save as dicom
                    series = [sitemaskpath, patient_id, f'{scan}_masks', 'totseg']
                    db.write_volume((mask, op.affine), series, ref=ref_series)

                # miblab models
                array = np.stack((op.values, ip.values, wi.values, fi.values), axis=-1)
                for model in ['nnunet', 'unetr']:
                    try:
                        rois = miblab.kidney_pc_dixon(array, model)
                    except Exception as e:
                        logging.error(f"Error processing {patient_id} {scan}_{i} with model {model}: {e}")
                    else:
                        png_file = os.path.join(sitemaskpath, f'{patient_id}_{scan}_{i}_{model}.png')
                        utils.kidney_masks_as_png(op.values, rois['kidney_left'].astype(float), rois['kidney_right'].astype(float), png_file)
                        # Convert to single array
                        mask = np.zeros(rois['kidney_left'].shape, dtype=np.int16)
                        for j, roi in enumerate(rois):
                            mask += (j+1) * rois[roi].astype(np.int16)
                        # Save as dicom
                        series = [sitemaskpath, patient_id, f'{scan}_masks', model]
                        db.write_volume((mask, op.affine), series, ref=ref_series)

                i+=1


def bari():
    #done = ['1128_001', '1128_002']
    done_until = 10
    done = ['1128_' + str(i).zfill(3) for i in range(1+done_until)]
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Bari", "Bari_Patients") 
    sitemaskpath = os.path.join(maskpath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    os.makedirs(sitemaskpath, exist_ok=True)
    patients = [f.path for f in os.scandir(sitedatapath) if f.is_dir()]
    for pat in patients:
        series_folders = os.listdir(pat)
        patient_id = os.path.basename(pat)
        if patient_id in done:
            continue
        for scan in ['Dixon', 'Dixon_post_contrast']:
            i=1
            while f'{scan}_{i}_in_phase' in series_folders:

                ref_series = db.series(os.path.join(pat, f'{scan}_{i}_out_phase'))[0]
                op = db.volume(os.path.join(pat, f'{scan}_{i}_out_phase'))[0] # need water?
                # ip = db.volume(os.path.join(pat, f'{scan}_{i}_in_phase'))[0]
                # wi = db.volume(os.path.join(pat, f'{scan}_{i}_water'))[0]
                # fi = db.volume(os.path.join(pat, f'{scan}_{i}_fat'))[0]
                
                # total segmentator
                try:
                    rois = miblab.totseg(op, cutoff=0.01, task='total_mr', device='cpu')
                except Exception as e:
                    logging.error(f"Error processing {patient_id} {scan}_{i} with total segmentator: {e}")
                else:
                    # TODO: Run a select largest cluster on the kidney masks
                    rois = {roi:vol.values for roi, vol in rois.items()}
                    print('Creating total segmentator .png')
                    png_file = os.path.join(sitemaskpath, f'{patient_id}_{scan}_{i}_totseg_all.png')
                    utils.total_masks_as_png(op.values, rois, png_file)
                    png_file = os.path.join(sitemaskpath, f'{patient_id}_{scan}_{i}_totseg.png')
                    utils.kidney_masks_as_png(op.values, rois, png_file)
                    print('Creating total segmentator .dcm')
                    # Convert to single array
                    mask = np.zeros(rois['kidney_left'].shape, dtype=np.int16)
                    for j, roi in enumerate(rois):
                        mask += (j+1) * rois[roi].astype(np.int16)
                    # Save as dicom
                    series = [sitemaskpath, patient_id, f'{scan}_masks', 'totseg']
                    db.write_volume((mask, op.affine), series, ref=ref_series)

                i+=1



if __name__=='__main__':
    # TODO: In DICOM Data save series description and patient name/ID to match the folder names
    # leeds()
    bari()
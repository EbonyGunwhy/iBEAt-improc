import os
import logging
import csv

import numpy as np
import dbdicom as db
import miblab
import torch
import scipy.ndimage as ndi

import utils.data


datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data') 
maskpath = os.path.join(os.getcwd(), 'build', 'kidneyvol_1_segment') 
os.makedirs(maskpath, exist_ok=True)


# Set up logging
logging.basicConfig(
    filename=os.path.join(maskpath, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def largest_cluster(array:np.ndarray)->np.ndarray:
    """Given a mask array, return a new mask array containing only the largest cluster.

    Args:
        array (np.ndarray): mask array with values 1 (inside) or 0 (outside)

    Returns:
        np.ndarray: mask array with only a single connect cluster of pixels.
    """
    # Label all features in the array
    label_img, cnt = ndi.label(array)
    # Find the label of the largest feature
    labels = range(1,cnt+1)
    size = [np.count_nonzero(label_img==l) for l in labels]
    max_label = labels[size.index(np.amax(size))]
    # Return a mask corresponding to the largest feature
    return label_img==max_label


def segment_site(sitedatapath, sitemaskpath):

    # List of selected dixon series
    record = utils.data.dixon_record()

    # Get out phase series
    series = db.series(sitedatapath)
    series_out_phase = [s for s in series if s[3][0][-9:]=='out_phase']

    # Loop over the out-phase series
    for series_op in series_out_phase:

        # Patient and output study
        patient = series_op[1]
        study = series_op[2][0]
        series_op_desc = series_op[3][0]
        sequence = series_op_desc[:-10]

        # Skip if it is not the right sequence
        selected_sequence = utils.data.dixon_series_desc(record, patient, study)
        if sequence != selected_sequence:
            continue

        # Skip if the kidney masks already exist
        mask_study = [sitemaskpath, patient, (study,0)]
        mask_series = mask_study + [(f'kidney_masks', 0)]
        if mask_series in db.series(mask_study):
            continue

        # Other source data series
        series_ip = series_op[:3] + [(sequence + '_in_phase', 0)]
        series_wi = series_op[:3] + [(sequence + '_water', 0)]
        series_fi = series_op[:3] + [(sequence + '_fat', 0)]

        # Read the in- and out of phase volumes
        try:
            op = db.volume(series_op)
            ip = db.volume(series_ip)
        except Exception as e:
            logging.error(f"Patient {patient} - error reading I-O {sequence}: {e}")
            continue

        # If there are only 2 channels, use total segmentator
        if series_wi not in db.series(series_op[:3]):
            try:
                device = 'gpu' if torch.cuda.is_available() else 'cpu'
                rois = miblab.totseg(op, cutoff=0.01, task='total_mr', device=device)
                # Remove smaller disconnected clusters
                rois = {roi:largest_cluster(vol.values) for roi, vol in rois.items() if roi in ['kidney_left', 'kidney_right']}
                # Reverse left and right for consistency with miblab models
                rois = {key:rois[key] for key in ['kidney_left', 'kidney_right']}
            except Exception as e:
                logging.error(f"Error processing {patient} {sequence} with total segmentator: {e}")
                continue

        # If there are 4 channels, use miblab nnunet:
        else:

            # Read fat and water data
            try:
                wi = db.volume(series_wi)
                fi = db.volume(series_fi)
            except Exception as e:
                logging.error(f"Patient {patient} - error reading F-W {sequence}: {e}")
                continue

            # Predict kidney masks
            try:
                array = np.stack((op.values, ip.values, wi.values, fi.values), axis=-1)
            except Exception as e:
                logging.error(f"{patient} {sequence} error building 4-channel input array: {e}")
                continue
            try:
                rois = miblab.kidney_pc_dixon(array, 'nnunet', verbose=True)
            except Exception as e:
                logging.error(f"Error processing {patient} {sequence} with nnunet: {e}")
                continue
            
        # Write in dicom as integer label arrays to save space
        print(f'Saving results')
        mask = np.zeros(rois['kidney_left'].shape, dtype=np.int16)
        for j, roi in enumerate(rois):
            mask += (j+1) * rois[roi].astype(np.int16)
        db.write_volume((mask, op.affine), mask_series, ref=series_op)



def leeds():
    sitedatapath = os.path.join(datapath, "Leeds", "Patients") 
    sitemaskpath = os.path.join(maskpath, "Leeds", "Patients")
    os.makedirs(sitemaskpath, exist_ok=True)
    segment_site(sitedatapath, sitemaskpath)

    
def bari():
    sitedatapath = os.path.join(datapath, "Bari", "Patients") 
    sitemaskpath = os.path.join(maskpath, "Bari", "Patients")
    os.makedirs(sitemaskpath, exist_ok=True)
    segment_site(sitedatapath, sitemaskpath)


def sheffield():
    sitedatapath = os.path.join(datapath, "Sheffield", "Patients") 
    sitemaskpath = os.path.join(maskpath, "Sheffield", "Patients")
    os.makedirs(sitemaskpath, exist_ok=True)
    segment_site(sitedatapath, sitemaskpath)


def all():
    sheffield()
    leeds()
    bari()


if __name__=='__main__':
    leeds()
    sheffield()
    bari()
    
    
    
    
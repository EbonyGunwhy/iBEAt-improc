import os
import logging

import numpy as np
import dbdicom as db
import miblab
import torch

from utils import data


datapath = os.path.join(os.getcwd(), 'build', 'dixon', 'stage_2_data') 
maskpath = os.path.join(os.getcwd(), 'build', 'totseg', 'stage_1_segment') 
os.makedirs(maskpath, exist_ok=True)


# Set up logging
logging.basicConfig(
    filename=os.path.join(maskpath, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def segment(group, site=None, batch_size=None):

    if site is None:
        sitedatapath = os.path.join(datapath, group)
        sitemaskpath = os.path.join(maskpath, group)
    else:
        sitedatapath = os.path.join(datapath, group, site)
        sitemaskpath = os.path.join(maskpath, group, site)
    os.makedirs(sitemaskpath, exist_ok=True)

    # List of selected dixon series
    record = data.dixon_record()

    # Get out phase series
    series = db.series(sitedatapath)
    series_out_phase = [s for s in series if s[3][0][-9:]=='out_phase']

    # Loop over the out-phase series
    count = 0
    for series_op in series_out_phase:

        # Patient and output study
        patient = series_op[1]
        study = series_op[2][0]
        series_op_desc = series_op[3][0]
        sequence = series_op_desc[:-10]

        # Skip if it is not the right sequence
        selected_sequence = data.dixon_series_desc(record, patient, study)
        if sequence != selected_sequence:
            continue

        # Skip if the masks already exist
        mask_study = [sitemaskpath, patient, (study,0)]
        mask_series = mask_study + [(f'total_mr', 0)]
        if mask_series in db.series(mask_study):
            continue

        # Other source data series
        series_wi = series_op[:3] + [(sequence + '_water', 0)]

        # Read volumes
        if series_wi in db.series(series_op[:3]):
            vol = db.volume(series_wi)
        else:
            vol = db.volume(series_op)

        # Perform segmentation
        try:
            device = 'gpu' if torch.cuda.is_available() else 'cpu'
            label_vol = miblab.totseg(vol, cutoff=0.01, task='total_mr', device=device)
        except Exception as e:
            logging.error(f"Error processing {patient} {sequence} with total segmentator: {e}")
            continue

        # Save results
        db.write_volume(label_vol, mask_series, ref=series_op)

        count += 1 
        if batch_size is not None:
            if count >= batch_size:
                return



    
    
    
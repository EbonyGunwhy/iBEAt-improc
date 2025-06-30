import os
import logging

import numpy as np
from tqdm import tqdm
import dbdicom as db

from utils import plot, data


datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
maskpath = os.path.join(os.getcwd(), 'build', 'kidneyvol_3_edit')
displaypath = os.path.join(os.getcwd(), 'build', 'kidneyvol_4_display')
os.makedirs(displaypath, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=os.path.join(displaypath, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def mosaic(sitedatapath, sitemaskpath, sitedisplaypath):

    # Build output folders
    display_kidneys = os.path.join(displaypath, sitedisplaypath)
    os.makedirs(display_kidneys, exist_ok=True)

    record = data.dixon_record()
    class_map = {1: "kidney_left", 2: "kidney_right"}

    # Loop over the masks
    for mask in tqdm(db.series(sitemaskpath), 'Displaying masks..'):

        # Get the corresponding outphase series
        patient_id = mask[1]
        study = mask[2][0]
        sequence = data.dixon_series_desc(record, patient_id, study)
        series_op = [sitedatapath, patient_id, study, f'{sequence}_out_phase']

        # Skip if file exists
        png_file = os.path.join(display_kidneys, f'{patient_id}_{sequence}_kidneys.png')
        if os.path.exists(png_file):
             continue

        # Get arrays
        op_arr = db.volume(series_op).values
        mask_arr = db.volume(mask).values
        rois = {}
        for idx, roi in class_map.items():
            rois[roi] = (mask_arr==idx).astype(np.int16)

        # Build mosaic
        try:
            plot.mosaic_overlay(op_arr, rois, png_file)
        except Exception as e:
            logging.error(f"{patient_id} {sequence} error building mosaic: {e}")




def leeds():
    sitedatapath = os.path.join(datapath, "Leeds", "Patients") 
    sitemaskpath = os.path.join(maskpath, "Leeds", "Patients")
    sitedisplaypath = os.path.join(displaypath, "Leeds", "Patients")
    # movie(sitedatapath, sitemaskpath, sitedisplaypath)
    mosaic(sitedatapath, sitemaskpath, sitedisplaypath)

def bari():
    sitedatapath = os.path.join(datapath, "Bari", "Patients") 
    sitemaskpath = os.path.join(maskpath, "Bari", "Patients")
    sitedisplaypath = os.path.join(displaypath, "Bari", "Patients")
    # movie(sitedatapath, sitemaskpath, sitedisplaypath)
    mosaic(sitedatapath, sitemaskpath, sitedisplaypath)

def sheffield():
    sitedatapath = os.path.join(datapath, "Sheffield", "Patients") 
    sitemaskpath = os.path.join(maskpath, "Sheffield", "Patients")
    sitedisplaypath = os.path.join(displaypath, "Sheffield", "Patients")
    # movie(sitedatapath, sitemaskpath, sitedisplaypath)
    mosaic(sitedatapath, sitemaskpath, sitedisplaypath)


def all():
    bari()
    leeds()
    sheffield()

if __name__=='__main__':
    bari()
    # leeds()
    # sheffield()
import os
import logging

import numpy as np
from tqdm import tqdm
import dbdicom as db

from utils import plot, data
from utils.constants import SITE_IDS


datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
maskpath = os.path.join(os.getcwd(), 'build', 'kidneyvol_1_segment')
displaypath = os.path.join(os.getcwd(), 'build', 'kidneyvol_2_display')
os.makedirs(displaypath, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=os.path.join(displaypath, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def mosaic(site, group):

    if group == 'Controls':
        sitedatapath = os.path.join(datapath, "Controls") 
        sitemaskpath = os.path.join(maskpath, "Controls")
        sitedisplaypath = os.path.join(displaypath, "Controls")
    else:
        sitedatapath = os.path.join(datapath, site, "Patients") 
        sitemaskpath = os.path.join(maskpath, site, "Patients")
        sitedisplaypath = os.path.join(displaypath, site, "Patients")
    os.makedirs(sitedisplaypath, exist_ok=True)

    record = data.dixon_record()
    class_map = {1: "kidney_left", 2: "kidney_right"}

    # Loop over the masks
    for mask in tqdm(db.series(sitemaskpath), 'Displaying masks..'):

        # Get the corresponding outphase series
        patient_id = mask[1]
        study = mask[2][0]
        sequence = data.dixon_series_desc(record, patient_id, study)
        series_op = [sitedatapath, patient_id, study, f'{sequence}_out_phase']

        # Skip if not in the right site
        if patient_id[:4] not in SITE_IDS[site]:
            continue

        # Skip if file exists
        png_file = os.path.join(sitedisplaypath, f'{patient_id}_{study}_{sequence}.png')
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





def all():
    mosaic('Bari', 'Patients')
    mosaic('Leeds', 'Patients')
    mosaic('Sheffield', 'Patients')
    mosaic('Bordeaux', 'Patients')
    mosaic('Controls', 'Patients')


if __name__=='__main__':
    mosaic('Bari', 'Controls')
    mosaic('Leeds', 'Controls')
    mosaic('Bordeaux', 'Controls')
    mosaic('Turku', 'Controls')
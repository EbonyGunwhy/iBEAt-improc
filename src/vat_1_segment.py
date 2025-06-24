import os
import logging

import numpy as np
import dbdicom as db
import miblab
import torch


datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data') 
maskpath = os.path.join(os.getcwd(), 'build', 'vat_1_segment') 
os.makedirs(maskpath, exist_ok=True)


# Set up logging
logging.basicConfig(
    filename=os.path.join(maskpath, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def segment_site(sitedatapath, sitemaskpath):

    # Get out phase series
    series = db.series(sitedatapath)
    series_out_phase = [s for s in series if s[-1][0][-9:]=='out_phase']

    # Loop over the out-phase series
    for series_op in series_out_phase:

        # Patient and output study
        patient = series_op[1]
        data_study = series_op[:3]
        mask_study = [sitemaskpath, patient, (f'tissue_types_mr', 0)]
        series_desc = series_op[-1][0][:-10]

        # Other source data series
        series_fi = data_study + [(series_desc + '_fat', 0)]
        channels = 4 if series_fi in db.series(data_study) else 2

        # Segment on fat if available, else use opposed phase
        source = series_op if channels==2 else series_fi

        # Perform the single-channel segmentation (totseg)
        mask_series = mask_study + [(f'{series_desc}', 0)]

        # Skip those that have been done already
        if mask_series not in db.series(mask_study):

            # Read the source volume
            try:
                source_vol = db.volume(source)
            except Exception as e:
                logging.error(f"Patient {patient} - error reading F-W {series_desc}: {e}")
                continue
            
            # Perform the segmentation
            try:
                device = 'gpu' if torch.cuda.is_available() else 'cpu'
                rois = miblab.totseg(source_vol, cutoff=0.01, task='tissue_types_mr', device=device)
                rois = {roi:vol.values for roi, vol in rois.items()}
            except Exception as e:
                logging.error(f"Error processing {patient} {series_desc} with total segmentator: {e}")
                continue

            # Write in dicom as integer label arrays to save space
            print('Saving total segmentator results')
            mask = np.zeros(rois['subcutaneous_fat'].shape, dtype=np.int16)
            for j, roi in enumerate(rois):
                mask += (j+1) * rois[roi].astype(np.int16)
            db.write_volume((mask, source_vol.affine), mask_series, ref=series_op)



def leeds():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients") 
    sitemaskpath = os.path.join(maskpath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients")
    os.makedirs(sitemaskpath, exist_ok=True)
    segment_site(sitedatapath, sitemaskpath)
    


def bari():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Bari", "Bari_Patients") 
    sitemaskpath = os.path.join(maskpath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    os.makedirs(sitemaskpath, exist_ok=True)
    segment_site(sitedatapath, sitemaskpath)


def all():
    #leeds()
    bari()


if __name__=='__main__':
    # bari()
    leeds()
    
    
    
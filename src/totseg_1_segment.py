import os
import logging

import numpy as np
import dbdicom as db
import miblab
import torch


datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data') 
maskpath = os.path.join(os.getcwd(), 'build', 'totseg_1_segment') 
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
        mask_study = [sitemaskpath, patient, (f'dixon_masks', 0)]
        series_op_desc = series_op[-1][0]

        # Other source data series
        series_ip = series_op[:3] + [(series_op_desc[:-9] + 'in_phase', 0)]
        series_wi = series_op[:3] + [(series_op_desc[:-9] + 'water', 0)]
        series_fi = series_op[:3] + [(series_op_desc[:-9] + 'fat', 0)]

        # Read the volumes for all available channels
        channels = 2
        try:
            op = db.volume(series_op)
            ip = db.volume(series_ip)
        except Exception as e:
            logging.error(f"Patient {patient} - error reading I-O {series_op_desc[:-10]}: {e}")
            continue
        if series_wi in db.series(series_op[:3]):
            channels = 4
            try:
                wi = db.volume(series_wi)
                fi = db.volume(series_fi)
            except Exception as e:
                logging.error(f"Patient {patient} - error reading F-W {series_op_desc[:-10]}: {e}")
                continue

        # Perform the single-channel segmentation (totseg)
        mask_series = mask_study + [(f'{series_op_desc[:-10]}_totseg', 0)]

        # Skip those that have been done already
        if mask_series not in db.series(mask_study):
            source=op if channels==2 else wi
            try:
                device = 'gpu' if torch.cuda.is_available() else 'cpu'
                rois = miblab.totseg(source, cutoff=0.01, task='total_mr', device=device)
                rois = {roi:vol.values for roi, vol in rois.items()}
            except Exception as e:
                logging.error(f"Error processing {patient} {series_op_desc[:-10]} with total segmentator: {e}")
                continue

            # Write in dicom as integer label arrays to save space
            print('Saving total segmentator results')
            mask = np.zeros(rois['kidney_left'].shape, dtype=np.int16)
            for j, roi in enumerate(rois):
                mask += (j+1) * rois[roi].astype(np.int16)
            db.write_volume((mask, op.affine), mask_series, ref=series_op)

        # Perform the 4-channel segmentation (miblab models)
        if channels==2:
            continue
        for model in ['nnunet', 'unetr']:
            mask_series = mask_study + [(f'{series_op_desc[:-10]}_{model}', 0)]

            # Skip those that have been done already
            if mask_series not in db.series(mask_study):

                # Run predictions
                array = np.stack((op.values, ip.values, wi.values, fi.values), axis=-1)
                try:
                    rois = miblab.kidney_pc_dixon(array, model, verbose=True)
                except Exception as e:
                    logging.error(f"Error processing {patient} {series_op_desc[:-10]} with miblab {model}: {e}")
                    continue
                
                # Write in dicom as integer label arrays to save space
                print(f'Saving miblab {model} results')
                mask = np.zeros(rois['kidney_left'].shape, dtype=np.int16)
                for j, roi in enumerate(rois):
                    mask += (j+1) * rois[roi].astype(np.int16)
                db.write_volume((mask, op.affine), mask_series, ref=series_op)



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
    bari()
    leeds()
    
    
    
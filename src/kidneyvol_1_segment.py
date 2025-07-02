import os
import logging

import numpy as np
import dbdicom as db
import miblab
import torch


import utils.data
from utils import radiomics


# These need fully manual segmentation
EXCLUDE = [ 
    '4128_055', # miblab nnunet No segmentation: large left kidney and tiny right kidney
    '7128_149', # miblab nnunet Segmentation failed: horseshoe kidney
]

# Exceptions: failed with nnunet/unetr for no obvious reason
TOTSEG = [
    '7128_085',

    # Leeds
    '4128_007',
    '4128_010', # poor images
    '4128_012',
    '4128_013', # poor images
    '4128_014',
    '4128_015',
    '4128_016',
    '4128_017',
    '4128_024',
    '4128_043',
    '4128_051',
    '4128_052',
    '4128_053',
    '4128_054',
    '4128_061',

    # Sheffield
    '7128_021',
    '7128_026',
    '7128_027',
    '7128_033',
    '7128_037',
    '7128_038',
    '7128_040',
    '7128_044',
    '7128_047',
    '7128_056',
    '7128_059',
    '7128_064',
    '7128_067',
    '7128_069',
    '7128_072',
    '7128_073',
    '7128_074',
    '7128_075',
    '7128_076',
    '7128_077',
    '7128_080',
    '7128_081',
    '7128_082',
    '7128_083',
    '7128_084',
    '7128_086',
    '7128_087',
    '7128_091',
    '7128_092',
    '7128_093',
    '7128_094',
    '7128_096',
    '7128_101',
    '7128_102',
    '7128_104',
    '7128_106',
    '7128_109',
    '7128_110',
    '7128_111',
    '7128_112',
    '7128_113',
    '7128_114', # very poor images
    '7128_115',
    '7128_116',
    '7128_117',
    '7128_118',
    '7128_129',
    '7128_132',
    '7128_137',
    '7128_140',
    '7128_144',
    '7128_146',
    '7128_147',
    '7128_156',
    '7128_157',
    '7128_160',
    '7128_163',
    '7128_164',
    '7128_165',
    '7128_166',

]


datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data') 
maskpath = os.path.join(os.getcwd(), 'build', 'kidneyvol_1_segment') 
os.makedirs(maskpath, exist_ok=True)


# Set up logging
logging.basicConfig(
    filename=os.path.join(maskpath, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def segment_site(site, batch_size=None):

    sitedatapath = os.path.join(datapath, site, "Patients") 
    sitemaskpath = os.path.join(maskpath, site, "Patients")
    os.makedirs(sitemaskpath, exist_ok=True)

    # List of selected dixon series
    record = utils.data.dixon_record()

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

        # Skip those marked for exclusion
        if patient in EXCLUDE:
            continue

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

        # Select model to use
        if series_wi not in db.series(series_op[:3]):
            # If there are only 2 channels, use total segmentator
            model = 'totseg'
        elif patient in TOTSEG: 
            # Exception: failed with nnunet/unetr for no obvious reason
            model = 'totseg'
        else:
            # Default for 4-channel data is nnunet
            model = 'nnunet'

        # If there are only 2 channels, use total segmentator
        if model=='totseg':
            try:
                device = 'gpu' if torch.cuda.is_available() else 'cpu'
                label_vol = miblab.totseg(op, cutoff=0.01, task='total_mr', device=device)
                # Extract kidneys only
                label_array = label_vol.values
                label_array[~np.isin(label_array, [2,3])] = 0
                # Relabel left and right
                label_array[label_array==3] = 1
                # Remove smaller disconnected clusters
                label_array = radiomics.largest_cluster_label(label_array)
            except Exception as e:
                logging.error(f"Error processing {patient} {sequence} with total segmentator: {e}")
                continue

        # If there are 4 channels, use miblab nnunet or unetr:
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
                label_array = miblab.kidney_pc_dixon(array, verbose=True)
            except Exception as e:
                logging.error(f"Error processing {patient} {sequence} with nnunet: {e}")
                continue
        
        db.write_volume((label_array, op.affine), mask_series, ref=series_op)

        count += 1 
        if batch_size is not None:
            if count >= batch_size:
                return



def all():
    segment_site('Sheffield')
    segment_site('Leeds')
    segment_site('Bari')


if __name__=='__main__':
    segment_site('Sheffield')
    segment_site('Leeds')
    segment_site('Bari')
    
    
    
    
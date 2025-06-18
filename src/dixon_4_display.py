import os

from totalsegmentator.map_to_binary import class_map
import numpy as np
import dbdicom as db

import utils


datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
maskpath = os.path.join(os.getcwd(), 'build', 'dixon_3_segment')
displaypath = os.path.join(os.getcwd(), 'build', 'dixon_4_display')


def bari():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Bari", "Bari_Patients") 
    sitemaskpath = os.path.join(maskpath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    sitedisplaypath = os.path.join(displaypath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    os.makedirs(sitedisplaypath, exist_ok=True)
    # TODO: This needs to loop the mask folder instead of the data folder
    # as not all data have masks
    patients = [f.path for f in os.scandir(sitedatapath) if f.is_dir()]
    for pat in patients:
        series_folders = os.listdir(pat)
        patient_id = os.path.basename(pat)
        for scan in ['Dixon', 'Dixon_post_contrast']:
            i=1
            while f'{scan}_{i}_in_phase' in series_folders:
                op = db.volume(os.path.join(pat, f'{scan}_{i}_out_phase'))[0]
                series = [sitemaskpath, patient_id, f'{scan}_masks', 'totseg']
                mask_vol = db.volume(series).values # use pixel_data?

                rois = {}
                for idx, roi in class_map['total_mr'].items():
                    rois[roi] = (mask_vol==idx).astype(np.int16)
                
                png_file = os.path.join(sitedisplaypath, f'{patient_id}_{scan}_{i}_totseg_all.png')
                utils.total_masks_as_png(op.values, rois, png_file)
                png_file = os.path.join(sitedisplaypath, f'{patient_id}_{scan}_{i}_totseg.png')
                utils.kidney_masks_as_png(op.values, rois, png_file)

                i+=1

def all():
    bari()

if __name__=='__main__':
    bari()
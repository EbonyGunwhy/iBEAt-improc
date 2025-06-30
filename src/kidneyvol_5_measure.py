import os
import logging

from tqdm import tqdm
import numpy as np
import dbdicom as db
import vreg
import pydmr

from utils import data, radiomics

datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
maskpath = os.path.join(os.getcwd(), 'build', 'kidneyvol_3_edit')
measurepath = os.path.join(os.getcwd(), 'build', 'kidneyvol_5_measure')
os.makedirs(measurepath, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=os.path.join(measurepath, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def concat(site):
    sitemeasurepath = os.path.join(measurepath, site, "Patients")
    # Concatenate all dmr files of each subject
    patients = [f.path for f in os.scandir(sitemeasurepath) if f.is_dir()]
    for patient in patients:
        dir = os.path.join(sitemeasurepath, patient)
        dmr_files = [f for f in os.listdir(dir) if f.endswith('.dmr.zip')]
        dmr_files = [os.path.join(dir, f) for f in dmr_files]
        dmr_file = os.path.join(sitemeasurepath, f'{patient}_results')
        pydmr.concat(dmr_files, dmr_file)


def measure(site):

    sitedatapath = os.path.join(datapath, site, "Patients") 
    sitemaskpath = os.path.join(maskpath, site, "Patients")
    sitemeasurepath = os.path.join(measurepath, site, "Patients")

    record = data.dixon_record()
    class_map = {1: "kidney_left", 2: "kidney_right"}

    all_mask_series = db.series(sitemaskpath)
    for mask_series in tqdm(all_mask_series, desc='Extracting metrics'):

        patient, study, series = mask_series[1], mask_series[2][0], mask_series[3][0]
        dir = os.path.join(sitemeasurepath, patient)
        os.makedirs(dir, exist_ok=True)

        sequence = data.dixon_series_desc(record, patient, study)
        data_study = [sitedatapath, patient, (study, 0)]
        all_data_series = db.series(data_study)
        
        # Loop over the classes
        for idx, roi in class_map.items():
            dmr_file = os.path.join(dir, f"{series}_{roi}")
            if os.path.exists(f'{dmr_file}.dmr.zip'):
                continue
            vol = db.volume(mask_series)
            mask = (vol.values==idx).astype(np.float32)
            if np.sum(mask) == 0:
                continue

            roi_vol = vreg.volume(mask, vol.affine)
            dmr = {'data':{}, 'pars':{}}

            # Get skimage features
            try:
                results = radiomics.volume_features(roi_vol, roi)
            except Exception as e:
                logging.error(f"Patient {patient} {roi} - error computing ski-shapes: {e}")
            else:
                dmr['data'] = dmr['data'] | {p: v[1:] for p, v in results.items()}
                dmr['pars'] = dmr['pars'] | {(patient, 'Baseline', p): v[0] for p, v in results.items()}

            # Get radiomics shape features
            try:
                results = radiomics.shape_features(roi_vol, roi)
            except Exception as e:
                logging.error(f"Patient {patient} {roi} - error computing radiomics-shapes: {e}")
            else:
                dmr['data'] = dmr['data'] | {p:v[1:] for p, v in results.items()}
                dmr['pars'] = dmr['pars'] | {(patient, 'Baseline', p): v[0] for p, v in results.items()}

            # Get radiomics texture features
            if roi in ['kidney_left', 'kidney_right']: # computational issues with larger ROIs.
                for img in ['out_phase', 'in_phase', 'fat', 'water']:
                    img_series = [sitedatapath, patient, (study, 0), (f"{sequence}_{img}", 0)]
                    if img_series not in all_data_series:
                        continue # Need a different solution here - compute assuming water dominant
                    img_vol = db.volume(img_series)
                    try:
                        results = radiomics.texture_features(roi_vol, img_vol, roi, img)
                    except Exception as e:
                        logging.error(f"Patient {patient} {roi} {img} - error computing radiomics-texture: {e}")
                    else:
                        dmr['data'] = dmr['data'] | {p:v[1:] for p, v in results.items()}
                        dmr['pars'] = dmr['pars'] | {(patient, 'Baseline', p): v[0] for p, v in results.items()}

            # Write results to file
            pydmr.write(dmr_file, dmr)

        # Both kidneys texture
        dmr_file = os.path.join(dir, f"{series}_{roi}.dmr.zip")
        if os.path.exists(dmr_file):
            continue
        class_index = {roi:idx for idx,roi in class_map.items()}
        vol = db.volume(mask_series)
        lk_mask = (vol.values==class_index['kidney_left']).astype(np.float32)
        rk_mask = (vol.values==class_index['kidney_right']).astype(np.float32)
        roi = 'kidneys_both'
        mask = lk_mask + rk_mask
        if np.sum(mask) == 0:
            continue
        roi_vol = vreg.volume(mask, vol.affine)
        dmr = {'data':{}, 'pars':{}}

        # Get radiomics texture features
        for img in ['out_phase', 'in_phase', 'fat', 'water']:
            img_series = [sitedatapath, patient, (study, 0), (f"{sequence}_{img}", 0)]
            if img_series not in all_data_series:
                continue
            img_vol = db.volume(img_series)
            try:
                results = radiomics.texture_features(roi_vol, img_vol, roi, img)
            except Exception as e:
                logging.error(f"Patient {patient} {roi} {img} - error computing radiomics-texture: {e}")
            else:
                dmr['data'] = dmr['data'] | {p:v[1:] for p, v in results.items()}
                dmr['pars'] = dmr['pars'] | {(patient, 'Baseline', p): v[0] for p, v in results.items()}

        # Write results to file
        pydmr.write(dmr_file, dmr)

    concat(site)






def all():
    measure('Bari')
    measure('Leeds')
    measure('Sheffield')

if __name__=='__main__':
    measure('Bari')
    # measure('Leeds')
    # measure('Sheffield')
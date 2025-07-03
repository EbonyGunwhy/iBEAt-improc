import os
import logging
import csv



from tqdm import tqdm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import dbdicom as db


datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
data_qc_path = os.path.join(os.getcwd(), 'build', 'dixon_3_check')
os.makedirs(data_qc_path, exist_ok=True)


# Set up logging
logging.basicConfig(
    filename=os.path.join(data_qc_path, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



def site_fatwater_swap(sitedatapath, file):

    # Skip if the site has no data yet.
    if not os.path.exists(sitedatapath):
        return

    # Skip if the file already exists.
    if os.path.exists(file):
        return

    # Get out-phase series
    series = db.series(sitedatapath)
    series_desc = [s[-1][0] for s in series]
    series_fat = [s for i, s in enumerate(series) if series_desc[i][-3:]=='fat']

    # If there are no fat images there is nothing to do
    if series_fat == []:
        return

    # Build list of center slices
    center_slices = []
    for series in tqdm(series_fat, desc='Reading fat images'):
        vol = db.volume(series)
        center_slice = vol.values[:,:,round(vol.shape[-1]/2)]
        center_slices.append(center_slice)

    # Display center slices as mosaic
    ncols = int(np.ceil(np.sqrt(len(center_slices))))
    fig, ax = plt.subplots(nrows=ncols, ncols=ncols, gridspec_kw = {'wspace':0, 'hspace':0}, figsize=(10,10), dpi=300)

    i=0
    for row in tqdm(ax, desc='Building png'):
        for col in row:

            col.set_xticklabels([])
            col.set_yticklabels([])
            col.set_aspect('equal')
            col.axis("off")

            if i < len(center_slices):

                # Show center image
                col.imshow(
                    center_slices[i].T, 
                    cmap='gray', 
                    interpolation='none', 
                    vmin=0, 
                    vmax=np.mean(center_slices[i]) + 2 * np.std(center_slices[i])
                )
                # Add white text with black background in upper-left corner
                patient_id = series_fat[i][1]
                series_desc = series_fat[i][-1][0]
                col.text(
                    0.01, 0.99,                   
                    f'{patient_id}\n{series_desc}',   
                    color='white',
                    fontsize=2,
                    ha='left',
                    va='top',
                    transform=col.transAxes,     # Use axes coordinates
                    bbox=dict(facecolor='black', alpha=0.7, boxstyle='round,pad=0.3')
                )

            i+=1 

    fig.suptitle('FatMaps', fontsize=14)
    fig.savefig(file)
    plt.close()



def fatwater_swap():
    for site in ['Leeds', 'Sheffield', 'Bari', 'Turku']:
        sitedatapath = os.path.join(datapath, site, "Patients") 
        sitepngpath = os.path.join(data_qc_path, f'{site}_fat_water_swap.png')
        site_fatwater_swap(sitedatapath, sitepngpath)



def fatwater_swap_record_template():
    """
    Template json file for manual recording of fat water swaps.

    Fat-water swaps should be manually recorded in this template by 
    setting the default value of 0 to 1. 
    
    The completed record should 
    be preserved in the data folder to be used in analyses.
    """

    csv_file = os.path.join(data_qc_path, 'fat_water_swap_record.csv')

    # If the file already exists, don't run it again
    if os.path.exists(csv_file):
        return

    swap_record = [
        ['Site', 'Patient', 'Study', 'Series', 'Swapped']
    ]
    for site in ['Leeds', 'Sheffield', 'Bari', 'Turku']:
        sitedatapath = os.path.join(datapath, site, "Patients") 
        if os.path.exists(sitedatapath):
            for series in tqdm(db.series(sitedatapath), desc=f"Building record for {site}"):
                patient_id = series[1]
                study_desc = series[2][0]
                series_desc = series[3][0]
                if series_desc[-3:]=='fat':
                    row = [site, patient_id, study_desc, series_desc[:-4], 0]
                    swap_record.append(row)

    # Write to CSV file
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(swap_record)


def count_dixons():

    # If the file already exists, don't run it again
    csv_file = os.path.join(data_qc_path, 'dixon_data.csv')
    if os.path.exists(csv_file):
        print('dixon_number_record.csv' + ' already exists. Skipping this step.')
        return
    
    # Build data
    data = [
        ['Site', 'Patient', 'Study', 'Dixon', 'Dixon_post_contrast', 'Use']
    ]
    for site in ['Leeds', 'Sheffield', 'Bari', 'Turku']:
        sitedatapath = os.path.join(datapath, site, "Patients") 
        for study in tqdm(db.studies(sitedatapath), desc=f"Counting dixons for {site}"):
            patient_id = study[1]
            study_desc = study[2][0]
            series = db.series(study)
            series_desc = [s[3][0] for s in series] #removed s[3][0] to make it work
            row = [site, patient_id, study_desc, 0, 0, '']
            for desc in ['Dixon', 'Dixon_post_contrast']:
                cnt=0
                while f'{desc}_{cnt+1}_out_phase' in series_desc:
                    cnt+=1
                if desc=='Dixon':
                    row[3] = f'{cnt}'
                else:
                    row[4] = f'{cnt}'
            # Use the last post-contrast if available, else the last precontrast.
            row[5] = f'Dixon_post_contrast_{row[4]}' if cnt>0 else f'Dixon_{row[3]}'
            data.append(row)

    # Save as csv
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)


def all():
    fatwater_swap()


if __name__=='__main__':
    fatwater_swap_record_template()
    fatwater_swap()
    count_dixons()

    # TODO export more detailed report of dixon data before running the segmentation
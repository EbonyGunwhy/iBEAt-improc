import os
import logging

from tqdm import tqdm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import dbdicom as db


datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
data_qc_path = os.path.join(os.getcwd(), 'build', 'dixon_3_data_check')
os.makedirs(data_qc_path, exist_ok=True)


# Set up logging
logging.basicConfig(
    filename=os.path.join(data_qc_path, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



def site_check_fatwater_swap(sitedatapath, sitepngpath):

    # If the file exists, dont build the figure
    file = os.path.join(sitepngpath, 'fat-water swap check.png')
    if os.path.exists(file):
        return

    # Get out phase series
    series = db.series(sitedatapath)
    series_desc = [s[-1][0] for s in series]
    series_fat = [s for s in series if series_desc[-3:]=='fat']

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
                col.text(
                    0.01, 0.99,                   
                    f'{series_fat[i][1][0]} - {series_fat[i][-1]}',   
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


def leeds_check_fatwater_swap():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients") 
    sitepngpath = os.path.join(data_qc_path, "BEAt-DKD-WP4-Leeds")
    os.makedirs(sitepngpath, exist_ok=True)
    site_check_fatwater_swap(sitedatapath, sitepngpath)


def sheffield_check_fatwater_swap():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Sheffield", "Sheffield_Patients") 
    sitepngpath = os.path.join(data_qc_path, "BEAt-DKD-WP4-Sheffield")
    os.makedirs(sitepngpath, exist_ok=True)
    site_check_fatwater_swap(sitedatapath, sitepngpath)



def all():
    leeds_check_fatwater_swap()
    sheffield_check_fatwater_swap()


if __name__=='__main__':
    leeds_check_fatwater_swap()
    sheffield_check_fatwater_swap()
import os
import logging

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm
from totalsegmentator.map_to_binary import class_map
import dbdicom as db


datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
maskpath = os.path.join(os.getcwd(), 'build', 'dixon_3_segment')
displaypath = os.path.join(os.getcwd(), 'build', 'dixon_4_display')
os.makedirs(displaypath, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=os.path.join(displaypath, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_distinct_colors(n, colormap='jet'):
    #cmap = cm.get_cmap(colormap, n)
    cmap = matplotlib.colormaps[colormap]
    colors = [cmap(i)[:3] + (0.6,) for i in np.linspace(0, 1, n)]  # Set alpha to 0.5 for transparency
    return colors


def total_masks_as_png(img, rois, file):

    # Define RGBA colors (R, G, B, Alpha) — alpha controls transparency
    colors = get_distinct_colors(len(rois), colormap='tab20')

    num_row_cols = int(np.ceil(np.sqrt(img.shape[2])))

    #fig, ax = plt.subplots(nrows=num_row_cols, ncols=num_row_cols, gridspec_kw = {'wspace':0, 'hspace':0}, figsize=(10,10), dpi=300)
    fig, ax = plt.subplots(nrows=num_row_cols, ncols=num_row_cols, gridspec_kw = {'wspace':0, 'hspace':0}, figsize=(num_row_cols,num_row_cols))

    i=0
    for row in tqdm(ax, desc='Building png'):
        for col in row:

            col.set_xticklabels([])
            col.set_yticklabels([])
            col.set_aspect('equal')
            col.axis("off")

            if i < img.shape[2]:

                # Display the background image
                col.imshow(img[:,:,i].T, cmap='gray', interpolation='none', vmin=0, vmax=np.mean(img) + 2 * np.std(img))

                # Overlay each mask
                for mask, color in zip([m.astype(bool) for m in rois.values()], colors):
                    rgba = np.zeros((img.shape[0], img.shape[1], 4), dtype=float)
                    for c in range(4):  # RGBA
                        rgba[..., c] = mask[:,:,i] * color[c]
                    col.imshow(rgba.transpose((1,0,2)), interpolation='none')

            i = i +1 

    fig.suptitle('TotalSegmentatorMask', fontsize=14)
    fig.savefig(file, dpi=600)
    #plt.savefig(file)
    plt.close()


def kidney_masks_as_png(img, rois, file):

    LK = rois['kidney_left'].astype(float)
    RK = rois['kidney_right'].astype(float)

    img = img.transpose((1,0,2))
    LK = LK.transpose((1,0,2))
    RK = RK.transpose((1,0,2))

    LK[LK >0.5] = 1
    LK[LK <0.5] = np.nan

    RK[RK >0.5] = 1
    RK[RK <0.5] = np.nan
    
    num_row_cols = int(np.ceil(np.sqrt(LK.shape[2])))

    #fig, ax = plt.subplots(nrows=num_row_cols, ncols=num_row_cols,gridspec_kw = {'wspace':0, 'hspace':0},figsize=(10,10), dpi=100)
    fig, ax = plt.subplots(nrows=num_row_cols, ncols=num_row_cols,gridspec_kw = {'wspace':0, 'hspace':0},figsize=(num_row_cols,num_row_cols))
    i=0
    for row in ax:
        for col in row:
            if i>=LK.shape[2]:
                col.set_xticklabels([])
                col.set_yticklabels([])
                col.set_aspect('equal')
                col.axis("off")
            else:  
            
                # Display the background image
                col.imshow(img[:,:,i], cmap='gray', interpolation='none', vmin=0, vmax=np.mean(img) + 2 * np.std(img))
            
                # Overlay the mask with transparency
                col.imshow(LK[:,:,i], cmap='autumn', interpolation='none', alpha=0.5)
                col.imshow(RK[:,:,i], cmap='summer', interpolation='none', alpha=0.5)

                col.set_xticklabels([])
                col.set_yticklabels([])
                col.set_aspect('equal')
                col.axis("off")
            i = i +1 

    fig.suptitle('AutoMask', fontsize=14)
    fig.savefig(file, dpi=600)
    #plt.savefig(file)
    plt.close()


def mosaic(sitedatapath, sitemaskpath, sitedisplaypath):

    # Build output folders
    display_all = os.path.join(displaypath, sitedisplaypath, 'Mask_overlay_all')
    display_kidneys = os.path.join(displaypath, sitedisplaypath, 'Mask_overlay_kidneys')
    os.makedirs(display_all, exist_ok=True)
    os.makedirs(display_kidneys, exist_ok=True)

    class_maps = {
        'totseg': class_map['total_mr'],
        'nnunet': {1: "kidney_left", 2: "kidney_right"},
        'unetr': {1: "kidney_left", 2: "kidney_right"},
    }

    # Loop over the masks
    for mask in tqdm(db.series(sitemaskpath), 'Displaying masks..'):

        # Get the corresponding outphase series
        patient_id = mask[1]
        mask_dixon_desc = mask[-1][0]

        # Find model from series description
        for model in class_maps.keys():
            if mask_dixon_desc[-len(model):]==model:
                break

        # Get opposed phase series
        mask_dixon = mask_dixon_desc[:-len(model)]
        series_op = [sitedatapath, patient_id, 'Baseline', f'{mask_dixon}out_phase']

        # Get arrays
        op_arr = db.volume(series_op).values
        mask_arr = db.volume(mask).values
        rois = {}
        for idx, roi in class_maps[model].items():
            rois[roi] = (mask_arr==idx).astype(np.int16)
        
        # Build display
        png_file = os.path.join(display_all, f'{patient_id}_{mask_dixon}{model}_all.png')
        if not os.path.exists(png_file):
            total_masks_as_png(op_arr, rois, png_file)
        png_file = os.path.join(display_kidneys, f'{patient_id}_{mask_dixon}{model}_kidneys.png')
        if not os.path.exists(png_file):
            kidney_masks_as_png(op_arr, rois, png_file)


def leeds():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients") 
    sitemaskpath = os.path.join(maskpath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients")
    sitedisplaypath = os.path.join(displaypath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients")
    mosaic(sitedatapath, sitemaskpath, sitedisplaypath)


def bari():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Bari", "Bari_Patients") 
    sitemaskpath = os.path.join(maskpath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    sitedisplaypath = os.path.join(displaypath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    mosaic(sitedatapath, sitemaskpath, sitedisplaypath)


def all():
    bari()
    leeds()

if __name__=='__main__':
    bari()
    leeds()
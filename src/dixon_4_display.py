import os
import logging
import shutil

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm
from totalsegmentator.map_to_binary import class_map
import dbdicom as db
import imageio.v2 as imageio  # Use v2 interface for compatibility
from moviepy import VideoFileClip


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
    colors = [cmap(i)[:3] + (0.6,) for i in np.linspace(0, 1, n)]  # Set alpha to 0.6 for transparency
    return colors


def animation_model(img, rois, file):

    # Define RGBA colors (R, G, B, Alpha) — alpha controls transparency
    if len(rois)==1:
        colors = [[255, 0, 0, 0.6]]
    elif len(rois)==2:
        colors = [[0, 255, 0, 0.6], [255, 0, 0, 0.6]]
    else:
        colors = get_distinct_colors(len(rois), colormap='tab20')

    # Directory to store temporary frames
    tmp = os.path.join(os.getcwd(), 'tmp')
    os.makedirs(tmp, exist_ok=True)
    filenames = []

    # Generate and save a sequence of plots
    for i in tqdm(range(img.shape[2]), desc='Building animation..'):

        # Set up figure
        fig, ax = plt.subplots(
            figsize=(5, 5),
            dpi=300,
        )

        # Display the background image
        ax.imshow(img[:,:,i].T, cmap='gray', interpolation='none', vmin=0, vmax=np.mean(img) + 2 * np.std(img))

        # Overlay each mask
        for mask, color in zip([m.astype(bool) for m in rois.values()], colors):
            rgba = np.zeros((img.shape[0], img.shape[1], 4), dtype=float)
            for c in range(4):  # RGBA
                rgba[..., c] = mask[:,:,i] * color[c]
            ax.imshow(rgba.transpose((1,0,2)), interpolation='none')

        # Save eachg image to a tmp file
        fname = os.path.join(tmp, f'frame_{i}.png')
        fig.savefig(fname)
        filenames.append(fname)
        plt.close(fig)

    # Create GIF
    print('Creating movie')
    gif = os.path.join(tmp, 'movie.gif')
    with imageio.get_writer(gif, mode="I", duration=0.2) as writer:
        for fname in filenames:
            image = imageio.imread(fname)
            writer.append_data(image)

    # Load gif
    clip = VideoFileClip(gif)

    # Save as MP4
    clip.write_videofile(file, codec='libx264')

    # Clean up temporary files
    shutil.rmtree(tmp)


def mosaic_model(img, rois, file):

    # Define RGBA colors (R, G, B, Alpha) — alpha controls transparency
    if len(rois)==1:
        colors = [[255, 0, 0, 0.6]]
    elif len(rois)==2:
        colors = [[255, 0, 0, 0.6], [0, 255, 0, 0.6]]
    else:
        colors = get_distinct_colors(len(rois), colormap='tab20')

    num_row_cols = int(np.ceil(np.sqrt(img.shape[2])))

    #fig, ax = plt.subplots(nrows=num_row_cols, ncols=num_row_cols, gridspec_kw = {'wspace':0, 'hspace':0}, figsize=(10,10), dpi=300)
    fig, ax = plt.subplots(
        nrows=num_row_cols, 
        ncols=num_row_cols, 
        gridspec_kw = {'wspace':0, 'hspace':0}, 
        figsize=(num_row_cols, num_row_cols),
        dpi=300,
    )
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

    fig.suptitle('AutoMask', fontsize=14)
    fig.savefig(file)
    #plt.savefig(file)
    plt.close()



def overlay(sitedatapath, sitemaskpath, sitedisplaypath, 
            kidney=False, all=False, liver_pancreas=False, movie=False, 
            mosaic=False):

    # Build output folders
    display_all = os.path.join(displaypath, sitedisplaypath, 'Mosaic_all')
    display_kidneys = os.path.join(displaypath, sitedisplaypath, 'Mosaic_kidneys')
    display_liver_pancreas = os.path.join(displaypath, sitedisplaypath, 'Mosaic_liver_pancreas')
    os.makedirs(display_all, exist_ok=True)
    os.makedirs(display_kidneys, exist_ok=True)
    os.makedirs(display_liver_pancreas, exist_ok=True)
    movies_all = os.path.join(displaypath, sitedisplaypath, 'Movies_all')
    movies_kidneys = os.path.join(displaypath, sitedisplaypath, 'Movies_kidneys')
    movies_liver_pancreas = os.path.join(displaypath, sitedisplaypath, 'Movies_liver_pancreas')
    os.makedirs(movies_all, exist_ok=True)
    os.makedirs(movies_kidneys, exist_ok=True)
    os.makedirs(movies_liver_pancreas, exist_ok=True)


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
        model = mask_dixon_desc.split('_')[-1]

        # Get opposed phase series
        mask_dixon = mask_dixon_desc[:-len(model)]
        series_op = [sitedatapath, patient_id, 'Baseline', f'{mask_dixon}out_phase']

        # Get arrays
        op_arr = db.volume(series_op).values
        mask_arr = db.volume(mask).values
        rois = {}
        for idx, roi in class_maps[model].items():
            rois[roi] = (mask_arr==idx).astype(np.int16)

        # Build movie (kidneys only)
        if kidney and movie:
            file = os.path.join(movies_kidneys, f'{patient_id}_{mask_dixon}{model}_kidneys.mp4')
            if not os.path.exists(file):
                rois_k = {k:v for k, v in rois.items() if k in ["kidney_left", "kidney_right"]}
                animation_model(op_arr, rois_k, file)

        # Build movie (all ROIS)
        if model == 'totseg':
            if all and movie:
                file = os.path.join(movies_all, f'{patient_id}_{mask_dixon}{model}_all.mp4')
                if not os.path.exists(file):
                    animation_model(op_arr, rois, file)
            if liver_pancreas and movie:
                file = os.path.join(movies_liver_pancreas, f'{patient_id}_{mask_dixon}{model}_pancreas_liver.mp4')
                if not os.path.exists(file):
                    rois_pl = {k:v for k, v in rois.items() if k in ["pancreas", "liver"]}
                    animation_model(op_arr, rois_pl, file)
        
        # Build mosaic (kidneys only)
        if kidney and mosaic:
            png_file = os.path.join(display_kidneys, f'{patient_id}_{mask_dixon}{model}_kidneys.png')
            if not os.path.exists(png_file):
                rois_k = {k:v for k, v in rois.items() if k in ["kidney_left", "kidney_right"]}
                mosaic_model(op_arr, rois_k, png_file)

        # Build mosaic (all ROIS)
        if model == 'totseg':
            if all and mosaic:
                png_file = os.path.join(display_all, f'{patient_id}_{mask_dixon}{model}_all.png')
                if not os.path.exists(png_file):
                    mosaic_model(op_arr, rois, png_file)
            if liver_pancreas and mosaic:
                png_file = os.path.join(display_liver_pancreas, f'{patient_id}_{mask_dixon}{model}_pancreas_liver.png')
                if not os.path.exists(png_file):
                    rois_pl = {k:v for k, v in rois.items() if k in ["pancreas", "liver"]}
                    mosaic_model(op_arr, rois_pl, png_file)




def leeds():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients") 
    sitemaskpath = os.path.join(maskpath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients")
    sitedisplaypath = os.path.join(displaypath, "BEAt-DKD-WP4-Leeds", "Leeds_Patients")
    #overlay(sitedatapath, sitemaskpath, sitedisplaypath, kidney=True, mosaic=True)
    overlay(sitedatapath, sitemaskpath, sitedisplaypath, all=True, mosaic=True)


def bari():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Bari", "Bari_Patients") 
    sitemaskpath = os.path.join(maskpath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    sitedisplaypath = os.path.join(displaypath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    #overlay(sitedatapath, sitemaskpath, sitedisplaypath, kidney=True, mosaic=True)
    overlay(sitedatapath, sitemaskpath, sitedisplaypath, all=True, mosaic=True)


def all():
    bari()
    leeds()

if __name__=='__main__':
    bari()
    leeds()
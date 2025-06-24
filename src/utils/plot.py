import os
import shutil

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm
import imageio.v2 as imageio  # Use v2 interface for compatibility
from moviepy import VideoFileClip




def get_distinct_colors(n, colormap='jet'):
    #cmap = cm.get_cmap(colormap, n)
    cmap = matplotlib.colormaps[colormap]
    colors = [cmap(i)[:3] + (0.6,) for i in np.linspace(0, 1, n)]  # Set alpha to 0.6 for transparency
    return colors


def movie_overlay(img, rois, file):

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


def mosaic_overlay(img, rois, file, colormap='tab20'):

    # Define RGBA colors (R, G, B, Alpha) — alpha controls transparency
    if len(rois)==1:
        colors = [[255, 0, 0, 0.6]]
    elif len(rois)==2:
        colors = [[255, 0, 0, 0.6], [0, 255, 0, 0.6]]
    elif len(rois)==3:
        colors = [[255, 0, 0, 0.6], [0, 255, 0, 0.6], [0, 0, 255, 0.6]]
    else:
        colors = get_distinct_colors(len(rois), colormap=colormap)

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
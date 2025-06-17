import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm



def get_distinct_colors(n, colormap='jet'):
    #cmap = cm.get_cmap(colormap, n)
    cmap = matplotlib.colormaps[colormap]
    colors = [cmap(i)[:3] + (0.6,) for i in np.linspace(0, 1, n)]  # Set alpha to 0.5 for transparency
    return colors


def total_masks_as_png(img, rois, file):

    # Define RGBA colors (R, G, B, Alpha) — alpha controls transparency
    colors = get_distinct_colors(len(rois), colormap='tab20')

    num_row_cols = int(np.ceil(np.sqrt(img.shape[2])))

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
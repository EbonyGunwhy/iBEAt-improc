import os

import dbdicom as db


def autosegmentation(group, site=None):
    datapath = os.path.join(os.getcwd(), 'build', 'totseg', 'stage_1_segment')
    archivepath = os.path.join("G:\\Shared drives", "iBEAt Build", 'totseg', 'stage_1_segment')
    if group == 'Controls':
        sitedatapath = os.path.join(datapath, "Controls") 
        sitearchivepath = os.path.join(archivepath, 'Controls')
    else:
        sitedatapath = os.path.join(datapath, "Patients", site) 
        sitearchivepath = os.path.join(archivepath, "Patients", site)
    db.archive(sitedatapath, sitearchivepath)

    
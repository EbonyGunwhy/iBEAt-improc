import os

import dbdicom as db


def archive_autosegmentation(site):
    datapath = os.path.join(os.getcwd(), 'build', 'kidneyvol_1_segment')
    archivepath = os.path.join("G:\\Shared drives", "iBEAt Build", 'kidneyvol_1_segment')
    if site == 'Controls':
        sitedatapath = os.path.join(datapath, "Controls") 
        sitearchivepath = os.path.join(archivepath, 'Controls')
    else:
        sitedatapath = os.path.join(datapath, site, "Patients") 
        sitearchivepath = os.path.join(archivepath, site, 'Patients')
    db.archive(sitedatapath, sitearchivepath)


def archive_edits(site):
    datapath = os.path.join(os.getcwd(), 'build', 'kidneyvol_3_edit')
    archivepath = os.path.join("G:\\Shared drives", "iBEAt Build", 'kidneyvol_3_edit')
    if site == 'Controls':
        sitedatapath = os.path.join(datapath, "Controls") 
        sitearchivepath = os.path.join(archivepath, 'Controls')
    else:
        sitedatapath = os.path.join(datapath, site, "Patients") 
        sitearchivepath = os.path.join(archivepath, site, 'Patients')
    db.archive(sitedatapath, sitearchivepath)
    

if __name__=='__main__':

    # archive_autosegmentation('Leeds')
    # archive_autosegmentation('Sheffield')
    # archive_autosegmentation('Bari')
    # archive_autosegmentation('Bordeaux')
    # archive_autosegmentation('Exeter')
    # archive_edits('Bari')
    # archive_edits('Leeds')
    # archive_edits('Sheffield')
    # archive_edits('Bordeaux')
    # archive_edits('Exeter')
    # archive_edits('Turku')

    archive_autosegmentation('Controls')
    archive_edits('Controls')
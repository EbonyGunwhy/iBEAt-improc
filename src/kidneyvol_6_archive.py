import os

import dbdicom as db


def archive_autosegmentation(site):
    datapath = os.path.join(os.getcwd(), 'build', 'kidneyvol_1_segment')
    archivepath = os.path.join("G:\\Shared drives", "iBEAt Build", 'kidneyvol_1_segment')
    sitedatapath = os.path.join(datapath, site, 'Patients')
    sitearchivepath = os.path.join(archivepath, site, 'Patients')
    db.archive(sitedatapath, sitearchivepath)


def archive_edits(site):
    datapath = os.path.join(os.getcwd(), 'build', 'kidneyvol_3_edit')
    archivepath = os.path.join("G:\\Shared drives", "iBEAt Build", 'kidneyvol_3_edit')
    sitedatapath = os.path.join(datapath, site, 'Patients')
    sitearchivepath = os.path.join(archivepath, site, 'Patients')
    db.archive(sitedatapath, sitearchivepath)

if __name__=='__main__':

    # archive_autosegmentation('Leeds')
    # archive_autosegmentation('Sheffield')
    # archive_autosegmentation('Bari')
    archive_edits('Bari')
    


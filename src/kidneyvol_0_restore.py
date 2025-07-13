import os
import logging

import dbdicom as db


def dixons(site):
    datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
    archivepath = os.path.join("G:\\Shared drives", "iBEAt Build", "dixon_2_data")
    sitedatapath = os.path.join(datapath, site, 'Patients')
    sitearchivepath = os.path.join(archivepath, site, 'Patients')
    db.restore(sitearchivepath, sitedatapath)


def segmentations(site):
    datapath = os.path.join(os.getcwd(), 'build', 'kidneyvol_1_segment')
    archivepath = os.path.join("G:\\Shared drives", "iBEAt Build", "kidneyvol_1_segment")
    sitedatapath = os.path.join(datapath, site, 'Patients')
    sitearchivepath = os.path.join(archivepath, site, 'Patients')
    db.restore(sitearchivepath, sitedatapath)

    datapath = os.path.join(os.getcwd(), 'build', 'kidneyvol_3_edit')
    archivepath = os.path.join("G:\\Shared drives", "iBEAt Build", "kidneyvol_3_edit")
    sitedatapath = os.path.join(datapath, site, 'Patients')
    sitearchivepath = os.path.join(archivepath, site, 'Patients')
    db.restore(sitearchivepath, sitedatapath)


if __name__=='__main__':

    dixons('Bari')


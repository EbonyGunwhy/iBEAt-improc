import os
import logging

import dbdicom as db

datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
archivepath = target_dir = os.path.join("G:\\Shared drives", "iBEAt Build", "dixon_2_data")


def restore(site):
    sitedatapath = os.path.join(datapath, site, 'Patients')
    sitearchivepath = os.path.join(archivepath, site, 'Patients')
    db.restore(sitearchivepath, sitedatapath)


if __name__=='__main__':

    # restore('Sheffield')
    restore('Bari')
    #restore('Leeds')


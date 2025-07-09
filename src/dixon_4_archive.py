import os


import dbdicom as db

datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')
archivepath = target_dir = os.path.join("G:\\Shared drives", "iBEAt Build", "dixon_2_data")


def archive_clean_dixons(site):
    sitedatapath = os.path.join(datapath, site, 'Patients')
    sitearchivepath = os.path.join(archivepath, site, 'Patients')
    db.archive(sitedatapath, sitearchivepath)


if __name__=='__main__':

    archive_clean_dixons('Leeds')
    archive_clean_dixons('Sheffield')
    archive_clean_dixons('Bari')
    


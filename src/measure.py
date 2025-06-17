import os

import dbdicom as db
from radiomics import featureextractor

datapath = os.path.join(os.getcwd(), 'build', 'Data')
maskpath = os.path.join(os.getcwd(), 'build', 'Masks')
measurepath = os.path.join(os.getcwd(), 'build', 'Measure')



def bari():
    sitedatapath = os.path.join(datapath, "BEAt-DKD-WP4-Bari", "Bari_Patients") 
    sitemaskpath = os.path.join(maskpath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    sitemeasurepath = os.path.join(measurepath, "BEAt-DKD-WP4-Bari", "Bari_Patients")
    os.makedirs(sitemeasurepath, exist_ok=True)
    for mask_series in db.series(sitemaskpath):
        pass


if __name__=='__main__':
    bari()
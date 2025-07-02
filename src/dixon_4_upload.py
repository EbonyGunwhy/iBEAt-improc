import os
import logging

import utils.osf

datapath = os.path.join(os.getcwd(), 'build', 'dixon_2_data')


# Set up logging
logging.basicConfig(
    filename=os.path.join(os.getcwd(), 'build', 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def upload(site):

    print('Uploading: ', site)
    OSF_TOKEN = utils.osf.token()
    COMPONENT_ID = "t7rgm"
    LOCAL_FOLDER = os.path.join(datapath, site)
    OSF_TARGET_FOLDER = os.path.join('iBEAt', 'dixon_2_data')  

    utils.osf.upload_folder(OSF_TOKEN, COMPONENT_ID, LOCAL_FOLDER, OSF_TARGET_FOLDER)


if __name__=='__main__':

    upload('Sheffield')
    upload('Bari')
    upload('Leeds')


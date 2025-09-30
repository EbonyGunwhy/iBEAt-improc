import os

import logging

from utils import export



LOCALPATH = os.path.join(os.getcwd(), 'build')
SHAREDPATH = os.path.join("G:\\Shared drives", "iBEAt_Build")


# Set up logging
logging.basicConfig(
    filename=os.path.join(LOCALPATH, 'error.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def export_antaros():
    input_file = "C:\\Users\\md1spsx\\Downloads\\BEAt_DKD_Interim_20231016.csv"
    export.antaros_to_redcap(input_file, LOCALPATH)




if __name__ == '__main__':
    export_antaros()
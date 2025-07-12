"""
Automatic download of DIXON data from XNAT.

"""

import os

from utils import xnat

path = os.path.join(os.getcwd(), 'build', 'dixon_1_download')  
os.makedirs(path, exist_ok=True)



def leeds_patients():
    username, password = xnat.credentials()
    xnat.download_scans(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        output_dir=path,
        project_id="BEAt-DKD-WP4-Leeds",
        subject_label="Leeds_Patients",
        attr="parameters/sequence",
        value="*fl3d2",
    )


def leeds_volunteers():
    username, password = xnat.credentials()
    xnat.download_scans(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        output_dir=path,
        project_id="BEAt-DKD-WP4-Leeds",
        subject_label="Leeds_volunteer_repeatability_study",
        attr="parameters/sequence",
        value="*fl3d2",
    )


def bari_patients():
    username, password = xnat.credentials()
    xnat.download_scans(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        output_dir=path,
        project_id="BEAt-DKD-WP4-Bari",
        subject_label="Bari_Patients",
        attr="series_description",
        value=[
            "T1w_abdomen_dixon_cor_bh", 
            "T1w_abdomen_post_contrast_dixon_cor_bh"
        ],
    )


def sheffield_patients():
    username, password = xnat.credentials()
    xnat.download_scans(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        output_dir=path,
        project_id="BEAt-DKD-WP4-Sheffield",
        attr="series_description",
        value=[
            # Philips data
            'T1w_abdomen_dixon_cor_bh', 
            'T1w_abdomen_post_contrast_dixon_cor_bh',
            # GE data
            'WATER: T1_abdomen_dixon_cor_bh',
            'FAT: T1_abdomen_dixon_cor_bh',
            'InPhase: T1_abdomen_dixon_cor_bh',
            'OutPhase: T1_abdomen_dixon_cor_bh',
            'WATER: T1_abdomen_post_contrast_dixon_cor_bh',
            'FAT: T1_abdomen_post_contrast_dixon_cor_bh',
            'InPhase: T1_abdomen_post_contrast_dixon_cor_bh',
            'OutPhase: T1_abdomen_post_contrast_dixon_cor_bh',
        ],
    )

def turku_ge_patients():
    username, password = xnat.credentials()
    xnat.download_scans(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        output_dir=path,
        project_id="BEAt-DKD-WP4-Turku",
        subject_label="Turku_Patients_GE",
        attr="series_description",
        value=[
            "WATER: T1_abdomen_dixon_cor_bh", 
            "FAT: T1_abdomen_dixon_cor_bh",
            "InPhase: T1_abdomen_dixon_cor_bh",
            "OutPhase: T1_abdomen_dixon_cor_bh",
            "WATER: T1_abdomen_post_contrast_dixon_cor_bh",
            "FAT: T1_abdomen_post_contrast_dixon_cor_bh",
            "InPhase: T1_abdomen_post_contrast_dixon_cor_bh",
            "OutPhase: T1_abdomen_post_contrast_dixon_cor_bh"
        ],
    )

def turku_philips_patients():
    username, password = xnat.credentials()
    xnat.download_scans(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        output_dir=path,
        project_id="BEAt-DKD-WP4-Turku",
        subject_label="Turku_Patients_Philips",
        attr="series_description",
        value=[
            'T1W-abdomen-Dixon-coronal-BH', 
            'T1W-abdomen-Dixon-post-coronal-BH',
        ],
    )

def bordeaux_patients_baseline():
    username, password = xnat.credentials()
    xnat.download_scans(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        output_dir=path,
        project_id="BEAt-DKD-WP4-Bordeaux",
        subject_label="Bordeaux_Patients_Baseline",
        attr="series_description",
        value=[
            "T1w_abdomen_dixon_cor_bh_opp", 
            "T1w_abdomen_dixon_cor_bh_in",
            "T1w_abdomen_dixon_cor_bh_F",
            "T1w_abdomen_dixon_cor_bh_W",
            "T1w_abdomen_post_contrast_dixon_cor_bh_opp",
            "T1w_abdomen_post_contrast_dixon_cor_bh_in",
            "T1w_abdomen_post_contrast_dixon_cor_bh_F",
            "T1w_abdomen_post_contrast_dixon_cor_bh_W"
        ],
    )

def bordeaux_patients_followup():
    username, password = xnat.credentials()
    xnat.download_scans(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        output_dir=path,
        project_id="BEAt-DKD-WP4-Bordeaux",
        subject_label="Bordeaux_Patients_Followup",
        attr="series_description",
        value=[
            "T1w_abdomen_dixon_cor_bh_opp", 
            "T1w_abdomen_dixon_cor_bh_in",
            "T1w_abdomen_dixon_cor_bh_F",
            "T1w_abdomen_dixon_cor_bh_W",
            "T1w_abdomen_post_contrast_dixon_cor_bh_opp",
            "T1w_abdomen_post_contrast_dixon_cor_bh_in",
            "T1w_abdomen_post_contrast_dixon_cor_bh_F",
            "T1w_abdomen_post_contrast_dixon_cor_bh_W"
        ],
    )

def exeter_patients_baseline():
    username, password = xnat.credentials()
    xnat.download_scans(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        output_dir=path,
        project_id="BEAt-DKD-WP4-Exeter",
        subject_label="Exeter_Patients_Baseline",
        attr="series_description",
        value=[
            "T1w_abdomen_dixon_cor_bh", 
            "T1w_abdomen_dixon_cor_bh_opp", 
            "T1w_abdomen_dixon_cor_bh_in",
            "T1w_abdomen_dixon_cor_bh_F",
            "T1w_abdomen_dixon_cor_bh_W",
            "T1w_abdomen_post_contrast_dixon_cor_bh",
            "T1w_abdomen_post_contrast_dixon_cor_bh_opp",
            "T1w_abdomen_post_contrast_dixon_cor_bh_in",
            "T1w_abdomen_post_contrast_dixon_cor_bh_F",
            "T1w_abdomen_post_contrast_dixon_cor_bh_W"
        ],
    )

def exeter_patients_followup():
    username, password = xnat.credentials()
    xnat.download_scans(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        output_dir=path,
        project_id="BEAt-DKD-WP4-Exeter",
        subject_label="Exeter_Patients_Followup",
        attr="series_description",
        value=[
            "T1w_abdomen_dixon_cor_bh_opp", 
            "T1w_abdomen_dixon_cor_bh_in",
            "T1w_abdomen_dixon_cor_bh_F",
            "T1w_abdomen_dixon_cor_bh_W",
            "T1w_abdomen_post_contrast_dixon_cor_bh_opp",
            "T1w_abdomen_post_contrast_dixon_cor_bh_in",
            "T1w_abdomen_post_contrast_dixon_cor_bh_F",
            "T1w_abdomen_post_contrast_dixon_cor_bh_W"
        ],
    )




# def all():
#     leeds_patients()
#     bari_patients()
#     sheffield_patients()
    # leeds_volunteers()



if __name__=='__main__':
   
    # leeds_patients()
    # bari_patients()
    #sheffield_patients()
    # turku_philips_patients()

    # bordeaux_patients_baseline()
    # bordeaux_patients_followup()
    exeter_patients_baseline()
    # exeter_patients_followup()

    # leeds_volunteers()



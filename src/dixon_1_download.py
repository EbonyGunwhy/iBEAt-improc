
import os
import requests
from requests.auth import HTTPBasicAuth

path = os.path.join(os.getcwd(), 'build', 'dixon_1_download')  
os.makedirs(path, exist_ok=True)

# import zipfile
# import datetime
# import xnat
# import io
# import pydicom


# def download_series_by_dicom_sequence_name(xnat_url, username, password,
#                                            project_id, subject_id, sequence_name,
#                                            output_dir="xnat_downloads"):
#     """
#     Downloads scan series from XNAT where DICOM SequenceName matches the given value.

#     Args:
#         xnat_url (str): Base XNAT URL.
#         username (str): XNAT login.
#         password (str): XNAT password.
#         project_id (str): Project ID.
#         subject_id (str): Subject ID.
#         sequence_name (str): DICOM SequenceName tag value to match.
#         output_dir (str): Directory to save matched series.
#     """

#     session = requests.Session()
#     session.auth = HTTPBasicAuth(username, password)
#     os.makedirs(output_dir, exist_ok=True)

#     # Get subject experiments
#     exp_url = f"{xnat_url}/data/projects/{project_id}/subjects/{subject_id}/experiments?format=json"
#     r = session.get(exp_url)
#     r.raise_for_status()
#     experiments = r.json()['ResultSet']['Result']

#     for exp in experiments:
#         exp_id = exp['ID']
#         scans_url = f"{xnat_url}/data/experiments/{exp_id}/scans?format=json"
#         r = session.get(scans_url)
#         r.raise_for_status()
#         scans = r.json()['ResultSet']['Result']

#         for scan in scans:
#             scan_id = scan['ID']
#             # Download a sample DICOM file to check SequenceName
#             sample_url = f"{xnat_url}/data/experiments/{exp_id}/scans/{scan_id}/resources/DICOM/files?format=zip"
#             r = session.get(sample_url)
#             if r.status_code != 200:
#                 continue
#             try:
#                 with zipfile.ZipFile(io.BytesIO(r.content)) as zip_file:
#                     # Get the first DICOM file in the archive
#                     dicom_names = [name for name in zip_file.namelist() if name.lower().endswith('.dcm')]
#                     if not dicom_names:
#                         continue
#                     with zip_file.open(dicom_names[0]) as dcm_file:
#                         dcm = pydicom.dcmread(dcm_file, stop_before_pixels=True)
#                         seq = getattr(dcm, "SequenceName", None)
#                         if seq == sequence_name:
#                             print(f"Matched scan {scan_id} (SequenceName: {seq})")
#                             out_path = os.path.join(output_dir, f"{subject_id}_{exp_id}_{scan_id}.zip")
#                             with open(out_path, 'wb') as f:
#                                 f.write(r.content)
#                             print(f"Saved scan to {out_path}")
#             except Exception as e:
#                 print(f"Error processing scan {scan_id}: {e}")



def download_series_by_attr_all_subjects(
    xnat_url, username, password,
    project_id,
    attr, value,
    output_dir,
):
    """
    Downloads all scan series with a given attribute value from all subjects in a project.

    Args:
        xnat_url (str): Base URL of the XNAT server.
        username (str): XNAT username.
        password (str): XNAT password.
        project_id (str): XNAT project ID.
        attr (str): Attribute to filter by (e.g., 'sequence').
        value: Desired value, or list of values, for the attribute.
        output_dir (str): Directory to store downloaded data.
    """

    session = requests.Session()
    session.auth = HTTPBasicAuth(username, password)

    os.makedirs(output_dir, exist_ok=True)

    # Get all subjects in the project
    subj_url = f"{xnat_url}/data/projects/{project_id}/subjects?format=json"
    r = session.get(subj_url)
    r.raise_for_status()
    subjects = r.json()['ResultSet']['Result']

    for subj in subjects:
        subject_id = subj['ID']
        subject_label = subj['label']
        print(f"Checking subject: {subject_label}")

        # Get subject's experiments
        exp_url = f"{xnat_url}/data/projects/{project_id}/subjects/{subject_id}/experiments?format=json"
        r = session.get(exp_url)
        r.raise_for_status()
        experiments = r.json()['ResultSet']['Result']

        for exp in experiments:
            exp_id = exp['ID']
            exp_label = exp['label']
            print(f"  Examining experiment: {exp_label}")

            # Get scans in the experiment
            scans_url = f"{xnat_url}/data/experiments/{exp_id}/scans?format=json"
            r = session.get(scans_url)
            r.raise_for_status()
            scans = r.json()['ResultSet']['Result']

            for scan in scans:
                scan_id = scan['ID']

                # Retrieve scan attributes
                attr_url = f"{xnat_url}/data/experiments/{exp_id}/scans/{scan_id}?format=json"
                r = session.get(attr_url)
                r.raise_for_status()
                scan_attrs = r.json()['items'][0]['data_fields']

                if scan_attrs.get(attr) == value:
                    print(f"    Downloading scan {scan_id} (matches {attr} == {value})")

                    download_url = f"{xnat_url}/data/experiments/{exp_id}/scans/{scan_id}/resources/DICOM/files?format=zip"
                    out_folder = os.path.join(output_dir, subject_label, exp_label)
                    out_path = os.path.join(out_folder, f"series_{scan_id.zfill(2)}.zip")
                    os.makedirs(out_folder, exist_ok=True)

                    r = session.get(download_url, stream=True)
                    with open(out_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)



def download_series_by_attr(xnat_url, username, password,
                            project_id, subject_id, 
                            attr, value,
                            output_dir):
    """
    Downloads all scan series from XNAT with a given value for a specific attribute.

    Args:
        xnat_url (str): Base URL of the XNAT server.
        username (str): Your XNAT username.
        password (str): Your XNAT password.
        project_id (str): XNAT project ID.
        subject_id (str): XNAT subject label (not internal ID).
        attr (str): XNAT attribute to filter by.
        value: value of the XNAT attribute.
        output_dir (str): Directory to save downloaded series.
    """
    if isinstance(value, str):
        value = [value]

    session = requests.Session()
    session.auth = HTTPBasicAuth(username, password)

    os.makedirs(output_dir, exist_ok=True)

    # Get subject experiments (sessions)
    exp_url = f"{xnat_url}/data/projects/{project_id}/subjects/{subject_id}/experiments?format=json"
    r = session.get(exp_url)
    r.raise_for_status()
    experiments = r.json()['ResultSet']['Result']

    for exp in experiments:
        exp_id = exp['ID']
        # Get all scans for this experiment
        scans_url = f"{xnat_url}/data/experiments/{exp_id}/scans?format=json"
        r = session.get(scans_url)
        r.raise_for_status()
        scans = r.json()['ResultSet']['Result']

        for scan in scans:
            scan_id = scan['ID']
            # Check the SequenceName
            attr_url = f"{xnat_url}/data/experiments/{exp_id}/scans/{scan_id}?format=json"
            r = session.get(attr_url)
            r.raise_for_status()
            scan_attrs = r.json()['items'][0]['data_fields']

            if scan_attrs.get(attr) in value:
                # Download DICOM files
                download_url = f"{xnat_url}/data/experiments/{exp_id}/scans/{scan_id}/resources/DICOM/files?format=zip"
                out_folder = os.path.join(output_dir, project_id, subject_id, f"{exp['label']}")
                out_path = os.path.join(out_folder, f"series_{scan_id.zfill(2)}.zip")
                os.makedirs(out_folder, exist_ok=True)
                r = session.get(download_url, stream=True)
                with open(out_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)




def create_user_file():
    # Ask the user for username and password
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    # Create a text file and write the username and password to it
    with open("user_XNAT.txt", "w") as file:
        file.write(f"Username: {username}\n")
        file.write(f"Password: {password}\n")

def read_user_file():
    # Read the username and password from the text file
    with open("user_XNAT.txt", "r") as file:
        lines = file.readlines()
        username = lines[0].split(":")[1].strip()
        password = lines[1].split(":")[1].strip()

    return username, password

def get_credentials():
    # Check if the file exists
    if os.path.exists("user_XNAT.txt"):
        # If the file exists, read username and password
        existing_username, existing_password = read_user_file()
    else:
        # If the file does not exist, create a new file and ask for username and password
        create_user_file()
        print("User file created successfully.")
        existing_username, existing_password = read_user_file()
    return existing_username, existing_password



def leeds_patients():
    username, password = get_credentials()
    download_series_by_attr(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        project_id="BEAt-DKD-WP4-Leeds",
        subject_id="Leeds_Patients",
        attr="parameters/sequence",
        value="*fl3d2",
        output_dir=path,
    )

def leeds_volunteers():
    username, password = get_credentials()
    download_series_by_attr(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        project_id="BEAt-DKD-WP4-Leeds",
        subject_id="Leeds_volunteer_repeatability_study",
        attr="parameters/sequence",
        value="*fl3d2",
        output_dir=path,
    )

def bari_patients():
    username, password = get_credentials()
    download_series_by_attr(
        xnat_url="https://qib.shef.ac.uk",
        username=username,
        password=password,
        project_id="BEAt-DKD-WP4-Bari",
        subject_id="Bari_Patients",
        attr="series_description",
        value=[
            "T1w_abdomen_dixon_cor_bh", 
            "T1w_abdomen_post_contrast_dixon_cor_bh"
        ],
        output_dir=path,
    )

def all():
    leeds_patients()
    leeds_volunteers()
    bari_patients()


if __name__=='__main__':
   
    leeds_patients()
    leeds_volunteers()
    bari_patients()


    # download_series_by_attr_all_subjects(
    #     xnat_url="https://qib.shef.ac.uk",
    #     username=username,
    #     password=password,
    #     project_id="BEAt-DKD-WP4-Sheffield",
    #     attr="parameters/sequence",
    #     value="*fl3d2",
    #     output_dir=path,
    # )

    # download_series_by_dicom_sequence_name(
    #     xnat_url="https://qib.shef.ac.uk",
    #     username="your_username",
    #     password="your_password",
    #     project_id="MYPROJECT",
    #     subject_id="sub-001",
    #     sequence_name="ep2d_diff_mddw_20dir",
    #     output_dir="./dicom_matches"
    # )


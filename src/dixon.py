"""
Task: Build a clean database with all pre- and post contrast Dixon scans.

dixon_1_download: Download from XNAT

dixon_1_data: Build a clean database
- standard series file organisation
- standard patient IDs
- standard sequence names and numbers
- correct fat water swap
- List best series among repetitions

dixon_3_check: perform checks on the database
- visualise fat water swaps per site
- visualise duplicates for easy selection of best
- Build summary csv with all sequences and counts
"""

import dixon_1_download
import dixon_2_data
import dixon_3_check
import kidneyvol_1_segment

if __name__=='__main__':

    dixon_2_data.exeter_patients('Baseline')
    dixon_2_data.exeter_patients('Followup')
    dixon_3_check.check_fatwater_swap('Exeter')


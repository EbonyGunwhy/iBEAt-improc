from pipelines.totseg import (
    stage_0_restore, 
    stage_1_segment, 
    stage_2_display,
    stage_4_archive,
)


def run():
    # stage_0_restore.dixons('Controls')
    # stage_1_segment.segment('Controls')
    # stage_2_display.mosaic('Controls')
    # stage_2_display.mosaic('Controls', organs=['pancreas', 'liver'])
    # stage_4_archive.autosegmentation('Controls')

    #for site in ['Bari', 'Bordeaux', 'Exeter', 'Leeds', 'Sheffield', 'Turku']:
    for site in ['Bordeaux']:
        stage_0_restore.dixons('Patients', site)
        stage_1_segment.segment('Patients', site)
        stage_2_display.mosaic('Patients', site)
        stage_2_display.mosaic('Patients', site, organs=['pancreas', 'liver'])
        stage_4_archive.autosegmentation('Patients', site)

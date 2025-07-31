from pipelines.totseg import (
    stage_0_restore, 
    stage_1_segment, 
    stage_2_display,
    stage_4_archive,
)


def run():
    # stage_0_restore.dixons('Controls')
    # stage_0_restore.segmentations('Controls')
    # stage_1_segment.segment('Controls')
    # stage_2_display.mosaic('Controls')
    # stage_2_display.mosaic('Controls', organs=['pancreas', 'liver'])
    stage_4_archive.autosegmentation('Controls')
    # stage_0_restore.dixons('Patients', 'Bari')
    # stage_1_segment.segment('Patients', 'Bari')

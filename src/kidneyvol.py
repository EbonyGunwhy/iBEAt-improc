"""
Task: Volumetry and shape analysis of kidneys
"""

import kidneyvol_1_segment
import kidneyvol_2_display

if __name__=='__main__':

   # kidneyvol_1_segment.all()
    kidneyvol_1_segment.segment_site('Sheffield', 1)
    kidneyvol_2_display.mosaic('Sheffield')

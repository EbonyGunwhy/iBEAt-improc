"""
Task: Volumetry and shape analysis of kidneys
"""

import kidneyvol_0_restore
import kidneyvol_1_segment
import kidneyvol_2_display
import kidneyvol_3_edit
import kidneyvol_4_display
import kidneyvol_5_measure

if __name__=='__main__':
    
   site = 'Exeter'
   kidneyvol_5_measure.measure(site)

   for site in ['Leeds', 'Bordeaux']:
      kidneyvol_0_restore.dixons(site)
      kidneyvol_0_restore.segmentations(site)
      kidneyvol_4_display.mosaic(site)
      kidneyvol_5_measure.measure(site)



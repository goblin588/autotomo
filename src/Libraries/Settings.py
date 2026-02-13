
"""
Waveplate hardware settings 

"""

from Libraries.Waveplate import Waveplate

hwp_in_oa = 54.57+45
# hwp_in_oa = 4.13+45
qwp_tom_oa = 107.58
hwp_tom_oa = 41.50
qwp_in_2_oa = 131.32
hwp_in_2_oa = 29.24

# hwp_in_stage = 6
# hwp_in_stage = 7 

hwp_in_stage = 6 

qwp_tom_stage = 9
hwp_tom_stage = 4
qwp_in_2_stage = 8
hwp_in_2_stage = 1

HWP_IN =  Waveplate(hwp_in_stage, hwp_in_oa)
QWP_TOM = Waveplate(qwp_tom_stage, qwp_tom_oa)
HWP_TOM = Waveplate(hwp_tom_stage, hwp_tom_oa)
QWP_IN_2 = Waveplate(qwp_in_2_stage, qwp_in_2_oa)
HWP_IN_2 = Waveplate(hwp_in_2_stage, hwp_in_2_oa)

COMPORT = 'COM6'

FIG_FILEPATH = '/Figures/'


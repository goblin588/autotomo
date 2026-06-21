
"""
Waveplate hardware settings

"""

import os
from pathlib import Path
from Libraries.Waveplate import Waveplate

SIM_MODE = os.environ.get('AUTOTOMO_SIM', '0') == '1'

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = PROJECT_ROOT / "data" / "Figures"

qwp_in_oa = 3
hwp_in_oa = 54.57+45
qwp_tom_oa = 107.58
hwp_tom_oa = 41.50
qwp_in_2_oa = 131.32
hwp_in_2_oa = 29.24

hwp_in_stage = 6
qwp_in_stage = 8

qwp_tom_stage = 9
hwp_tom_stage = 4
qwp_in_2_stage = 7
hwp_in_2_stage = 1

QWP_IN = Waveplate(qwp_in_stage, qwp_in_oa)
HWP_IN =  Waveplate(hwp_in_stage, hwp_in_oa)
QWP_TOM = Waveplate(qwp_tom_stage, qwp_tom_oa)
HWP_TOM = Waveplate(hwp_tom_stage, hwp_tom_oa)
QWP_IN_2 = Waveplate(qwp_in_2_stage, qwp_in_2_oa)
HWP_IN_2 = Waveplate(hwp_in_2_stage, hwp_in_2_oa)

COMPORT = 'COM6'


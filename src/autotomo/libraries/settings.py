
"""
Waveplate hardware settings
"""

import os
from pathlib import Path


class Waveplate:
    def __init__(self, id, oa=0):
        self.ID = id
        self.OA = oa

    def setOA(self, oa):
        self.OA = oa

SIM_MODE = os.environ.get('AUTOTOMO_SIM', '0') == '1'

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIG_DIR = PROJECT_ROOT / "data" / "Figures"

qwp_in_oa = 3
hwp_in_oa = 54.57 + 45  # +45: true input polarisation is V, not H (basis_angles assumes H)
qwp_tom_dump_oa = 73
hwp_tom_dump_oa = 35.5
qwp_in_2_oa = 131.32
hwp_in_2_oa = 29.24
hwp_tom_1_oa = 41.5
qwp_tom_1_oa = 107.58
hwp_out_2_oa = 13
qwp_out_2_oa = 12.5

# Interferometer plates (realise the h1/q1/h2/q2 angles in getUnitary,
# previously fixed/manual, now motorised). OA not yet characterised.
hwp_1_oa = 84.31
qwp_1_oa = 353.3
hwp_12_oa = 16.28
qwp_12_oa = 170.63


# STAGES
hwp_in_stage = 6
qwp_in_stage = 8

qwp_in_2_stage = 7
hwp_in_2_stage = 1

hwp_tom_1_stage = 4
qwp_tom_1_stage = 21  # was 9; that ID now belongs to QWP_12

hwp_out_2_stage = 14
qwp_out_2_stage = 12

qwp_tom_dump_stage = 13
hwp_tom_dump_stage = 11

hwp_1_stage = 17
qwp_1_stage = 10
hwp_12_stage = 18
qwp_12_stage = 9

QWP_IN   = Waveplate(qwp_in_stage,    qwp_in_oa)
HWP_IN   = Waveplate(hwp_in_stage,    hwp_in_oa)
QWP_TOM_DUMP = Waveplate(qwp_tom_dump_stage, qwp_tom_dump_oa)
HWP_TOM_DUMP = Waveplate(hwp_tom_dump_stage, hwp_tom_dump_oa)
QWP_IN_2 = Waveplate(qwp_in_2_stage,  qwp_in_2_oa)
HWP_IN_2 = Waveplate(hwp_in_2_stage,  hwp_in_2_oa)
HWP_TOM_1 = Waveplate(hwp_tom_1_stage, hwp_tom_1_oa)
QWP_TOM_1 = Waveplate(qwp_tom_1_stage, qwp_tom_1_oa)
HWP_OUT_2 = Waveplate(hwp_out_2_stage, hwp_out_2_oa)
QWP_OUT_2 = Waveplate(qwp_out_2_stage, qwp_out_2_oa)
HWP_1  = Waveplate(hwp_1_stage,  hwp_1_oa)
QWP_1  = Waveplate(qwp_1_stage,  qwp_1_oa)
HWP_12 = Waveplate(hwp_12_stage, hwp_12_oa)
QWP_12 = Waveplate(qwp_12_stage, qwp_12_oa)

COMPORT = 'COM6'


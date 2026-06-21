"""
Functions associated with Tomography control / movement of stages
"""

from Libraries.BasisVectors import basis_angles
from Libraries.Settings import SIM_MODE
import time

if SIM_MODE:
    from Interfaces.mock import MockSMC100Connection as _Connection, MockSMC100Stage as _Stage
else:
    import Interfaces.SMC100 as _smc
    _Connection = _smc.SMC100Connection
    _Stage = _smc.SMC100Stage

#region Stage control and Reading 
def full_input_tomography(qwp, hwp, hwp_in, qwp_in, powermeter, smc_port):
    res = {}
    # Iterates over inputs H,V,A,D,R,L and performs a tomo at each
    # for basis in input_basis_angles.keys():
    for basis in ['H', 'V', 'A', 'D']:
        print("Setting New Input Basis : |{}>".format(basis))
        move_stage(hwp_in, basis_angles[basis][0], smc_port)
        move_stage(qwp_in, basis_angles[basis][1], smc_port)
        #Tomography
        res[basis] = single_tomography(qwp, hwp, powermeter, smc_port)
        
    return res

def HV_tomography(qwp, hwp, hwp_in, qwp_in, powermeter, smc_port):
    res = {}
    # Iterates over inputs H,V,A,D,R,L and performs a tomo at each
    for basis in ['H', 'V']:
        print("Setting New Input Basis : |{}>".format(basis))
        move_stage(hwp_in, basis_angles[basis][0], smc_port)
        move_stage(qwp_in, basis_angles[basis][1], smc_port)
        #Tomography
        res[basis] = single_tomography(qwp, hwp, powermeter, smc_port)
    return res

def single_tomography(qwp, hwp, powermeter, smc_port):
    res = {}
    # Iterates through mapping each output H,V,A,D,R,L to detector
    # for basis in basis_angles.keys():
    for basis in ['H', 'V', 'A', 'D', 'R','L']:
        print("Measuring Output |{}>, HWP: {}. QWP {}".format(basis, basis_angles[basis][0], basis_angles[basis][1]))
        # Set HWP 
        move_stage(hwp, basis_angles[basis][0], smc_port)
        # Set QWP 
        move_stage(qwp, basis_angles[basis][1], smc_port)
        time.sleep(0.1)
        pwr, err = powermeter.read(n=300) 
        print("Power: " + str(round(pwr*1000,2)) + " mW")
        res[basis] = (pwr,err)
    return res

def move_stage(this_stage, angle, smc_port):
    with _Connection(port=smc_port) as stages:
        stage = _Stage(stages, smcID=this_stage.ID)
        stage.enable()
        stage.move_absolute(angle + this_stage.OA)
        stage.disable()
#endregion
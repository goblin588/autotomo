"""
Functions for normalisation/calculating unitaries

"""
import Libraries.OpticsLib as ol
import numpy as np
from Libraries.OpticsLib import PBS, PBS_dag

# devimals to rouind to 
ROUND_TO = 8

# Function to normalize pairs of measurements
def normalise_pair(val1, val2):
    total = val1 + val2
    if total == 0: return 0.5, 0.5
    return val1 / total, val2 / total

def normalise_err(meas1, meas2, norm1, norm2):
    # Takes two arrays of form (pwr, err) and accoridng normalised val
    err1 = (meas1[1]/meas1[0])*norm1
    err2 = (meas2[1]/meas2[0])*norm2
    return err1, err2


def normalise_full_tomo_data(res):
    """
    Normalises dict of res data which looks like 
    {
    "H": {H:000, "V":000...}
    "V": ..
     :
    }
    """
    normalized = {}
    for input_state in res.keys():
        normalized[input_state] = {}
        for k1, k2 in [("H", "V"), ("A", "D"), ("R", "L")]:
            normalized[input_state][k1] = [0, 0]
            normalized[input_state][k2] = [0, 0]

            normalized[input_state][k1][0], normalized[input_state][k2][0] =  normalise_pair(res[input_state][k1][0], res[input_state][k2][0])
            normalized[input_state][k1][1], normalized[input_state][k2][1] = normalise_err(res[input_state][k1], res[input_state][k2], normalized[input_state][k1][0], normalized[input_state][k2][0])
    return normalized

def normalise_measurements(measurements):
    normalized = {}
    
    for k1, k2 in [("H", "V"), ("A", "D"), ("R", "L")]:
        normalized[k1] = [0, 0]
        normalized[k2] = [0, 0]
        
        normalized[k1][0], normalized[k2][0] = normalise_pair(measurements[k1][0], measurements[k2][0])
        normalized[k1][1], normalized[k2][1] = normalise_err(measurements[k1], measurements[k2], normalized[k1][0], normalized[k2][0])
    return normalized

def UnitaryToProb(U, measurementBasis, input):
    """
    Converts unitary into probability distribution.
    Returns plain floats, not np.matrix objects.
    """
    res_prob_mat = {}
    epsilon = 1e-12

    for k1, k2 in [("H", "V"), ("A", "D"), ("R", "L")]:
        # np.matrix inner products return (1,1) matrices — squeeze to scalar
        def inner_prod_sq(bra, ket):
            val = np.conjugate(np.transpose(bra)) @ ket
            return float(np.squeeze(np.asarray(np.square(np.abs(val)))))

        p1 = inner_prod_sq(measurementBasis[k1], U @ input)
        p2 = inner_prod_sq(measurementBasis[k2], U @ input)
        denom = p1 + p2 + epsilon

        res_prob_mat[k1] = p1 / denom
        res_prob_mat[k2] = p2 / denom

    return res_prob_mat

    
def getUnitary(qf2=0,hf2=0,qf1=0,hf1=0, m3=0,m2=0,h2=0,q2=0,m1=0,h1=0,q1=0,qin2=0,hin2=0):
    """
    Returns 4x4 Unitary Matrix.
    Input: input angles: will default to 0 if not explicitly set.

    """
    QWPf2 = ol.QWP_p2(qf2)

    HWPf2 = ol.HWP_p2(hf2)

    QWPf1= ol.QWP_p1(qf1)

    HWPf1 = ol.HWP_p1(hf1)

    HWP2 = ol.HWP_p2(h2)

    QWP2 = ol.QWP_p2(q2)

    HWP1 = ol.HWP_p1(h1)

    QWP1 = ol.QWP_p1(q1)
    
    QWPin2= ol.QWP_p2(qin2)

    HWPin2 = ol.HWP_p2(hin2)

    M3 = ol.Mirror4(m3, m1)
       
    M2 = ol.Mirror4(m2, m2)
    
    M1 = ol.Mirror4(m1,m3)

    # U = HWPf2@QWPf12@PBS_dag@M3@M2@M1@HWP12@QWP12@HWP1@QWP1@PBS@HWPin2@M0
    U = HWPf2@QWPf2@HWPf1@QWPf1@PBS_dag@M3@M2@M1@HWP2@QWP2@HWP1@QWP1@PBS@HWPin2@QWPin2
    return U



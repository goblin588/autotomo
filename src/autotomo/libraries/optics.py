"""
Jones-calculus matrices for the two-path polarisation interferometer.

Basis convention (the one piece of implicit knowledge everything else in
this codebase relies on): every 4-vector/4x4 matrix here is written in the
basis [H_path1, V_path1, H_path2, V_path2] — i.e. two polarisation
components (H, V) per spatial path, path 1 first. A waveplate that
physically sits on path 1 only acts on the top-left 2x2 quadrant and is the
identity on the bottom-right quadrant (path 2), and vice versa for a
path-2 waveplate — see HWP_p1/HWP_p2 below for the embedding this implies.
`PBS` swaps the V components of the two paths (H1/H2 each pass straight
through their own path; V1<->V2 couple across, with a factor of 1j) — the
physical behaviour of a polarising beamsplitter combining the two paths —
which is why its matrix isn't block-diagonal like the per-path waveplates.
"""

import numpy as np

ROUND_TO = 8

## Maths ##

def overlap(psi, basis):
    """
    Checks the overlap of psi on the basis state 'basis'
    """
    return np.square(np.abs(np.transpose(np.conjugate(psi))@basis))


## 2X2 Components ##
def HWP(theta):
    theta = np.deg2rad(theta)
    return (-1j)*np.array([[np.round(np.cos(2*theta),ROUND_TO),np.round(np.sin(2*theta),ROUND_TO)],
                           [np.round(np.sin(2*theta),ROUND_TO),np.round(-1*np.cos(2*theta),ROUND_TO)]])

def QWP(theta):
    theta = np.deg2rad(theta)
    return (1/np.sqrt(2))*np.array([[np.round(1-(1j*np.cos(2*theta)),ROUND_TO),np.round(-1j*np.sin(2*theta),ROUND_TO)],
                                    [np.round(-1j*np.sin(2*theta),ROUND_TO),np.round(1+1j*np.cos(2*theta),ROUND_TO)]])

## 4X4 Components##

def Mirror4(phi, phi2):
    # ASSUMING PHI RELATIVE PHASE SHIFT IN RADIANS
    m = np.array([[1,0,0,0],
        [0,np.exp(1j*phi),0,0],
        [0,0,1,0],
        [0,0,0,np.exp(1j*phi2)]])
    return m 

def HWP_p1(theta):
    theta = np.deg2rad(theta)
    return (-1j)*np.array([[np.round(np.cos(2*theta),ROUND_TO),np.round(np.sin(2*theta),ROUND_TO),0,0],[np.round(np.sin(2*theta),ROUND_TO),np.round(-1*np.cos(2*theta),ROUND_TO),0,0],
                           [0,0,1j,0],[0,0,0,1j]])

def HWP_p2(theta):
    theta = np.deg2rad(theta)
    return (-1j)*np.array([[1j,0,0,0],[0,1j,0,0],
                            [0,0,np.round(np.cos(2*theta),ROUND_TO),np.round(np.sin(2*theta),ROUND_TO)],[0,0,np.round(np.sin(2*theta),ROUND_TO),np.round(-1*np.cos(2*theta),ROUND_TO)]])

def QWP_p1(theta):
    theta = np.deg2rad(theta)
    return (1/np.sqrt(2))*np.array([[np.round(1-(1j*np.cos(2*theta)),ROUND_TO),np.round(-1j*np.sin(2*theta),ROUND_TO),0,0],[np.round(-1j*np.sin(2*theta),ROUND_TO),np.round(1+1j*np.cos(2*theta),ROUND_TO),0,0],
                                    [0,0,np.sqrt(2),0],[0,0,0,np.sqrt(2)]])

def QWP_p2(theta):    
    theta = np.deg2rad(theta)
    return (1/np.sqrt(2))*np.array([[np.sqrt(2),0,0,0],[0,np.sqrt(2),0,0],
                                      [0,0,np.round(1-(1j*np.cos(2*theta)),ROUND_TO),np.round(-1j*np.sin(2*theta),ROUND_TO)],[0,0,np.round(-1j*np.sin(2*theta),ROUND_TO),np.round(1+(1j*np.cos(2*theta)),ROUND_TO)]])

PBS = np.array([[1,0,0,0],
            [0,0,0,1j],
            [0,0,1,0],
            [0,1j,0,0]])

PBS_dag = np.conjugate(np.transpose(PBS))
    

import numpy as np

# 4x1 Vectors

H = np.transpose(np.matrix([0,0,1,0]))
V = np.transpose(np.matrix([0, 0, 0, 1]))
A = (1/np.sqrt(2))*(H-V)
D = (1/np.sqrt(2))*(H+V)
R = (1/np.sqrt(2))*(H-(1j*V))
L = (1/np.sqrt(2))*(H+(1j*V)) 

basis_vectors = {
    "H": H,
    "V": V,
    "A": A,
    "D": D,
    "R": R,
    "L": L
}

# 2x1 Vectors 

H_2 = np.transpose(np.matrix([1,0]))
V_2 = np.transpose(np.matrix([0,1]))
A_2 = (1/np.sqrt(2))*(H_2-V_2)
D_2 = (1/np.sqrt(2))*(H_2+V_2)
R_2 = (1/np.sqrt(2))*(H_2-(1j*V_2))
L_2 = (1/np.sqrt(2))*(H_2+(1j*V_2)) 

basis_vectors_2 = {
    "H": H_2,
    "V": V_2,
    "A": A_2,
    "D": D_2,
    "R": R_2,
    "L": L_2
}

# For projection in tomography
# Angles [HWP, QWP] 
basis_angles = {
    "H": [0,0],
    "V": [45,90],
    "A": [-22.5,45],
    "D": [22.5,45],
    "R": [22.5,0],
    "L": [-22.5,0],
    "s0_3": [32.88, 98.72],
    "s0_4": [278.74, 168.59], 
    "s0_5": [14.33, 76.94], 
    "s0_6": [10.99, 61.65]
}

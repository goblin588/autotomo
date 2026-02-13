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
    "H": H,
    "V": V,
    "A": A,
    "D": D,
    "R": R,
    "L": L
}

# For projection in tomography
# Angles [HWP, QWP] 
basis_angles = {
    "H": [0,0],
    "V": [45,90],
    "A": [-22.5,45],
    "D": [22.5,45],
    "R": [22.5,0],
    "L": [-22.5,0]
}

input_basis_angles = {
    "H": [0],
    "V": [45],
    "A": [-22.5],
    "D": [22.5]
}
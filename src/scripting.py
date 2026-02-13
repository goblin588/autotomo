#%% FINDING WP ANGS FOR INPUT OUTPUT
import Libraries.OpticsLib as ol
from Libraries.BasisVectors import A_2, H_2, D_2, V_2, R_2, L_2
import numpy as np


def find_angles(input, output):
    ang = [-45, -22.5, 0, 22.5, 45]
    res = []
    for t1  in ang:
        for t2 in ang:
            c = ol.overlap(ol.HWP(t2)@ol.QWP(t1)@input, output)
            if np.isclose(c, 1.0):
                res.append(['QWP: {}'.format(t1), 'HWP: {}'.format(t2), "overlap: {}".format(c)])
    return res

print("H in: {}".format(find_angles(H_2, V_2)))
print("D in: {}".format(find_angles(D_2, V_2)))

#%% PROCESSING MULTI RUN DATA
import Libraries.DataProcessingLib as dpl
import Libraries.CharPlotLib as cpl

data = dpl.load_csv_data('/run/user/1000/gvfs/smb-share:server=research.storage.griffith.edu.au,share=researchstorage,user=staff%5Cs2997062/CQD-PRYDE-GROUP/CQD-PRYDE-SHARE/Projects & Experiments/Extreme Dimensionality Advantage -Brendan/Goblin/Python/src/Figures/Figures_2025-08-28/Full_Figures_2025-08-28/2025-08-28__17-56/yep2_DATA.csv')
print(data)
# avg_data = dpl.average_measurements(data['raw_data'])
avg_data = data['raw_data'][0]
print(avg_data)

Angles = {'hf2': 55.57, 'qf2': 14.87, 'h1': 175.09, 'q1': 285.9, 'h12': 43.43, 'q12': 11.05, 'hin2': 0, 'qin2': 0, 'm3': 3.74, 'm2': 3.77, 'm1': 3.16, 'm0': 0, 'title': 'U'}
cpl.plot_characterisation(avg_data, 'Avg U data n=15', angles=Angles )



#%% FIDELITY 
import Libraries.CharModellingLib as cml

angles = {'hf2': 55.57, 
         'qf2': 14.87,
         'h1': 175.09, 
         'q1': 285.90,
         'h12': 43.43,
         'q12': 11.05,
         'hin2': 0,
         'qin2': 0, 
         'm3': 3.74,
         'm2': 3.77,
         'm1': 3.16,
         'm0': 0,
         'title': 'U'}  

searchMatrix = cml.getUnitary(q1=angles['q1'], h1=angles['h1'], q12=angles['q12'], 
                                    h12=angles['h12'], qf12=angles['qf2'], hf2=angles['hf2'], 
                                    qin2=angles['qin2'], hin2=angles['hin2'],  m0=angles['m0'], 
                                    m1=angles['m1'], m2=angles['m2'], m3=angles['m3'])

exp_data = data['norm_data'][0]
print(f'expdata: {exp_data}')
print(f'searchdata: {searchMatrix}')

#%% CHECKING WP OUTPUTS
import Libraries.OpticsLib as ol
from Libraries.BasisVectors import H_2, D_2, V_2, R_2

x = lambda a: ol.HWP(a[0])@ol.QWP(a[1])

print(ol.overlap(x([-22.5,-45])@D_2, V_2))

#%%
import Libraries.OpticsLib as ol
from Libraries.BasisVectors import H_2, D_2, V_2, R_2
import numpy as np

out = ol.QWP(45)@H_2
print(ol.overlap(out, L_2))

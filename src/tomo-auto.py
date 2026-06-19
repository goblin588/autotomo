"""
This file performs an automated characterisation of a single output in the dimensionality advantage experiment

This characterisation requires connection to the following:
    Thorlabs PowerMeter
    3 smc100 stages - 1 input, 2 tomo output  
"""
import Interfaces.PM100USB as pml
import Libraries.TomoLibrary as tl
import Libraries.CharModellingLib as cml
from Libraries.BasisVectors import basis_angles
from Libraries.Settings import HWP_IN, QWP_IN, QWP_TOM, HWP_TOM, HWP_IN_2, QWP_IN_2, COMPORT
from Libraries.AngMenu import angle_menu
from Libraries.NotificationService.main import send_email
import Libraries.CharPlotLib as cpl
import winsound
import datetime

# Settings 
frequency = 2200
duration = 1000  

# Do you want email notifications
email_notification = False
email_receiver = 'brendanwallis01@gmail.com'
notif_subject = 'Tomo Measurement Completed'


# def tomo_measurement(input_states, measurement_states, powermeter, qwp = QWP_TOM, hwp = HWP_TOM, hwp_in = HWP_IN, smc_port = COMPORT):
#     res = {}
#     for input_ in input_states:
#         if input_ in input_basis_angles.keys()
#             print("Setting New Input Basis : |{}>".format(basis))
#             move_stage(hwp_in, input_basis_angles[basis][0], smc_port)
#             res[basis] = tl.single_tomography(qwp, hwp, powermeter, smc_port)
#         else:
#             print('Could not find basis \'{input_}\' in dict')     

#         winsound.Beep(frequency, duration)
#         # cpl.plot_single(res, graph_title=angles['title'], angles=angles)
#         cpl.plot_characterisation(res, graph_title=f'{angles['title']}', plot_type='Single', angles=angles, show_plot=True)
#     return res


def set_stages(basis_in, basis_out):
    tl.move_stage(HWP_IN, basis_angles[basis_in.upper()][0], COMPORT)
    tl.move_stage(QWP_IN, basis_angles[basis_in.upper()][1], COMPORT)
    tl.move_stage(HWP_IN_2, basis_angles[basis_out.upper()][0], COMPORT)
    tl.move_stage(QWP_IN_2, basis_angles[basis_out.upper()][1], COMPORT)

def polarisation_tuner():
    this_basis = 'H'
    tok = True
    while(tok):
        print("Press enter to swap basis or type stop to exit, or type 'char' to characterise input phase")
        user_input = input()
        if user_input.lower() == 'stop':
            tok = False
        elif user_input.upper() in basis_angles.keys():
            set_stages(user_input, user_input)
            print("Measuring {} basis", user_input.upper())          
        else:
            # Swap basis
            if this_basis == 'D':
                this_basis = 'H'
                set_stages('H','V')
                print("Measuring H in V OUT")
            else:
                this_basis = 'D'
                set_stages('D','A')
                print("Measuring D in A OUT")
        print("READY")
        winsound.Beep(frequency, duration)

def single_tomo(basis):
    print("Performing Tomography for single Input Basis : |{}>".format(basis))
    tl.move_stage(HWP_IN, basis_angles[basis][0], COMPORT)
    res = {}
    with pml.PM100USB(wavelength=1550, verbose=True) as pm:
        res[basis] = tl.single_tomography(qwp = QWP_TOM, hwp = HWP_TOM, powermeter = pm, smc_port = COMPORT)
    winsound.Beep(frequency, duration)

    # cpl.plot_single(res, graph_title=angles['title'], angles=angles)
    cpl.plot_characterisation(res, graph_title=f'{angles['title']}', plot_type='Single', angles=angles, show_plot=True)

def full_tomo():
    print("Performing tomography for all input states")
    with pml.PM100USB(wavelength=1550, verbose=True) as pm:
        res = tl.full_input_tomography(QWP_TOM, HWP_TOM, HWP_IN, pm, COMPORT)
    winsound.Beep(frequency, duration)

    cpl.plot_characterisation(res, graph_title=f'{angles['title']}', angles=angles,plot_type='Full', show_plot=False)

def hv_tomo():
    print("Performing tomography for H and V input states")
    with pml.PM100USB(wavelength=1550, verbose=True) as pm:
        res = tl.HV_tomography(QWP_TOM, HWP_TOM, HWP_IN, pm, COMPORT)
    cpl.plot_characterisation(res, graph_title=f'{angles['title']}', angles=angles, plot_type='HV', show_plot=True)

def multi_run():
    # Collect n measurements
    n = int(input("Collect for how many measurements?: "))
    res_OUT = {}
    with pml.PM100USB(wavelength=1550, verbose=True) as pm:
        try:
            for i in range(n):
                print(f"Now performing measurement: {i}...")                
                res_OUT[i] = tl.full_input_tomography(QWP_TOM, HWP_TOM, HWP_IN, pm, COMPORT)
        except:
            print("Failed")

    winsound.Beep(frequency, duration)

    # make each plot and save to file 
    for iter in res_OUT: 
        cpl.plot_characterisation(res_OUT[iter], graph_title=angles['title'], angles=angles, plot_type='{n}_Multi', save_data=False, save_plot=False, show_plot=False)
    # write all data to a single file 
    
    norm_data = {}
    for n in res_OUT.keys():
        norm_data[n] = cml.normalise_full_tomo_data(res_OUT[n])
    
    filepath = datetime.datetime.now().strftime("Figures/Figures_%Y-%m-%d/%Y-%m-%d__%H-%M/")
    filepath = filepath + f"{angles['title']}_ITERATIONS"
    cpl.writeData2File(filename=filepath, data=res_OUT, normalised_data=norm_data, angles=angles, plot_type='Multi')

def prepare_s0_state(N):
    tl.move_stage(HWP_IN, basis_angles['s0_{N}'][0], COMPORT)
    tl.move_stage(QWP_IN, basis_angles['s0_{N}'][1], COMPORT)

if __name__ == "__main__":
    print("Automated Tomography Characterisation")

    # Get user to choose interal WP angles
    angles = angle_menu()

    run = True
    while run:
        # Check what input to perform tomography on
        basis = input("For what input state should tomography be performed? 'f' for all basis, 'm' for multi-run or 't' for quick tuning polarisation\nEnter: ").upper()

        # Single Input Tomography
        if basis in ['H','V','A','D','R','L']:
            single_tomo(basis)
            if email_notification:
                notif_subject += f': Single Tomo |{basis}>'
            run = False

        # Tomography for H V A D in
        elif basis == 'F':
            full_tomo()
            if email_notification:
                notif_subject += f': Full Tomo>'
            run = False

        # Tomography for H and V in
        elif basis == 'HV':
            hv_tomo()
            run = False
            
        elif basis == 'M':
            multi_run()
            email_notification = True
            if email_notification:
                notif_subject += f': Multi-Run Full Tomo'
            run = False

        elif basis == 'T':
            polarisation_tuner()
            run = False
        elif basis == 'S':
            prepare_s0_state(4)
        else: 
            print("Input basis must be one of the following: ", end="")
            for key in ['H', 'V', 'A', 'D']:
                print("'" + key + "', ", end="")
            print("\nEnter your selection or Ctrl D to cancel:")

    if email_notification:
        send_email(email_receiver, notif_subject)
    

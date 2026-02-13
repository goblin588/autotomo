#%%
from Libraries.BasisVectors import basis_angles, input_basis_angles
import Libraries.TomoLibrary as tl
from Libraries.Settings import HWP_IN, QWP_TOM, HWP_TOM, COMPORT, HWP_IN_2, QWP_IN_2
import winsound

frequency = 4400
duration = 800  # Set duration in milliseconds

hwp_in = HWP_IN
hwp_out = HWP_TOM
qwp_out = QWP_TOM

if __name__ == "__main__":
    print("Input State: ", end="")
    user_input = input().upper()
    if input_basis_angles.keys().__contains__(user_input):
        # Set input state
        print("Setting New Input Basis : |{}>".format(user_input))
        # Set input to correct basis
        tl.move_stage(hwp_in, input_basis_angles[user_input][0], COMPORT)
    print("\n")
    print("Measure State: ", end="")

    user_input = input().upper()
    if user_input.lower().strip() == 'set':
        print(f' Which plates to set, in or out? (type i or o) ')
        user_input = input().upper()
        if user_input.lower().strip() == 'i':
            input_angle = float(input("Set QWP angle: "))
            tl.move_stage(QWP_IN_2, input_angle, COMPORT)

            input_angle = float(input("Set HWP angle: "))
            tl.move_stage(HWP_IN_2, input_angle, COMPORT)
        if user_input.lower().strip() == 'o':
            input_angle = float(input("Set QWP angle: "))
            tl.move_stage(QWP_TOM, input_angle, COMPORT)

            input_angle = float(input("Set HWP angle: "))
            tl.move_stage(HWP_TOM, input_angle, COMPORT)
    
    elif basis_angles.keys().__contains__(user_input):
        # Set input state
        print("Setting New Measurement Basis : |{}>".format(user_input))
        # Set input to correct basis
        tl.move_stage(hwp_out, basis_angles[user_input][0], COMPORT)
        tl.move_stage(qwp_out, basis_angles[user_input][1], COMPORT)
        print("READY")
        winsound.Beep(frequency, duration)
    
    else:
        print("Invalid input state. Please enter a valid basis state.")

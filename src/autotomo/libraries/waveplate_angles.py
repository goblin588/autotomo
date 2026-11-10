import numpy as np


def _reduce_angles(angles: dict) -> dict:
    """Reduce HWP angles mod 90 and QWP angles mod 180; leave mirrors (m*) untouched."""
    reduced = {}
    for key, value in angles.items():
        if key.startswith("h"):
            reduced[key] = value % 90
        elif key.startswith("q"):
            reduced[key] = value % 180
        else:
            reduced[key] = value
    return reduced


U_3_angles = _reduce_angles({
    "h1": np.rad2deg(1.57158),
    "q1": np.rad2deg(0.0017101),
    "h2": np.rad2deg(3.99667),
    "q2": np.rad2deg(1.92368),
    "hin2": np.rad2deg(1.58668),
    "qin2": np.rad2deg(4.79562),
    "hf1": np.rad2deg(4.31667),
    "qf1": np.rad2deg(4.55094),
    "hf2": np.rad2deg(5.83508),
    "qf2": np.rad2deg(1.38684),
    "m1": 3.16,
    "m2": 3.77,
    "m3": 3.74,
})


U_4_angles = _reduce_angles({
    "h1": np.rad2deg(3.144),
    "q1": np.rad2deg(0.0),
    "h2": np.rad2deg(0.845031),
    "q2": np.rad2deg(2.74251),
    "hin2": np.rad2deg(0.710524),
    "qin2": np.rad2deg(0.0),
    "hf1": np.rad2deg(2.54209),
    "qf1": np.rad2deg(4.49778),
    "hf2": np.rad2deg(5.83761),
    "qf2": np.rad2deg(3.40202),
    "m1": 3.16,
    "m2": 3.77,
    "m3": 3.74
})

U_5_angles = _reduce_angles({
    "h1": np.rad2deg(1.5707),
    "q1": np.rad2deg(1.57092),
    "h2": np.rad2deg(2.48831),
    "q2": np.rad2deg(4.44748),
    "hin2": np.rad2deg(2.751),
    "qin2": np.rad2deg(1.2807),
    "hf1": np.rad2deg(4.1716),
    "qf1": np.rad2deg(2.91341),
    "hf2": np.rad2deg(2.83674),
    "qf2": np.rad2deg(4.93841),
    "m1": 3.16,
    "m2": 3.77,
    "m3": 3.74,
})

U_6_angles = _reduce_angles({
    "h1": np.rad2deg(1.57076),
    "q1": np.rad2deg(4.71234),
    "h2": np.rad2deg(5.99134),
    "q2": np.rad2deg(3.60292),
    "hin2": np.rad2deg(3.1633),
    "qin2": np.rad2deg(2.21049),
    "hf1": np.rad2deg(4.61802),
    "qf1": np.rad2deg(2.06573),
    "hf2": np.rad2deg(5.65754),
    "qf2": np.rad2deg(5.72802),
    "m1": 3.16,
    "m2": 3.77,
    "m3": 3.74
})

unitaries_angles = {
    '3': U_3_angles,
    '4': U_4_angles, 
    '5': U_5_angles,
    '6': U_6_angles
}
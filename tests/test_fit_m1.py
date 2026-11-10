"""compute_fit/fit_m1 correctness checks: pure math, no hardware.

fit_m1 frees up a single interferometer mirror phase (m1, radians, periodic
over [0, 2*pi)) and searches for the value that best matches theory to
measured data, holding every other angle fixed. These tests build synthetic
"measured" data directly from a known m1 via the real getUnitary/UnitaryToProb
math (zero noise) and confirm fit_m1 recovers it.
"""
import numpy as np

import autotomo.libraries.plotting as cpl
from autotomo.libraries.tomography import HVAD_BASES
from autotomo.libraries.waveplate_angles import U_3_angles, U_4_angles


def _synthetic_data(angles: dict, true_m1: float, path: int = 2, bases=HVAD_BASES) -> dict:
    """Exact theory probabilities (as if measured with zero noise) for the
    given angles with m1 overridden to true_m1."""
    U = cpl._unitary_from_angles({**angles, 'm1': true_m1}, path=path)
    data = {}
    for basis in bases:
        theory = cpl.UnitaryToProb(U, cpl.input_state_vector(basis), path=path)
        # Tiny nonzero floor avoids a divide-by-zero in normalise_err for any
        # exactly-zero conjugate-pair component.
        data[basis] = {k: (p + 1e-9, (p + 1e-9) * 1e-6) for k, p in theory.items()}
    return data


def _angle_diff(a: float, b: float) -> float:
    """Smallest difference between two angles (radians), wraparound-safe."""
    d = abs(a - b) % (2 * np.pi)
    return min(d, 2 * np.pi - d)


def test_fit_m1_recovers_known_single_unitary():
    true_m1 = 1.2345
    wrong_angles = {**U_3_angles, 'm1': 0.0}
    data = _synthetic_data(U_3_angles, true_m1)

    best_m1, best_fit = cpl.fit_m1([(data, wrong_angles)])

    assert _angle_diff(best_m1, true_m1) < 1e-2
    assert best_fit < 1e-4


def test_fit_m1_recovers_known_shared_across_unitaries():
    true_m1 = 4.0  # > pi, exercises the mod-2pi wraparound
    data_3 = _synthetic_data(U_3_angles, true_m1)
    data_4 = _synthetic_data(U_4_angles, true_m1)
    measurements = [
        (data_3, {**U_3_angles, 'm1': 0.0}),
        (data_4, {**U_4_angles, 'm1': 0.0}),
    ]

    best_m1, best_fit = cpl.fit_m1(measurements)

    assert _angle_diff(best_m1, true_m1) < 1e-2
    assert best_fit < 1e-4


def test_compute_fit_matches_plot_characterisation():
    """Guards compute_fit against drifting from plot_characterisation's own
    residual sum — they must stay numerically identical."""
    data = _synthetic_data(U_3_angles, 2.0)
    angles = {**U_3_angles, 'm1': 2.0, 'title': 'test'}

    expected = cpl.plot_characterisation(data, 'test', angles, save_plot=False,
                                         save_data=False, show_plot=False)
    actual = cpl.compute_fit(data, angles)

    assert np.isclose(actual, expected, atol=1e-9)

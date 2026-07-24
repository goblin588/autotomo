"""Regression check: set_stage_angles.py's out2 pair must use tomo_angles
(matching tom1 and single_tomography), not basis_angles, or R/L get swapped
between manual out2 checks and the automated tomo sweep."""
import numpy as np
from libraries.basis_vectors import basis_angles, tomo_angles
from libraries.optics import HWP, QWP
from set_stage_angles import _PAIRS

H = np.array([[1], [0]], dtype=complex)
R = (H - 1j * np.array([[0], [1]], dtype=complex)) / np.sqrt(2)
L = (H + 1j * np.array([[0], [1]], dtype=complex)) / np.sqrt(2)


def _analyzed_state(hwp_ang, qwp_ang):
    op = HWP(hwp_ang) @ QWP(qwp_ang)
    phi = np.conjugate(op).T @ H
    return phi / np.linalg.norm(phi)


def test_out2_pair_uses_tomo_angles():
    assert _PAIRS['out2'][3] is tomo_angles
    assert _PAIRS['tom1'][3] is tomo_angles


def test_tomo_angles_r_and_l_are_not_swapped():
    r_phi = _analyzed_state(*tomo_angles['R'])
    l_phi = _analyzed_state(*tomo_angles['L'])
    assert np.isclose(abs(np.vdot(R, r_phi)) ** 2, 1.0, atol=1e-6)
    assert np.isclose(abs(np.vdot(L, l_phi)) ** 2, 1.0, atol=1e-6)


def test_basis_angles_would_swap_r_and_l():
    """Documents why out2 can't use basis_angles: this is the bug."""
    r_phi = _analyzed_state(*basis_angles['R'])
    l_phi = _analyzed_state(*basis_angles['L'])
    assert np.isclose(abs(np.vdot(L, r_phi)) ** 2, 1.0, atol=1e-6)
    assert np.isclose(abs(np.vdot(R, l_phi)) ** 2, 1.0, atol=1e-6)

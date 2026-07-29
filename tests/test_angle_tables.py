"""Physics sanity checks for the angle tables and plate-order/sign
conventions across both paths, cross-checked against optics.py Jones
matrices. Confirmed physical model (see memory / CLAUDE.md history):

  input prep      (IN, and IN_2 in loop mode): HWP -> QWP, normal sign
  input analyze    (IN_2/TOM_1/OUT_2, non-loop): QWP -> HWP, normal sign
  loop analyze     (OUT_2 in loop mode):        HWP -> QWP, QWP negated

Loop mode's QWP negation applies to both ends (IN_2 prep, OUT_2 analyze)
because the loop physically reverses the beam through both plate pairs."""
import numpy as np

from libraries.basis_vectors import basis_angles, tomo_angles, loop_analyzer_angles
from libraries.optics import HWP, QWP
from polarisation_tuner import _D_TO_V_OUT, _D_TO_V_OUT_LOOP

BASES = ('H', 'V', 'A', 'D', 'R', 'L')
CONJUGATE = {'H': 'V', 'V': 'H', 'A': 'D', 'D': 'A', 'R': 'L', 'L': 'R'}
H_KET = np.array([[1.0 + 0j], [0.0]])

EXPECTED = {
    'H': np.array([1, 0]),
    'V': np.array([0, 1]),
    'A': np.array([1, -1]) / np.sqrt(2),
    'D': np.array([1, 1]) / np.sqrt(2),
    'R': np.array([1, -1j]) / np.sqrt(2),
    'L': np.array([1, 1j]) / np.sqrt(2),
}


def _prep(basis):
    """HWP-then-QWP order — used for both IN (non-loop) and IN_2 (loop),
    where loop's command negation and backwards mount cancel out to give
    the same net physical operator as the non-loop case."""
    hwp, qwp = basis_angles[basis]
    return QWP(qwp) @ HWP(hwp) @ H_KET


def _analyze_straight(hwp, qwp, state):
    """Non-loop analyzer order: QWP first, then HWP. No sign flip."""
    return HWP(hwp) @ QWP(qwp) @ state


def _analyze_loop(command_hwp, command_qwp, state):
    """Loop analyzer order: HWP first, then QWP. QWP command is negated
    relative to the physical angle (backwards-mounted), same convention
    as loop-mode IN_2 prep."""
    physical_qwp = -command_qwp
    return QWP(physical_qwp) @ HWP(command_hwp) @ state


def test_basis_angles_prep_reproduces_basis_vectors():
    for basis in BASES:
        state = _prep(basis).flatten()
        state = state / state[np.argmax(np.abs(state))]
        expected = EXPECTED[basis] / EXPECTED[basis][np.argmax(np.abs(EXPECTED[basis]))]
        assert np.allclose(state, expected, atol=1e-6)


def test_tomo_angles_gives_full_mub_pattern():
    """Non-loop analyzer role (IN_2/TOM_1/OUT_2 straight): every basis
    must read certain on itself and zero on its conjugate."""
    for basis in BASES:
        state = _prep(basis)
        self_hwp, self_qwp = tomo_angles[basis]
        conj_hwp, conj_qwp = tomo_angles[CONJUGATE[basis]]
        self_prob = abs(_analyze_straight(self_hwp, self_qwp, state)[0, 0]) ** 2
        conj_prob = abs(_analyze_straight(conj_hwp, conj_qwp, state)[0, 0]) ** 2
        assert np.isclose(self_prob, 1.0, atol=1e-6)
        assert np.isclose(conj_prob, 0.0, atol=1e-6)


def test_loop_analyzer_angles_gives_full_mub_pattern():
    """Loop analyzer role (OUT_2, beam reversed): same requirement, under
    the loop's HWP-then-QWP + negated-QWP convention."""
    for basis in BASES:
        state = _prep(basis)
        self_hwp, self_qwp = loop_analyzer_angles[basis]
        conj_hwp, conj_qwp = loop_analyzer_angles[CONJUGATE[basis]]
        self_prob = abs(_analyze_loop(self_hwp, self_qwp, state)[0, 0]) ** 2
        conj_prob = abs(_analyze_loop(conj_hwp, conj_qwp, state)[0, 0]) ** 2
        assert np.isclose(self_prob, 1.0, atol=1e-6)
        assert np.isclose(conj_prob, 0.0, atol=1e-6)


def test_non_loop_and_loop_v_rotations():
    """D->V and H->V, both paths. Loop and non-loop D->V use genuinely
    different commands for the same physical rotation (different plate
    order/sign convention) -- must not be conflated."""
    xD, xH = _prep('D'), _prep('H')

    out = _analyze_straight(*_D_TO_V_OUT, xD)
    probs = np.abs(out.flatten()) ** 2
    assert np.isclose(probs[0], 0.0, atol=1e-6) and np.isclose(probs[1], 1.0, atol=1e-6)

    out = _analyze_loop(*_D_TO_V_OUT_LOOP, xD)
    probs = np.abs(out.flatten()) ** 2
    assert np.isclose(probs[0], 0.0, atol=1e-6) and np.isclose(probs[1], 1.0, atol=1e-6)

    v_hwp, v_qwp = basis_angles['V']  # (45, 0) -- same command works both paths since QWP=0
    out = _analyze_straight(v_hwp, v_qwp, xH)
    probs = np.abs(out.flatten()) ** 2
    assert np.isclose(probs[0], 0.0, atol=1e-6) and np.isclose(probs[1], 1.0, atol=1e-6)

    out = _analyze_loop(v_hwp, v_qwp, xH)
    probs = np.abs(out.flatten()) ** 2
    assert np.isclose(probs[0], 0.0, atol=1e-6) and np.isclose(probs[1], 1.0, atol=1e-6)


def test_loop_d_to_v_differs_from_non_loop():
    """The two constants must not be conflated back into one shared value."""
    assert tuple(_D_TO_V_OUT) != tuple(_D_TO_V_OUT_LOOP)

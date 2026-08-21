"""Regression check for fibre_tomo's loop-path angle tables.

Confirmed (user, 2026-07-29): in loop mode, OUT_2 sees the beam backwards
like IN_2 does — HWP-then-QWP order (not its usual non-loop QWP-then-HWP,
tomo_angles). But unlike IN_2, OUT_2's QWP is NOT mounted backwards —
command is the physical angle directly.

Getting here took three wrong turns, worth remembering the shape of:
1. Original bug: OUT_2 reused IN_2's prep table directly for analysis.
   Wrong because analyzing (basis->H) is the inverse of preparing
   (H->basis), not the same formula — they only coincided for H/V.
2. Assumed OUT_2 keeps its default QWP-then-HWP order in loop mode, based
   on D->V reproducing correctly under that order with the *shared*
   _D_TO_V_OUT constant — that was actually testing the non-loop code
   path's constant, not a loop-mode fact.
3. Assumed OUT_2's QWP is ALSO backwards-mounted (negated), by analogy
   with IN_2. H/V/A/D all have QWP=0 for OUT_2 in loop mode, so this
   never actually got tested until R/L (nonzero QWP) exposed it as wrong
   — command is the physical angle as-is, no negation."""
import numpy as np

from libraries.basis_vectors import basis_angles, loop_analyzer_angles
from libraries.optics import HWP, QWP
from tomo_auto import fibre_tomo

BASES = ('H', 'V', 'A', 'D', 'R', 'L')
H_KET = np.array([[1.0 + 0j], [0.0]])


def _prep_loop_table():
    # Mirrors the table built inside fibre_tomo(loop=True) for IN_2.
    return {b: (h, -q) for b, (h, q) in basis_angles.items()}


def _prep(basis):
    hwp, qwp = basis_angles[basis]
    return QWP(qwp) @ HWP(hwp) @ H_KET


def _apply_loop_out2(command_hwp, command_qwp, state):
    """OUT_2 in loop mode: HWP-then-QWP order. Command is the physical
    angle directly -- OUT_2's QWP is not backwards-mounted (unlike IN_2's)."""
    return QWP(command_qwp) @ HWP(command_hwp) @ state


def test_loop_prep_table_negates_qwp_only():
    table = _prep_loop_table()
    for basis, (hwp, qwp) in basis_angles.items():
        assert table[basis][0] == hwp
        assert table[basis][1] == -qwp


def test_d_to_v_loop_rotation_matches_bench():
    """Locks in the bench-confirmed loop D->V command (2026-07-29):
    QWP command 0, not the non-loop case's -45."""
    D_TO_V_OUT_LOOP = (-22.5, 0)
    out = _apply_loop_out2(*D_TO_V_OUT_LOOP, _prep('D'))
    probs = np.abs(out.flatten()) ** 2
    assert np.isclose(probs[0], 0.0, atol=1e-6)  # H component
    assert np.isclose(probs[1], 1.0, atol=1e-6)  # V component


def test_loop_analyzer_table_reproduces_mub_pattern():
    """OUT_2's loop_analyzer_angles, applied via the confirmed loop
    order/sign convention, must map every basis to H with certainty and
    its conjugate basis to zero."""
    conjugate = {'H': 'V', 'V': 'H', 'A': 'D', 'D': 'A', 'R': 'L', 'L': 'R'}
    for basis in BASES:
        state = _prep(basis)
        hwp, qwp = loop_analyzer_angles[basis]
        prob_self = np.abs(_apply_loop_out2(hwp, qwp, state)[0, 0]) ** 2
        hwp_c, qwp_c = loop_analyzer_angles[conjugate[basis]]
        prob_conj = np.abs(_apply_loop_out2(hwp_c, qwp_c, state)[0, 0]) ** 2
        assert np.isclose(prob_self, 1.0, atol=1e-6)
        assert np.isclose(prob_conj, 0.0, atol=1e-6)


def test_fibre_tomo_loop_uses_loop_analyzer_table():
    import inspect
    src = inspect.getsource(fibre_tomo)
    assert 'analyzer_table = loop_table, tl.loop_analyzer_angles' in src, (
        "loop mode must analyze via loop_analyzer_angles, not the default "
        "tomo_angles (that's OUT_2's non-loop role)")


def test_fibre_tomo_loop_kwarg_present():
    assert 'loop' in fibre_tomo.__code__.co_varnames

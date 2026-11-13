"""Exit-bin distribution math checks: pure math, no hardware.

Covers the N-way normalisers (normalise_set/normalise_set_err),
path_occupancy_prob (total probability in one path's subspace, not a
within-pair conditional probability like UnitaryToProb), and
theory_exit_distribution (the theory curve plotted against normalised
measured exit powers for the s{j}_{N} process states).
"""
import numpy as np

import autotomo.libraries.plotting as cpl
from autotomo.libraries.basis_vectors import basis_vectors, process_state_angles
from autotomo.libraries.waveplate_angles import U_3_angles


def test_normalise_set_sums_to_one_and_preserves_ratios():
    values = {"a": 1.0, "b": 2.0, "c": 3.0}
    result = cpl.normalise_set(values)

    assert np.isclose(sum(result.values()), 1.0)
    assert np.isclose(result["b"] / result["a"], 2.0)
    assert np.isclose(result["c"] / result["a"], 3.0)


def test_normalise_set_zero_guard():
    values = {"a": 0.0, "b": 0.0, "c": 0.0}
    result = cpl.normalise_set(values)

    assert all(np.isclose(v, 1 / 3) for v in result.values())


def test_normalise_set_err_matches_manual_propagation():
    measurements = {"a": (2.0, 0.2), "b": (3.0, 0.3), "c": (5.0, 0.1)}
    normalized = cpl.normalise_set({k: v for k, (v, _) in measurements.items()})

    result = cpl.normalise_set_err(measurements, normalized)

    for k, (val, err) in measurements.items():
        expected = (err / val) * normalized[k]
        assert np.isclose(result[k], expected)


def test_path_occupancy_prob_identity_unitary():
    U = np.eye(4, dtype=complex)
    input_vec = basis_vectors["H"]  # a pure path-2 state

    assert np.isclose(cpl.path_occupancy_prob(U, input_vec, path=2), 1.0)
    assert np.isclose(cpl.path_occupancy_prob(U, input_vec, path=1), 0.0)


def test_path_occupancy_prob_conserves_total_probability():
    """U is unitary and the 4-dim space is exactly path1 (+) path2, so for
    any input, total probability must split exactly between the two path
    subspaces regardless of which path's analyzer was baked into U."""
    U = cpl._unitary_from_angles(U_3_angles, path=1)
    v = cpl.input_state_vector("s0_3")

    p1 = cpl.path_occupancy_prob(U, v, path=1)
    p2 = cpl.path_occupancy_prob(U, v, path=2)

    assert np.isclose(p1 + p2, 1.0)


def test_theory_exit_distribution_sums_to_one_and_has_n_plus_one_entries():
    dist = cpl.theory_exit_distribution(U_3_angles, "3", path=2)

    assert len(dist) == 4
    assert np.isclose(sum(dist.values()), 1.0)
    assert all(0.0 <= v <= 1.0 for v in dist.values())


def test_theory_exit_distribution_matches_manual_computation():
    """Guards theory_exit_distribution against drifting from a manual loop
    over path_occupancy_prob + normalise_set."""
    N = "3"
    path = 2
    U = cpl._unitary_from_angles(U_3_angles, path=path)
    s_keys = tuple(k for k in process_state_angles if k.endswith(f"_{N}"))
    expected_raw = {k: cpl.path_occupancy_prob(U, cpl.input_state_vector(k), path=path)
                    for k in s_keys}
    expected = cpl.normalise_set(expected_raw)

    actual = cpl.theory_exit_distribution(U_3_angles, N, path=path)

    assert actual.keys() == expected.keys()
    for k in expected:
        assert np.isclose(actual[k], expected[k])


def test_output_tomography_fit_zero_when_all_match_s0_theory():
    """Synthetic 'measured' data built exactly from s0's own theory, for
    every s{j}_3 state, should fit ~0 against the s0 reference — confirming
    the function compares every state to the SAME s0 target."""
    N = "3"
    path = 2
    U = cpl._unitary_from_angles(U_3_angles, path=path)
    s0_theory = cpl.UnitaryToProb(U, cpl.input_state_vector(f"s0_{N}"), path=path)
    s_keys = tuple(k for k in process_state_angles if k.endswith(f"_{N}"))
    data = {state: {k: (p + 1e-9, (p + 1e-9) * 1e-6) for k, p in s0_theory.items()}
            for state in s_keys}

    fits = cpl.output_tomography_fit(data, U_3_angles, N, path=path)

    assert fits.keys() == data.keys()
    assert all(f < 1e-4 for f in fits.values())


def test_output_tomography_fit_nonzero_against_per_state_theory():
    """'Measured' data built from s1's own theory (not s0's) should fit
    poorly against the fixed s0 reference — confirms the comparison target
    is always s0, not whichever state was actually measured."""
    N = "3"
    path = 2
    U = cpl._unitary_from_angles(U_3_angles, path=path)
    s1_theory = cpl.UnitaryToProb(U, cpl.input_state_vector(f"s1_{N}"), path=path)
    data = {f"s1_{N}": {k: (p + 1e-9, (p + 1e-9) * 1e-6) for k, p in s1_theory.items()}}

    fits = cpl.output_tomography_fit(data, U_3_angles, N, path=path)

    assert fits[f"s1_{N}"] > 1e-3

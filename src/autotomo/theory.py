"""
The physics model: build the system unitary from waveplate/mirror angles,
predict measurement probabilities from it, and fit the free mirror phase
m1 against already-measured data.

Pure math — numpy + autotomo.libraries.optics/basis_vectors only, no
matplotlib, no hardware, no settings import. Safe to import from any other
project with no side effects: `pip install -e /path/to/autotomo` then
`import autotomo.theory` just works, no COM port or power meter needed.
"""

import numpy as np

import autotomo.libraries.optics as ol
from autotomo.libraries.optics import PBS, PBS_dag
from autotomo.libraries.basis_vectors import (basis_vectors, basis_vectors_p1,
                                              basis_vectors_2, process_state_angles)


# ── Normalisation ─────────────────────────────────────────────────────────────

def normalise_pair(val1: float, val2: float) -> tuple[float, float]:
    total = val1 + val2
    if total == 0:
        return 0.5, 0.5
    return val1 / total, val2 / total


def normalise_err(meas1, meas2, norm1: float, norm2: float) -> tuple[float, float]:
    err1 = (meas1[1] / meas1[0]) * norm1
    err2 = (meas2[1] / meas2[0]) * norm2
    return err1, err2


def normalise_measurements(measurements: dict) -> dict:
    normalized = {}
    for k1, k2 in [("H", "V"), ("A", "D"), ("R", "L")]:
        normalized[k1] = [0, 0]
        normalized[k2] = [0, 0]
        normalized[k1][0], normalized[k2][0] = normalise_pair(measurements[k1][0], measurements[k2][0])
        normalized[k1][1], normalized[k2][1] = normalise_err(
            measurements[k1], measurements[k2], normalized[k1][0], normalized[k2][0]
        )
    return normalized


def normalise_full_tomo_data(res: dict) -> dict:
    """
    Normalise nested tomo result.
    Input:  {input_state: {output_state: (power, err)}}
    Output: {input_state: {output_state: [norm_val, norm_err]}}
    """
    normalized = {}
    for input_state in res:
        normalized[input_state] = {}
        for k1, k2 in [("H", "V"), ("A", "D"), ("R", "L")]:
            normalized[input_state][k1] = [0, 0]
            normalized[input_state][k2] = [0, 0]
            normalized[input_state][k1][0], normalized[input_state][k2][0] = normalise_pair(
                res[input_state][k1][0], res[input_state][k2][0]
            )
            normalized[input_state][k1][1], normalized[input_state][k2][1] = normalise_err(
                res[input_state][k1], res[input_state][k2],
                normalized[input_state][k1][0], normalized[input_state][k2][0],
            )
    return normalized


# ── Unitary math ──────────────────────────────────────────────────────────────

def getUnitary(qf2=0, hf2=0, qf1=0, hf1=0, m3=0, m2=0, h2=0, q2=0,
               m1=0, h1=0, q1=0, qin2=0, hin2=0, path=2) -> np.ndarray:
    """Return 4×4 unitary matrix for the current waveplate angle configuration.

    The analyzer pair on the measured `path` (f1/TOM_1 for path 1, f2/OUT_2 for
    path 2) is excluded from U — it is modeled by the basis projection in
    UnitaryToProb. The opposite path's pair stays in U at its fixed angles.
    """
    HWP2   = ol.HWP_p2(h2);   QWP2   = ol.QWP_p2(q2)
    HWP1   = ol.HWP_p1(h1);   QWP1   = ol.QWP_p1(q1)
    QWPin2 = ol.QWP_p2(qin2); HWPin2 = ol.HWP_p2(hin2)
    M3 = ol.Mirror4(m3, m1)
    M2 = ol.Mirror4(m2, m2)
    M1 = ol.Mirror4(m1, m3)
    U = PBS_dag @ M3 @ M2 @ M1 @ HWP2 @ QWP2 @ HWP1 @ QWP1 @ PBS @ HWPin2 @ QWPin2
    if path == 2:
        return ol.HWP_p1(hf1) @ ol.QWP_p1(qf1) @ U
    return ol.HWP_p2(hf2) @ ol.QWP_p2(qf2) @ U


def input_state_vector(basis: str) -> np.ndarray:
    """4-vector for a named input basis, or an s{j}_{N} process state computed
    from its prep angles: QWP(q) @ HWP(h) @ |H> (input arm is HWP-then-QWP),
    embedded in path 2 like the named basis vectors.
    """
    if basis in basis_vectors:
        return basis_vectors[basis]
    hwp, qwp = process_state_angles[basis]
    v = np.asarray(ol.QWP(qwp) @ ol.HWP(hwp) @ basis_vectors_2['H'])
    return np.vstack([np.zeros((2, 1)), v])


def UnitaryToProb(U: np.ndarray, input: np.ndarray, path: int = 2) -> dict:
    """Convert unitary to probability distribution over measurement basis pairs.

    path: which output path to project onto (1 or 2, default 2).
    """
    epsilon = 1e-12
    mb = basis_vectors if path == 2 else basis_vectors_p1
    res = {}
    output = U @ input

    def inner_prod_sq(bra, ket):
        val = np.conjugate(np.transpose(bra)) @ ket
        return float(np.squeeze(np.asarray(np.square(np.abs(val)))))

    for k1, k2 in [("H", "V"), ("A", "D"), ("R", "L")]:
        p1 = inner_prod_sq(mb[k1], output)
        p2 = inner_prod_sq(mb[k2], output)
        denom = p1 + p2 + epsilon
        res[k1] = p1 / denom
        res[k2] = p2 / denom

    return res


def _unitary_from_angles(angles: dict, path: int = 2) -> np.ndarray:
    return getUnitary(
        q1=angles['q1'],           h1=angles['h1'],
        q2=angles['q2'],           h2=angles['h2'],
        qf2=angles['qf2'],         hf2=angles['hf2'],
        qf1=angles.get('qf1', 0),  hf1=angles.get('hf1', 0),
        qin2=angles['qin2'],       hin2=angles['hin2'],
        m1=angles['m1'],           m2=angles['m2'],  m3=angles['m3'],
        path=path,
    )


def compute_fit(data: dict, angles: dict, path: int = 2, identity: bool = False) -> float:
    """Pure-math total L2 fit residual (measured vs theory, summed over all
    input bases in `data`) — the non-plotting twin of the residual sum
    plotting.plot_characterisation computes via its subplot renderer. Has
    no matplotlib calls, so it's safe to call thousands of times in an
    optimizer loop (e.g. fit_m1 below).
    """
    U = np.eye(4, dtype=complex) if identity else _unitary_from_angles(angles, path=path)
    normalized_data = normalise_full_tomo_data(data)
    labels = list(basis_vectors.keys())
    fit = 0.0
    for basis, norm_slice in normalized_data.items():
        theory = UnitaryToProb(U, input_state_vector(basis), path=path)
        measured = np.array([norm_slice[k][0] for k in labels])
        theory_vals = np.array([theory[k] for k in labels])
        fit += float(np.linalg.norm(measured - theory_vals))
    return fit


def fit_m1(measurements: list[tuple[dict, dict]], path: int = 2,
          coarse_points: int = 361, refine_iters: int = 3,
          bounds: tuple[float, float] = (0, 2 * np.pi)) -> tuple[float, float]:
    """Find the single shared m1 (interferometer mirror phase, radians,
    periodic over [0, 2*pi)) that minimises the TOTAL compute_fit residual
    summed across every (data, angles) pair in `measurements`, holding every
    other angle in each pair fixed. A 1-element list fits one measurement in
    isolation; an N-element list fits one shared m1 jointly across all N.

    m1 enters getUnitary twice (once via M1, once via M3, multiplied in
    sequence), so the fit-vs-m1 landscape can have more than one local
    minimum (first- and second-harmonic content) — a brute-force grid scan
    over `bounds` (the full period by default) avoids the local-minima trap
    a purely local optimizer (golden-section, gradient descent) could fall
    into, then a shrinking local refine sharpens the result. Pass a
    narrower `bounds` to restrict the search when the mirror phase is
    known to lie near a particular value. No scipy needed.

    Returns (best_m1, best_total_fit).
    """
    def total_fit(m1: float) -> float:
        return sum(compute_fit(data, {**angles, 'm1': m1}, path=path)
                  for data, angles in measurements)

    lo, hi = bounds
    grid = np.linspace(lo, hi, coarse_points)
    fits = np.array([total_fit(m) for m in grid])
    best_idx = int(np.argmin(fits))
    best_m1, best_fit = float(grid[best_idx]), float(fits[best_idx])

    span = (hi - lo) / coarse_points
    for _ in range(refine_iters):
        local_grid = np.clip(np.linspace(best_m1 - span, best_m1 + span, 21), lo, hi)
        local_fits = [total_fit(m) for m in local_grid]
        idx = int(np.argmin(local_fits))
        if local_fits[idx] < best_fit:
            best_fit, best_m1 = float(local_fits[idx]), float(local_grid[idx])
        span *= 0.1

    return best_m1 % (2 * np.pi), best_fit

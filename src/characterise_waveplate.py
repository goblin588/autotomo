"""
Characterise a single waveplate's optical axis by sweeping it through 360°
between crossed polarizers (H-polarizer -> waveplate -> V-polarizer -> power
meter) and fitting the period-90° null pattern common to both HWP and QWP.

Run with AUTOTOMO_SIM=1 or --sim for mock hardware.
"""
import os
import sys

if '--sim' in sys.argv:
    os.environ['AUTOTOMO_SIM'] = '1'

import numpy as np
import matplotlib.pyplot as plt

import libraries.tomography as tl
from libraries.plotting import _make_directory_name, createDir
from libraries.settings import (Waveplate, COMPORT, SIM_MODE,
                                 QWP_IN, QWP_TOM_DUMP, QWP_IN_2, QWP_TOM_1, QWP_OUT_2)

ANGLE_STEP = 2   # degrees between sweep points
N_READS = 10     # power-meter reads averaged per angle; also reused for the
                 # single reference read below (ponytail: one noisy reading
                 # rather than a dedicated higher-N constant — bump N_READS
                 # if that looks noisy in practice)

# Already-calibrated QWPs available to use as the fast/slow-axis reference.
_QWP_REFS: dict[int, Waveplate] = {
    wp.ID: wp for wp in (QWP_IN, QWP_TOM_DUMP, QWP_IN_2, QWP_TOM_1, QWP_OUT_2)
}


def _get_powermeter(wavelength=1550, verbose=True):
    if SIM_MODE:
        from interfaces.mock import MockPowerMeter
        return MockPowerMeter(wavelength=wavelength, verbose=verbose)
    import interfaces.pm100usb as pml
    return pml.PM100USB(wavelength=wavelength, verbose=verbose)


def _fit_sinusoid(angles_deg: np.ndarray, power: np.ndarray) -> tuple[float, float, float]:
    """Least-squares fit of I(theta) = I_mean + A*cos(4*theta) + B*sin(4*theta).
    Returns (I_mean, A, B)."""
    th = np.deg2rad(angles_deg)
    X = np.column_stack([np.ones_like(th), np.cos(4 * th), np.sin(4 * th)])
    (i_mean, a, b), *_ = np.linalg.lstsq(X, power, rcond=None)
    return float(i_mean), float(a), float(b)


def fit_optical_axis(angles_deg: np.ndarray, power: np.ndarray) -> float:
    """Return the optical-axis angle theta0 in [0, 90) where I is minimised
    (the crossed-polarizer null)."""
    i_mean, a, b = _fit_sinusoid(angles_deg, power)
    return float(np.degrees(np.arctan2(-b, -a)) / 4 % 90)


def fit_peak_power(angles_deg: np.ndarray, power: np.ndarray) -> float:
    """Return the fitted peak transmitted power (max of the fitted sinusoid).

    For a QWP this peak is I0/2 (sin^2(pi/4)), where I0 is the power with no
    polarization selection at all — so this peak doubles as an implicit I0
    estimate for resolve_fast_axis below, with no separate reference
    measurement needed."""
    i_mean, a, b = _fit_sinusoid(angles_deg, power)
    return i_mean + float(np.hypot(a, b))


def resolve_fast_axis(theta0: float, sweep_peak_W: float, pm) -> float | None:
    """Resolve whether theta0 is the test plate's fast or slow axis.

    Call only once the test plate has been rotated to theta0+45 deg
    (circularising the input). Prompts for an already-calibrated reference
    QWP to insert after the test plate, before the analyzer, then moves it
    to lab angle 45 deg. With the reference's fast axis there, a test QWP
    whose null axis (theta0) IS its fast axis converts the circular light
    back to pure V (full power I0 through the crossed analyzer); if theta0
    is the slow axis instead, it converts to pure H (zero power). sweep_peak_W
    (I0/2, see fit_peak_power) is the midpoint between those two outcomes, so
    it's the threshold — no separate I0 reference measurement needed.

    Returns the resolved fast-axis angle, or None if the user skips/enters
    an unrecognised reference stage.
    """
    ref_id = input(
        "  To resolve fast vs slow axis (R/L), insert an already-calibrated "
        "reference QWP after the test plate, before the analyzer.\n"
        "  Reference QWP stage ID (blank to skip): "
    ).strip()
    if not ref_id:
        return None
    try:
        ref = _QWP_REFS[int(ref_id)]
    except (ValueError, KeyError):
        print("  Unrecognised reference QWP stage ID — skipping fast/slow disambiguation.")
        return None

    tl.move_stage(ref, 45.0, COMPORT)
    input("  Reference QWP set to 45°. Press Enter once it is inserted in the beam: ")
    power, _ = pm.read(n=N_READS)
    is_fast = power > sweep_peak_W
    print(f"  Reference read: {power * 1000:.4f} mW (sweep peak was "
          f"{sweep_peak_W * 1000:.4f} mW) -> null axis is the "
          f"{'fast' if is_fast else 'slow'} axis")
    return theta0 if is_fast else theta0 + 90


def sweep(waveplate: Waveplate, pm) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rotate waveplate through 0-360 deg in ANGLE_STEP increments, reading
    power at each stop. Returns (angles_deg, power_W, power_std_W)."""
    angles = np.arange(0, 360, ANGLE_STEP, dtype=float)
    power = np.zeros_like(angles)
    err = np.zeros_like(angles)
    for i, angle in enumerate(angles):
        tl.move_stage(waveplate, angle, COMPORT)
        p, e = pm.read(n=N_READS)
        power[i] = p
        err[i] = e
        print(f"  {angle:6.1f}°  {p * 1000:8.4f} mW")
    return angles, power, err


def plot_sweep(angles, power, err, theta0, stage_id, directory_name,
               plate_type=None, fast_axis=None) -> None:
    """Plot power vs angle, mark fitted axis + its 90°-spaced repeats, save PNG."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.errorbar(angles, power * 1000, yerr=err * 1000, fmt='o-', ms=3,
                 color='tab:blue', ecolor='gray', capsize=2, label='Measured power')
    for k, rep in enumerate(theta0 + 90 * np.arange(4)):
        ax.axvline(rep, color='tab:red', linestyle='--', alpha=0.7,
                    label='Fitted axis (±90° repeats)' if k == 0 else None)
    ax.set_xlabel('Waveplate angle (deg)')
    ax.set_ylabel('Transmitted power (mW)')
    title = f'Stage {stage_id} — optical axis ≈ {theta0:.2f}° (mod 90°)'
    if plate_type:
        title += f'  [{plate_type}]'
    if fast_axis is not None:
        title += f'  fast axis ≈ {fast_axis:.2f}°'
    ax.set_title(title)
    ax.set_xlim(0, 360)
    ax.legend()
    fig.tight_layout()

    createDir(directory_name)
    fig.savefig(f"{directory_name}/stage{stage_id}_waveplate_axis_FIGURE.png")
    plt.show()


def main() -> None:
    if SIM_MODE:
        print("[SIM MODE] Running without hardware")

    print("Waveplate Optical-Axis Characterisation")
    print("Setup required: H-polarizer -> waveplate under test -> V-polarizer (crossed) -> power meter")
    stage_id = int(input("Stage ID of waveplate under test: ").strip())
    waveplate = Waveplate(stage_id, oa=0)
    plate_type = input("Is this a HWP or QWP? [h/q]: ").strip().upper()
    plate_type = 'QWP' if plate_type.startswith('Q') else 'HWP'

    fast_axis = None
    with _get_powermeter() as pm:
        print(f"Sweeping stage {stage_id} from 0° to 360° in {ANGLE_STEP}° steps "
              f"({N_READS} reads/angle)...")
        angles, power, err = sweep(waveplate, pm)

        theta0 = fit_optical_axis(angles, power)
        print(f"\nFitted optical axis: {theta0:.2f}° (mod 90°)")

        if plate_type == 'QWP':
            peak = fit_peak_power(angles, power)
            tl.move_stage(waveplate, theta0 + 45, COMPORT)
            fast_axis = resolve_fast_axis(theta0, peak, pm)
    tl.beep()

    print(f"Equivalent axes in [0, 360): "
          f"{', '.join(f'{a:.2f}°' for a in theta0 + 90 * np.arange(4))}")
    if fast_axis is not None:
        print(f"Resolved fast axis: {fast_axis:.2f}°")

    directory_name = _make_directory_name(plot_type='WaveplateCharacterisation',
                                           note=f'stage{stage_id}')
    createDir(directory_name)
    np.savetxt(f"{directory_name}/stage{stage_id}_waveplate_sweep.csv",
               np.column_stack([angles, power, err]),
               delimiter=',', header='angle_deg,power_W,power_std_W', comments='')
    print(f"Raw data saved to: {directory_name}/stage{stage_id}_waveplate_sweep.csv")

    plot_sweep(angles, power, err, theta0, stage_id, directory_name,
               plate_type=plate_type, fast_axis=fast_axis)
    print(f"Plot saved to: {directory_name}/stage{stage_id}_waveplate_axis_FIGURE.png")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted — stages disabled.")

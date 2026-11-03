"""Sanity checks for characterise_waveplate's fitting/classification logic,
using synthetic crossed-polarizer sweep data:
I(theta) = i_mean - contrast*cos(4*(theta-theta0)), contrast == i_mean for an
ideal null (peak = i_mean + contrast, trough = 0)."""
import numpy as np

from characterise_waveplate import (fit_optical_axis, fit_peak_power,
                                     classify_waveplate)


def _synthetic_sweep(theta0_deg, i_mean=1.0, contrast=0.9, step=2, noise=0.0, seed=0):
    angles = np.arange(0, 360, step, dtype=float)
    theta = np.deg2rad(angles)
    power = i_mean - contrast * np.cos(4 * (theta - np.deg2rad(theta0_deg)))
    if noise:
        rng = np.random.default_rng(seed)
        power = power + rng.normal(0, noise, power.shape)
    return angles, power


def test_fit_optical_axis_recovers_known_angle():
    for theta0 in (0.0, 15.0, 37.3, 63.0, 89.0):
        angles, power = _synthetic_sweep(theta0)
        fitted = fit_optical_axis(angles, power)
        assert min(abs(fitted - theta0), 90 - abs(fitted - theta0)) < 1e-6


def test_fit_optical_axis_robust_to_noise():
    angles, power = _synthetic_sweep(theta0_deg=42.0, noise=0.01, seed=1)
    fitted = fit_optical_axis(angles, power)
    assert min(abs(fitted - 42.0), 90 - abs(fitted - 42.0)) < 1.0


def test_fit_peak_power_recovers_known_peak():
    angles, power = _synthetic_sweep(theta0_deg=20.0, i_mean=1.0, contrast=1.0)
    assert np.isclose(fit_peak_power(angles, power), 2.0, atol=1e-6)


def test_classify_waveplate_hwp_full_contrast():
    # HWP: peak/I0 ~= 1.0 (sin^2(pi/2))
    angles, power = _synthetic_sweep(theta0_deg=10.0, i_mean=0.5, contrast=0.5)
    i0 = 1.0
    assert classify_waveplate(fit_peak_power(angles, power), i0) == 'HWP'


def test_classify_waveplate_qwp_half_contrast():
    # QWP: peak/I0 ~= 0.5 (sin^2(pi/4))
    angles, power = _synthetic_sweep(theta0_deg=10.0, i_mean=0.25, contrast=0.25)
    i0 = 1.0
    assert classify_waveplate(fit_peak_power(angles, power), i0) == 'QWP'

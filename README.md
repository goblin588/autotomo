# autotomo

![tests](https://img.shields.io/badge/tests-19%20passing-brightgreen)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![sim mode](https://img.shields.io/badge/sim%20mode-%E2%9C%93-informational)
![hardware](https://img.shields.io/badge/hardware-Newport%20SMC100%20%2B%20Thorlabs%20PM100USB-lightgrey)

Automated polarisation quantum-process-tomography lab control. Drives 14
Newport SMC100 motorised rotation stages (7 HWP/QWP waveplate pairs) and a
Thorlabs PM100USB power meter to characterise a photonic polarisation
qubit's optical unitaries against their theoretical Jones-matrix prediction.

## Where do I start

- **Running a measurement?** Start at `tomo_auto.py` — it's the main menu
  and the entry point for everything in the table below.
- **Understanding the physics?** Start at `getUnitary` in
  `src/autotomo/theory.py` — it builds the 4x4 unitary a given set of
  waveplate angles implies. The basis convention it (and every matrix in
  `optics.py`) uses is documented at the top of `optics.py` — read that
  first, it's the single most load-bearing piece of implicit knowledge in
  the codebase.
- **Adding a newly-calibrated unitary?** Start at `waveplate_angles.py` —
  add a new `U_N_angles` dict alongside `U_3`-`U_6`.
- **Importing the physics model into another project** (no hardware, no
  `AUTOTOMO_SIM` needed): `pip install -e /path/to/autotomo` then
  `import autotomo.theory` — it's pure numpy, importing it never touches
  matplotlib or the hardware layer.

## Setup

```bash
uv sync
```

## Entry points

| Script | Console script | Purpose |
|--------|-----------------|---------|
| `src/autotomo/tomo_auto.py` | `tomo-auto` | Main tomography menu (see below) |
| `src/autotomo/set_stage_angles.py` | `set-stages` | Manually move waveplate stage pairs to a named basis/angle, set a unitary's fixed plates, or check polarisation visibility |
| `src/autotomo/characterise_waveplate.py` | `characterise-waveplate` | Fit a single waveplate's optical axis / peak power |
| `src/autotomo/home_stages.py` | `home-stages` | Home every motor stage |

### `tomo_auto.py` menu options

| Choice | Does |
|--------|------|
| `H`/`V`/`A`/`D`/`R`/`L` | Single-basis tomography |
| `HV` | H + V inputs only |
| `F` | HVAD (4 input states) |
| `6` | HVADRL (all 6 input states) |
| `S` | Process-state (`s_j`) tomography |
| `FIB` | Fibre tomo — straight or loop path, theory unitary = identity |
| `M` | Multi-run — repeat a measurement N times and average |
| `T` | Interactive polarisation tuner (live-tuning tool, see note below) |
| `P` | Replot previously saved data |
| `CA` | Characterise a chosen subset of unitaries (0, 3, 4, 5, 6) back to back, no prompts in between; choose HVAD/S-states/both per run |

After any single measurement or a `CA` batch, you're offered the chance to
fit the interferometer's free mirror phase `m1` against the data you just
collected (no new hardware measurement) — see `autotomo.theory.fit_m1`.

### `set_stage_angles.py` options

Set a named pair (`in`/`in2`/`dump`/`tom1`/`out2`) or single stage to a
basis or raw angle; `u3`/`u4`/`u5`/`u6` sets a whole unitary's fixed
internal waveplates at once; `vis` runs an end-to-end polarisation
visibility check (send D, analyze D then A; send H, analyze H then V;
reports `(max-min)/(max+min)` as a percentage).

## `notebooks/m1_fit_explorer.py`

A [marimo](https://marimo.io) notebook: pick any previously recorded
`*_DATA.csv` (new or old format), see its measured-vs-theory plot, then fit
`m1` against that same data and see the improved plot — no hardware
needed. Run with:

```bash
uv run --with marimo marimo edit notebooks/m1_fit_explorer.py
```

## Project structure

```
src/autotomo/
├── __init__.py
├── theory.py              # The physics model: getUnitary, UnitaryToProb,
│                           #   compute_fit, fit_m1 — pure numpy, no matplotlib,
│                           #   no hardware. Importable standalone.
├── tomo_auto.py            # Main entry point — tomography menu
├── set_stage_angles.py     # Manually move stage pairs / set a unitary / check visibility
├── characterise_waveplate.py
├── home_stages.py
├── interfaces/
│   ├── smc100.py           # Newport SMC100 serial driver
│   ├── pm100usb.py         # Thorlabs PM100USB power meter driver
│   ├── tlpmx.py            # Thorlabs TLPMX ctypes binding (auto-generated, don't hand-edit)
│   └── mock.py             # Sim-mode stubs (stages + power meter)
└── libraries/
    ├── settings.py          # Waveplate stage IDs and optical axis offsets (COM6, machine-specific)
    ├── basis_vectors.py     # Polarisation basis state vectors and HWP/QWP angles
    ├── waveplate_angles.py  # Calibrated angle sets for each unitary (U3-U6)
    ├── optics.py            # Jones matrix definitions (HWP, QWP, PBS, mirror) + the basis convention doc
    ├── tomography.py        # Stage movement and measurement loops
    ├── plotting.py          # Bar-chart plots + saving to disk; imports theory.py for the math
    ├── data_processing.py   # Bespoke CSV re-parsing and multi-run averaging
    ├── angle_menu.py         # Interactive angle-selection CLI
    ├── polarisation_tuner.py # Interactive live-tuning tool — note: lives here as a
    │                         #   library-importable function (used by tomo_auto's `T`
    │                         #   option) but is itself a standalone CLI, not a utility module
    └── notifier.py           # ntfy.sh push notifications
```

## Sim mode

Run without hardware using mock stages and power meter:

```bash
AUTOTOMO_SIM=1 tomo-auto
# or
AUTOTOMO_SIM=1 python -m autotomo.tomo_auto
```

## Hardware

- **Motor stages:** 14x Newport SMC100 (serial, one COM port, multi-drop —
  configured via `COMPORT` and per-stage IDs/optical-axis offsets in
  `src/autotomo/libraries/settings.py`)
- **Power meter:** Thorlabs PM100USB
- **Waveplate pairs (7, 14 stages):** input (`IN`), input path 2 (`IN_2`),
  tomography dump (`TOM_DUMP`), tomography path 1 (`TOM_1`), output path 2
  (`OUT_2`) — plus two fixed interferometer-internal pairs (`_1`, `_12`)
  that realise the chosen unitary rather than a basis prep/analysis step.

## This project also exists elsewhere

`autoqstochmeasure` and `stochprocsim` (siblings under `../`) each
independently reimplement or hand-forked this project's optics model and
calibration data — see `PROJECT_REVIEW_AND_OVERHAUL_PLAN.md` for the full
writeup of the overlap and what to do about it.

## Notifications

Push notifications via [ntfy.sh](https://ntfy.sh) are sent on tomo completion. Subscribe to "goblin-lab-r9k2mq" in the ntfy app to receive them.

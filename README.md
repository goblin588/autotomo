# autotomo

Automated polarisation tomography for photonic experiments. Controls SMC100 motor stages (HWP/QWP waveplate pairs) and a Thorlabs PM100USB power meter to characterise optical unitaries.

## Setup

```bash
uv sync
```

## Entry points

| Script | Purpose |
|--------|---------|
| `python src/tomo_auto.py` | Main tomography menu — single basis, HVAD, HVADRL, multi-run, replot |
| `python src/measurement.py` | Set input waveplates to the s0 state for a given unitary |
| `python src/set_stage_angles.py` | Manually move waveplate stage pairs to a named basis or angle |

## Sim mode

Run without hardware using mock stages and power meter:

```bash
AUTOTOMO_SIM=1 python src/tomo_auto.py
# or
python src/tomo_auto.py --sim
```

## Hardware

- **Motor stages:** Newport SMC100 (serial, configured via `COMPORT` in `src/libraries/settings.py`)
- **Power meter:** Thorlabs PM100USB
- **Stages:** 4 × waveplate — `HWP_IN`, `QWP_IN` (input path), `HWP_TOM`, `QWP_TOM` (tomography path)

## Notifications

Push notifications via [ntfy.sh](https://ntfy.sh) are sent on tomo completion. Subscribe to "goblin-lab-r9k2mq" in the ntfy app to receive them.

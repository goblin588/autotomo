"""
Automated polarisation tomography characterisation.

Requires:
    Thorlabs PM100USB power meter
    SMC100 motor stages (1 input HWP/QWP pair, 1 tomography HWP/QWP pair)

Run with AUTOTOMO_SIM=1 to use mock hardware (no physical connection needed):
    AUTOTOMO_SIM=1 python tomo_auto.py
"""
import datetime
import io
import os
import sys
import threading
import time

if '--sim' in sys.argv:
    os.environ['AUTOTOMO_SIM'] = '1'

import autotomo.libraries.data_processing as dpl
import autotomo.libraries.plotting as cpl
import autotomo.libraries.tomography as tl
from autotomo.libraries.angle_menu import angle_menu
from autotomo.libraries.basis_vectors import process_state_angles
from autotomo.libraries.settings import (HWP_IN, QWP_IN, HWP_IN_2, QWP_IN_2, HWP_TOM_1, QWP_TOM_1,
                                HWP_OUT_2, QWP_OUT_2, COMPORT, SIM_MODE)
from autotomo.libraries.notifier import notify
from autotomo.libraries.polarisation_tuner import polarisation_tuner
from autotomo.libraries.waveplate_angles import unitaries_angles

ZERO_ANGLES = {k: 0 for k in
              ('q1', 'h1', 'q2', 'h2', 'qf1', 'hf1', 'qf2', 'hf2', 'qin2', 'hin2')}
ZERO_ANGLES.update(m1=3.16, m2=3.77, m3=3.74)


def _run_quiet_with_spinner(label_fn, fn, *args, **kwargs):
    """Run fn in the background with its prints swallowed, showing a
    bouncing-dots spinner in their place. label_fn() is called fresh on
    every tick, so it can report live progress. Returns fn's return value."""
    out = {}

    def target():
        try:
            out['value'] = fn(*args, **kwargs)
        except Exception as e:
            out['error'] = e

    real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    thread = threading.Thread(target=target)
    thread.start()

    frames = [*range(1, 6), *range(4, 0, -1)]
    i = 0
    try:
        while thread.is_alive():
            dots = '.' * frames[i % len(frames)]
            real_stdout.write(f'\r{label_fn()}{dots:<5}')
            real_stdout.flush()
            time.sleep(0.2)
            i += 1
    finally:
        thread.join()
        sys.stdout = real_stdout
    real_stdout.write(f'\r{label_fn()}{"":<5}\r')

    if 'error' in out:
        raise out['error']
    return out.get('value')


class _Progress:
    """Thread-safe-enough (single incrementer, GIL-protected) step counter."""

    def __init__(self, total: int):
        self.done = 0
        self.total = total

    def tick(self):
        self.done += 1

    def pct(self) -> int:
        return round(100 * self.done / self.total) if self.total else 100


def _quiet(fn, *args, **kwargs):
    """Call fn with its prints swallowed. Returns fn's return value.

    Unlike _run_quiet_with_spinner, this runs fn on the calling thread —
    use it for matplotlib work, which isn't thread-safe and must not run
    on the background thread a spinner uses."""
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        return fn(*args, **kwargs)
    finally:
        sys.stdout = real_stdout


def _tomo_stages(path: int):
    if path == 1:
        return HWP_TOM_1, QWP_TOM_1
    return HWP_OUT_2, QWP_OUT_2


def _get_powermeter(wavelength=1550, verbose=True):
    if SIM_MODE:
        from autotomo.interfaces.mock import MockPowerMeter
        return MockPowerMeter(wavelength=wavelength, verbose=verbose)
    import autotomo.interfaces.pm100usb as pml
    return pml.PM100USB(wavelength=wavelength, verbose=verbose)


def _measure_tomo(angles, path, bases, angle_table=None, on_progress=None):
    """Hardware-only: set the fixed waveplates, tomo each input basis.
    Returns the raw {input_basis: {output_state: (power, err)}} results.

    angle_table: prep-angle lookup passed to input_tomography (default
    basis_angles; pass process_state_angles for s{j}_{N} inputs).
    on_progress: called after every output-basis measurement.
    """
    print(f"Performing tomography for input states: {', '.join(bases)}")
    hwp_tom, qwp_tom = _tomo_stages(path)
    with tl.open_connection(COMPORT) as connection, _get_powermeter() as pm:
        tl.set_fixed_waveplates(angles, path, connection=connection)
        res = tl.input_tomography(qwp_tom, hwp_tom, HWP_IN, QWP_IN, pm, COMPORT,
                                  bases=bases, angle_table=angle_table, on_progress=on_progress,
                                  connection=connection)
    tl.beep()
    return res


def _offer_m1_fit(measurements, path, note, show_plot=False):
    """measurements: list of (res, angles, plot_type) sharing one m1.

    Prompts to fit a single shared m1 (interferometer mirror phase) against
    the already-measured data in `measurements` -- no new hardware
    measurement. On yes, regenerates+saves each measurement's plot under a
    '_m1fit'-suffixed plot_type, alongside (never overwriting) the original,
    and reports the before/after fit plus the shared best_m1.
    """
    if input("Would you like to fit an m1 value? [y/N]: ").strip().lower() != 'y':
        return None

    before_fits = [cpl.compute_fit(res, angles, path=path) for res, angles, _ in measurements]
    best_m1, best_total = cpl.fit_m1([(res, angles) for res, angles, _ in measurements], path=path)
    print(f"m1 fit: before={sum(before_fits):.4f}  after={best_total:.4f}  best_m1={best_m1:.4f} rad")

    for (res, angles, plot_type), before in zip(measurements, before_fits):
        fitted_angles = {**angles, 'm1': best_m1}
        new_fit = _quiet(cpl.plot_characterisation, res, graph_title=angles['title'],
                        angles=fitted_angles, plot_type=f'{plot_type}_m1fit',
                        show_plot=show_plot, path=path, note=note)
        print(f"  {plot_type}: {before:.4f} -> {new_fit:.4f}")
    return best_m1


def run_tomo(angles, path, bases, plot_type, show_plot=False, angle_table=None, note=None,
            label=None, progress=None, offer_fit=True):
    """Tomo each input basis in bases, measuring quietly behind a live
    progress spinner, then plot against theory and notify.

    label: text shown before the spinner's (%) and dots (default: plot_type).
    progress: a _Progress counter to share across several run_tomo calls,
    e.g. one shared % for a whole batch; defaults to a fresh one scoped to
    just this call (len(bases) x 6 output-basis measurements).
    offer_fit: ask (and run) an m1 fit against this measurement's data once
    it's done. characterise_all sets this False and offers its own
    batch-wide fit after the whole run instead.
    """
    if progress is None:
        progress = _Progress(len(bases) * 6)
    label = label if label is not None else plot_type
    label_fn = lambda: f"Measuring {label} ({progress.pct()}%) "

    res = _run_quiet_with_spinner(label_fn, _measure_tomo, angles, path, bases,
                                  angle_table=angle_table, on_progress=progress.tick)
    fit = _quiet(cpl.plot_characterisation, res, graph_title=angles['title'], angles=angles,
                plot_type=plot_type, show_plot=show_plot, path=path, note=note)
    print(f"{label_fn()}fit: {fit:.4f}")
    notify(f"{plot_type} tomo done — fit: {fit:.4f} — {angles['title']}",
           title=f"{plot_type} tomo complete",
           priority="high" if len(bases) > 2 else "default")

    if offer_fit:
        _offer_m1_fit([(res, angles, plot_type)], path, note, show_plot=show_plot)
    return fit, res


ALL_N = ('0', '3', '4', '5', '6')


def characterise_all(path: int = 2):
    """Run a full characterisation for a chosen subset of N=0 (zeroed internal
    angles, plain HVAD tomo) and configured unitaries 3-6 (HVAD tomo and/or
    process-state tomo of all s_j states — your choice), back to back with
    no prompts in between. All runs share one folder-name prefix."""
    choice = input(f"Which unitaries? ({','.join(ALL_N)}, Enter for all): ").strip()
    if choice:
        wanted = set(choice.replace(',', ' ').split())
        n_list = tuple(n for n in ALL_N if n in wanted)
        if not n_list:
            print(f"No valid unitaries in {choice!r}. Valid: {', '.join(ALL_N)}")
            return
    else:
        n_list = ALL_N

    mode = input("For N=3-6, characterise with HVAD inputs, S states, or both? [H/S/B]: ").strip().upper()[:1]
    if mode not in ('H', 'S', 'B'):
        mode = 'H'

    custom_title = input("Custom title to append to the folder name (blank for none): ").strip()
    note = datetime.datetime.now().strftime("MultipleUnitaryMeasurement_%Y-%m-%d__%H-%M")
    if custom_title:
        note += f"_{custom_title}"

    # N=0 has no s-states, so it's always just HVAD regardless of mode.
    # Each run carries (N, kind, bases, angle_table, plot_type).
    runs = []
    for N in n_list:
        if N == '0':
            runs.append(('0', 'HVAD', tl.HVAD_BASES, None, 'Full'))
        else:
            if mode in ('H', 'B'):
                runs.append((N, 'HVAD', tl.HVAD_BASES, None, f'Full{N}'))
            if mode in ('S', 'B'):
                s_keys = tuple(k for k in process_state_angles if k.endswith(f'_{N}'))
                runs.append((N, 'S', s_keys, process_state_angles, f'S{N}'))

    # Progress updates per input-basis x output-basis measurement (single_tomography's
    # inner loop), across the whole batch — not just once per unitary.
    progress = _Progress(sum(len(bases) * 6 for _, _, bases, _, _ in runs))

    total = len(runs)
    completed = []
    results = []  # (res, angles, plot_type) per completed run, for the post-batch m1 fit
    try:
        for N, kind, bases, angle_table, plot_type in runs:
            angles = ({**ZERO_ANGLES, 'title': 'Zeroes', 'N': '0'} if N == '0'
                      else {**unitaries_angles[N], 'title': 'U', 'N': N})
            fit, res = run_tomo(angles, path, bases, plot_type, angle_table=angle_table, note=note,
                                label=f"unitary {N} {kind}", progress=progress, offer_fit=False)
            results.append((res, angles, plot_type))
            completed.append(f'{N}({kind})')
    finally:
        # Each completed run's plot/data was already written to disk before
        # its call returned, so a Ctrl-C here only drops the *remaining*
        # runs, not the finished ones — report what made it.
        tl.beep()
        done_str = ','.join(completed) if completed else 'none'
        if len(completed) == total:
            notify(f"Characterise-all run complete ({done_str})",
                   title="Characterise all complete", priority="high")
        else:
            remaining = ','.join(f'{n}({k})' for n, k in runs if f'{n}({k})' not in completed)
            print(f"Characterise-all stopped early — done: {done_str} — not run: {remaining}")
            notify(f"Characterise-all interrupted — done: {done_str} — not run: {remaining}",
                   title="Characterise all interrupted", priority="high")

    if results:
        _offer_m1_fit(results, path, note, show_plot=False)


def _measure_fibre(bases, loop, on_progress=None):
    """Hardware-only half of fibre_tomo: one shared connection for the
    whole run instead of one per stage move."""
    if loop:
        loop_table = {b: (h, -q) for b, (h, q) in tl.basis_angles.items()}
        analyzer_qwp, analyzer_hwp, prep_hwp, prep_qwp = QWP_OUT_2, HWP_OUT_2, HWP_IN_2, QWP_IN_2
        prep_table, analyzer_table = loop_table, tl.loop_analyzer_angles
    else:
        analyzer_qwp, analyzer_hwp, prep_hwp, prep_qwp = QWP_IN_2, HWP_IN_2, HWP_IN, QWP_IN
        prep_table, analyzer_table = None, None
    print(f"Performing {'loop ' if loop else ''}fibre tomography for input states: {', '.join(bases)}")
    with tl.open_connection(COMPORT) as connection, _get_powermeter() as pm:
        res = tl.input_tomography(analyzer_qwp, analyzer_hwp, prep_hwp, prep_qwp, pm, COMPORT,
                                  bases=bases, angle_table=prep_table, analyzer_table=analyzer_table,
                                  on_progress=on_progress, connection=connection)
    tl.beep()
    return res


def fibre_tomo(bases=tl.FULL_BASES, loop=False):
    """Tomo straight through the fibre. No internal optics in between and no
    unitary to fit — it's measured beforehand — so theory is identity.

    loop=False: IN preps, IN_2 analyzes (straight path).
    loop=True:  IN_2 preps, OUT_2 analyzes (loop path). Both plate pairs
    see the beam backwards in loop mode (HWP-then-QWP, not OUT_2's usual
    non-loop QWP-then-HWP analyzer role) — confirmed (user, 2026-07-29).
    Only IN_2's QWP is mounted backwards, though; OUT_2's is not. So OUT_2
    uses basis_vectors.loop_analyzer_angles, not tomo_angles.
    """
    angles = {'title': 'Fibre (loop)' if loop else 'Fibre'}
    progress = _Progress(len(bases) * 6)
    label_fn = lambda: f"Measuring {angles['title']} ({progress.pct()}%) "

    res = _run_quiet_with_spinner(label_fn, _measure_fibre, bases, loop, on_progress=progress.tick)
    fit = _quiet(cpl.plot_characterisation, res, graph_title=angles['title'], angles=angles,
                plot_type='Fibre', show_plot=True, identity=True)
    print(f"{label_fn()}fit: {fit:.4f}")
    notify(f"Fibre tomo done — fit: {fit:.4f}",
           title="Fibre tomo complete", priority="default")


def s_tomo(angles, path):
    """Tomo the s{j}_{N} process states for the chosen unitary N."""
    N = angles.get('N', '3')
    s_keys = tuple(k for k in process_state_angles if k.endswith(f'_{N}'))
    j = input(f"Which s state for N={N}? (0-{len(s_keys) - 1}, or Enter for all): ").strip()
    if j:
        key = f's{j}_{N}'
        if key not in process_state_angles:
            print(f"No state {key}. Options: {', '.join(s_keys)}")
            return
        bases = (key,)
    else:
        bases = s_keys
    run_tomo(angles, path, bases, plot_type=f'S{N}', angle_table=process_state_angles)


def multi_run(angles, path: int = 2):
    n = int(input("Collect how many measurements?: "))
    hwp_tom, qwp_tom = _tomo_stages(path)
    res_out = {}
    progress = _Progress(n * len(tl.HVAD_BASES) * 6)
    label_fn = lambda: f"Collecting {n} runs ({progress.pct()}%) "

    def _measure_all():
        with tl.open_connection(COMPORT) as connection, _get_powermeter() as pm:
            tl.set_fixed_waveplates(angles, path, connection=connection)
            for i in range(n):
                res_out[i] = tl.input_tomography(qwp_tom, hwp_tom, HWP_IN, QWP_IN, pm, COMPORT,
                                                 bases=tl.HVAD_BASES, on_progress=progress.tick,
                                                 connection=connection)
                notify(f"Run {i + 1}/{n} done — {angles['title']}", title="Multi-run progress")
        tl.beep()

    try:
        _run_quiet_with_spinner(label_fn, _measure_all)
    except Exception as e:
        print(f"{label_fn()}failed: {e}")
        notify(f"Measurement failed at run {len(res_out)}/{n}: {e}", title="autotomo error", priority="urgent")

    print(f"{label_fn()}done ({len(res_out)}/{n} runs)")
    notify(f"All {len(res_out)} runs complete — {angles['title']}", title="Multi-run complete", priority="high")

    fits = [_quiet(cpl.plot_characterisation, res_out[i], graph_title=angles['title'], angles=angles,
                   plot_type=f'{i}_Multi', save_data=False, save_plot=False, show_plot=False, path=path)
            for i in res_out]
    print("Fits: " + ", ".join(f"{f:.4f}" for f in fits))

    norm_data = {i: cpl.normalise_full_tomo_data(res_out[i]) for i in res_out}
    filepath = datetime.datetime.now().strftime("Figures/Figures_%Y-%m-%d/%Y-%m-%d__%H-%M/")
    filepath += f"{angles['title']}_ITERATIONS"
    cpl.writeData2File(filename=filepath, data=res_out, normalised_data=norm_data, angles=angles, plot_type='Multi')


def replot(angles, path: int = 2):
    filepath = input("Path to data CSV: ").strip()
    try:
        data = dpl.load_csv_data(filepath)
        avg_data = dpl.average_measurements(data['raw_data'])
        cpl.plot_characterisation(avg_data, f"Replot — {angles['title']}", angles=angles, path=path)
    except Exception as e:
        print(f"Error loading data: {e}")


def main():
    if SIM_MODE:
        print("[SIM MODE] Running without hardware")

    print("Automated Tomography Characterisation")

    while True:
        choice = input(
            "Mode?\n"
            "  H/V/A/D/R/L  — single basis tomo\n"
            "  HV            — H + V only\n"
            "  F             — HVAD (4 input states)\n"
            "  6             — HVADRL (all 6 input states)\n"
            "  S             — s_j process state tomo\n"
            "  FIB           — fibre tomo (straight or loop path, unitary = identity)\n"
            "  M             — multi-run\n"
            "  T             — polarisation tuner\n"
            "  P             — replot saved data\n"
            "  CA            — characterise chosen unitaries (0, 3, 4, 5, 6) in sequence\n"
            "> "
        ).upper()

        if choice == 'T':
            polarisation_tuner()
            break
        if choice not in (*tl.FULL_BASES, 'HV', 'F', '6', 'S', 'FIB', 'M', 'P', 'CA'):
            print("Valid inputs: H, V, A, D, R, L, HV, F, 6, S, FIB, M, T, P, CA")
            continue

        if choice == 'FIB':
            loop = input("Loop path? [y/N]: ").strip().lower() == 'y'
            fibre_tomo(loop=loop)
            break

        if choice == 'CA':
            _p = input("Output path [1/2, default 2]: ").strip()
            characterise_all(path=1 if _p == '1' else 2)
            break

        angles = angle_menu()
        _p = input("Output path [1/2, default 2]: ").strip()
        path = 1 if _p == '1' else 2

        if choice in tl.FULL_BASES:
            run_tomo(angles, path, (choice,), 'Single', show_plot=True)
        elif choice == 'HV':
            run_tomo(angles, path, tl.HV_BASES, 'HV', show_plot=True)
        elif choice == 'F':
            run_tomo(angles, path, tl.HVAD_BASES, 'Full')
        elif choice == '6':
            run_tomo(angles, path, tl.FULL_BASES, 'Full6')
        elif choice == 'S':
            s_tomo(angles, path)
        elif choice == 'M':
            multi_run(angles, path)
        elif choice == 'P':
            replot(angles, path)
        break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted — stages disabled.")

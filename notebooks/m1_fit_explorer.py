"""
m1 fit explorer — marimo notebook.

Pick a recorded tomography/characterisation data file, see its measured-vs-
theory plot, then fit the free interferometer mirror phase m1 against that
same data and see the improved plot.

Run with (from the repo root):
    uv run --with marimo marimo edit notebooks/m1_fit_explorer.py

Works on old data too: files recorded before the h2/q2 angle keys were named
that (they used h12/q12, plus a since-dropped m0) are auto-aliased on load.
"""

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import csv
    from pathlib import Path

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np

    import libraries.plotting as cpl

    return Path, cpl, csv, mo, np, plt


@app.cell
def _(mo):
    mo.md("""
    # m1 fit explorer
    """)
    return


@app.cell
def _(Path, csv, np):
    ROOT = Path(__file__).resolve().parents[1]
    # Old data lived under figures/ and archive/Archived Figures/ before the
    # Figures/ layout settled; all three are scanned so "old data" just works.
    DATA_ROOTS = [ROOT / "Figures", ROOT / "figures", ROOT / "archive" / "Archived Figures"]

    # Angle dict keys renamed at some point (h12/q12 -> h2/q2); m0 was dropped
    # entirely (no longer a free parameter in getUnitary). Old files keep the
    # old names on disk, so alias them back on load instead of touching history.
    _ANGLE_ALIASES = {"h12": "h2", "q12": "q2"}

    def find_data_files() -> list[Path]:
        files = [f for root in DATA_ROOTS if root.exists() for f in root.rglob("*_DATA.csv")]
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

    def _safe_eval(expr: str):
        """ANGLES/RAW_DATA rows are Python dict reprs, including np.float64(...)
        calls, so ast.literal_eval can't parse them — eval with a locked-down
        namespace instead. Trusted data: these are only files this same repo
        wrote via writeData2File."""
        return eval(expr, {"__builtins__": {}, "np": np})

    def _parse_rows(path: Path) -> dict[str, str]:
        with open(path, newline="") as f:
            rows = {}
            for row in csv.reader(f, delimiter=" ", quotechar='"'):
                if row:
                    label, _, value = row[0].partition(": ")
                    rows[label] = value
            return rows

    def load_data_file(path: Path) -> dict | None:
        """Parse a *_DATA.csv file into {angles, data, plot_type}. Returns
        None for files this viewer doesn't support: multi-run saves split
        RAW_DATA into one 'RAW DATA [i]' row per run index rather than the
        single {input_basis: {...}} dict compute_fit/plot_characterisation
        expect (the multi-run averaged replot is saved separately in its own
        standard-format file, so nothing is lost by skipping these)."""
        rows = _parse_rows(path)
        if "RAW_DATA" not in rows:
            return None
        angles = _safe_eval(rows["ANGLES"])
        angles = {_ANGLE_ALIASES.get(k, k): v for k, v in angles.items()}
        return {
            "angles": angles,
            "data": _safe_eval(rows["RAW_DATA"]),
            "plot_type": rows.get("PLOT TYPE"),
        }

    return ROOT, find_data_files, load_data_file


@app.cell
def _(ROOT, find_data_files, mo):
    _files = find_data_files()
    _options = {f"{p.relative_to(ROOT)}  ({p.stat().st_mtime:.0f})": p for p in _files}
    file_picker = mo.ui.dropdown(
        options=_options,
        value=next(iter(_options), None),
        label=f"Recorded data file ({len(_files)} found)",
    )
    file_picker
    return (file_picker,)


@app.cell
def _(file_picker, load_data_file, mo):
    mo.stop(file_picker.value is None, mo.md("No data file selected, or none found."))
    record = load_data_file(file_picker.value)
    mo.stop(
        record is None,
        mo.md("This file is a multi-run split (per-index `RAW DATA [i]` rows), "
              "not a single characterisation — pick another file."),
    )
    record
    return (record,)


@app.cell
def _(mo, record):
    _is_fibre = bool(record["plot_type"] and "Fibre" in record["plot_type"])
    path_selector = mo.ui.radio(options=["2", "1"], value="2", label="Output path")
    identity_toggle = mo.ui.checkbox(
        value=_is_fibre, label="Identity unitary (direct link, e.g. Fibre data)"
    )
    mo.hstack([path_selector, identity_toggle])
    return identity_toggle, path_selector


@app.cell
def _(cpl, identity_toggle, mo, path_selector, plt, record):
    _fit = cpl.plot_characterisation(
        record["data"], record["angles"].get("title", "data"), record["angles"],
        save_plot=False, save_data=False, show_plot=False,
        path=int(path_selector.value), identity=identity_toggle.value,
    )
    original_fig = plt.gcf()
    plt.close(original_fig)
    mo.vstack([mo.md(f"**Original fit residual:** {_fit:.4f}"), original_fig])
    return


@app.cell
def _(mo):
    fit_button = mo.ui.run_button(label="Fit m1 against this data")
    fit_button
    return (fit_button,)


@app.cell
def _(fit_button, identity_toggle, mo):
    mo.stop(
        identity_toggle.value,
        mo.md("m1 is an interferometer mirror phase — fitting it doesn't apply "
              "to an identity (direct-link) dataset."),
    )
    mo.stop(not fit_button.value, mo.md("Click **Fit m1 against this data** to run the optimizer."))
    return


@app.cell
def _(cpl, fit_button, identity_toggle, mo, path_selector, plt, record):
    mo.stop(identity_toggle.value or not fit_button.value)

    _path = int(path_selector.value)
    best_m1, best_fit = cpl.fit_m1([(record["data"], record["angles"])], path=_path)
    fitted_angles = {**record["angles"], "m1": best_m1}

    cpl.plot_characterisation(
        record["data"], fitted_angles.get("title", "data"), fitted_angles,
        save_plot=False, save_data=False, show_plot=False, path=_path,
    )
    fitted_fig = plt.gcf()
    plt.close(fitted_fig)

    mo.vstack([
        mo.md(f"**Fitted m1:** {best_m1:.4f} rad &nbsp;&nbsp; **Fit residual:** {best_fit:.4f}"),
        fitted_fig,
    ])
    return


if __name__ == "__main__":
    app.run()

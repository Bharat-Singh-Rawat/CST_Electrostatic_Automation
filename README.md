# CST Electrostatic Automation — AEgIS Electrode ROM

**Python and MATLAB scripts for building a Reduced Order Surrogate model of the electrostatic potential of the AEgIS Penning Trap electrode system.**

This repository automates [CST Studio Suite](https://www.3ds.com/products/simulia/cst-studio-suite) to generate the training data for an electrostatic Reduced Order Model (ROM) of the AEgIS Penning–Malmberg trap. Each electrode is energized individually and its potential map is exported, producing a **unit-potential basis**. By linearity of the electrostatic problem, an arbitrary electrode configuration can then be reconstructed in milliseconds as a weighted superposition of these basis maps — the core idea behind the surrogate model.

It is the electrostatics counterpart to the magnetostatic automation pipeline.

---

## 📁 Repository contents

| File | Language | Purpose |
| --- | --- | --- |
| `Efield_datasetgeneration.py` | Python | Drives CST via its Python API to sweep electrode voltages and export the resulting potential maps (basis generation). |
| `Potential_Map_RZ.m` | MATLAB | Loads a single CST-exported potential file and plots the 2-D potential map (Y–Z plane) and the 1-D axial profile V(Z). |
| `.gitignore` | — | Ignores everything except the tracked scripts. |

---

## ⚙️ `Efield_datasetgeneration.py`

Connects to a running or new CST design environment (`cst.interface.DesignEnvironment.connect_to_any_or_new()`), opens the electrostatic project, and for **each electrode** in the trap:

1. Draws **Latin Hypercube samples** of the applied voltage (`scipy.stats.qmc.LatinHypercube`) over a configurable range.
2. Sets the target electrode to the sampled voltage (all others held at 0 V) by injecting VBA `StoreParameter` calls and rebuilding the model.
3. Runs the CST electrostatic solver.
4. Exports the `Potential [Es]` field over a defined subvolume as a fixed-width ASCII file (`Potential_<electrode>_<voltage>.txt`), on a 10 mm grid.

It includes **resume/overwrite handling**: on restart it can skip files that already exist, so a run interrupted by a solver or licence crash can be continued without repeating completed samples.

### Key configuration (edit at the top of the file)

| Variable | Meaning |
| --- | --- |
| `PROJECT_PATH` | Path to the `.cst` project. |
| `BASE_RESULT_FOLDER` | Output directory; one sub-folder is created per electrode. |
| `NUM_SAMPLES` | Number of LHS voltage samples per electrode. |
| `VOLTAGE_MIN` / `VOLTAGE_MAX` | Sampling range (default −500 V to +500 V). |
| `ELECTRODE_DEFAULTS` | The full list of trap electrodes (C, HV, P, T, B, A series, plus guard rings G1/G2) and their default potentials. |
| `SUB_VOL` | Export subvolume `[Xmin, Xmax, Ymin, Ymax, Zmin, Zmax]`. |

> The paths in the script are Windows absolute paths (e.g. `D:\CST Python\...`). Update them to your own environment before running.

---

## 📊 `Potential_Map_RZ.m`

A MATLAB viewer/sanity-check for a single exported potential file. It reads the 4-column CST export (X, Y, Z, Potential) and produces:

- **Figure 1** — a filled-contour **2-D potential map** in the Y–Z plane at the chosen x-slice, with automatically scaled colour limits.
- **Figure 2** — the **1-D axial potential profile** V(Z) along the central axis.

It automatically snaps to the nearest available slice, sorts the CST data (which can be exported out of order), and handles the degenerate uniform-field case. Set `filename`, `target_x`, and `target_y` at the top before running.

---

## 🚀 Workflow

```
1. Build a parametrized CST electrostatic project
   (electrode voltages exposed as named parameters matching ELECTRODE_DEFAULTS).

2. Run Efield_datasetgeneration.py
   → produces one folder per electrode, each containing the
     LHS-sampled potential-map text files (the ROM basis).

3. Assemble the ROM
   → superpose the per-electrode unit-potential maps to reconstruct
     the field for any voltage configuration.

4. Inspect / validate any export with Potential_Map_RZ.m.
```

---

## 🔧 Requirements

- **CST Studio Suite** with its Python interface (the `cst` package ships with the CST Python distribution).
- **Python 3** with `numpy` and `scipy`:
  ```bash
  pip install numpy scipy
  ```
- **MATLAB** (any reasonably recent version) for the plotting script.
- **Windows** — CST and the hard-coded paths assume a Windows environment.

The `cst.interface` module is provided by your CST installation and cannot be installed from PyPI; run the script with the Python interpreter bundled with CST, or add the CST Python libraries to your path.

---

## 🔬 Scientific context

AEgIS confines and manipulates charged particles using a long stack of cylindrical electrodes. Modelling the electrostatic potential from the full CAD geometry with a 3-D solver is accurate but slow — impractical for real-time control or for scanning many voltage configurations. Because the electrostatic problem is linear in the applied voltages, the field for any configuration is a linear combination of the fields produced by each electrode acting alone. This repository generates exactly those single-electrode fields, giving a basis from which the ROM reconstructs the full potential almost instantly, benchmarked against the CST 3-D electrostatic solver.

---

## 👤 Author

**Dr. Bharat Singh Rawat**
📧 bharat.bharat22@gmail.com

Developed for the **AEgIS Collaboration** at **CERN**.

---

## 📜 License

[MIT License](https://choosealicense.com/licenses/mit/).

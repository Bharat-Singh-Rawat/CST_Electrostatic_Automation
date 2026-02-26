import os
import time
import cst.interface
import numpy as np
from scipy.stats import qmc

# --- Configuration ---
PROJECT_PATH = r"D:\CST Python\EfieldRuns\Efield_5T_1T.cst"
BASE_RESULT_FOLDER = r"D:\CST Python\EfieldRuns\Results"

NUM_SAMPLES = 10
VOLTAGE_MIN = -500.0
VOLTAGE_MAX = 500.0

# Directly encoded default electrode voltages (used only to get the list of names now)
ELECTRODE_DEFAULTS = {
    "C0": 0.0, "HV1": 0.0, "C1": 0.0, "C2": 0.0, "C3": 0.0, "C4": 0.0, "C5": 0.0, 
    "C6": 0.0, "C7": 0.0, "C8": 0.0, "C9": 0.0, "C10": 0.0, "C11": 0.0, "C12": 0.0, 
    "C13": 0.0, "C14": 0.0, "C15": 0.0, "C16": 0.0, "C17": 0.0, "C18": 0.0, "C19": 0.0, 
    "HV2": 0.0, "P1": 0.0, "P2": 0.0, "P3": 0.0, "P4": 0.0, 
    "P5": -180.0, "P6": -42.973, "P7": -77.619, "P8": -63.961, "P9": -162.5, 
    "P10": -62.541, "P11": -60.960, "P12": -59.990, "P13": -56.137, "P14": -52.836, 
    "HV3": -47.773, "T1": -43.256, "T2": -40.431, "T3": -37.207, "T4": -34.696, 
    "T5": -32.701, "T6": -31.190, "B0": -30.108, "B1": -30.005, "B2": -30.672, 
    "B3": -31.957, "B4": -33.878, "B5": -36.419, "B6": -39.574, "B7": -43.438, 
    "B8": -47.209, "B9": -47.601, "B10": -50.075, "HV4": -51.714, "HV5": -53.945, 
    "HV6": -56.110, "A8": -58.258, "A7": -60.672, "A6": -62.643, "A5": -66.873, 
    "A4": -66.586, "A3": -66.098, "A2": -71.969, "A1": -70.307, "A0T": -70.929, 
    "A0R": -70.006, "G1": -450.0, "G2": 150.0
}

SUB_VOL = [-528.94, 520.94, -528.94, 520.94, -1673.55, 3493.39]

def main():
    # --- Check for Existing Progress ---
    mode = "run"
    if os.path.exists(BASE_RESULT_FOLDER) and os.listdir(BASE_RESULT_FOLDER):
        print("Existing result folders detected.")
        choice = input("Do you want to (O)verwrite everything or (R)esume from the last crash? [O/R]: ").strip().lower()
        if choice == 'r':
            mode = "resume"
            print("Mode set to RESUME: Existing files will be skipped.")
        else:
            print("Mode set to OVERWRITE: Existing data will be replaced.")

    de = cst.interface.DesignEnvironment.connect_to_any_or_new()
    
    try:
        prj = de.open_project(PROJECT_PATH)

        for target_electrode in ELECTRODE_DEFAULTS.keys():
            electrode_folder = os.path.join(BASE_RESULT_FOLDER, str(target_electrode))
            if not os.path.exists(electrode_folder):
                os.makedirs(electrode_folder)

            # Generate LHS Samples (-500V to +500V) 
            sampler = qmc.LatinHypercube(d=1, seed=42) 
            sample = sampler.random(n=NUM_SAMPLES)
            current_values = qmc.scale(sample, [VOLTAGE_MIN], [VOLTAGE_MAX]).flatten()

            print(f"\nProcessing Electrode: {target_electrode}")

            for i, val in enumerate(current_values):
                val = round(float(val), 3)
                file_name = f"Potential_{target_electrode}_{val}.txt"
                full_path_os = os.path.join(electrode_folder, file_name)
                
                # --- RESUME LOGIC ---
                if mode == "resume" and os.path.exists(full_path_os):
                    print(f"  [Skipping] {file_name} already exists.")
                    continue

                print(f"  [Running] {target_electrode} = {val} V ({i+1}/{NUM_SAMPLES})")

                # VBA: Update Parameters
                vba_set_params = "Sub Main\n"
                for electrode_name in ELECTRODE_DEFAULTS.keys():
                    # Set target to test voltage; set all other electrodes to 0.0
                    set_val = val if electrode_name == target_electrode else 0.0
                    vba_set_params += f'  StoreParameter("{electrode_name}", {set_val})\n'
                vba_set_params += "  Rebuild\nEnd Sub"
                prj.schematic.execute_vba_code(vba_set_params)
                
                # Solver
                try:
                    prj.model3d.run_solver()
                except Exception as e:
                    print(f"    Solver error: {e}")

                # Export Electric Potential
                full_path_vba = full_path_os.replace("\\", "\\\\")
                export_vba = f"""
                Sub Main
                    ' Target the 3D Potential map instead of E-Field
                    SelectTreeItem("2D/3D Results\\Potential\\potential")
                    With ASCIIExport
                        .Reset
                        .FileName ("{full_path_vba}")
                        .Mode "FixedWidth"
                        .StepX 10: .StepY 10: .StepZ 10
                        .SetSubvolume {SUB_VOL[0]}, {SUB_VOL[1]}, {SUB_VOL[2]}, {SUB_VOL[3]}, {SUB_VOL[4]}, {SUB_VOL[5]}
                        .UseSubvolume True
                        .Execute
                    End With
                End Sub
                """
                prj.schematic.execute_vba_code(export_vba)
                prj.save()

    except Exception as e:
        print(f"Critical error: {e}")
    finally:
        print("\nBatch process finished.")

if __name__ == "__main__":
    main()
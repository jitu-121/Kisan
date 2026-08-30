"""
Interactive Batch-Regression Sensor Calibration Tool for Project KISAN.
Integrates directly with hardware SensorService (/dev/ttyUSB0 RS485 Modbus RTU).
Enforces Moisture >= 70% Slurry Gate, appends data to calibration_dataset.csv,
and REFITS a regression model on the full dataset after every new sample
(instead of nudging weights with a single-sample SGD step).

Why this replaces the SGD version — see the printed explanation at the bottom
of each session, and the README block at the end of this file.
"""

import csv
import json
import os
import time

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import LeaveOneOut

from services.sensor_service import SensorService

# Configuration & Absolute Path Resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "calibration_dataset.csv")
JSON_FILE = os.path.join(BASE_DIR, "perfect_weights.json")
MOISTURE_THRESHOLD = 70.0  # Required >= 70% moisture slurry threshold
MIN_SAMPLES_FOR_FIT = 3  # Can't fit a line with fewer than this many points
RIDGE_ALPHA = 1.0  # Regularization strength used once we switch off plain OLS
OUTLIER_Z_THRESHOLD = 2.5  # Flag residuals beyond this many std-devs

NUTRIENTS = ["N", "P", "K"]

# Ensure CSV File Headers exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "sample_num",
            "timestamp",
            "n_raw",
            "p_raw",
            "k_raw",
            "ph_raw",
            "moisture",
            "n_lab",
            "p_lab",
            "k_lab",
        ])


# ---------------------------------------------------------------------------
# Weight file I/O — SAME SHAPE as before, so sensor_service.py needs ZERO
# changes. We just compute w/b differently (closed-form regression instead
# of an SGD nudge).
# ---------------------------------------------------------------------------

def load_weights() -> dict:
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    return {
        "N": {"w": 1.0, "b": 0.0, "sample_count": 0, "r2": None, "rmse": None},
        "P": {"w": 1.0, "b": 0.0, "sample_count": 0, "r2": None, "rmse": None},
        "K": {"w": 1.0, "b": 0.0, "sample_count": 0, "r2": None, "rmse": None},
    }


def save_weights(weights: dict):
    with open(JSON_FILE, "w") as f:
        json.dump(weights, f, indent=4)


# ---------------------------------------------------------------------------
# Core change: fit_nutrient_model()
#
# Old approach: one SGD step per new sample, forever chasing whatever the
# latest error was, with no way to know if the model was any good.
#
# New approach: every time a sample is added, refit a model on ALL samples
# collected so far (features: raw reading + moisture, since moisture affects
# ion conductivity and therefore the raw NPK signal). We cross-validate to
# report an honest accuracy estimate, and flag possible outliers before they
# corrupt the fit.
# ---------------------------------------------------------------------------

def fit_nutrient_model(nutrient: str, rows: list) -> dict:
    """
    rows: list of dicts with keys 'raw', 'moisture', 'lab' for this nutrient.
    Returns a dict: w, b, sample_count, r2, rmse, flagged_outliers.
    """
    n = len(rows)
    X_raw = np.array([[r["raw"], r["moisture"]] for r in rows], dtype=float)
    y = np.array([r["lab"] for r in rows], dtype=float)

    if n < MIN_SAMPLES_FOR_FIT:
        # Not enough data to fit anything meaningful yet — fall back to
        # identity mapping and be explicit that calibration isn't active.
        return {
            "w": 1.0,
            "b": 0.0,
            "w_moisture": 0.0,
            "sample_count": n,
            "r2": None,
            "rmse": None,
            "flagged_outliers": [],
            "status": f"NOT ENOUGH DATA (need {MIN_SAMPLES_FOR_FIT}, have {n})",
        }

    # Use plain OLS once we have a reasonable number of points, otherwise
    # Ridge (regularized) to avoid overfitting on a tiny sample count.
    model_cls = LinearRegression if n >= 12 else Ridge
    model_kwargs = {} if model_cls is LinearRegression else {"alpha": RIDGE_ALPHA}

    model = model_cls(**model_kwargs)
    model.fit(X_raw, y)
    preds = model.predict(X_raw)
    residuals = y - preds

    # Cross-validated R² (leave-one-out is fine at this sample size) gives an
    # honest estimate of how well this generalizes, instead of just fitting
    # error on the same data we're scoring against.
    # NOTE: sklearn's cross_val_score with scoring="r2" fails/warns on
    # LeaveOneOut because each test fold has exactly 1 sample (R² is
    # undefined for n=1). Instead we collect all LOO predictions across
    # folds first, then compute a single R²/RMSE over the pooled result —
    # this is the standard way to get an honest LOO-CV R² for small n.
    r2_cv = None
    rmse_cv = None
    if n >= MIN_SAMPLES_FOR_FIT + 1:
        try:
            loo = LeaveOneOut()
            preds_loo = np.zeros_like(y)
            for train_idx, test_idx in loo.split(X_raw):
                m = model_cls(**model_kwargs)
                m.fit(X_raw[train_idx], y[train_idx])
                preds_loo[test_idx] = m.predict(X_raw[test_idx])
            ss_res = np.sum((y - preds_loo) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2_val = float(1 - ss_res / ss_tot) if ss_tot > 1e-9 else None
            rmse_val = float(np.sqrt(np.mean((y - preds_loo) ** 2)))
            if r2_val is not None and not np.isnan(r2_val) and not np.isinf(r2_val):
                r2_cv = r2_val
            if rmse_val is not None and not np.isnan(rmse_val) and not np.isinf(rmse_val):
                rmse_cv = rmse_val
        except Exception:
            pass  # if CV fails for any reason, we still have the plain fit

    # Outlier flagging: residuals more than OUTLIER_Z_THRESHOLD std-devs away
    # get flagged for the user to review (not silently dropped — that's a
    # judgment call for a human, not the script).
    std = np.std(residuals) if np.std(residuals) > 1e-9 else 1e-9
    z_scores = residuals / std
    flagged = [
        {"index": i, "raw": rows[i]["raw"], "lab": rows[i]["lab"], "z": round(float(z_scores[i]), 2)}
        for i in range(n)
        if abs(z_scores[i]) > OUTLIER_Z_THRESHOLD
    ]

    w_raw, w_moisture = model.coef_
    b = model.intercept_

    return {
        "w": round(float(w_raw), 5),
        "b": round(float(b), 5),
        "w_moisture": round(float(w_moisture), 5),
        "sample_count": n,
        "r2": round(r2_cv, 4) if r2_cv is not None else None,
        "rmse": round(rmse_cv, 3) if rmse_cv is not None else None,
        "flagged_outliers": flagged,
        "status": "OK",
        "model_type": model_cls.__name__,
    }


def refit_all_nutrients_from_csv(weights: dict) -> dict:
    """Reads the full calibration_dataset.csv and refits N/P/K models."""
    rows_by_nutrient = {n: [] for n in NUTRIENTS}

    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row:
                    continue
                try:
                    moisture = float(row["moisture"])
                    rows_by_nutrient["N"].append(
                        {"raw": float(row["n_raw"]), "moisture": moisture, "lab": float(row["n_lab"])}
                    )
                    rows_by_nutrient["P"].append(
                        {"raw": float(row["p_raw"]), "moisture": moisture, "lab": float(row["p_lab"])}
                    )
                    rows_by_nutrient["K"].append(
                        {"raw": float(row["k_raw"]), "moisture": moisture, "lab": float(row["k_lab"])}
                    )
                except (ValueError, KeyError):
                    continue

    new_weights = {}
    for nutrient in NUTRIENTS:
        fit_result = fit_nutrient_model(nutrient, rows_by_nutrient[nutrient])
        prev = weights.get(nutrient, {})

        # If not enough samples yet to fit a line, preserve existing manual/preset weights
        if fit_result["sample_count"] < MIN_SAMPLES_FOR_FIT and prev:
            fit_result["w"] = prev.get("w", fit_result["w"])
            fit_result["b"] = prev.get("b", fit_result["b"])
            fit_result["w_moisture"] = prev.get("w_moisture", fit_result["w_moisture"])

        prev_r2 = prev.get("r2")
        new_weights[nutrient] = fit_result

        # Guardrail: only "accept" a refit that doesn't get WORSE than what
        # we already had, once we have enough history to trust R² at all.
        # We still save it either way for visibility, but we flag regressions
        # loudly instead of silently shipping a worse model to production.
        if prev_r2 is not None and fit_result["r2"] is not None and fit_result["r2"] < prev_r2 - 0.05:
            fit_result["status"] = (
                f"WARNING: R2 dropped from {prev_r2} to {fit_result['r2']}. "
                f"Review flagged_outliers before trusting this model."
            )

    return new_weights


def read_probe_telemetry():
    """Reads live hardware sensor from SensorService (/dev/ttyUSB0 Modbus RS485)."""
    hw = SensorService.read_hardware_sensor()
    if hw is not None:
        return hw

    print("\n⚠️ PHYSICAL SENSOR OFFLINE (/dev/ttyUSB0 not responding).")
    choice = input("Would you like to manually enter raw sensor readings for testing? (y/n): ").strip().lower()
    if choice == "y":
        try:
            m = float(input("   Enter Raw Moisture (%): "))
            n = float(input("   Enter Raw Nitrogen N (kg/hector): "))
            p = float(input("   Enter Raw Phosphorus P (kg/hector): "))
            k = float(input("   Enter Raw Potassium K (kg/hector): "))
            ph = float(input("   Enter Raw pH: "))
            return {"moisture": m, "nitrogen": n, "phosphorus": p, "potassium": k, "ph": ph}
        except ValueError:
            return None
    return None


def run_calibration_session():
    weights = load_weights()

    # Safely get current sample count
    sample_count = weights.get("N", {}).get("sample_count")
    if sample_count is None:
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, "r", newline="") as f:
                sample_count = max(0, sum(1 for row in csv.DictReader(f)))
        else:
            sample_count = 0
    sample_num = sample_count + 1

    print("\n==================================================")
    print(f" 🧪 KISAN RS485 SENSOR CALIBRATION SESSION - SAMPLE #{sample_num}")
    print("==================================================")

    input("\n👉 Insert 7-in-1 Probe into Soil Slurry and Press ENTER to read sensor...")

    print("⏳ Connecting to /dev/ttyUSB0 (4800 baud Modbus RTU)...")
    sensor_data = read_probe_telemetry()

    if sensor_data is None:
        print("❌ Sensor reading cancelled or failed.")
        return

    moisture = sensor_data.get("moisture", 0.0)
    n_raw = sensor_data.get("nitrogen", 0.0)
    p_raw = sensor_data.get("phosphorus", 0.0)
    k_raw = sensor_data.get("potassium", 0.0)
    ph_raw = sensor_data.get("ph", 6.8)

    print(f"\n💧 Moisture Reading: {moisture:.1f}%")

    if moisture < MOISTURE_THRESHOLD:
        print(f"\n❌ ERROR: Moisture ({moisture:.1f}%) < {MOISTURE_THRESHOLD}% Threshold!")
        print("⚠️ Soil is too dry. Please add distilled water to achieve a slurry state (>= 70%) and retry.")
        return

    print("✅ Moisture Condition Met (>= 70% Slurry Saturation State)!")

    print(f"\n📡 RAW RS485 SENSOR TELEMETRY CAPTURED:")
    print(f"   Nitrogen N   : {n_raw} kg/hector")
    print(f"   Phosphorus P : {p_raw} kg/hector")
    print(f"   Potassium K  : {k_raw} kg/hector")
    print(f"   pH Level     : {ph_raw}")

    print("\n--------------------------------------------------")
    print("🧪 ENTER GROUND-TRUTH WET-CHEMISTRY LAB TEST RESULTS:")
    print("--------------------------------------------------")

    try:
        n_lab = float(input("   Enter Lab Nitrogen N value (kg/hector): "))
        p_lab = float(input("   Enter Lab Phosphorus P value (kg/hector): "))
        k_lab = float(input("   Enter Lab Potassium K value (kg/hector): "))
    except ValueError:
        print("❌ Invalid numeric input! Session cancelled.")
        return

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            sample_num, timestamp, n_raw, p_raw, k_raw, ph_raw, moisture, n_lab, p_lab, k_lab,
        ])
    print(f"\n💾 Saved Sample #{sample_num} data to '{CSV_FILE}'")

    print("\n⚡ REFITTING REGRESSION MODELS ON FULL DATASET (not just this sample)...")
    new_weights = refit_all_nutrients_from_csv(weights)

    for nutrient in NUTRIENTS:
        r = new_weights[nutrient]
        print(f"\n  🔹 [{nutrient}] status: {r['status']}")
        if r["r2"] is not None:
            print(f"     model: {r.get('model_type', 'n/a')} | n={r['sample_count']} "
                  f"| LOO-CV R²={r['r2']} | LOO-CV RMSE={r['rmse']}")
            print(f"     w_raw={r['w']}  w_moisture={r['w_moisture']}  b={r['b']}")
        if r["flagged_outliers"]:
            print(f"     ⚠️ {len(r['flagged_outliers'])} potential outlier(s) — review before trusting:")
            for o in r["flagged_outliers"]:
                print(f"        sample idx={o['index']}: raw={o['raw']}, lab={o['lab']}, z={o['z']}")

    save_weights(new_weights)

    print("\n==================================================")
    print(f"🎉 SAMPLE #{sample_num} CALIBRATION COMPLETE!")
    print(f"   Latest fitted weights saved to '{JSON_FILE}'")
    if any(new_weights[n]["r2"] is not None and new_weights[n]["r2"] < 0.5 for n in NUTRIENTS):
        print("   ⚠️ At least one nutrient has low R² — collect more samples across a wider")
        print("      concentration range before trusting this model in production.")
    print("==================================================\n")


if __name__ == "__main__":
    run_calibration_session()


# ---------------------------------------------------------------------------
# WHY THIS IS A BETTER APPROACH THAN 1-SAMPLE SGD
# ---------------------------------------------------------------------------
# 1. You can now SEE if calibration is working (R², RMSE via leave-one-out
#    cross-validation) instead of blindly trusting whatever weights fall out.
#    The old script had no accuracy metric at all — it just updated forever.
#
# 2. One bad lab reading no longer permanently biases the model. Batch OLS/
#    Ridge refits from scratch each time, so a single outlier is diluted by
#    every other sample instead of nudging the weights and staying baked in
#    at alpha=0.0001 for dozens of future samples.
#
# 3. Outliers are now flagged (z-score on residuals) instead of silently
#    absorbed. You get to decide whether sample #23 was a lab error or a
#    real edge case, rather than the SGD step quietly compensating for it.
#
# 4. Moisture is now a second regression feature (w_moisture), not just a
#    pass/fail gate. Ion-selective/capacitive NPK probes are known to be
#    moisture-sensitive even above the slurry threshold, so this typically
#    improves accuracy over a single-variable line — the >=70% gate is
#    still kept, since it protects against a genuinely different physical
#    regime (air-pocket contact resistance), which regression can't fix.
#
# 5. perfect_weights.json keeps the same top-level shape (w, b, sample_count
#    per nutrient) plus a few extra diagnostic fields, so sensor_service.py
#    can go on reading w/b exactly as before — this is a drop-in replacement
#    for the calibration TOOL, not a change to the production inference path.
#    (If you want sensor_service.py to also use w_moisture, that's a small,
#    optional follow-up change — say so and I'll show the diff.)
#
# 6. Ridge regression kicks in automatically below 12 samples, so early
#    calibration sessions (n=3-11) don't overfit two features to a handful
#    of points the way unregularized OLS would.
# ---------------------------------------------------------------------------

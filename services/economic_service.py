"""
Stage 2 Analytical Prescriptive Economic Engine for Project KISAN.
Provides non-trainable, deterministic financial & agronomic decision scoring.
Executes in sub-millisecond time (<0.5ms) fully offline.
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

MPKV_COSTS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "database", "data", "mpkv_costs.json")
)
APMC_MANDI_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "database", "data", "apmc_mandi_data.json")
)

# Standard fertilizer cost constants per kg of active nutrient element
PRICE_PER_KG_N = 5.95    # Urea (46% N) @ ~₹268 / 45kg bag
PRICE_PER_KG_P = 52.50   # SSP (16% P2O5) @ ~₹420 / 50kg bag
PRICE_PER_KG_K = 56.67   # MOP (60% K2O) @ ~₹1700 / 50kg bag


class EconomicService:
    """
    Stage 2 Economic Decision Framework Engine.
    Combines Stage 1 ML agronomic probabilities with deterministic APMC Mandi prices,
    MPKV baseline cultivation costs, and MSP floor protections.
    """

    def __init__(self):
        self.mpkv_costs = self._load_json(MPKV_COSTS_PATH)
        self.apmc_data = self._load_json(APMC_MANDI_PATH)

    @staticmethod
    def _load_json(file_path: str) -> Dict[str, Any]:
        """Load JSON data file safely."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Economic engine data file missing: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def calculate_economic_ranking(
        self,
        soil_n: float,
        soil_p: float,
        soil_k: float,
        land_acres: float = 1.0,
        stage1_recommendations: Optional[List[Dict[str, Any]]] = None,
        month: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Computes financial metrics, expected yields, and Stage 2 MCDA Prescriptive Scores
        for candidate crops.

        :param soil_n: Soil Nitrogen (kg/ha)
        :param soil_p: Soil Phosphorus (kg/ha)
        :param soil_k: Soil Potassium (kg/ha)
        :param land_acres: Land size in acres (default: 1.0)
        :param stage1_recommendations: List of dicts [{'crop': 'rice', 'confidence': 85.0}, ...]
        :param month: Target harvest month (1-12). Defaults to current month if None.
        :return: List of evaluated crops ordered by Stage 2 Prescriptive Score (descending).
        """
        start_time = time.perf_counter()

        if month is None or not (1 <= month <= 12):
            month = datetime.now().month

        if not stage1_recommendations:
            # Fallback to evaluating all crops equally if Stage 1 list is empty
            stage1_recommendations = [
                {"crop": crop, "confidence": 50.0} for crop in self.mpkv_costs.keys()
            ]

        evaluated_crops = []

        for rec in stage1_recommendations:
            crop_name = rec["crop"].lower().strip()
            s_agronomic = float(rec.get("confidence", 50.0))

            cost_data = self.mpkv_costs.get(crop_name)
            mandi_data = self.apmc_data.get(crop_name)

            if not cost_data or not mandi_data:
                continue

            # 1. Harvest Price Estimator Formula
            p_modal = float(mandi_data.get("Pmodal", 2000.0))
            ema30 = float(mandi_data.get("EMA30", p_modal))
            p_msp = float(mandi_data.get("PMSP", 0.0))

            iseasonal_dict = mandi_data.get("Iseasonal", {})
            i_seasonal = float(iseasonal_dict.get(str(month), 1.0))

            price_trend = (p_modal - ema30) / ema30 if ema30 > 0 else 0.0
            p_harvest_est = p_modal * i_seasonal * (1.0 + 0.50 * price_trend)

            # 2. MSP Floor Constraint
            p_effective = max(p_harvest_est, p_msp)
            msp_backed = 1 if (p_msp > 0 and p_effective == p_msp) else (1 if p_msp > 0 else 0)

            # 3. Dynamic Expected Yield Formula
            ympkv_base = float(cost_data.get("YMPKV_base", 10.0))
            y_expected_per_acre = ympkv_base * (0.60 + 0.40 * (s_agronomic / 100.0))

            # 4. Remediation Cost Integration (NPK deficit)
            req_n = float(cost_data.get("req_N", 30.0))
            req_p = float(cost_data.get("req_P", 20.0))
            req_k = float(cost_data.get("req_K", 20.0))

            delta_n = max(0.0, req_n - soil_n)
            delta_p = max(0.0, req_p - soil_p)
            delta_k = max(0.0, req_k - soil_k)

            c_remediation_per_acre = (
                (delta_n * PRICE_PER_KG_N) +
                (delta_p * PRICE_PER_KG_P) +
                (delta_k * PRICE_PER_KG_K)
            )

            # 5. Total Cultivation Cost & Revenue Calculations
            c_seeds = float(cost_data.get("Cseeds", 2000.0))
            c_labor = float(cost_data.get("Clabor", 8000.0))
            c_irrigation = float(cost_data.get("Cirrigation", 3000.0))
            c_pesticides = float(cost_data.get("Cpesticides", 3000.0))

            c_total_per_acre = c_seeds + c_labor + c_irrigation + c_pesticides + c_remediation_per_acre
            r_expected_per_acre = y_expected_per_acre * p_effective
            net_profit_per_acre = r_expected_per_acre - c_total_per_acre

            roi_percent = (net_profit_per_acre / c_total_per_acre * 100.0) if c_total_per_acre > 0 else 0.0

            evaluated_crops.append({
                "crop": crop_name,
                "s_agronomic": round(s_agronomic, 2),
                "y_expected_per_acre": round(y_expected_per_acre, 2),
                "total_yield_acres": round(y_expected_per_acre * land_acres, 2),
                "p_harvest_est": round(p_harvest_est, 2),
                "p_effective": round(p_effective, 2),
                "p_msp": round(p_msp, 2),
                "msp_backed": msp_backed,
                "c_remediation_per_acre": round(c_remediation_per_acre, 2),
                "c_total_per_acre": round(c_total_per_acre, 2),
                "total_cost_land": round(c_total_per_acre * land_acres, 2),
                "r_expected_per_acre": round(r_expected_per_acre, 2),
                "net_profit_per_acre": round(net_profit_per_acre, 2),
                "total_net_profit_land": round(net_profit_per_acre * land_acres, 2),
                "roi_percent": round(roi_percent, 2),
                "cost_breakdown": {
                    "seeds": round(c_seeds, 2),
                    "labor": round(c_labor, 2),
                    "irrigation": round(c_irrigation, 2),
                    "pesticides": round(c_pesticides, 2),
                    "remediation": round(c_remediation_per_acre, 2)
                }
            })

        if not evaluated_crops:
            return []

        # 6. MCDA Prescriptive Score Calculation
        min_profit = min(item["net_profit_per_acre"] for item in evaluated_crops)
        max_profit = max(item["net_profit_per_acre"] for item in evaluated_crops)
        profit_range = max_profit - min_profit

        for item in evaluated_crops:
            if profit_range > 0:
                s_profit_norm = ((item["net_profit_per_acre"] - min_profit) / profit_range) * 100.0
            else:
                s_profit_norm = 100.0

            i_msp_floor = 100.0 if item["p_msp"] > 0 else 0.0

            s_prescriptive = (
                (0.40 * item["s_agronomic"]) +
                (0.40 * s_profit_norm) +
                (0.20 * i_msp_floor)
            )

            item["s_profit_norm"] = round(s_profit_norm, 2)
            item["s_prescriptive"] = round(s_prescriptive, 2)

        # Sort descending by Stage 2 Prescriptive Score
        evaluated_crops.sort(key=lambda x: x["s_prescriptive"], reverse=True)

        execution_latency_ms = (time.perf_counter() - start_time) * 1000.0
        # Store latency tag in the top element metadata or return structure
        for item in evaluated_crops:
            item["latency_ms"] = round(execution_latency_ms, 4)

        return evaluated_crops

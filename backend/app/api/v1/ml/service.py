from datetime import datetime, timedelta
from typing import List

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.monitoring import Monitoring
from app.api.v1.monitoring.service import (
    CPU_THRESHOLD,
    RAM_THRESHOLD,
    DISK_THRESHOLD,
    get_metrics_history,
)

MIN_SAMPLES_FOR_ML = 10


def _history_as_arrays(history: List[Monitoring]):
    """
    monitoring history comes back newest-first (see get_metrics_history);
    ML wants it oldest-first so trends/forecasts read left-to-right.
    """
    ordered = sorted(history, key=lambda m: m.created_at)

    cpu = np.array([m.cpu_usage for m in ordered], dtype=float)
    ram = np.array([m.ram_usage for m in ordered], dtype=float)
    disk = np.array([m.disk_usage for m in ordered], dtype=float)

    return ordered, cpu, ram, disk


# =====================================================
# Anomaly Detection
# =====================================================

def detect_anomalies(db: Session, asset_id: int):
    history = get_metrics_history(db, asset_id)

    if len(history) < MIN_SAMPLES_FOR_ML:
        return {
            "asset_id": asset_id,
            "sample_size": len(history),
            "anomalies_found": 0,
            "points": [],
            "message": (
                f"Not enough monitoring history yet "
                f"(need at least {MIN_SAMPLES_FOR_ML} data points, "
                f"have {len(history)})."
            ),
        }

    ordered, cpu, ram, disk = _history_as_arrays(history)

    features = np.column_stack([cpu, ram, disk])

    # contamination is an estimate of the expected proportion of outliers;
    # 0.1 is a reasonable default for infrastructure telemetry.
    model = IsolationForest(
        n_estimators=200,
        contamination=0.1,
        random_state=42,
    )
    model.fit(features)

    predictions = model.predict(features)  # -1 = anomaly, 1 = normal
    scores = model.decision_function(features)  # higher = more normal

    points = []
    anomalies_found = 0

    for m, pred, score in zip(ordered, predictions, scores):
        is_anomaly = bool(pred == -1)
        if is_anomaly:
            anomalies_found += 1

        points.append(
            {
                "id": m.id,
                "created_at": m.created_at,
                "cpu_usage": round(m.cpu_usage, 2),
                "ram_usage": round(m.ram_usage, 2),
                "disk_usage": round(m.disk_usage, 2),
                "is_anomaly": is_anomaly,
                "anomaly_score": round(float(score), 4),
            }
        )

    return {
        "asset_id": asset_id,
        "sample_size": len(history),
        "anomalies_found": anomalies_found,
        "points": points,
        "message": None,
    }


# =====================================================
# Usage Forecasting
# =====================================================

def forecast_usage(db: Session, asset_id: int, horizon: int = 5):
    history = get_metrics_history(db, asset_id)

    if len(history) < MIN_SAMPLES_FOR_ML:
        return {
            "asset_id": asset_id,
            "sample_size": len(history),
            "horizon": horizon,
            "forecast": [],
            "trend": {},
            "message": (
                f"Not enough monitoring history yet "
                f"(need at least {MIN_SAMPLES_FOR_ML} data points, "
                f"have {len(history)})."
            ),
        }

    ordered, cpu, ram, disk = _history_as_arrays(history)

    n = len(ordered)
    x = np.arange(n).reshape(-1, 1)

    def fit_and_predict(y: np.ndarray):
        reg = LinearRegression()
        reg.fit(x, y)

        future_x = np.arange(n, n + horizon).reshape(-1, 1)
        preds = reg.predict(future_x)

        # Usage percentages are bounded [0, 100]
        preds = np.clip(preds, 0, 100)

        return preds, float(reg.coef_[0])

    cpu_preds, cpu_slope = fit_and_predict(cpu)
    ram_preds, ram_slope = fit_and_predict(ram)
    disk_preds, disk_slope = fit_and_predict(disk)

    last_timestamp = ordered[-1].created_at

    # Estimate typical spacing between samples to label forecast steps
    if n >= 2:
        deltas = [
            (ordered[i + 1].created_at - ordered[i].created_at)
            for i in range(n - 1)
        ]
        avg_delta = sum(deltas, timedelta()) / len(deltas)
    else:
        avg_delta = timedelta(minutes=5)

    forecast = []
    for step in range(horizon):
        future_time = last_timestamp + avg_delta * (step + 1)
        forecast.append(
            {
                "step": step + 1,
                "label": future_time.strftime("%Y-%m-%d %H:%M"),
                "predicted_cpu_usage": round(float(cpu_preds[step]), 2),
                "predicted_ram_usage": round(float(ram_preds[step]), 2),
                "predicted_disk_usage": round(float(disk_preds[step]), 2),
            }
        )

    def slope_label(slope: float) -> str:
        if slope > 0.5:
            return "increasing"
        if slope < -0.5:
            return "decreasing"
        return "stable"

    return {
        "asset_id": asset_id,
        "sample_size": n,
        "horizon": horizon,
        "forecast": forecast,
        "trend": {
            "cpu": slope_label(cpu_slope),
            "ram": slope_label(ram_slope),
            "disk": slope_label(disk_slope),
        },
        "message": None,
    }


# =====================================================
# Composite Health Score
# =====================================================

def compute_health_score(db: Session, asset_id: int):
    history = get_metrics_history(db, asset_id)

    if not history:
        return {
            "asset_id": asset_id,
            "health_score": 0.0,
            "risk_level": "unknown",
            "factors": {},
            "message": "No monitoring history available for this asset yet.",
        }

    recent = history[: min(20, len(history))]  # newest-first slice

    avg_cpu = sum(m.cpu_usage for m in recent) / len(recent)
    avg_ram = sum(m.ram_usage for m in recent) / len(recent)
    avg_disk = sum(m.disk_usage for m in recent) / len(recent)

    def usage_penalty(avg_value: float, threshold: float) -> float:
        # 0 penalty at/under threshold, scales up to 40 as usage -> 100%
        if avg_value <= threshold:
            return (avg_value / threshold) * 15 if threshold else 0
        overage_ratio = min((avg_value - threshold) / max(100 - threshold, 1), 1)
        return 15 + overage_ratio * 25

    cpu_penalty = usage_penalty(avg_cpu, CPU_THRESHOLD)
    ram_penalty = usage_penalty(avg_ram, RAM_THRESHOLD)
    disk_penalty = usage_penalty(avg_disk, DISK_THRESHOLD)

    open_alerts = (
        db.query(Alert)
        .filter(Alert.asset_id == asset_id, Alert.status == "Open")
        .count()
    )
    alert_penalty = min(open_alerts * 5, 20)

    anomaly_result = None
    anomaly_penalty = 0.0
    if len(history) >= MIN_SAMPLES_FOR_ML:
        anomaly_result = detect_anomalies(db, asset_id)
        recent_points = anomaly_result["points"][-20:]
        recent_anomalies = sum(1 for p in recent_points if p["is_anomaly"])
        anomaly_penalty = min(recent_anomalies * 3, 15)

    total_penalty = (
        cpu_penalty + ram_penalty + disk_penalty + alert_penalty + anomaly_penalty
    )
    health_score = round(max(0.0, 100.0 - total_penalty), 2)

    if health_score >= 85:
        risk_level = "low"
    elif health_score >= 60:
        risk_level = "medium"
    else:
        risk_level = "high"

    return {
        "asset_id": asset_id,
        "health_score": health_score,
        "risk_level": risk_level,
        "factors": {
            "avg_cpu_usage": round(avg_cpu, 2),
            "avg_ram_usage": round(avg_ram, 2),
            "avg_disk_usage": round(avg_disk, 2),
            "open_alerts": open_alerts,
            "recent_anomalies": (
                anomaly_result["anomalies_found"] if anomaly_result else 0
            ),
            "sample_size": len(recent),
        },
        "message": None,
    }

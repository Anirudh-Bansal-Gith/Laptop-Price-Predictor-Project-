"""Inference and user input formatting module.

Provides inference abstractions for real-time model evaluation:
- Loading serialized estimators.
- Formatting single-instance user dictionaries into structured predictor DataFrames.
- Computing required derived attributes (e.g. PPI, brand indicators, CPU tier).
- Generating point predictions in standard currency units.
"""

from typing import Dict, Any
import joblib
import pandas as pd

from src.data.feature_engineering import compute_ppi, classify_cpu_tier


def load_model(model_path: str = "models/best_model.pkl"):
    """Load serialized scikit-learn pipeline from disk.

    Args:
        model_path: Path to serialized artifact.

    Returns:
        Pipeline: Loaded scikit-learn Pipeline object.
    """
    return joblib.load(model_path)


def prepare_input(features: Dict[str, Any]) -> pd.DataFrame:
    """Transform user specification payload into a validated predictor DataFrame.

    Synthesizes derived features required by the ColumnTransformer preprocessor:
        - PPI pixel density.
        - Binary flags for touchscreen, IPS, premium brand, and dedicated GPU.
        - Normalized CPU tier and OS classification.

    Args:
        features: Input hardware specification dictionary.

    Returns:
        pd.DataFrame: Single-row DataFrame matching the training feature schema.
    """
    screen_size = float(features.get("screen_size", 15.6))
    res_x = int(features.get("resolution_x", 1920))
    res_y = int(features.get("resolution_y", 1080))
    ppi = compute_ppi(res_x, res_y, screen_size)

    storage_gb = int(features.get("storage_gb", 512))
    storage_type = str(features.get("storage_type", "SSD")).upper()

    processor_name = str(features.get("processor_name", ""))
    cpu_tier = classify_cpu_tier(processor_name)

    brand = str(features.get("brand", "Dell"))
    premium_brands = {"Apple", "Microsoft", "Razer", "Google", "Huawei", "MSI", "Samsung"}
    is_premium = 1 if brand in premium_brands else 0

    gpu_brand = str(features.get("gpu_brand", "Intel"))
    has_dedicated_gpu = 1 if gpu_brand in {"Nvidia", "AMD"} else 0

    os_raw = str(features.get("os", "Windows")).lower()
    if "windows" in os_raw:
        os_clean = "Windows"
    elif "mac" in os_raw:
        os_clean = "macOS"
    elif "linux" in os_raw:
        os_clean = "Linux/Other"
    else:
        os_clean = "No OS/Other"

    record = {
        "screen_size": screen_size,
        "cpu_freq_ghz": float(features.get("cpu_freq_ghz", 2.5)),
        "ram_gb": int(features.get("ram_gb", 8)),
        "ssd_gb": storage_gb if storage_type == "SSD" else 0,
        "hdd_gb": storage_gb if storage_type == "HDD" else 0,
        "total_storage_gb": storage_gb,
        "weight_kg": float(features.get("weight_kg", 2.0)),
        "res_x": res_x,
        "res_y": res_y,
        "ppi": ppi,
        "is_touchscreen": int(features.get("is_touchscreen", False)),
        "is_ips": int(features.get("is_ips", True)),
        "has_dedicated_gpu": has_dedicated_gpu,
        "is_premium_brand": is_premium,
        "screen_area": screen_size**2 * 0.4,
        "brand": brand,
        "type_name": str(features.get("type_name", "Notebook")),
        "cpu_brand": str(features.get("processor_brand", "Intel")),
        "cpu_tier": cpu_tier,
        "gpu_brand": gpu_brand,
        "os_clean": os_clean,
        "primary_storage_type": storage_type if storage_type in {"SSD", "HDD"} else "SSD",
    }

    return pd.DataFrame([record])


def predict_price(model: Any, features: Dict[str, Any]) -> float:
    """Predict market price for a single laptop hardware configuration.

    Args:
        model: Trained scikit-learn estimator or pipeline.
        features: Hardware specification dictionary matching `LaptopFeatures` schema.

    Returns:
        float: Estimated price in Euros, bounded to non-negative values.
    """
    input_df = prepare_input(features)
    predicted_val = model.predict(input_df)[0]
    return max(0.0, round(float(predicted_val), 2))

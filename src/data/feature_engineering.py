"""Feature engineering module for laptop market price estimation.

This module applies domain transformations to cleaned hardware attributes:
- Pixels Per Inch (PPI) computation from pixel resolutions and diagonal dimensions.
- CPU tier segmentation (Intel Core i3/i5/i7/i9, AMD Ryzen variants, Budget chips).
- Premium hardware brand indicator flags.
- Dedicated graphics processing unit identification.
"""

from typing import Dict, List
import numpy as np
import pandas as pd


def compute_ppi(res_x: int, res_y: int, screen_size: float) -> float:
    """Calculate Pixels Per Inch (PPI) pixel density.

    Mathematical formulation:
        PPI = sqrt(res_x^2 + res_y^2) / screen_size

    Args:
        res_x: Horizontal screen resolution in pixels.
        res_y: Vertical screen resolution in pixels.
        screen_size: Screen diagonal measurement in inches.

    Returns:
        float: Computed PPI value. Returns 0.0 if screen_size <= 0.
    """
    if screen_size <= 0:
        return 0.0
    diagonal_pixels = np.sqrt(res_x**2 + res_y**2)
    return float(diagonal_pixels / screen_size)


def classify_cpu_tier(cpu_type: str) -> str:
    """Classify raw CPU description string into standardized performance tiers.

    Args:
        cpu_type: Raw processor designation (e.g., 'Core i7 8550U', 'Ryzen 5 5600H').

    Returns:
        str: Categorical processor tier ('i9', 'i7', 'i5', 'i3',
             'AMD_Performance', 'AMD_Budget', 'Budget', 'Other').
    """
    lowered = str(cpu_type).lower()
    if "i9" in lowered:
        return "i9"
    elif "i7" in lowered:
        return "i7"
    elif "i5" in lowered:
        return "i5"
    elif "i3" in lowered:
        return "i3"
    elif any(b in lowered for b in ["celeron", "pentium", "atom"]):
        return "Budget"
    elif any(a in lowered for a in ["a9", "a6", "a10", "a12"]):
        return "AMD_Budget"
    elif any(r in lowered for r in ["ryzen", "fx", "threadripper"]):
        return "AMD_Performance"
    return "Other"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generate engineered predictor features from cleaned dataframe.

    Features synthesized:
        - ppi: Pixels Per Inch display density.
        - cpu_tier: Normalized CPU performance bracket.
        - is_premium_brand: Binary indicator for premium tier manufacturers.
        - has_dedicated_gpu: Binary indicator for dedicated graphics silicon.
        - screen_area: Approximation of panel display area.
        - log_price: Natural logarithm of target price (np.log1p) for log-space models.

    Args:
        df: Cleaned dataframe produced by `clean_laptop_data`.

    Returns:
        pd.DataFrame: Feature-engineered dataframe ready for modeling.
    """
    engineered = df.copy()

    # Pixels Per Inch (PPI)
    engineered["ppi"] = engineered.apply(
        lambda row: compute_ppi(row["res_x"], row["res_y"], row["screen_size"]),
        axis=1,
    )

    # CPU classification
    engineered["cpu_tier"] = engineered["cpu_type"].apply(classify_cpu_tier)

    # Premium manufacturer classification
    premium_brands = {"Apple", "Microsoft", "Razer", "Google", "Huawei", "MSI", "Samsung"}
    engineered["is_premium_brand"] = engineered["brand"].isin(premium_brands).astype(int)

    # Dedicated GPU classification
    dedicated_gpu_vendors = {"Nvidia", "AMD"}
    engineered["has_dedicated_gpu"] = engineered["gpu_brand"].isin(dedicated_gpu_vendors).astype(int)

    # Display panel surface area approximation (assuming ~16:9 aspect ratio constant)
    engineered["screen_area"] = engineered["screen_size"] ** 2 * 0.4

    # Log-transformed price target (if price exists)
    if "price" in engineered.columns:
        engineered["log_price"] = np.log1p(engineered["price"])

    return engineered


def get_feature_columns() -> Dict[str, List[str]]:
    """Return explicit grouping of numerical and categorical feature names.

    Returns:
        Dict[str, List[str]]: Mapping containing 'numeric' and 'categorical' lists.
    """
    return {
        "numeric": [
            "screen_size",
            "cpu_freq_ghz",
            "ram_gb",
            "ssd_gb",
            "hdd_gb",
            "total_storage_gb",
            "weight_kg",
            "res_x",
            "res_y",
            "ppi",
            "is_touchscreen",
            "is_ips",
            "has_dedicated_gpu",
            "is_premium_brand",
            "screen_area",
        ],
        "categorical": [
            "brand",
            "type_name",
            "cpu_brand",
            "cpu_tier",
            "gpu_brand",
            "os_clean",
            "primary_storage_type",
        ],
    }

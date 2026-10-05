"""Data ingestion, normalization, and parsing module.

This module provides preprocessing functions for raw laptop specifications:
- Parsing display resolutions and extracting aspect ratios.
- Deconstructing composite storage strings (e.g., '128GB SSD + 1TB HDD').
- Normalizing operating system categories.
- Extracting display hardware flags (Touchscreen, IPS Panel).
"""

from typing import Tuple, Dict, Any
import re
import pandas as pd


def load_raw_data(filepath: str) -> pd.DataFrame:
    """Load the raw laptop dataset from a CSV file.

    Args:
        filepath: Filesystem path to the raw dataset CSV.

    Returns:
        pd.DataFrame: Loaded raw dataset.
    """
    return pd.read_csv(filepath)


def parse_resolution(screen_res: str) -> Tuple[int, int]:
    """Extract horizontal and vertical pixel counts from resolution strings.

    Examples:
        'IPS Panel Retina Display 2560x1600' -> (2560, 1600)
        'Full HD 1920x1080'                  -> (1920, 1080)
        '1366x768'                           -> (1366, 768)

    Args:
        screen_res: Raw screen resolution string.

    Returns:
        Tuple[int, int]: (horizontal_pixels, vertical_pixels). Returns (0, 0) if unparseable.
    """
    match = re.search(r"(\d{3,4})x(\d{3,4})", str(screen_res))
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 0


def parse_memory(memory_str: str) -> Dict[str, int]:
    """Deconstruct raw memory/storage string into discrete capacity metrics.

    Handles single-drive specifications ('256GB SSD') as well as hybrid configurations
    ('128GB SSD + 1TB HDD'). Normalizes Terabytes (TB) to Gigabytes (GB).

    Args:
        memory_str: Raw memory column value.

    Returns:
        Dict[str, int]: Storage breakdown containing:
            - 'ssd_gb': SSD capacity in GB
            - 'hdd_gb': HDD capacity in GB
            - 'flash_gb': Flash storage capacity in GB
            - 'hybrid_gb': Hybrid drive capacity in GB
            - 'total_storage_gb': Combined capacity in GB
    """
    storage_map = {
        "ssd_gb": 0,
        "hdd_gb": 0,
        "flash_gb": 0,
        "hybrid_gb": 0,
    }

    segments = str(memory_str).split("+")
    for segment in segments:
        segment = segment.strip()
        match = re.search(r"([\d.]+)\s*(TB|GB)", segment, re.IGNORECASE)
        if not match:
            continue

        capacity = float(match.group(1))
        unit = match.group(2).upper()
        if unit == "TB":
            capacity *= 1000
        capacity_int = int(capacity)

        lower_segment = segment.lower()
        if "ssd" in lower_segment:
            storage_map["ssd_gb"] += capacity_int
        elif "hdd" in lower_segment:
            storage_map["hdd_gb"] += capacity_int
        elif "flash" in lower_segment:
            storage_map["flash_gb"] += capacity_int
        elif "hybrid" in lower_segment:
            storage_map["hybrid_gb"] += capacity_int

    storage_map["total_storage_gb"] = sum(storage_map.values())
    return storage_map


def has_feature_in_screen(screen_res: str, feature: str) -> bool:
    """Check whether a specific keyword exists within the screen resolution description.

    Args:
        screen_res: Screen description string.
        feature: Target keyword (e.g., 'Touchscreen', 'IPS').

    Returns:
        bool: True if keyword is present, False otherwise.
    """
    return feature.lower() in str(screen_res).lower()


def normalize_os(os_name: str) -> str:
    """Standardize operating system names into primary market categories.

    Args:
        os_name: Raw operating system name from dataset.

    Returns:
        str: Normalized category ('Windows', 'macOS', 'Linux/Other', 'No OS/Other').
    """
    lowered = str(os_name).lower().strip()
    if "windows" in lowered:
        return "Windows"
    elif "mac" in lowered:
        return "macOS"
    elif "linux" in lowered or "chrome" in lowered or "android" in lowered:
        return "Linux/Other"
    return "No OS/Other"


def clean_laptop_data(df: pd.DataFrame) -> pd.DataFrame:
    """Execute complete dataset cleaning and tabular standardization.

    Pipeline operations:
        1. Remove duplicate observations.
        2. Extract horizontal and vertical resolution components.
        3. Extract display hardware flags (Touchscreen, IPS Panel).
        4. Parse compound storage configurations into discrete numeric columns.
        5. Normalize operating system labels.
        6. Standardize column identifiers.

    Args:
        df: Raw laptop specifications DataFrame.

    Returns:
        pd.DataFrame: Cleaned and structured DataFrame ready for feature engineering.
    """
    cleaned = df.copy().drop_duplicates()

    # Resolution parsing
    res_tuples = cleaned["ScreenResolution"].apply(parse_resolution)
    cleaned["res_x"] = res_tuples.apply(lambda r: r[0])
    cleaned["res_y"] = res_tuples.apply(lambda r: r[1])

    # Display flags
    cleaned["is_touchscreen"] = cleaned["ScreenResolution"].apply(
        lambda val: 1 if has_feature_in_screen(val, "Touchscreen") else 0
    )
    cleaned["is_ips"] = cleaned["ScreenResolution"].apply(
        lambda val: 1 if has_feature_in_screen(val, "IPS") else 0
    )

    # Storage decomposition
    storage_df = cleaned["Memory"].apply(parse_memory).apply(pd.Series)
    cleaned = pd.concat([cleaned, storage_df], axis=1)

    # Operating system normalization
    cleaned["os_clean"] = cleaned["OpSys"].apply(normalize_os)

    # Primary storage categorization
    def identify_primary_storage(mem_str: str) -> str:
        lower = str(mem_str).lower()
        if "ssd" in lower:
            return "SSD"
        if "hdd" in lower:
            return "HDD"
        if "flash" in lower:
            return "Flash"
        return "Hybrid"

    cleaned["primary_storage_type"] = cleaned["Memory"].apply(identify_primary_storage)

    # Standardize column naming conventions
    column_renames = {
        "Company": "brand",
        "TypeName": "type_name",
        "Inches": "screen_size",
        "CPU_Company": "cpu_brand",
        "CPU_Type": "cpu_type",
        "CPU_Frequency (GHz)": "cpu_freq_ghz",
        "RAM (GB)": "ram_gb",
        "GPU_Company": "gpu_brand",
        "GPU_Type": "gpu_type",
        "Weight (kg)": "weight_kg",
        "Price (Euro)": "price",
    }
    cleaned = cleaned.rename(columns=column_renames)

    # Prune superseded columns
    drop_cols = ["ScreenResolution", "Memory", "OpSys", "Product"]
    existing_drops = [c for c in drop_cols if c in cleaned.columns]
    cleaned = cleaned.drop(columns=existing_drops)

    return cleaned

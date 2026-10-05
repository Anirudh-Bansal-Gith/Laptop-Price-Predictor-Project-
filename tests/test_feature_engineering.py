"""Unit tests for feature engineering transformations."""

import pandas as pd
import pytest

from src.data.feature_engineering import (
    classify_cpu_tier,
    compute_ppi,
    engineer_features,
    get_feature_columns,
)


class TestComputePPI:
    def test_standard_fhd_15_6(self):
        ppi = compute_ppi(1920, 1080, 15.6)
        assert 140.0 < ppi < 143.0

    def test_uhd_4k_15_6(self):
        ppi = compute_ppi(3840, 2160, 15.6)
        assert 280.0 < ppi < 285.0

    def test_boundary_zero_screen(self):
        assert compute_ppi(1920, 1080, 0.0) == 0.0


class TestCpuClassification:
    def test_intel_tiers(self):
        assert classify_cpu_tier("Core i9 12900H") == "i9"
        assert classify_cpu_tier("Core i7 8550U") == "i7"
        assert classify_cpu_tier("Core i5 7200U") == "i5"
        assert classify_cpu_tier("Core i3 6006U") == "i3"
        assert classify_cpu_tier("Celeron N3350") == "Budget"

    def test_amd_tiers(self):
        assert classify_cpu_tier("Ryzen 7 5800H") == "AMD_Performance"
        assert classify_cpu_tier("A9-Series 9420") == "AMD_Budget"


class TestFeatureGrouping:
    def test_columns_contract(self):
        groups = get_feature_columns()
        assert "numeric" in groups
        assert "categorical" in groups
        assert "ram_gb" in groups["numeric"]
        assert "ppi" in groups["numeric"]
        assert "brand" in groups["categorical"]

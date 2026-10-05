"""Unit tests for data parsing and cleaning functions."""

import pandas as pd
import pytest

from src.data.cleaning import (
    clean_laptop_data,
    has_feature_in_screen,
    normalize_os,
    parse_memory,
    parse_resolution,
)


class TestParseResolution:
    def test_standard_hd_resolution(self):
        assert parse_resolution("1366x768") == (1366, 768)

    def test_full_hd_string(self):
        assert parse_resolution("Full HD 1920x1080") == (1920, 1080)

    def test_ips_retina_display(self):
        assert parse_resolution("IPS Panel Retina Display 2560x1600") == (2560, 1600)

    def test_touchscreen_embedded(self):
        assert parse_resolution("Full HD / Touchscreen 1920x1080") == (1920, 1080)

    def test_invalid_string(self):
        assert parse_resolution("Unspecified") == (0, 0)


class TestParseMemory:
    def test_single_ssd_allocation(self):
        result = parse_memory("256GB SSD")
        assert result["ssd_gb"] == 256
        assert result["hdd_gb"] == 0
        assert result["total_storage_gb"] == 256

    def test_single_hdd_allocation(self):
        result = parse_memory("500GB HDD")
        assert result["hdd_gb"] == 500
        assert result["total_storage_gb"] == 500

    def test_hybrid_ssd_and_hdd(self):
        result = parse_memory("128GB SSD +  1TB HDD")
        assert result["ssd_gb"] == 128
        assert result["hdd_gb"] == 1000
        assert result["total_storage_gb"] == 1128

    def test_terabyte_conversion(self):
        result = parse_memory("1TB HDD")
        assert result["hdd_gb"] == 1000

    def test_flash_memory(self):
        result = parse_memory("128GB Flash Storage")
        assert result["flash_gb"] == 128

    def test_hybrid_drive(self):
        result = parse_memory("1.0TB Hybrid")
        assert result["hybrid_gb"] == 1000


class TestNormalizeOS:
    def test_windows_variants(self):
        assert normalize_os("Windows 10") == "Windows"
        assert normalize_os("Windows 10 S") == "Windows"

    def test_macos_variants(self):
        assert normalize_os("macOS") == "macOS"
        assert normalize_os("Mac OS X") == "macOS"

    def test_linux(self):
        assert normalize_os("Linux") == "Linux/Other"

    def test_no_os(self):
        assert normalize_os("No OS") == "No OS/Other"


class TestHasFeature:
    def test_feature_detection(self):
        assert has_feature_in_screen("Full HD / Touchscreen 1920x1080", "Touchscreen")
        assert not has_feature_in_screen("Full HD 1920x1080", "Touchscreen")
        assert has_feature_in_screen("IPS Panel Full HD 1920x1080", "IPS")


class TestCleanLaptopData:
    @pytest.fixture
    def mock_raw_df(self):
        return pd.DataFrame({
            "Company": ["Dell", "HP"],
            "Product": ["XPS 13", "Pavilion"],
            "TypeName": ["Ultrabook", "Notebook"],
            "Inches": [13.3, 15.6],
            "ScreenResolution": ["IPS Panel Full HD 1920x1080", "1366x768"],
            "CPU_Company": ["Intel", "AMD"],
            "CPU_Type": ["Core i7", "A9-Series"],
            "CPU_Frequency (GHz)": [2.8, 2.5],
            "RAM (GB)": [16, 8],
            "Memory": ["512GB SSD", "1TB HDD"],
            "GPU_Company": ["Intel", "AMD"],
            "GPU_Type": ["UHD Graphics", "Radeon R5"],
            "OpSys": ["Windows 10", "Linux"],
            "Weight (kg)": [1.2, 2.1],
            "Price (Euro)": [1299.0, 450.0],
        })

    def test_transformed_columns_present(self, mock_raw_df):
        cleaned = clean_laptop_data(mock_raw_df)
        assert "res_x" in cleaned.columns
        assert "res_y" in cleaned.columns
        assert "is_touchscreen" in cleaned.columns
        assert "ssd_gb" in cleaned.columns
        assert "os_clean" in cleaned.columns
        assert "ScreenResolution" not in cleaned.columns

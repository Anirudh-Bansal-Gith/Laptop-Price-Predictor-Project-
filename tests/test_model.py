"""Unit tests for model inference inputs and transformations."""

import pandas as pd
import pytest

from src.models.predict import prepare_input


class TestPrepareInput:
    def test_single_record_dataframe_output(self):
        sample = {
            "brand": "Dell",
            "processor_brand": "Intel",
            "processor_name": "Core i7",
            "ram_gb": 16,
            "storage_gb": 512,
            "storage_type": "SSD",
            "gpu_brand": "Nvidia",
            "screen_size": 15.6,
            "resolution_x": 1920,
            "resolution_y": 1080,
            "is_touchscreen": False,
            "os": "Windows",
        }
        df_out = prepare_input(sample)
        assert isinstance(df_out, pd.DataFrame)
        assert len(df_out) == 1
        assert "ppi" in df_out.columns
        assert df_out.iloc[0]["ppi"] > 0
        assert df_out.iloc[0]["cpu_tier"] == "i7"
        assert df_out.iloc[0]["has_dedicated_gpu"] == 1

"""Pydantic request and response schemas for FastAPI API contracts.

Defines strict type boundaries, default ranges, and validation constraints
for client-provided laptop specifications and inference output payloads.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class LaptopFeatures(BaseModel):
    """Input payload representing laptop specifications for valuation."""

    brand: str = Field(
        ...,
        description="Laptop brand or manufacturer",
        examples=["Dell", "HP", "Apple", "Lenovo", "Asus"],
    )
    processor_brand: str = Field(
        ...,
        description="CPU manufacturer",
        examples=["Intel", "AMD"],
    )
    processor_name: str = Field(
        ...,
        description="Processor model name or family",
        examples=["Core i7", "Core i5", "Ryzen 5 5600H", "Core i9"],
    )
    ram_gb: int = Field(
        ...,
        ge=2,
        le=128,
        description="System memory in gigabytes (GB)",
        examples=[8, 16, 32],
    )
    storage_gb: int = Field(
        ...,
        ge=32,
        le=4000,
        description="Primary storage capacity in gigabytes (GB)",
        examples=[256, 512, 1024],
    )
    storage_type: str = Field(
        ...,
        description="Physical storage drive medium",
        examples=["SSD", "HDD"],
    )
    gpu_brand: str = Field(
        ...,
        description="Graphics processing unit brand",
        examples=["Nvidia", "Intel", "AMD"],
    )
    screen_size: float = Field(
        ...,
        ge=10.0,
        le=20.0,
        description="Display diagonal measurement in inches",
        examples=[13.3, 14.0, 15.6, 17.3],
    )
    resolution_x: int = Field(
        1920,
        ge=800,
        le=4096,
        description="Horizontal display resolution in pixels",
        examples=[1920, 2560, 3840],
    )
    resolution_y: int = Field(
        1080,
        ge=600,
        le=2400,
        description="Vertical display resolution in pixels",
        examples=[1080, 1440, 2160],
    )
    is_touchscreen: bool = Field(
        False,
        description="Presence of touchscreen digitizer hardware",
    )
    os: str = Field(
        "Windows",
        description="Pre-installed operating system",
        examples=["Windows", "macOS", "Linux"],
    )
    type_name: str = Field(
        "Notebook",
        description="Chassis form factor category",
        examples=["Notebook", "Ultrabook", "Gaming", "2 in 1 Convertible", "Workstation"],
    )
    weight_kg: float = Field(
        2.0,
        ge=0.5,
        le=6.0,
        description="Device mass in kilograms",
        examples=[1.37, 2.1],
    )
    cpu_freq_ghz: float = Field(
        2.5,
        ge=0.5,
        le=5.5,
        description="Base processor clock speed in GHz",
        examples=[2.3, 2.8],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
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
                "type_name": "Notebook",
                "weight_kg": 2.1,
                "cpu_freq_ghz": 2.8,
            }
        }
    }


class PricePrediction(BaseModel):
    """Response payload containing model valuation and metadata."""

    predicted_price: float = Field(
        ...,
        description="Estimated market price in specified currency units",
    )
    currency: str = Field(
        "EUR",
        description="Standard ISO currency identifier",
    )
    formatted_price: str = Field(
        ...,
        description="Human-readable formatted currency string with symbol",
    )


class HealthResponse(BaseModel):
    """Diagnostic response model reporting service operational status."""

    status: str = Field("ok", description="Server status indicator")
    model_loaded: bool = Field(False, description="Whether ML model pipeline is active in memory")

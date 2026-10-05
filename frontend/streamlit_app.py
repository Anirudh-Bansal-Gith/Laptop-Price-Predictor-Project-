"""Streamlit interactive dashboard for laptop price estimation.

Provides a rapid exploratory frontend for testing predictions against
the FastAPI microservice or verifying model inference manually.
"""

import streamlit as st
import requests

# Layout and page configuration
st.set_page_config(
    page_title="Laptop Price Predictor",
    layout="wide",
)

st.title("Laptop Price Predictor")
st.caption("Machine learning system estimating hardware market valuation.")

# Backend API URL resolution
API_ENDPOINT = "http://localhost:8000/api/v1/predict"
HEALTH_ENDPOINT = "http://localhost:8000/health"

# Diagnostics check
try:
    health_resp = requests.get(HEALTH_ENDPOINT, timeout=2)
    if health_resp.status_code == 200:
        health_payload = health_resp.json()
        if health_payload.get("model_loaded"):
            st.success("API status: Online | Model status: Loaded")
        else:
            st.warning("API status: Online | Model status: Not Loaded (Run training first)")
    else:
        st.error("API status: Unhealthy response code")
except requests.exceptions.RequestException:
    st.warning("FastAPI backend is offline. Launch via: uvicorn api.main:app --port 8000")

st.divider()

col_brand, col_specs, col_hardware = st.columns(3)

with col_brand:
    st.subheader("Brand and Form Factor")
    brand = st.selectbox(
        "Manufacturer",
        ["Acer", "Apple", "Asus", "Dell", "HP", "Lenovo", "MSI", "Microsoft", "Razer", "Samsung", "Toshiba", "Other"],
    )
    type_name = st.selectbox(
        "Chassis Type",
        ["Notebook", "Ultrabook", "Gaming", "2 in 1 Convertible", "Workstation", "Netbook"],
    )
    os_choice = st.selectbox("Operating System", ["Windows", "macOS", "Linux"])
    weight_kg = st.slider("Weight (kg)", 0.5, 5.0, 2.0, 0.1)

with col_specs:
    st.subheader("Processor and RAM")
    processor_brand = st.selectbox("CPU Manufacturer", ["Intel", "AMD"])
    processor_name = st.selectbox(
        "CPU Model Family",
        ["Core i3", "Core i5", "Core i7", "Core i9", "Celeron", "Pentium", "Ryzen 3", "Ryzen 5", "Ryzen 7", "Ryzen 9", "A9-Series"],
    )
    cpu_freq = st.slider("Clock Speed (GHz)", 0.5, 5.0, 2.5, 0.1)
    ram_gb = st.selectbox("RAM (GB)", [4, 8, 12, 16, 24, 32, 64], index=1)

with col_hardware:
    st.subheader("Storage and Display")
    storage_gb = st.selectbox("Storage Capacity (GB)", [128, 256, 512, 1024, 2048], index=2)
    storage_type = st.selectbox("Drive Medium", ["SSD", "HDD"])
    gpu_brand = st.selectbox("GPU Silicon", ["Intel", "Nvidia", "AMD"])
    screen_size = st.selectbox("Diagonal Size (Inches)", [11.6, 12.5, 13.3, 14.0, 15.6, 17.3], index=4)
    resolution = st.selectbox("Resolution", ["1366x768", "1600x900", "1920x1080", "2560x1440", "2560x1600", "3840x2160"], index=2)
    res_x, res_y = map(int, resolution.split("x"))
    is_touchscreen = st.checkbox("Touchscreen Enabled")

st.divider()

if st.button("Calculate Market Valuation", type="primary", use_container_width=True):
    payload = {
        "brand": brand,
        "processor_brand": processor_brand,
        "processor_name": processor_name,
        "ram_gb": ram_gb,
        "storage_gb": storage_gb,
        "storage_type": storage_type,
        "gpu_brand": gpu_brand,
        "screen_size": screen_size,
        "resolution_x": res_x,
        "resolution_y": res_y,
        "is_touchscreen": is_touchscreen,
        "os": os_choice,
        "type_name": type_name,
        "weight_kg": weight_kg,
        "cpu_freq_ghz": cpu_freq,
    }

    try:
        with st.spinner("Executing valuation..."):
            response = requests.post(API_ENDPOINT, json=payload, timeout=5)

        if response.status_code == 200:
            result_data = response.json()
            col_metric1, col_metric2 = st.columns(2)
            with col_metric1:
                st.metric(label="Estimated Fair Value", value=result_data["formatted_price"])
            with col_metric2:
                st.metric(label="Currency Standard", value=result_data["currency"])
        else:
            st.error(f"Prediction failed with status {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as err:
        st.error(f"Connection failed: {err}")

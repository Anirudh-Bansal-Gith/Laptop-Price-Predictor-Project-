"use client";

import React, { useState } from "react";

interface PredictionFormProps {
  onPredict: (data: any) => Promise<void>;
  loading: boolean;
}

export default function PredictionForm({ onPredict, loading }: PredictionFormProps) {
  const [formData, setFormData] = useState({
    brand: "Dell",
    type_name: "Notebook",
    processor_brand: "Intel",
    processor_name: "Core i7",
    cpu_freq_ghz: 2.8,
    ram_gb: 16,
    storage_gb: 512,
    storage_type: "SSD",
    gpu_brand: "Nvidia",
    screen_size: 15.6,
    resolution: "1920x1080",
    is_touchscreen: false,
    os: "Windows",
    weight_kg: 2.0,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    if (type === "checkbox") {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData((prev) => ({ ...prev, [name]: checked }));
    } else if (name === "ram_gb" || name === "storage_gb") {
      setFormData((prev) => ({ ...prev, [name]: parseInt(value, 10) }));
    } else if (name === "screen_size" || name === "weight_kg" || name === "cpu_freq_ghz") {
      setFormData((prev) => ({ ...prev, [name]: parseFloat(value) }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const [res_x, res_y] = formData.resolution.split("x").map(Number);
    const payload = {
      brand: formData.brand,
      processor_brand: formData.processor_brand,
      processor_name: formData.processor_name,
      ram_gb: formData.ram_gb,
      storage_gb: formData.storage_gb,
      storage_type: formData.storage_type,
      gpu_brand: formData.gpu_brand,
      screen_size: formData.screen_size,
      resolution_x: res_x,
      resolution_y: res_y,
      is_touchscreen: formData.is_touchscreen,
      os: formData.os,
      type_name: formData.type_name,
      weight_kg: formData.weight_kg,
      cpu_freq_ghz: formData.cpu_freq_ghz,
    };
    onPredict(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Manufacturer
          </label>
          <select
            name="brand"
            value={formData.brand}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {["Acer", "Apple", "Asus", "Dell", "HP", "Lenovo", "MSI", "Microsoft", "Razer", "Samsung", "Toshiba"].map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Form Factor
          </label>
          <select
            name="type_name"
            value={formData.type_name}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {["Notebook", "Ultrabook", "Gaming", "2 in 1 Convertible", "Workstation", "Netbook"].map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            CPU Manufacturer
          </label>
          <select
            name="processor_brand"
            value={formData.processor_brand}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="Intel">Intel</option>
            <option value="AMD">AMD</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Processor Tier
          </label>
          <select
            name="processor_name"
            value={formData.processor_name}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {["Core i3", "Core i5", "Core i7", "Core i9", "Celeron", "Pentium", "Ryzen 3", "Ryzen 5", "Ryzen 7", "Ryzen 9", "A9-Series"].map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            System Memory (RAM)
          </label>
          <select
            name="ram_gb"
            value={formData.ram_gb}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {[4, 8, 12, 16, 24, 32, 64].map((r) => (
              <option key={r} value={r}>{r} GB</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Storage Configuration
          </label>
          <div className="flex gap-2">
            <select
              name="storage_gb"
              value={formData.storage_gb}
              onChange={handleChange}
              className="w-2/3 bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              {[128, 256, 512, 1024, 2048].map((s) => (
                <option key={s} value={s}>{s >= 1024 ? `${s / 1024} TB` : `${s} GB`}</option>
              ))}
            </select>
            <select
              name="storage_type"
              value={formData.storage_type}
              onChange={handleChange}
              className="w-1/3 bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="SSD">SSD</option>
              <option value="HDD">HDD</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Graphics Processing Unit (GPU)
          </label>
          <select
            name="gpu_brand"
            value={formData.gpu_brand}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="Intel">Intel Integrated</option>
            <option value="Nvidia">Nvidia GeForce</option>
            <option value="AMD">AMD Radeon</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Resolution
          </label>
          <select
            name="resolution"
            value={formData.resolution}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="1366x768">1366 x 768 (HD)</option>
            <option value="1600x900">1600 x 900 (HD+)</option>
            <option value="1920x1080">1920 x 1080 (FHD)</option>
            <option value="2560x1440">2560 x 1440 (QHD)</option>
            <option value="2560x1600">2560 x 1600 (Retina)</option>
            <option value="3840x2160">3840 x 2160 (4K UHD)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Diagonal Screen Size (Inches)
          </label>
          <select
            name="screen_size"
            value={formData.screen_size}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {[11.6, 12.5, 13.3, 14.0, 15.6, 17.3].map((size) => (
              <option key={size} value={size}>{size}&quot;</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Operating System
          </label>
          <select
            name="os"
            value={formData.os}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="Windows">Windows</option>
            <option value="macOS">macOS</option>
            <option value="Linux">Linux / Other</option>
          </select>
        </div>
      </div>

      <div className="flex items-center gap-3 pt-2">
        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            name="is_touchscreen"
            checked={formData.is_touchscreen}
            onChange={handleChange}
            className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
          />
          Touchscreen Display
        </label>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 px-4 rounded-lg font-medium text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 transition"
      >
        {loading ? "Computing Prediction..." : "Estimate Market Price"}
      </button>
    </form>
  );
}

"use client";

import React, { useState } from "react";
import PredictionForm from "@/components/PredictionForm";
import ResultCard from "@/components/ResultCard";

export default function Home() {
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async (features: any) => {
    setLoading(true);
    setError(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      const response = await fetch(`${apiUrl}/api/v1/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(features),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || `HTTP Error ${response.status}`);
      }

      const data = await response.json();
      setPrediction(data);
    } catch (err: any) {
      console.error("Inference request failed:", err);
      setError(err.message || "Unable to reach prediction backend. Ensure FastAPI service is listening on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col justify-between">
      <div>
        <header className="mb-8 border-b border-slate-800 pb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Laptop Market Valuation Service
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Machine learning inference platform for hardware specification pricing.
            </p>
          </div>
          <div>
            <span className="inline-flex items-center px-3 py-1 rounded text-xs font-medium bg-slate-900 text-slate-300 border border-slate-700">
              Microservice Architecture: FastAPI + Next.js
            </span>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <div className="lg:col-span-7 bg-slate-900/60 border border-slate-800 p-6 rounded-xl shadow-lg">
            <h2 className="text-lg font-semibold text-slate-100 mb-4">
              Hardware Specification Input
            </h2>
            <PredictionForm onPredict={handlePredict} loading={loading} />
          </div>

          <div className="lg:col-span-5 space-y-6">
            <ResultCard prediction={prediction} loading={loading} error={error} />

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-xs text-slate-400">
              <h3 className="text-slate-200 font-semibold mb-3">Pipeline Specifications</h3>
              <ul className="space-y-2">
                <li className="flex justify-between py-1 border-b border-slate-800">
                  <span>Display Density Formula:</span>
                  <span className="text-slate-200 font-mono">sqrt(x^2 + y^2) / inches</span>
                </li>
                <li className="flex justify-between py-1 border-b border-slate-800">
                  <span>Regression Estimators:</span>
                  <span className="text-slate-200 font-mono">XGBRegressor, RandomForestRegressor</span>
                </li>
                <li className="flex justify-between py-1 border-b border-slate-800">
                  <span>Feature Transforms:</span>
                  <span className="text-slate-200 font-mono">StandardScaler, OneHotEncoder</span>
                </li>
                <li className="flex justify-between py-1">
                  <span>API Protocol:</span>
                  <span className="text-slate-200 font-mono">REST JSON (OpenAPI v3)</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <footer className="mt-16 pt-6 border-t border-slate-800 text-center text-xs text-slate-500">
        <p>Laptop Price Predictor Starter Scaffold. Open source project repository.</p>
      </footer>
    </main>
  );
}

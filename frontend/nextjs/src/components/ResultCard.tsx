"use client";

import React from "react";

interface ResultCardProps {
  prediction: {
    predicted_price: number;
    currency: string;
    formatted_price: string;
  } | null;
  loading: boolean;
  error: string | null;
}

export default function ResultCard({ prediction, loading, error }: ResultCardProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 flex flex-col items-center justify-center min-h-[260px]">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent mb-4"></div>
        <p className="text-sm text-slate-400 font-medium">Computing inference through ML regression pipeline...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-900/40 bg-rose-950/20 p-6 flex flex-col items-center justify-center min-h-[260px] text-center">
        <h3 className="text-base font-semibold text-rose-300 mb-2">Inference Error</h3>
        <p className="text-xs text-rose-400/80 max-w-sm">{error}</p>
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/30 p-8 flex flex-col items-center justify-center min-h-[260px] text-center">
        <h3 className="text-base font-semibold text-slate-300 mb-1">Awaiting Specifications</h3>
        <p className="text-xs text-slate-500 max-w-xs">
          Select target configuration attributes on the left and submit to generate market price estimate.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-indigo-500/30 bg-slate-900/90 p-8 shadow-xl relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Inference Successful
        </span>
        <span className="text-xs text-slate-400">Currency: {prediction.currency}</span>
      </div>

      <div className="mb-6">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
          Estimated Market Valuation
        </div>
        <div className="text-4xl font-bold text-white tracking-tight">
          {prediction.formatted_price}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-800 text-xs text-slate-400">
        <div className="bg-slate-950 p-3 rounded border border-slate-800">
          <div className="text-slate-500 font-medium">Model Backend</div>
          <div className="font-semibold text-slate-200 mt-0.5">XGBoost / Random Forest</div>
        </div>
        <div className="bg-slate-950 p-3 rounded border border-slate-800">
          <div className="text-slate-500 font-medium">Target Standard</div>
          <div className="font-semibold text-slate-200 mt-0.5">European Market (EUR)</div>
        </div>
      </div>
    </div>
  );
}

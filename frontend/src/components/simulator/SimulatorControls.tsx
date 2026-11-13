"use client";

import { useState } from "react";
import { Play, Pause, RotateCcw, Zap } from "lucide-react";
import { SimulatorStatus } from "@/types/simulator";
import { simulatorService } from "@/services/simulatorService";

const SPEEDS = [1, 5, 10, 30, 60];

interface SimulatorControlsProps {
  status: SimulatorStatus | null;
  onStatusChange?: (s: SimulatorStatus) => void;
}

export function SimulatorControls({ status, onStatusChange }: SimulatorControlsProps) {
  const [loading, setLoading] = useState(false);
  const state = status?.state ?? "IDLE";

  async function call(fn: () => Promise<SimulatorStatus>) {
    setLoading(true);
    try {
      const s = await fn();
      onStatusChange?.(s);
    } catch (e) {
      console.error("Simulator operation failed:", e);
    } finally {
      setLoading(false);
    }
  }

  const stateColors: Record<string, string> = {
    IDLE: "text-slate-400 border-slate-700 bg-slate-800/40",
    RUNNING: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
    PAUSED: "text-amber-400 border-amber-500/30 bg-amber-500/10",
    COMPLETED: "text-sky-400 border-sky-500/30 bg-sky-500/10",
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">Transaction Replay Simulator</h3>
          <p className="text-xs text-slate-400 mt-0.5">Stream historic transactions in real-time</p>
        </div>
        <span
          className={`px-2.5 py-1 rounded text-xs font-mono font-bold border ${
            stateColors[state] || stateColors.IDLE
          }`}
        >
          {state}
        </span>
      </div>

      {/* Progress info */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-slate-400 font-mono">
          <span>Processed: {status ? status.processed_count.toLocaleString("en-IN") : "0"}</span>
          <span>Total: {status ? status.total_count.toLocaleString("en-IN") : "0"}</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-500 transition-all duration-300"
            style={{ width: `${status?.progress_percentage ?? 0}%` }}
          />
        </div>
        <div className="text-right text-[11px] text-slate-500 font-mono">
          {status?.progress_percentage.toFixed(1) ?? "0.0"}% completed
        </div>
      </div>

      {/* Buttons & speed */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-800/80">
        <div className="flex items-center gap-2">
          {state !== "RUNNING" ? (
            <button
              onClick={() => call(simulatorService.start)}
              disabled={loading || state === "COMPLETED"}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600/20 text-emerald-300 
                border border-emerald-500/30 text-xs font-semibold hover:bg-emerald-600/30 
                disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <Play size={13} /> Start Replay
            </button>
          ) : (
            <button
              onClick={() => call(simulatorService.pause)}
              disabled={loading}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-amber-600/20 text-amber-300
                border border-amber-500/30 text-xs font-semibold hover:bg-amber-600/30
                disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <Pause size={13} /> Pause
            </button>
          )}

          <button
            onClick={() => call(simulatorService.reset)}
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-300
              border border-slate-700 text-xs font-semibold hover:bg-slate-700
              disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <RotateCcw size={13} /> Reset
          </button>
        </div>

        {/* Speed Selector */}
        <div className="flex items-center gap-1.5">
          <Zap size={13} className="text-amber-400" />
          <span className="text-xs text-slate-400 mr-1">Speed:</span>
          <div className="flex gap-1">
            {SPEEDS.map((s) => (
              <button
                key={s}
                onClick={() => call(() => simulatorService.setSpeed(s))}
                disabled={loading}
                className={`px-2 py-0.5 rounded text-xs font-mono border transition-colors ${
                  status?.speed_multiplier === s
                    ? "bg-indigo-600/30 text-indigo-300 border-indigo-500/50"
                    : "bg-slate-800 text-slate-400 border-slate-700 hover:border-slate-500"
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

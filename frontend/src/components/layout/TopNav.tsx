"use client";

import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Menu, RefreshCw, Terminal } from "lucide-react";
import { StatusDot } from "@/components/ui/StatusDot";
import { healthService } from "@/services/healthService";
import { SystemHealthResponse } from "@/types/health";

interface TopNavProps {
  onToggleMobileNav?: () => void;
}

export function TopNav({ onToggleMobileNav }: TopNavProps) {
  const pathname = usePathname();
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<boolean>(false);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const data = await healthService.getSystemHealth();
      setHealth(data);
      setError(false);
    } catch {
      setError(true);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // 30s heartbeat
    return () => clearInterval(interval);
  }, []);

  const getPageTitle = () => {
    if (pathname === "/") return "Platform Overview";
    if (pathname === "/transactions") return "Transaction Stream Monitoring";
    if (pathname === "/fraud") return "Supervised Fraud Detection";
    if (pathname === "/anomaly") return "Behavioral Anomaly Monitoring";
    if (pathname === "/aml") return "AML Typology & Graph Analysis";
    if (pathname === "/risk") return "Multi-Model Risk Assessment";
    if (pathname === "/alerts") return "Security Alerts & Incident Queue";
    if (pathname === "/analytics") return "Analytical Reports & Metrics";
    return "Financial Security Platform";
  };

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-4 lg:px-6 flex items-center justify-between z-20">
      {/* Left: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileNav}
          className="lg:hidden p-2 rounded-md text-slate-400 hover:text-slate-100 hover:bg-slate-900 focus:outline-none"
          aria-label="Toggle navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div>
          <h1 className="text-sm md:text-base font-semibold text-slate-100 tracking-tight">
            {getPageTitle()}
          </h1>
          <p className="text-[11px] text-slate-400 hidden sm:block">
            AI-Driven Transaction Surveillance & AML Intelligence
          </p>
        </div>
      </div>

      {/* Right: Telemetry & Status Badges */}
      <div className="flex items-center gap-3">
        {/* Backend Heartbeat */}
        <div className="flex items-center gap-2 rounded border border-slate-800 bg-slate-900/70 px-2.5 py-1 text-xs">
          <StatusDot
            status={error ? "unhealthy" : health?.status === "healthy" ? "healthy" : "warning"}
            pulse={health?.status === "healthy"}
          />
          <span className="font-mono text-[11px] text-slate-300 hidden sm:inline">
            {error
              ? "API Disconnected"
              : health?.status === "healthy"
              ? "API Online"
              : "Connecting..."}
          </span>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="text-slate-500 hover:text-slate-300 transition-colors ml-1"
            title="Refresh API Connection"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {/* Security Persona */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="h-7 w-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
            <Terminal className="h-3.5 w-3.5 text-sky-400" />
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-medium text-slate-200">Security Analyst</div>
            <div className="text-[10px] text-slate-400 font-mono">SOC Tier 2</div>
          </div>
        </div>
      </div>
    </header>
  );
}

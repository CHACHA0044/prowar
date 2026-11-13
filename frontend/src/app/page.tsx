"use client";

export const dynamic = "force-dynamic";

import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  Database,
  TrendingUp,
  Users,
  Activity,
  Server,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";
import {
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { StatusDot } from "@/components/ui/StatusDot";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { CountUp } from "@/components/ui/CountUp";
import { SimulatorControls } from "@/components/simulator/SimulatorControls";
import { LiveFeed } from "@/components/simulator/LiveFeed";
import { useSimulatorStream } from "@/hooks/useSimulatorStream";
import { useDatasetSummary } from "@/hooks/useDatasetSummary";
import { datasetService } from "@/services/datasetService";
import { healthService } from "@/services/healthService";
import { formatNumber } from "@/lib/format";
import { DatasetStatusResponse } from "@/types/dataset";
import { SimulatorStatus } from "@/types/simulator";
import { SystemHealthResponse, DatabaseHealthResponse } from "@/types/health";

const CHANNEL_COLORS = [
  "#6366f1",
  "#06b6d4",
  "#10b981",
  "#8b5cf6",
  "#f59e0b",
  "#ec4899",
  "#f97316",
  "#14b8a6",
];

export default function OverviewPage() {
  const { data: summary, loading: summaryLoading } = useDatasetSummary();
  const { events: streamEvents, status: streamStatus, isConnected } = useSimulatorStream();
  const [simulatorStatus, setSimulatorStatus] = useState<SimulatorStatus | null>(null);
  const [dsStatus, setDsStatus] = useState<DatasetStatusResponse | null>(null);
  const [sysHealth, setSysHealth] = useState<SystemHealthResponse | null>(null);
  const [dbHealth, setDbHealth] = useState<DatabaseHealthResponse | null>(null);

  useEffect(() => {
    if (streamStatus) setSimulatorStatus(streamStatus);
  }, [streamStatus]);

  useEffect(() => {
    async function init() {
      const [ds, sys, db] = await Promise.allSettled([
        datasetService.getStatus(),
        healthService.getSystemHealth(),
        healthService.getDatabaseHealth(),
      ]);
      if (ds.status === "fulfilled") setDsStatus(ds.value);
      if (sys.status === "fulfilled") setSysHealth(sys.value);
      if (db.status === "fulfilled") setDbHealth(db.value);
    }
    init();
  }, []);

  const totalVolumeCr = summary ? summary.total_volume_inr / 10000000 : 0;
  const avgTxnK = summary ? summary.avg_transaction_inr / 1000 : 0;

  const kpis = [
    {
      label: "Total Ingested Transactions",
      value: summary?.total_transactions ?? 0,
      icon: Activity,
      color: "text-indigo-400",
      spotlight: "rgba(99, 102, 241, 0.15)",
      prefix: "",
      suffix: "",
      decimals: 0,
    },
    {
      label: "Cumulative Volume (INR)",
      value: totalVolumeCr,
      icon: TrendingUp,
      color: "text-emerald-400",
      spotlight: "rgba(16, 185, 129, 0.15)",
      prefix: "₹",
      suffix: " Cr",
      decimals: 2,
    },
    {
      label: "Distinct Account Entities",
      value: summary?.unique_accounts_total ?? 0,
      icon: Users,
      color: "text-sky-400",
      spotlight: "rgba(6, 182, 212, 0.15)",
      prefix: "",
      suffix: "",
      decimals: 0,
    },
    {
      label: "Average Transaction Size",
      value: avgTxnK,
      icon: Database,
      color: "text-violet-400",
      spotlight: "rgba(139, 92, 246, 0.15)",
      prefix: "₹",
      suffix: " K",
      decimals: 1,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Platform Banner */}
      <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 p-6 shadow-subtle">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <ShieldAlert className="text-red-400" size={20} />
              <Badge variant="safe">PHASE 2 OPERATIONAL</Badge>
              <span className="text-xs text-slate-400 font-mono">
                Sentinel.AML · Dataset & Real-Time Surveillance Engine
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              Financial Fraud Detection & AML Command Center
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              High-throughput surveillance pipeline monitoring synthetic core banking and payment
              streams. Ground-truth evaluation metadata is strictly segregated from operational
              scoring.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            {dsStatus && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950/60">
                <StatusDot
                  status={dsStatus.import_status === "COMPLETED" ? "healthy" : "warning"}
                />
                <span className="text-xs font-mono text-slate-300">
                  Dataset: {dsStatus.import_status} ({dsStatus.imported_rows.toLocaleString()} rows)
                </span>
              </div>
            )}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950/60">
              <StatusDot status={sysHealth ? "healthy" : "unhealthy"} />
              <span className="text-xs font-mono text-slate-300">
                Backend: {sysHealth ? sysHealth.status : "Offline"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => (
          <SpotlightCard key={kpi.label} spotlightColor={kpi.spotlight} className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                {kpi.label}
              </span>
              <kpi.icon size={18} className={kpi.color} />
            </div>
            <div className={`text-2xl font-bold font-mono ${kpi.color}`}>
              {summaryLoading ? (
                <span className="text-slate-600 animate-pulse">Loading…</span>
              ) : (
                <CountUp
                  to={kpi.value}
                  prefix={kpi.prefix}
                  suffix={kpi.suffix}
                  decimals={kpi.decimals}
                  separator=","
                />
              )}
            </div>
          </SpotlightCard>
        ))}
      </div>

      {/* Recharts Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Volume AreaChart */}
        <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Daily Transaction Volume</h2>
              <p className="text-xs text-slate-400">Time-series distribution across observation window</p>
            </div>
            <Link
              href="/analytics"
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
            >
              Full Analytics <ArrowRight size={12} />
            </Link>
          </div>

          {summaryLoading ? (
            <div className="h-56 flex items-center justify-center text-xs text-slate-500">
              Loading chart data…
            </div>
          ) : (
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={summary?.daily_volume ?? []}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: "#64748b", fontSize: 10 }}
                    tickLine={false}
                    interval={6}
                  />
                  <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#090d16",
                      borderColor: "#1e293b",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: "#f8fafc",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="#6366f1"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorCount)"
                    name="Transactions"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Channel Distribution PieChart */}
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-slate-200">Channel Distribution</h2>
            <p className="text-xs text-slate-400">Payment mechanism share</p>
          </div>

          {summaryLoading ? (
            <div className="h-56 flex items-center justify-center text-xs text-slate-500">
              Loading distribution…
            </div>
          ) : (
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={summary?.channel_distribution ?? []}
                    cx="50%"
                    cy="45%"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={3}
                    dataKey="count"
                    nameKey="channel"
                  >
                    {(summary?.channel_distribution ?? []).map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CHANNEL_COLORS[index % CHANNEL_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#090d16",
                      borderColor: "#1e293b",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: "#f8fafc",
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    iconSize={8}
                    wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Simulator & Live Feed Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SimulatorControls status={simulatorStatus} onStatusChange={setSimulatorStatus} />
        <LiveFeed events={streamEvents} isConnected={isConnected} />
      </div>

      {/* Ground Truth Evaluation Metadata (Clearly Disclaimed) */}
      {summary && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle size={16} className="text-amber-400" />
              <h3 className="text-sm font-semibold text-amber-300">
                Synthetic Dataset Evaluation Metadata
              </h3>
            </div>
            <Badge variant="warning">GROUND TRUTH LABELS — NOT MODEL DETECTIONS</Badge>
          </div>

          <p className="text-xs text-slate-400 mb-4">
            The dataset includes verified ground-truth labels designed for supervised ML evaluation,
            unsupervised anomaly benchmarking, and AML graph validation in Phase 3+. These labels
            remain strictly segregated from production transaction inference endpoints.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase font-medium">Evaluated Rows</span>
              <p className="text-base font-bold font-mono text-slate-100 mt-0.5">
                {formatNumber(summary.ground_truth_evaluation.total_evaluated_rows)}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase font-medium">Fraud Labels</span>
              <p className="text-base font-bold font-mono text-red-400 mt-0.5">
                {formatNumber(summary.ground_truth_evaluation.ground_truth_fraud_count)}{" "}
                <span className="text-xs font-normal text-slate-500">
                  ({summary.ground_truth_evaluation.ground_truth_fraud_rate.toFixed(2)}%)
                </span>
              </p>
            </div>
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase font-medium">AML Patterns</span>
              <p className="text-base font-bold font-mono text-amber-400 mt-0.5">
                {formatNumber(summary.ground_truth_evaluation.ground_truth_aml_count)}{" "}
                <span className="text-xs font-normal text-slate-500">
                  ({summary.ground_truth_evaluation.ground_truth_aml_rate.toFixed(2)}%)
                </span>
              </p>
            </div>
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase font-medium">Edge Cases</span>
              <p className="text-base font-bold font-mono text-sky-400 mt-0.5">
                {formatNumber(summary.ground_truth_evaluation.ground_truth_edge_cases_count)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* System & Database Health */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Server size={15} className="text-indigo-400" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
              FastAPI Service Health
            </h3>
          </div>
          <div className="space-y-1 text-xs text-slate-400 font-mono">
            <div className="flex justify-between">
              <span>Status:</span>
              <span className="text-emerald-400 font-bold">{sysHealth?.status ?? "Offline"}</span>
            </div>
            <div className="flex justify-between">
              <span>Environment:</span>
              <span>{sysHealth?.environment ?? "development"}</span>
            </div>
            <div className="flex justify-between">
              <span>Engine Version:</span>
              <span>{sysHealth?.version ?? "v0.1.0"}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Database size={15} className="text-emerald-400" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
              Database Connectivity
            </h3>
          </div>
          <div className="space-y-1 text-xs text-slate-400 font-mono">
            <div className="flex justify-between">
              <span>Dialect:</span>
              <span className="text-slate-200">{dbHealth?.dialect ?? "SQLite"}</span>
            </div>
            <div className="flex justify-between">
              <span>Connection Pool:</span>
              <span className="text-emerald-400 font-bold">
                {dbHealth?.connected ? "ACTIVE" : "RECONNECTING"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Dataset Scope:</span>
              <span>{dsStatus ? `${dsStatus.imported_rows.toLocaleString()} txns` : "Ready"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

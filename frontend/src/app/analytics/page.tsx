"use client";

export const dynamic = "force-dynamic";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useDatasetSummary } from "@/hooks/useDatasetSummary";
import { formatNumber } from "@/lib/format";
import { AlertTriangle, Database, PieChart as PieIcon, BarChart2 } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

const BUCKET_COLORS = [
  "#6366f1",
  "#06b6d4",
  "#10b981",
  "#8b5cf6",
  "#f59e0b",
  "#ec4899",
];

export default function AnalyticsPage() {
  const { data: summary, loading, error } = useDatasetSummary();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 text-sm text-slate-500 font-mono">
        Aggregating analytics parameters across 129,675 dataset transactions…
      </div>
    );
  }

  if (error) {
    return <div className="text-center py-20 text-sm text-red-400">{error}</div>;
  }

  if (!summary) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Analytics & Distribution Intelligence</h1>
        <p className="text-sm text-slate-400">
          In-depth distribution histograms, merchant categorization, and ground-truth validation
          benchmarks.
        </p>
      </div>

      {/* Row 1: Amount Distribution & Merchant Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Amount Buckets */}
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <div className="flex items-center gap-2 mb-3">
            <BarChart2 size={16} className="text-indigo-400" />
            <h2 className="text-sm font-semibold text-slate-200">Amount Bracket Distribution</h2>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Volume segmentation across INR transaction sizes
          </p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={summary.amount_buckets}
                margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="bucket" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} />
                <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#090d16",
                    borderColor: "#1e293b",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "#f8fafc",
                  }}
                  formatter={(value: any) => [formatNumber(Number(value) || 0), "Transactions"]}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {summary.amount_buckets.map((_, i) => (
                    <Cell key={i} fill={BUCKET_COLORS[i % BUCKET_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Merchant Category Breakdown */}
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <div className="flex items-center gap-2 mb-3">
            <PieIcon size={16} className="text-cyan-400" />
            <h2 className="text-sm font-semibold text-slate-200">Category Segmentation</h2>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Top transaction purposes & merchant categories
          </p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={summary.category_distribution.slice(0, 8)}
                layout="vertical"
                margin={{ top: 5, right: 15, left: 40, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fill: "#64748b", fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="category"
                  tick={{ fill: "#94a3b8", fontSize: 10 }}
                  tickLine={false}
                  width={75}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#090d16",
                    borderColor: "#1e293b",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "#f8fafc",
                  }}
                  formatter={(value: any) => [formatNumber(Number(value) || 0), "Count"]}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} fill="#06b6d4" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Row 2: Metadata Coverage Assessment */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <div className="flex items-center gap-2 mb-2">
          <Database size={16} className="text-emerald-400" />
          <h2 className="text-sm font-semibold text-slate-200">Dataset Metadata Completeness</h2>
        </div>
        <p className="text-xs text-slate-400 mb-4">
          Tracking unpopulated optional attributes (vital for realistic fraud feature engineering)
        </p>

        <div className="space-y-3 font-mono">
          {Object.entries(summary.missing_metadata_counts).map(([field, count]) => {
            const pct = (count / summary.total_transactions) * 100;
            return (
              <div key={field} className="flex items-center gap-4 text-xs">
                <span className="text-slate-300 w-44">{field}</span>
                <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-500/70"
                    style={{ width: `${Math.min(100, pct)}%` }}
                  />
                </div>
                <span className="text-slate-400 w-24 text-right">
                  {formatNumber(count)} ({pct.toFixed(2)}%)
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Row 3: Ground Truth Evaluation Breakdown */}
      <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-400" />
            <h2 className="text-sm font-semibold text-amber-300">
              Ground Truth Pattern Breakdown
            </h2>
          </div>
          <Badge variant="warning">SYNTHETIC LABELS — NOT INFERRED DETECTION</Badge>
        </div>

        <p className="text-xs text-slate-400">
          The table below reflects synthetic label distribution embedded in the dataset for model
          validation. Operational fraud scoring will independently generate predictions in Phase
          3+.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="border-b border-amber-500/10 text-slate-400 text-left">
                <th className="pb-2 font-semibold">Pattern Typology</th>
                <th className="pb-2 font-semibold text-right">Count</th>
                <th className="pb-2 font-semibold text-right">Proportion</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {Object.entries(summary.ground_truth_evaluation.pattern_breakdown)
                .sort(([, a], [, b]) => b - a)
                .map(([pattern, count]) => (
                  <tr key={pattern} className="hover:bg-slate-800/30">
                    <td className="py-2.5 text-slate-200 capitalize">
                      {pattern.replace(/_/g, " ")}
                    </td>
                    <td className="py-2.5 text-right text-slate-300 font-bold">
                      {formatNumber(count)}
                    </td>
                    <td className="py-2.5 text-right text-slate-400">
                      {((count / summary.total_transactions) * 100).toFixed(2)}%
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

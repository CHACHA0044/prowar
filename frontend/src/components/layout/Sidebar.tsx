"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ArrowLeftRight,
  ShieldAlert,
  Activity,
  Network,
  Gauge,
  BellRing,
  BarChart3,
  ShieldCheck,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";

export const NAVIGATION_ITEMS = [
  {
    title: "Overview",
    href: "/",
    icon: LayoutDashboard,
    description: "System pulse & health telemetry",
  },
  {
    title: "Transactions",
    href: "/transactions",
    icon: ArrowLeftRight,
    description: "Real-time payment streaming",
  },
  {
    title: "Fraud Detection",
    href: "/fraud",
    icon: ShieldAlert,
    badge: "ML",
    description: "Supervised classification engine",
  },
  {
    title: "Anomaly Monitoring",
    href: "/anomaly",
    icon: Activity,
    badge: "IForest",
    description: "Unsupervised baseline deviation",
  },
  {
    title: "AML Investigation",
    href: "/aml",
    icon: Network,
    badge: "Graph",
    description: "Typology and cycle analysis",
  },
  {
    title: "Risk Analysis",
    href: "/risk",
    icon: Gauge,
    description: "Ensemble scoring & tiering",
  },
  {
    title: "Security Alerts",
    href: "/alerts",
    icon: BellRing,
    description: "Analyst case triage queue",
  },
  {
    title: "Reports & Analytics",
    href: "/analytics",
    icon: BarChart3,
    description: "Performance metrics & SAR exports",
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex flex-col w-64 border-r border-slate-800/80 bg-slate-950/90 text-slate-300 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-800/80">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-sm tracking-wide text-slate-100">
              SENTINEL<span className="text-sky-400">.AML</span>
            </span>
          </div>
          <p className="text-[10px] text-slate-400 tracking-wider uppercase font-mono">
            PromptWars 2026
          </p>
        </div>
      </div>

      {/* Nav Link List */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-mono uppercase tracking-wider text-slate-400">
          Navigation Modules
        </div>
        {NAVIGATION_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center justify-between rounded-md px-3 py-2 text-xs font-medium transition-all duration-150",
                isActive
                  ? "bg-slate-800/90 text-sky-400 font-semibold border-l-2 border-sky-400 shadow-subtle"
                  : "text-slate-300 hover:bg-slate-900 hover:text-slate-100"
              )}
            >
              <div className="flex items-center gap-2.5 truncate">
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0 transition-colors",
                    isActive ? "text-sky-400" : "text-slate-400 group-hover:text-slate-300"
                  )}
                />
                <span className="truncate">{item.title}</span>
              </div>

              <div className="flex items-center gap-1.5">
                {item.badge && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded font-mono bg-slate-800 text-slate-300 border border-slate-700/60">
                    {item.badge}
                  </span>
                )}
                {isActive && <ChevronRight className="h-3 w-3 text-sky-400" />}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Security Context Badge in Sidebar Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950">
        <div className="rounded border border-slate-800/70 bg-slate-900/60 p-2.5">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase">Environment</span>
            <Badge variant="safe">SYNTHETIC</Badge>
          </div>
          <p className="text-[11px] text-slate-400 leading-tight">
            Anonymized financial transactions dataset. No real customer PII.
          </p>
        </div>
      </div>
    </aside>
  );
}


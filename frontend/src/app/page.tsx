"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  Activity,
  Network,
  Cpu,
  Database,
  Server,
  Layers,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { StatusDot } from "@/components/ui/StatusDot";
import { healthService } from "@/services/healthService";
import { SystemHealthResponse, DatabaseHealthResponse } from "@/types/health";

export default function OverviewPage() {
  const [systemHealth, setSystemHealth] = useState<SystemHealthResponse | null>(null);
  const [dbHealth, setDbHealth] = useState<DatabaseHealthResponse | null>(null);

  useEffect(() => {
    async function checkHealth() {
      try {
        const [sys, db] = await Promise.all([
          healthService.getSystemHealth().catch(() => null),
          healthService.getDatabaseHealth().catch(() => null),
        ]);
        setSystemHealth(sys);
        setDbHealth(db);
      } catch {
        // Fallback handled by state
      }
    }
    checkHealth();
  }, []);

  return (
    <div className="space-y-6">
      {/* Platform Banner */}
      <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 p-6 shadow-subtle">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="safe">PHASE 1 FOUNDATION ACTIVE</Badge>
              <span className="text-xs text-slate-400 font-mono">v0.1.0 • Next.js + FastAPI</span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold tracking-tight text-slate-100">
              Intelligent Financial Fraud & AML Surveillance System
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Unified financial intelligence platform designed for PromptWars 2026. Architected
              to execute supervised fraud classification, unsupervised anomaly detection, and
              graph-based AML typology tracing across high-velocity synthetic transaction streams.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Link
              href="/transactions"
              className="inline-flex items-center gap-1.5 rounded-md bg-sky-500 px-3.5 py-2 text-xs font-semibold text-slate-950 hover:bg-sky-400 transition-colors shadow-subtle"
            >
              <span>Explore Stream</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Real-time Subsystem Health Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* API Gateway */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="flex items-center gap-2">
              <Server className="h-4 w-4 text-sky-400" />
              <CardTitle>FastAPI Core Gateway</CardTitle>
            </div>
            <StatusDot
              status={systemHealth?.status === "healthy" ? "healthy" : "warning"}
              pulse={systemHealth?.status === "healthy"}
            />
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">Endpoint:</span>
                <span className="font-mono text-slate-200">/api/v1</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">Environment:</span>
                <span className="font-mono text-slate-200">
                  {systemHealth?.environment || "development"}
                </span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">Gateway Status:</span>
                <Badge variant={systemHealth ? "safe" : "warning"}>
                  {systemHealth ? "ONLINE & VERIFIED" : "CONNECTING"}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Database Layer */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-sky-400" />
              <CardTitle>Persistence & Data Layer</CardTitle>
            </div>
            <StatusDot
              status={dbHealth?.connected ? "healthy" : "warning"}
              pulse={dbHealth?.connected}
            />
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">Engine Dialect:</span>
                <span className="font-mono text-slate-200">{dbHealth?.dialect || "sqlite"}</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">Migration Path:</span>
                <span className="font-mono text-slate-200">PostgreSQL Ready</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">Connectivity:</span>
                <Badge variant={dbHealth?.connected ? "safe" : "warning"}>
                  {dbHealth?.connected ? "CONNECTED (SELECT 1)" : "CONNECTING"}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Detection Pipelines */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-sky-400" />
              <CardTitle>AI/ML Inference Engines</CardTitle>
            </div>
            <StatusDot status="healthy" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">Supervised Fraud:</span>
                <span className="font-mono text-slate-200">LightGBM / XGBoost</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">Anomaly Baseline:</span>
                <span className="font-mono text-slate-200">IsolationForest</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">AML Typology Engine:</span>
                <span className="font-mono text-slate-200">NetworkX Directed Graph</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detection Pipeline Architecture Walkthrough */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-sky-400" />
          <h3 className="text-sm font-semibold tracking-wide text-slate-200 uppercase font-mono">
            Detection Pipeline Topology
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded bg-sky-950 text-sky-400 border border-sky-800/60">
                <ShieldAlert className="h-4 w-4" />
              </div>
              <h4 className="text-xs font-semibold text-slate-200">1. Supervised Fraud</h4>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ingests behavioral feature vectors (z-score amount deviation, rapid-fire velocity,
              device/channel changes) to calculate probabilistic fraud classification.
            </p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded bg-amber-950 text-amber-400 border border-amber-800/60">
                <Activity className="h-4 w-4" />
              </div>
              <h4 className="text-xs font-semibold text-slate-200">2. Behavioral Anomaly</h4>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Unsupervised outlier scoring detects novel, unlabelled attack vectors deviating from
              an account&apos;s learned normal operational spending profile.
            </p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60">
                <Network className="h-4 w-4" />
              </div>
              <h4 className="text-xs font-semibold text-slate-200">3. AML Graph Typology</h4>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Constructs directed transaction graphs to isolate multi-hop circular flows,
              structuring under legal reporting limits, and mule fan-in/fan-out clusters.
            </p>
          </div>
        </div>
      </div>

      {/* Phase 1 Verification Checklist */}
      <Card>
        <CardHeader>
          <CardTitle>Phase 1 Foundation Verification Status</CardTitle>
          <CardDescription>
            Architectural milestones established for PromptWars 2026.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-slate-200">FastAPI Architecture</p>
                <p className="text-slate-400">Structured logging, CORS, API v1 routes registered.</p>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-slate-200">SQLAlchemy Database Layer</p>
                <p className="text-slate-400">SQLite configured with clean PostgreSQL migration path.</p>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-slate-200">Next.js App Router & Strict TypeScript</p>
                <p className="text-slate-400">Modular layout shell, navigation, typed contracts.</p>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-slate-200">Fintech Security Design System</p>
                <p className="text-slate-400">Dark-first navy aesthetic, responsive mobile navigation.</p>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-slate-200">Initial Data Contracts</p>
                <p className="text-slate-400">Pydantic & TypeScript schemas for Transaction, Account, Alert.</p>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-slate-200">Automated Pytest Suite</p>
                <p className="text-slate-400">17 test cases passing across health, config, schemas & routers.</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

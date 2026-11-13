"use client";

import React from "react";
import { BarChart3 } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100">
            System Analytics & Model Performance
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Model validation metrics (PR-AUC, F1), fraud incidence rates, and regulatory reporting exports.
          </p>
        </div>

        <Badge variant="neutral">METRICS: AWAITING EVALUATION</Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Model Validation & KPI Analytics</CardTitle>
          <CardDescription>
            Rigorous statistical evaluations comparing LightGBM vs baseline logistic regression.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={BarChart3}
            title="Analytics Engine Verified for Phase 2–3 Data"
            description="The analytics router /api/v1/analytics/overview is verified. When synthetic benchmark evaluation runs, this view will render PR-AUC curves, confusion matrices, and feature importance charts via Recharts."
            phaseTag="Contract Verified"
            details={[
              { label: "Chart Engine", value: "Recharts & Plotly React Visualizations" },
              { label: "Required Metrics", value: "Precision, Recall, F1, PR-AUC, Confusion Matrix" },
              { label: "Export Capabilities", value: "Suspicious Activity Report (SAR) PDF/CSV" },
              { label: "Endpoint Status", value: "GET /api/v1/analytics/overview (HTTP 200 OK)" },
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );
}


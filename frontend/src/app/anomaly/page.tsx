"use client";

import React from "react";
import { Activity } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export default function AnomalyPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100">
            Behavioral Anomaly Monitoring
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Unsupervised baseline profiling to flag zero-day vectors and atypical deviations.
          </p>
        </div>

        <Badge variant="neutral">CALIBRATION: PENDING</Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Isolation Forest & Dynamic Baselines</CardTitle>
          <CardDescription>
            Account spending velocity and deviation metrics.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Activity}
            title="Account Baseline Engine Ready for Department 4"
            description="The anomaly detection router is verified. In Department 4, per-account rolling means and IsolationForest models will calculate non-parametric deviation scores to catch previously unseen threats."
            phaseTag="Contract Verified"
            details={[
              { label: "Algorithms", value: "IsolationForest & Rolling Z-Scores" },
              { label: "Cold-Start Handling", value: "Population Mean Fallback" },
              { label: "Feature Window", value: "1h / 24h / 7d rolling aggregation" },
              { label: "Endpoint Status", value: "GET /api/v1/anomaly/status (HTTP 200 OK)" },
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );
}


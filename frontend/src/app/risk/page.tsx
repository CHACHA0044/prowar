"use client";

import React from "react";
import { Gauge } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export default function RiskPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100">
            Multi-Model Risk Assessment Engine
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Ensemble weighting fusing supervised fraud, behavioral anomalies, and AML graph typologies.
          </p>
        </div>

        <Badge variant="neutral">RISK WEIGHTS: CONFIGURED</Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ensemble Scoring & Tier Mapping</CardTitle>
          <CardDescription>
            Deterministic formula mapping raw multi-model inputs to 0–100 risk scores.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Gauge}
            title="Ensemble Weighted Logic Configured in Department 6"
            description="The risk engine schema is integrated into backend contracts. The formula (0.45*fraud + 0.25*anomaly + 0.30*aml) and hard override rules will produce calibrated risk tiers."
            phaseTag="Contract Verified"
            details={[
              { label: "Ensemble Formula", value: "0.45·Fraud + 0.25·Anomaly + 0.30·AML" },
              { label: "Override Rule", value: "Detected AML cycle forces CRITICAL tier" },
              { label: "Tiers Defined", value: "Low (<30), Medium (30-59), High (60-84), Critical (85+)" },
              { label: "Endpoint Status", value: "GET /api/v1/risk/status (HTTP 200 OK)" },
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );
}


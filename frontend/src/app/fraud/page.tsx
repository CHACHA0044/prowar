"use client";

import React from "react";
import { ShieldAlert } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export default function FraudDetectionPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100">
            Supervised Fraud Detection Engine
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Machine learning classifier trained on synthetic behavioral features to flag point-in-time fraud.
          </p>
        </div>

        <Badge variant="neutral">MODEL STATUS: UNTRAINED</Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Supervised Model Pipeline</CardTitle>
          <CardDescription>
            LightGBM classification engine with SHAP explainability layer.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={ShieldAlert}
            title="Model Artifacts Awaiting Phase 3 Implementation"
            description="Supervised fraud detection architecture prepared. During Department 3, the model will be trained on synthetic labeled fraud data using class-imbalance weighting and time-based cross validation."
            phaseTag="Contract Verified"
            details={[
              { label: "Classifier Architecture", value: "LightGBM / Scikit-Learn" },
              { label: "Evaluation Criteria", value: "PR-AUC, F1-Score, Confusion Matrix" },
              { label: "Explainability Interface", value: "SHAP Local Feature Attributions" },
              { label: "Endpoint Status", value: "GET /api/v1/fraud/status (HTTP 200 OK)" },
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import React from "react";
import { Network } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export default function AMLPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100">
            Anti-Money Laundering (AML) Graph Investigation
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Topological money flow analysis: smurfing/structuring, circular laundering cycles, and mule hubs.
          </p>
        </div>

        <Badge variant="neutral">GRAPH ENGINE: MOUNTED</Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Directed Graph Typology Engine</CardTitle>
          <CardDescription>
            NetworkX graph constructs identifying coordinated money movements.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Network}
            title="Typology Detectors Ready for Department 5"
            description="The graph router /api/v1/aml is mounted and ready. Department 5 will build NetworkX directed multigraphs with automated detection of cycles, structuring under ₹50k, and fan-out mule syndicates."
            phaseTag="Contract Verified"
            details={[
              { label: "Graph Library", value: "NetworkX Directed Multigraphs" },
              { label: "Detectors", value: "Cycles, Structuring, Fan-In/Out, Pass-Through" },
              { label: "Privacy Protection", value: "Deterministic Account Masking" },
              { label: "Endpoint Status", value: "GET /api/v1/aml/status (HTTP 200 OK)" },
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );
}


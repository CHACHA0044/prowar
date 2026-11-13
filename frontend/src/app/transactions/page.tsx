"use client";

import React from "react";
import { ArrowLeftRight } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export default function TransactionsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100">
            Transaction Surveillance Stream
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time high-throughput synthetic transaction feed and event ingestion buffer.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="neutral">FEED: INACTIVE (PHASE 1)</Badge>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Stream Ingestion Queue</CardTitle>
              <CardDescription>
                Synthetic financial transactions will be generated and streamed here in Phase 2.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={ArrowLeftRight}
            title="Transaction Stream Ready for Phase 2 Replay"
            description="The REST endpoint /api/v1/transactions is live and schema-validated. Ingestion simulator (5-20 tx/sec) will stream synthetic UPI, Card, and NEFT payments in Department 1 & 8."
            phaseTag="Contract Verified"
            details={[
              { label: "Target Ingestion Rate", value: "10-25 transactions / sec" },
              { label: "Data Pipeline", value: "FastAPI REST + In-memory ring buffer" },
              { label: "Contract Model", value: "TransactionBase (10 mandatory fields)" },
              { label: "Endpoint Status", value: "GET /api/v1/transactions (HTTP 200 OK)" },
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );
}

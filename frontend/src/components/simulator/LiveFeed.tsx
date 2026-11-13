"use client";

import { TransactionResponse } from "@/types/transaction";
import { ChannelBadge } from "@/components/ui/ChannelBadge";
import { maskAccountId, formatINR, formatTimestamp, shortenId } from "@/lib/format";
import { Radio } from "lucide-react";

interface LiveFeedProps {
  events: TransactionResponse[];
  isConnected: boolean;
}

export function LiveFeed({ events, isConnected }: LiveFeedProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden flex flex-col h-[260px]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-950/40">
        <div className="flex items-center gap-2">
          <Radio size={14} className={isConnected ? "text-emerald-400" : "text-slate-500"} />
          <span className="text-sm font-semibold text-slate-300">Live Transaction Stream (SSE)</span>
        </div>
        <span
          className={`flex items-center gap-1.5 text-xs font-mono font-semibold ${
            isConnected ? "text-emerald-400" : "text-slate-500"
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? "bg-emerald-400 animate-pulse" : "bg-slate-600"
            }`}
          />
          {isConnected ? "STREAM ACTIVE" : "OFFLINE"}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 p-1">
        {events.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center text-xs text-slate-500">
            <p>No streamed events yet.</p>
            <p className="mt-1 text-slate-600">Start the replay simulator to stream transactions live.</p>
          </div>
        ) : (
          events.map((tx) => (
            <div
              key={tx.transaction_id}
              className="flex items-center gap-3 px-3 py-2 hover:bg-slate-800/50 transition-colors"
            >
              <ChannelBadge channel={tx.channel} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 text-xs font-mono">
                  <span className="text-indigo-400 font-semibold">{shortenId(tx.transaction_id, 10)}</span>
                  <span className="text-slate-600">·</span>
                  <span className="text-slate-400 truncate">{maskAccountId(tx.sender_account_id)}</span>
                  <span className="text-slate-600">→</span>
                  <span className="text-slate-400 truncate">{maskAccountId(tx.receiver_account_id)}</span>
                </div>
                <span className="text-[11px] text-slate-500">{formatTimestamp(tx.timestamp)}</span>
              </div>
              <span className="text-xs font-mono font-bold text-slate-200 whitespace-nowrap">
                {formatINR(tx.amount)}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

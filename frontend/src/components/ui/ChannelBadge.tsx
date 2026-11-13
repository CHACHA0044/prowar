import React from "react";

const CHANNEL_STYLES: Record<string, string> = {
  UPI: "bg-indigo-500/15 text-indigo-400 border-indigo-500/30",
  CARD: "bg-sky-500/15 text-sky-400 border-sky-500/30",
  NEFT: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  IMPS: "bg-violet-500/15 text-violet-400 border-violet-500/30",
  RTGS: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  WALLET: "bg-pink-500/15 text-pink-400 border-pink-500/30",
  ATM: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  NACH: "bg-teal-500/15 text-teal-400 border-teal-500/30",
};

export function ChannelBadge({ channel }: { channel: string }) {
  const cls = CHANNEL_STYLES[channel.toUpperCase()] || "bg-slate-700/50 text-slate-300 border-slate-600/50";
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-semibold border ${cls}`}
    >
      {channel}
    </span>
  );
}

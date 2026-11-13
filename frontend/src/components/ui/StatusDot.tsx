import React from "react";
import { cn } from "@/lib/utils";

interface StatusDotProps {
  status: "healthy" | "unhealthy" | "degraded" | "warning" | "idle";
  pulse?: boolean;
  className?: string;
}

export function StatusDot({ status, pulse = false, className }: StatusDotProps) {
  const colorMap = {
    healthy: "bg-emerald-500",
    unhealthy: "bg-rose-500",
    degraded: "bg-amber-500",
    warning: "bg-amber-500",
    idle: "bg-slate-500",
  };

  const pulseColorMap = {
    healthy: "bg-emerald-400",
    unhealthy: "bg-rose-400",
    degraded: "bg-amber-400",
    warning: "bg-amber-400",
    idle: "bg-slate-400",
  };

  return (
    <span className={cn("relative inline-flex h-2.5 w-2.5 items-center justify-center", className)}>
      {pulse && (
        <span
          className={cn(
            "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
            pulseColorMap[status]
          )}
        />
      )}
      <span className={cn("relative inline-flex h-2 w-2 rounded-full", colorMap[status])} />
    </span>
  );
}


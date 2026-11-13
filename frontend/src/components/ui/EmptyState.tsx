import React from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";

export interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  phaseTag?: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
  details?: { label: string; value: string }[];
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  phaseTag = "Phase 1 Foundation",
  actionText,
  onAction,
  className,
  details,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-800 bg-slate-900/40 p-8 md:p-12 text-center",
        className
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-800/80 text-sky-400 border border-slate-700/60 mb-4">
        <Icon className="h-7 w-7" />
      </div>

      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-base font-semibold text-slate-100">{title}</h3>
        {phaseTag && <Badge variant="neutral">{phaseTag}</Badge>}
      </div>

      <p className="max-w-md text-xs text-slate-400 leading-relaxed mb-6">
        {description}
      </p>

      {details && details.length > 0 && (
        <div className="w-full max-w-md rounded border border-slate-800 bg-slate-950/60 p-3 mb-6 text-left">
          <p className="text-[11px] font-mono uppercase text-slate-500 mb-2">
            Module Architecture Contract:
          </p>
          <div className="space-y-1">
            {details.map((d, i) => (
              <div key={i} className="flex justify-between text-xs text-slate-300">
                <span className="text-slate-400">{d.label}:</span>
                <span className="font-mono text-sky-400">{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {actionText && onAction && (
        <button
          onClick={onAction}
          className="text-xs text-sky-400 hover:text-sky-300 underline underline-offset-4"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}


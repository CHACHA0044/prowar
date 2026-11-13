"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { X, ShieldCheck } from "lucide-react";
import { NAVIGATION_ITEMS } from "@/components/layout/Sidebar";
import { cn } from "@/lib/utils";

interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MobileNav({ isOpen, onClose }: MobileNavProps) {
  const pathname = usePathname();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div className="fixed inset-y-0 left-0 w-72 bg-slate-950 border-r border-slate-800 p-4 shadow-xl flex flex-col justify-between">
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <span className="font-semibold text-sm text-slate-100">
                SENTINEL<span className="text-sky-400">.AML</span>
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-900"
              aria-label="Close menu"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Links */}
          <nav className="mt-4 space-y-1">
            {NAVIGATION_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-xs font-medium transition-colors",
                    isActive
                      ? "bg-slate-800 text-sky-400 font-semibold border-l-2 border-sky-400"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                  )}
                >
                  <Icon className={cn("h-4 w-4", isActive ? "text-sky-400" : "text-slate-500")} />
                  <span>{item.title}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer info */}
        <div className="border-t border-slate-800 pt-3 text-[11px] text-slate-500 font-mono">
          PromptWars 2026 • Phase 1
        </div>
      </div>
    </div>
  );
}


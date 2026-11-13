import React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export function Button({
  className,
  variant = "primary",
  size = "md",
  disabled,
  children,
  ...props
}: ButtonProps) {
  const baseStyles =
    "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-sky-500 disabled:pointer-events-none disabled:opacity-50 select-none";

  const sizeStyles = {
    sm: "h-8 px-3 text-xs",
    md: "h-9 px-4 text-sm",
    lg: "h-10 px-5 text-base",
  };

  const variantStyles = {
    primary: "bg-sky-500 text-slate-950 hover:bg-sky-400 active:bg-sky-600 font-semibold",
    secondary: "bg-slate-800 text-slate-200 hover:bg-slate-700 active:bg-slate-900 border border-slate-700",
    outline: "border border-slate-700 text-slate-200 hover:bg-slate-800 active:bg-slate-900",
    ghost: "text-slate-300 hover:bg-slate-800/80 active:bg-slate-800",
    danger: "bg-rose-600 text-white hover:bg-rose-500 active:bg-rose-700",
  };

  return (
    <button
      className={cn(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}


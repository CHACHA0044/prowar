"use client";

import { useEffect, useRef, useState } from "react";

interface CountUpProps {
  from?: number;
  to: number;
  duration?: number;
  delay?: number;
  prefix?: string;
  suffix?: string;
  separator?: string;
  decimals?: number;
  className?: string;
}

function formatWithSeparator(n: number, separator: string, decimals: number): string {
  const fixed = n.toFixed(decimals);
  const parts = fixed.split(".");
  const intPart = parts[0] || "0";
  const decPart = parts[1];
  const formatted = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, separator);
  return decimals > 0 && decPart !== undefined ? `${formatted}.${decPart}` : formatted;
}

export function CountUp({
  from = 0,
  to,
  duration = 1800,
  delay = 0,
  prefix = "",
  suffix = "",
  separator = ",",
  decimals = 0,
  className = "",
}: CountUpProps) {
  const [value, setValue] = useState(from);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const prefersReduced =
      typeof window !== "undefined"
        ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
        : false;

    if (prefersReduced) {
      setValue(to);
      return;
    }

    const startTime = performance.now() + delay;
    const range = to - from;

    function animate(now: number) {
      if (now < startTime) {
        rafRef.current = requestAnimationFrame(animate);
        return;
      }
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(from + range * eased);

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      } else {
        setValue(to);
      }
    }

    rafRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [to, from, duration, delay]);

  return (
    <span className={className}>
      {prefix}
      {formatWithSeparator(value, separator, decimals)}
      {suffix}
    </span>
  );
}

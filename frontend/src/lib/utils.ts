import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility for merging Tailwind CSS classes cleanly.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Mask account identifier for analyst safety in UI.
 * e.g., ACC_9876543210 -> ACC_*****3210
 */
export function maskAccountId(accountId: string): string {
  if (!accountId) return "UNKNOWN";
  if (accountId.length <= 6) return `${accountId.slice(0, 2)}***`;
  return `${accountId.slice(0, 4)}***${accountId.slice(-4)}`;
}

/**
 * Currency formatter (INR default).
 */
export function formatCurrency(amount: number, currency: string = "INR"): string {
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: currency,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toFixed(2)}`;
  }
}


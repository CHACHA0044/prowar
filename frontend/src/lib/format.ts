export function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat("en-IN").format(n);
}

export function maskAccountId(id: string): string {
  if (!id || id.length < 5) return id;
  const parts = id.split("_");
  const prefix = parts.length > 1 ? parts[0] : id.substring(0, 3);
  const suffix = id.slice(-4);
  return `${prefix}_****${suffix}`;
}

export function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    if (isNaN(d.getTime())) return ts;
    return d.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

export function shortenId(id: string, maxLen = 14): string {
  if (!id) return "";
  if (id.length <= maxLen) return id;
  return id.substring(0, maxLen) + "…";
}

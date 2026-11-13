import type { Metadata } from "next";
import "@/styles/globals.css";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "Sentinel.AML — Financial Fraud & AML Intelligence Platform",
  description:
    "AI-powered financial security platform for fraud detection, behavioral anomaly surveillance, and anti-money laundering typologies.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-slate-100 antialiased selection:bg-sky-500 selection:text-slate-950">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}


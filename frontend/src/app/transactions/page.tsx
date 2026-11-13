"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";
import { TransactionResponse, TransactionFilter } from "@/types/transaction";
import { transactionService } from "@/services/transactionService";
import { ChannelBadge } from "@/components/ui/ChannelBadge";
import { maskAccountId, formatINR, formatTimestamp, shortenId } from "@/lib/format";

const PAGE_SIZES = [20, 50, 100];
const CHANNELS = ["UPI", "CARD", "NEFT", "IMPS", "RTGS", "WALLET", "ATM", "NACH"];

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<TransactionResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [search, setSearch] = useState("");
  const [channel, setChannel] = useState("");
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");
  const [sortBy, setSortBy] = useState<"timestamp" | "amount" | "transaction_id">("timestamp");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Selected transaction drawer
  const [selectedTx, setSelectedTx] = useState<TransactionResponse | null>(null);

  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchTransactions = useCallback(async (filter: TransactionFilter) => {
    setLoading(true);
    setError(null);
    try {
      const result = await transactionService.list(filter);
      setTransactions(result.items);
      setTotal(result.total);
      setTotalPages(result.total_pages);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load transactions");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const filter: TransactionFilter = {
      limit: pageSize,
      offset: (page - 1) * pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(search && { search }),
      ...(channel && { channel }),
      ...(minAmount && { min_amount: parseFloat(minAmount) }),
      ...(maxAmount && { max_amount: parseFloat(maxAmount) }),
    };
    fetchTransactions(filter);
  }, [page, pageSize, sortBy, sortOrder, channel, minAmount, maxAmount, fetchTransactions]);

  function handleSearchChange(val: string) {
    setSearch(val);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      setPage(1);
      const filter: TransactionFilter = {
        limit: pageSize,
        offset: 0,
        sort_by: sortBy,
        sort_order: sortOrder,
        ...(val && { search: val }),
        ...(channel && { channel }),
        ...(minAmount && { min_amount: parseFloat(minAmount) }),
        ...(maxAmount && { max_amount: parseFloat(maxAmount) }),
      };
      fetchTransactions(filter);
    }, 300);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Transaction Surveillance Explorer</h1>
          <p className="text-sm text-slate-400">
            {total > 0
              ? `${total.toLocaleString("en-IN")} operational records loaded (Server-side paginated)`
              : "Querying financial data repository…"}
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search by TXN ID, sender, receiver…"
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/60 font-mono"
            />
          </div>

          {/* Channel selector */}
          <select
            value={channel}
            onChange={(e) => {
              setChannel(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-300 focus:outline-none focus:border-indigo-500/60"
          >
            <option value="">All Channels</option>
            {CHANNELS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          {/* Sort order */}
          <select
            value={`${sortBy}:${sortOrder}`}
            onChange={(e) => {
              const [by, order] = e.target.value.split(":") as [
                "timestamp" | "amount" | "transaction_id",
                "asc" | "desc"
              ];
              setSortBy(by);
              setSortOrder(order);
              setPage(1);
            }}
            className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-300 focus:outline-none focus:border-indigo-500/60"
          >
            <option value="timestamp:desc">Newest First</option>
            <option value="timestamp:asc">Oldest First</option>
            <option value="amount:desc">Highest Value</option>
            <option value="amount:asc">Lowest Value</option>
          </select>

          {/* Page size */}
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-300 focus:outline-none focus:border-indigo-500/60 font-mono"
          >
            {PAGE_SIZES.map((s) => (
              <option key={s} value={s}>
                {s} / page
              </option>
            ))}
          </select>
        </div>

        {/* Amount filter */}
        <div className="flex items-center gap-2 pt-2 border-t border-slate-800/80">
          <span className="text-xs text-slate-400">Amount Filter (₹):</span>
          <input
            type="number"
            placeholder="Min"
            value={minAmount}
            onChange={(e) => {
              setMinAmount(e.target.value);
              setPage(1);
            }}
            className="w-28 px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          />
          <span className="text-slate-600 text-xs">to</span>
          <input
            type="number"
            placeholder="Max"
            value={maxAmount}
            onChange={(e) => {
              setMaxAmount(e.target.value);
              setPage(1);
            }}
            className="w-28 px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>
      </div>

      {/* Transaction Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden">
        {loading ? (
          <div className="p-16 text-center text-sm text-slate-500 font-mono">
            Loading transaction batch…
          </div>
        ) : error ? (
          <div className="p-16 text-center text-sm text-red-400">{error}</div>
        ) : transactions.length === 0 ? (
          <div className="p-16 text-center text-sm text-slate-500">
            No transactions match the selected filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    TXN ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Sender Account
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Receiver Account
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Amount
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Channel
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Category
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Device
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {transactions.map((tx) => (
                  <tr
                    key={tx.transaction_id}
                    onClick={() => setSelectedTx(tx)}
                    className="hover:bg-slate-800/50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 text-indigo-400 font-semibold">
                      {shortenId(tx.transaction_id, 12)}
                    </td>
                    <td className="px-4 py-3 text-slate-400">
                      {maskAccountId(tx.sender_account_id)}
                    </td>
                    <td className="px-4 py-3 text-slate-400">
                      {maskAccountId(tx.receiver_account_id)}
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-slate-200">
                      {formatINR(tx.amount)}
                    </td>
                    <td className="px-4 py-3 font-sans">
                      <ChannelBadge channel={tx.channel} />
                    </td>
                    <td className="px-4 py-3 text-slate-300 font-sans capitalize">
                      {tx.merchant_category}
                    </td>
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                      {formatTimestamp(tx.timestamp)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {tx.device_id ? (
                        <span className="text-emerald-400 font-bold" title={tx.device_id}>
                          ●
                        </span>
                      ) : (
                        <span className="text-slate-600" title="Device unknown">
                          ○
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {!loading && !error && total > 0 && (
          <div className="border-t border-slate-800 px-4 py-3 flex items-center justify-between bg-slate-950/40">
            <span className="text-xs text-slate-400 font-mono">
              Showing page {page} of {totalPages} ({total.toLocaleString("en-IN")} total)
            </span>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={15} />
              </button>
              <span className="text-xs text-slate-300 px-2 font-mono">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight size={15} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Transaction Detail Drawer */}
      {selectedTx && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm"
          onClick={() => setSelectedTx(null)}
        >
          <div
            className="w-full max-w-md h-full bg-slate-900 border-l border-slate-800 shadow-2xl p-6 overflow-y-auto space-y-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-base font-bold text-slate-100">Transaction Details</h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  ID: {selectedTx.transaction_id}
                </p>
              </div>
              <button
                onClick={() => setSelectedTx(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4 font-mono text-xs">
              <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2">
                <span className="text-[11px] font-sans text-slate-400 uppercase font-semibold">
                  Financial Movement
                </span>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-400">Amount:</span>
                  <span className="text-lg font-bold text-emerald-400">
                    {formatINR(selectedTx.amount)} {selectedTx.currency}
                  </span>
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>Channel:</span>
                  <ChannelBadge channel={selectedTx.channel} />
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>Status:</span>
                  <span className="text-emerald-400 font-semibold">
                    {selectedTx.transaction_status}
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2">
                <span className="text-[11px] font-sans text-slate-400 uppercase font-semibold">
                  Counterparties
                </span>
                <div className="flex justify-between">
                  <span className="text-slate-400">Sender Account:</span>
                  <span className="text-slate-200">{maskAccountId(selectedTx.sender_account_id)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Receiver Account:</span>
                  <span className="text-slate-200">{maskAccountId(selectedTx.receiver_account_id)}</span>
                </div>
                {selectedTx.sender_balance_before !== null &&
                  selectedTx.sender_balance_before !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">Sender Prior Balance:</span>
                      <span className="text-slate-300">
                        {formatINR(selectedTx.sender_balance_before)}
                      </span>
                    </div>
                  )}
              </div>

              <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2">
                <span className="text-[11px] font-sans text-slate-400 uppercase font-semibold">
                  Audit Telemetry
                </span>
                <div className="flex justify-between">
                  <span className="text-slate-400">Merchant / Category:</span>
                  <span className="text-slate-200 capitalize">
                    {selectedTx.merchant_category}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Location Origin:</span>
                  <span className="text-slate-200">{selectedTx.location || "Online"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Device Fingerprint:</span>
                  <span className="text-slate-200">{selectedTx.device_id || "Unregistered"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Timestamp:</span>
                  <span className="text-slate-200">{formatTimestamp(selectedTx.timestamp)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { SimulatorEvent, SimulatorStatus } from "@/types/simulator";
import { TransactionResponse } from "@/types/transaction";
import { simulatorService } from "@/services/simulatorService";

const MAX_EVENTS = 50;
const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 30000;

export function useSimulatorStream() {
  const [events, setEvents] = useState<TransactionResponse[]>([]);
  const [status, setStatus] = useState<SimulatorStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectDelay = useRef(RECONNECT_BASE_MS);

  const connect = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
    }
    const es = new EventSource(simulatorService.getStreamUrl());
    esRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
      setError(null);
      reconnectDelay.current = RECONNECT_BASE_MS;
    };

    es.onmessage = (e) => {
      try {
        const event: SimulatorEvent = JSON.parse(e.data);
        if (event.status) {
          setStatus(event.status);
        }
        if (event.event_type === "TRANSACTION" && event.data) {
          setEvents((prev) => [event.data!, ...prev].slice(0, MAX_EVENTS));
        }
      } catch {
        // Safe parse skip
      }
    };

    es.onerror = () => {
      setIsConnected(false);
      es.close();
      esRef.current = null;
      const delay = reconnectDelay.current;
      reconnectDelay.current = Math.min(delay * 2, RECONNECT_MAX_MS);
      reconnectTimer.current = setTimeout(connect, delay);
      setError("Stream disconnected. Reconnecting...");
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (esRef.current) {
        esRef.current.close();
      }
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
    };
  }, [connect]);

  return { events, status, isConnected, error };
}

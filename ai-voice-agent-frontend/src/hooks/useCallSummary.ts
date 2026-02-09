"use client";

import { useCallback, useState } from "react";
import { CallSummaryData } from "../lib/types";

export function useCallSummary() {
  const [summary, setSummary] = useState<CallSummaryData | null>(null);

  const onDataReceived = useCallback((payload: Uint8Array) => {
    try {
      const text = new TextDecoder().decode(payload);
      const data: CallSummaryData = JSON.parse(text);
      setSummary(data);
    } catch (e) {
      console.error("Failed to parse call summary:", e);
    }
  }, []);

  const clearSummary = useCallback(() => {
    setSummary(null);
  }, []);

  return { summary, onDataReceived, clearSummary };
}

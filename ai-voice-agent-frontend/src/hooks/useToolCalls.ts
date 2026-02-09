"use client";

import { useCallback, useState } from "react";
import { ToolCallEvent } from "../lib/types";

export function useToolCalls() {
  const [toolCalls, setToolCalls] = useState<ToolCallEvent[]>([]);

  const onDataReceived = useCallback((payload: Uint8Array) => {
    try {
      const text = new TextDecoder().decode(payload);
      const event: ToolCallEvent = JSON.parse(text);

      setToolCalls((prev) => {
        if (event.status === "completed" || event.status === "error") {
          // Replace the matching "started" entry with the completed one
          const idx = prev.findIndex(
            (tc) =>
              tc.tool_name === event.tool_name && tc.status === "started"
          );
          if (idx !== -1) {
            const updated = [...prev];
            updated[idx] = event;
            return updated;
          }
        }
        // Append new event (started, or completed without a matching started)
        return [...prev, event];
      });
    } catch (e) {
      console.error("Failed to parse tool call event:", e);
    }
  }, []);

  const clearToolCalls = useCallback(() => {
    setToolCalls([]);
  }, []);

  return { toolCalls, onDataReceived, clearToolCalls };
}

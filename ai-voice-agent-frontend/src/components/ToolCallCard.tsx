"use client";

import { ToolCallEvent } from "../lib/types";
import { formatToolName, getToolColor, formatRelativeTime } from "../lib/utils";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";

interface ToolCallCardProps {
  event: ToolCallEvent;
}

export function ToolCallCard({ event }: ToolCallCardProps) {
  const isStarted = event.status === "started";
  const isCompleted = event.status === "completed";
  const isError = event.status === "error";

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getToolColor(event.tool_name)}`}
        >
          {formatToolName(event.tool_name)}
        </span>
        <div className="flex items-center gap-1.5">
          {isStarted && (
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
          )}
          {isCompleted && (
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          )}
          {isError && <AlertCircle className="h-4 w-4 text-red-500" />}
          <span className="text-xs text-gray-400">
            {formatRelativeTime(event.timestamp)}
          </span>
        </div>
      </div>

      {/* Arguments */}
      {Object.keys(event.arguments).length > 0 && (
        <div className="mb-2">
          <p className="text-xs font-medium text-gray-500 mb-1">Arguments</p>
          <div className="text-xs bg-gray-50 rounded p-2 font-mono">
            {Object.entries(event.arguments).map(([key, value]) => (
              <div key={key}>
                <span className="text-gray-500">{key}:</span>{" "}
                <span className="text-gray-800">
                  {typeof value === "string" ? value : JSON.stringify(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Result */}
      {isCompleted && event.result && (
        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">Result</p>
          <pre className="text-xs bg-green-50 rounded p-2 font-mono overflow-x-auto max-h-32 overflow-y-auto text-green-800">
            {JSON.stringify(event.result, null, 2)}
          </pre>
        </div>
      )}

      {/* Error */}
      {isError && event.result && (
        <div>
          <p className="text-xs font-medium text-red-500 mb-1">Error</p>
          <pre className="text-xs bg-red-50 rounded p-2 font-mono text-red-800">
            {JSON.stringify(event.result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

"use client";

import { CallSummaryData, ToolCallEvent } from "../lib/types";
import { formatToolName, getToolColor } from "../lib/utils";
import { CheckCircle2, Phone, X } from "lucide-react";

interface CallSummaryProps {
  summary: CallSummaryData;
  toolCalls: ToolCallEvent[];
  onDisconnect: () => void;
}

export function CallSummary({
  summary,
  toolCalls,
  onDisconnect,
}: CallSummaryProps) {
  const completedTools = toolCalls.filter((tc) => tc.status === "completed");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-500 to-emerald-500 px-6 py-4 flex items-center gap-3">
          <CheckCircle2 className="h-6 w-6 text-white" />
          <h2 className="text-lg font-semibold text-white">Call Summary</h2>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Summary text */}
          <div className="mb-5">
            <p className="text-gray-700 leading-relaxed">{summary.summary}</p>
          </div>

          {/* Tools used */}
          {completedTools.length > 0 && (
            <div className="mb-5">
              <p className="text-xs font-medium text-gray-500 mb-2">
                Actions performed ({completedTools.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {completedTools.map((tc, i) => (
                  <span
                    key={i}
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getToolColor(tc.tool_name)}`}
                  >
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    {formatToolName(tc.tool_name)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Disconnect button */}
          <button
            onClick={onDisconnect}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-red-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-600 transition-colors"
          >
            <Phone className="h-4 w-4" />
            End Call
          </button>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef } from "react";
import { ToolCallEvent } from "../lib/types";
import { ToolCallCard } from "./ToolCallCard";
import { Wrench } from "lucide-react";

interface ToolCallPanelProps {
  toolCalls: ToolCallEvent[];
}

export function ToolCallPanel({ toolCalls }: ToolCallPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest tool call
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [toolCalls]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200">
        <Wrench className="h-4 w-4 text-gray-600" />
        <h2 className="text-sm font-semibold text-gray-700">Tool Calls</h2>
        {toolCalls.length > 0 && (
          <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
            {toolCalls.length}
          </span>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2">
        {toolCalls.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Wrench className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No tool calls yet</p>
            <p className="text-xs">
              Tool calls will appear here as the agent works
            </p>
          </div>
        ) : (
          toolCalls.map((event, index) => (
            <ToolCallCard key={`${event.tool_name}-${index}`} event={event} />
          ))
        )}
      </div>
    </div>
  );
}

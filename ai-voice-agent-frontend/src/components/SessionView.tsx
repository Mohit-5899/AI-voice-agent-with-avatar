"use client";

import { useEffect } from "react";
import {
  useDataChannel,
  useConnectionState,
  useRoomContext,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { ToolCallEvent, CallSummaryData } from "../lib/types";
import { useToolCalls } from "../hooks/useToolCalls";
import { useCallSummary } from "../hooks/useCallSummary";
import { AvatarDisplay } from "./AvatarDisplay";
import { TranscriptPanel } from "./TranscriptPanel";
import { ToolCallPanel } from "./ToolCallPanel";
import { CallSummary } from "./CallSummary";
import { RoomAudioRenderer } from "@livekit/components-react";
import { Phone } from "lucide-react";

interface SessionViewProps {
  onDisconnect: () => void;
}

export function SessionView({ onDisconnect }: SessionViewProps) {
  const room = useRoomContext();
  const connectionState = useConnectionState();
  const { toolCalls, onDataReceived: onToolData } = useToolCalls();
  const { summary, onDataReceived: onSummaryData } = useCallSummary();

  // Subscribe to tool_call data channel
  useDataChannel("tool_call", (msg) => {
    onToolData(msg.payload);
  });

  // Subscribe to call_summary data channel
  useDataChannel("call_summary", (msg) => {
    onSummaryData(msg.payload);
  });

  const handleDisconnect = () => {
    room.disconnect();
    onDisconnect();
  };

  if (connectionState === ConnectionState.Connecting) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Connecting to Dr. Ava...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Render audio from all participants */}
      <RoomAudioRenderer />

      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm font-medium text-gray-700">
            Dr. Ava - Appointment Assistant
          </span>
        </div>
        <button
          onClick={handleDisconnect}
          className="flex items-center gap-1.5 rounded-lg bg-red-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-600 transition-colors"
        >
          <Phone className="h-3.5 w-3.5" />
          End Call
        </button>
      </div>

      {/* Main content grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-0 overflow-hidden">
        {/* Left panel: Avatar + Transcript */}
        <div className="lg:col-span-2 flex flex-col overflow-hidden">
          {/* Avatar */}
          <div className="p-4 pb-2">
            <AvatarDisplay />
          </div>

          {/* Transcript */}
          <div className="flex-1 overflow-hidden border-t border-gray-200 mt-2">
            <TranscriptPanel />
          </div>
        </div>

        {/* Right panel: Tool calls */}
        <div className="border-l border-gray-200 bg-white overflow-hidden">
          <ToolCallPanel toolCalls={toolCalls} />
        </div>
      </div>

      {/* Call summary modal */}
      {summary && (
        <CallSummary
          summary={summary}
          toolCalls={toolCalls}
          onDisconnect={handleDisconnect}
        />
      )}
    </div>
  );
}

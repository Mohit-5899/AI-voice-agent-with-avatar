"use client";

import {
  useVoiceAssistant,
  VideoTrack,
  BarVisualizer,
} from "@livekit/components-react";
import { User } from "lucide-react";

export function AvatarDisplay() {
  const { agent, state, videoTrack, audioTrack } = useVoiceAssistant();

  // If agent has a video track (Tavus avatar), render it
  if (videoTrack) {
    return (
      <div className="relative w-full aspect-video rounded-xl overflow-hidden bg-gray-900">
        <VideoTrack
          trackRef={videoTrack}
          className="w-full h-full object-cover"
        />
        {/* State indicator */}
        <div className="absolute bottom-3 left-3">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-black/50 px-2.5 py-1 text-xs text-white backdrop-blur-sm">
            <span
              className={`h-2 w-2 rounded-full ${
                state === "speaking"
                  ? "bg-green-400 animate-pulse"
                  : state === "thinking"
                    ? "bg-yellow-400 animate-pulse"
                    : state === "listening"
                      ? "bg-blue-400"
                      : "bg-gray-400"
              }`}
            />
            {state === "speaking"
              ? "Speaking"
              : state === "thinking"
                ? "Thinking"
                : state === "listening"
                  ? "Listening"
                  : "Idle"}
          </span>
        </div>
      </div>
    );
  }

  // Fallback: audio-only with visualizer
  return (
    <div className="relative w-full aspect-video rounded-xl overflow-hidden bg-gradient-to-br from-gray-800 to-gray-900 flex flex-col items-center justify-center">
      {/* Avatar placeholder */}
      <div className="w-20 h-20 rounded-full bg-gray-700 flex items-center justify-center mb-4">
        <User className="h-10 w-10 text-gray-400" />
      </div>
      <p className="text-white text-sm font-medium mb-1">Dr. Ava</p>
      <p className="text-gray-400 text-xs mb-4">Appointment Assistant</p>

      {/* Audio visualizer */}
      {audioTrack && (
        <div className="w-48 h-12">
          <BarVisualizer
            trackRef={audioTrack}
            barCount={24}
            className="w-full h-full"
            options={{ minHeight: 2 }}
          />
        </div>
      )}

      {/* State indicator */}
      <div className="absolute bottom-3 left-3">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-black/50 px-2.5 py-1 text-xs text-white backdrop-blur-sm">
          <span
            className={`h-2 w-2 rounded-full ${
              state === "speaking"
                ? "bg-green-400 animate-pulse"
                : state === "thinking"
                  ? "bg-yellow-400 animate-pulse"
                  : state === "listening"
                    ? "bg-blue-400"
                    : "bg-gray-400"
            }`}
          />
          {state === "speaking"
            ? "Speaking"
            : state === "thinking"
              ? "Thinking"
              : state === "listening"
                ? "Listening"
                : agent
                  ? "Idle"
                  : "Connecting..."}
        </span>
      </div>
    </div>
  );
}

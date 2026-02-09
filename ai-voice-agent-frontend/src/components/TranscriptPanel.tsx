"use client";

import { useEffect, useRef } from "react";
import { useTranscriptions } from "@livekit/components-react";
import { MessageSquare } from "lucide-react";

export function TranscriptPanel() {
  const transcriptions = useTranscriptions();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcriptions]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200">
        <MessageSquare className="h-4 w-4 text-gray-600" />
        <h2 className="text-sm font-semibold text-gray-700">Transcript</h2>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2">
        {transcriptions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <MessageSquare className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">Waiting for conversation...</p>
            <p className="text-xs">Start speaking to see the transcript</p>
          </div>
        ) : (
          transcriptions.map((entry, index) => {
            const isAgent = !entry.participantInfo.identity.startsWith("user");
            return (
              <div
                key={index}
                className={`flex ${isAgent ? "justify-start" : "justify-end"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                    isAgent
                      ? "bg-gray-100 text-gray-800"
                      : "bg-blue-500 text-white"
                  }`}
                >
                  <p className="text-xs font-medium opacity-70 mb-0.5">
                    {isAgent ? "Dr. Ava" : "You"}
                  </p>
                  <p>{entry.text}</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

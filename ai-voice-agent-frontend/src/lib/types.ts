export interface ToolCallEvent {
  tool_name: string;
  status: "started" | "completed" | "error";
  arguments: Record<string, unknown>;
  result: Record<string, unknown> | null;
  timestamp: string;
}

export interface CallSummaryData {
  summary: string;
}

export type ConnectionState = "welcome" | "connecting" | "connected" | "summary";
